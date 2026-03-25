"use client";

import { useState } from "react";
import { Headphones, MessageSquare, AlertTriangle, CheckCircle2, User, Edit3, Send, Plus, Trash2, BookOpen, Truck, Package as PackageIcon, MessageCircle, ChevronDown, ChevronUp, X } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

const CONVERSATIONS: Array<{ customer: string; product: string; question: string; reply: string | null; confidence: number; autoSent: boolean }> = [];

const ORDER_INFO: Record<number, { orderId: string; status: string; courier: string; trackingNo: string }> = {};

const INITIAL_FAQS: Array<{ id: number; question: string; answer: string }> = [];

const GENERAL_SCRIPTS = [
  "亲，感谢您的咨询！有任何问题随时联系我们~",
  "非常抱歉给您带来不便，我们会尽快为您处理！",
  "感谢您的耐心等待，问题已为您解决，祝您购物愉快！",
];

function UrgentConversations() {
  const urgent = CONVERSATIONS.filter((c) => c.confidence < 0.7);
  const [replies, setReplies] = useState<Record<number, string>>({});
  const [sent, setSent] = useState<Record<number, boolean>>({});

  if (urgent.length === 0) {
    return <div className="text-xs text-muted-foreground">暂无需要人工处理的对话</div>;
  }

  return (
    <div className="space-y-3">
      {urgent.map((conv, i) => (
        <div key={i} className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 space-y-2">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-3 w-3 text-red-400" />
            <span className="text-xs text-muted-foreground">{conv.customer}</span>
            <Badge variant="outline" className="text-[10px]">{conv.product}</Badge>
            <Badge variant="outline" className="text-[10px] text-red-400 border-red-500/30">
              置信度 {(conv.confidence * 100).toFixed(0)}%
            </Badge>
          </div>
          <p className="text-xs"><span className="text-muted-foreground">客户：</span>{conv.question}</p>
          {sent[i] ? (
            <div className="text-xs text-green-400 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" /> 已回复
            </div>
          ) : (
            <div className="flex gap-2">
              <input
                type="text"
                value={replies[i] || ""}
                onChange={(e) => setReplies({ ...replies, [i]: e.target.value })}
                placeholder="输入回复..."
                className="flex-1 text-xs rounded-lg border border-border/50 bg-background px-2 py-1.5 outline-none focus:border-cyan-500/50"
              />
              <button
                onClick={() => { if (replies[i]?.trim()) setSent({ ...sent, [i]: true }); }}
                className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-2 py-1 hover:bg-cyan-500/10 flex items-center gap-1"
              >
                <Send className="h-3 w-3" /> 发送
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function CSPage() {
  const [editingReplyIndex, setEditingReplyIndex] = useState<number | null>(null);
  const [editedReply, setEditedReply] = useState("");
  const [humanReplies, setHumanReplies] = useState<Record<number, string>>({});
  const [faqList, setFaqList] = useState(INITIAL_FAQS);
  const [showAddFaq, setShowAddFaq] = useState(false);
  const [newFaq, setNewFaq] = useState({ question: "", answer: "" });
  const [editingFaqId, setEditingFaqId] = useState<number | null>(null);
  const [editingFaqData, setEditingFaqData] = useState({ question: "", answer: "" });
  const [expandedLogistics, setExpandedLogistics] = useState<Record<number, boolean>>({});
  const [sentReplies, setSentReplies] = useState<Record<number, string>>({});

  const sortedConversations = [...CONVERSATIONS].sort((a, b) => a.confidence - b.confidence);

  const handleAddFaq = () => {
    if (!newFaq.question.trim() || !newFaq.answer.trim()) return;
    setFaqList([...faqList, { id: Date.now(), question: newFaq.question, answer: newFaq.answer }]);
    setNewFaq({ question: "", answer: "" });
    setShowAddFaq(false);
  };

  const handleDeleteFaq = (id: number) => {
    setFaqList(faqList.filter(f => f.id !== id));
  };

  const handleStartEditFaq = (faq: typeof INITIAL_FAQS[0]) => {
    setEditingFaqId(faq.id);
    setEditingFaqData({ question: faq.question, answer: faq.answer });
  };

  const handleSaveEditFaq = () => {
    if (!editingFaqData.question.trim() || !editingFaqData.answer.trim()) return;
    setFaqList(faqList.map(f => f.id === editingFaqId ? { ...f, ...editingFaqData } : f));
    setEditingFaqId(null);
  };

  return (
    <ModulePageLayout
      moduleId="customer_service"
      title="AI客服"
      autoView={
        <AutoModePanel
          moduleId="customer_service"
          icon={<Headphones className="h-5 w-5" />}
          description="置信度>0.9自动回复，0.7-0.9建议确认，<0.7转人工。投诉类永不自动回复"
          quickActions={<UrgentConversations />}
          metrics={[
            { label: "今日咨询", value: 0 },
            { label: "自动回复", value: 0 },
            { label: "待确认", value: 0 },
            { label: "转人工", value: 0 },
          ]}
          recentActions={[]}
        />
      }
      reviewView={
        <Tabs defaultValue="conversations">
          <TabsList className="w-full">
            <TabsTrigger value="conversations" className="text-xs flex-1">
              <MessageCircle className="h-3.5 w-3.5 mr-1" />
              对话列表
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="text-xs flex-1">
              <BookOpen className="h-3.5 w-3.5 mr-1" />
              知识库
            </TabsTrigger>
          </TabsList>

          {/* ===== 对话列表 Tab ===== */}
          <TabsContent value="conversations" className="mt-4">
            <div className="space-y-4">
              <div className="text-sm text-muted-foreground">客户咨询列表——按置信度排序，低置信度优先处理：</div>
              {sortedConversations.map((conv, i) => {
                const originalIndex = CONVERSATIONS.indexOf(conv);
                const order = ORDER_INFO[originalIndex];
                const logisticsOpen = expandedLogistics[originalIndex] ?? false;

                return (
                  <div key={i} className="rounded-xl border border-border/50 p-4">
                    {/* Header */}
                    <div className="flex items-center gap-2 mb-2">
                      <User className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">{conv.customer}</span>
                      <Badge variant="outline" className="text-[10px]">{conv.product}</Badge>
                      <Badge
                        variant="outline"
                        className={`text-[10px] ${
                          conv.confidence >= 0.9
                            ? "text-green-400 border-green-500/30"
                            : conv.confidence >= 0.7
                            ? "text-amber-400 border-amber-500/30"
                            : "text-red-400 border-red-500/30"
                        }`}
                      >
                        置信度 {(conv.confidence * 100).toFixed(0)}%
                      </Badge>
                      {conv.autoSent && (
                        <Badge variant="outline" className="text-[10px] text-green-400 border-green-500/30">已自动发送</Badge>
                      )}
                    </div>

                    {/* Customer question */}
                    <div className="bg-card/50 rounded-lg p-3 mb-2">
                      <p className="text-sm"><span className="text-muted-foreground">客户：</span>{conv.question}</p>
                    </div>

                    {/* AI reply or human needed */}
                    {conv.reply ? (
                      sentReplies[originalIndex] ? (
                        <div className="bg-cyan-500/5 border border-cyan-500/10 rounded-lg p-3">
                          <p className="text-sm"><span className="text-muted-foreground">AI回复（已编辑）：</span>{sentReplies[originalIndex]}</p>
                        </div>
                      ) : editingReplyIndex === originalIndex ? (
                        <div className="space-y-2">
                          <Textarea
                            value={editedReply}
                            onChange={(e) => setEditedReply(e.target.value)}
                            className="text-sm min-h-[80px] border-cyan-500/20 focus:border-cyan-500/40"
                            placeholder="编辑AI回复..."
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                setSentReplies({ ...sentReplies, [originalIndex]: editedReply });
                                setEditingReplyIndex(null);
                              }}
                              className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 flex items-center gap-1"
                            >
                              <Send className="h-3 w-3" />
                              发送修改后的回复
                            </button>
                            <button
                              onClick={() => setEditingReplyIndex(null)}
                              className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50 flex items-center gap-1"
                            >
                              <X className="h-3 w-3" />
                              取消
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-cyan-500/5 border border-cyan-500/10 rounded-lg p-3 group/reply relative">
                          <p className="text-sm"><span className="text-muted-foreground">AI回复：</span>{conv.reply}</p>
                          <button
                            onClick={() => {
                              setEditingReplyIndex(originalIndex);
                              setEditedReply(conv.reply!);
                            }}
                            className="absolute top-2 right-2 text-xs text-muted-foreground hover:text-cyan-400 border border-border/50 hover:border-cyan-500/30 rounded-md px-2 py-1 flex items-center gap-1 opacity-0 group-hover/reply:opacity-100 transition-opacity"
                          >
                            <Edit3 className="h-3 w-3" />
                            编辑
                          </button>
                        </div>
                      )
                    ) : (
                      <div className="space-y-2">
                        <div className="bg-red-500/5 border border-red-500/10 rounded-lg p-3 flex items-center gap-2">
                          <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
                          <p className="text-sm text-red-400">需要人工处理（涉及售后/投诉）</p>
                        </div>
                        {/* M6-B2: Human reply input */}
                        {sentReplies[originalIndex] ? (
                          <div className="bg-cyan-500/5 border border-cyan-500/10 rounded-lg p-3">
                            <p className="text-sm"><span className="text-muted-foreground">人工回复：</span>{sentReplies[originalIndex]}</p>
                            <Badge variant="outline" className="text-[10px] text-green-400 border-green-500/30 mt-1">已发送</Badge>
                          </div>
                        ) : (
                          <div className="border border-border/50 rounded-lg p-3 space-y-2">
                            <Textarea
                              value={humanReplies[originalIndex] || ""}
                              onChange={(e) => setHumanReplies({ ...humanReplies, [originalIndex]: e.target.value })}
                              className="text-sm min-h-[60px] border-border/30"
                              placeholder="输入人工回复..."
                            />
                            <button
                              onClick={() => {
                                if (!humanReplies[originalIndex]?.trim()) return;
                                setSentReplies({ ...sentReplies, [originalIndex]: humanReplies[originalIndex] });
                              }}
                              className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 flex items-center gap-1"
                            >
                              <Send className="h-3 w-3" />
                              发送回复
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Action buttons row */}
                    {!conv.autoSent && conv.reply && !sentReplies[originalIndex] && editingReplyIndex !== originalIndex && (
                      <div className="mt-2 flex gap-2">
                        <button className="text-xs border border-green-500/30 text-green-400 rounded-lg px-3 py-1.5 hover:bg-green-500/10">
                          确认发送
                        </button>
                        <button
                          onClick={() => {
                            setEditingReplyIndex(originalIndex);
                            setEditedReply(conv.reply!);
                          }}
                          className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50"
                        >
                          编辑后发送
                        </button>
                      </div>
                    )}

                    {/* M6-C1: Logistics quick action */}
                    <div className="mt-3 pt-3 border-t border-border/30">
                      <button
                        onClick={() => setExpandedLogistics({ ...expandedLogistics, [originalIndex]: !logisticsOpen })}
                        className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50 flex items-center gap-1"
                      >
                        <Truck className="h-3 w-3" />
                        查询物流
                        {logisticsOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      </button>
                      {logisticsOpen && order && (
                        <div className="mt-2 bg-card/50 rounded-lg p-3 grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-muted-foreground">订单号：</span>
                            <span className="font-mono">{order.orderId}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">物流状态：</span>
                            <Badge variant="outline" className={`text-[10px] ${
                              order.status === "已签收" ? "text-green-400 border-green-500/30" :
                              order.status === "已发货" ? "text-cyan-400 border-cyan-500/30" :
                              "text-amber-400 border-amber-500/30"
                            }`}>{order.status}</Badge>
                          </div>
                          <div>
                            <span className="text-muted-foreground">快递公司：</span>
                            <span>{order.courier}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">运单号：</span>
                            <span className="font-mono">{order.trackingNo}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </TabsContent>

          {/* ===== 知识库 Tab ===== */}
          <TabsContent value="knowledge" className="mt-4">
            <div className="space-y-6">
              {/* FAQ Section */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium flex items-center gap-1.5">
                    <MessageSquare className="h-3.5 w-3.5 text-cyan-400" />
                    FAQ列表
                  </h3>
                  <button
                    onClick={() => setShowAddFaq(true)}
                    className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 flex items-center gap-1"
                  >
                    <Plus className="h-3 w-3" />
                    添加FAQ
                  </button>
                </div>

                {/* Add FAQ form */}
                {showAddFaq && (
                  <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 mb-3 space-y-3">
                    <Textarea
                      value={newFaq.question}
                      onChange={(e) => setNewFaq({ ...newFaq, question: e.target.value })}
                      className="text-sm min-h-[40px] border-border/30"
                      placeholder="输入常见问题..."
                    />
                    <Textarea
                      value={newFaq.answer}
                      onChange={(e) => setNewFaq({ ...newFaq, answer: e.target.value })}
                      className="text-sm min-h-[60px] border-border/30"
                      placeholder="输入标准回复..."
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleAddFaq}
                        className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10"
                      >
                        保存
                      </button>
                      <button
                        onClick={() => { setShowAddFaq(false); setNewFaq({ question: "", answer: "" }); }}
                        className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50"
                      >
                        取消
                      </button>
                    </div>
                  </div>
                )}

                {/* FAQ list */}
                <div className="space-y-2">
                  {faqList.map((faq) => (
                    <div key={faq.id} className="rounded-xl border border-border/50 p-3">
                      {editingFaqId === faq.id ? (
                        <div className="space-y-2">
                          <Textarea
                            value={editingFaqData.question}
                            onChange={(e) => setEditingFaqData({ ...editingFaqData, question: e.target.value })}
                            className="text-sm min-h-[40px] border-border/30"
                          />
                          <Textarea
                            value={editingFaqData.answer}
                            onChange={(e) => setEditingFaqData({ ...editingFaqData, answer: e.target.value })}
                            className="text-sm min-h-[60px] border-border/30"
                          />
                          <div className="flex gap-2">
                            <button onClick={handleSaveEditFaq} className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10">保存</button>
                            <button onClick={() => setEditingFaqId(null)} className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50">取消</button>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-medium">Q: {faq.question}</p>
                            <div className="flex items-center gap-1 shrink-0">
                              <button
                                onClick={() => handleStartEditFaq(faq)}
                                className="text-muted-foreground hover:text-cyan-400 p-1 rounded-md hover:bg-muted/50"
                              >
                                <Edit3 className="h-3 w-3" />
                              </button>
                              <button
                                onClick={() => handleDeleteFaq(faq.id)}
                                className="text-muted-foreground hover:text-red-400 p-1 rounded-md hover:bg-muted/50"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">A: {faq.answer}</p>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* General Scripts Section */}
              <div>
                <h3 className="text-sm font-medium flex items-center gap-1.5 mb-3">
                  <BookOpen className="h-3.5 w-3.5 text-cyan-400" />
                  通用话术
                </h3>
                <div className="space-y-2">
                  {GENERAL_SCRIPTS.map((script, i) => (
                    <div key={i} className="rounded-xl border border-border/50 p-3 flex items-center justify-between gap-2">
                      <p className="text-xs text-muted-foreground">{script}</p>
                      <button className="text-muted-foreground hover:text-cyan-400 p-1 rounded-md hover:bg-muted/50 shrink-0">
                        <Edit3 className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      }
    />
  );
}
