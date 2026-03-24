"use client";

import { Headphones, MessageSquare, AlertTriangle, CheckCircle2, User } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

const CONVERSATIONS = [
  { customer: "用户***8821", product: "冰丝防晒衣", question: "请问有M码吗？", reply: "您好，有的！M码对应身高155-165cm，体重90-110斤。", confidence: 0.95, autoSent: true },
  { customer: "用户***3456", product: "冰丝防晒衣", question: "发什么快递？多久能到？", reply: "我们发圆通快递，一般2-3天到达。如需其他快递可以备注。", confidence: 0.88, autoSent: false },
  { customer: "用户***7789", product: "便携风扇USB", question: "我收到的风扇不转了，要退货", reply: null, confidence: 0.3, autoSent: false },
];

export default function CSPage() {
  return (
    <ModulePageLayout
      moduleId="customer_service"
      title="AI客服"
      autoView={
        <AutoModePanel
          moduleId="customer_service"
          icon={<Headphones className="h-5 w-5" />}
          description="置信度>0.9自动回复，0.7-0.9建议确认，<0.7转人工。投诉类永不自动回复"
          metrics={[
            { label: "今日咨询", value: 12 },
            { label: "自动回复", value: 8 },
            { label: "待确认", value: 3 },
            { label: "转人工", value: 1 },
          ]}
          recentActions={[
            { time: "15:20", text: "[自动回复] \"请问有M码吗\" → 已自动发送 (置信度 0.95)" },
            { time: "15:15", text: "[待确认] \"发什么快递\" → 生成回复待你确认 (置信度 0.88)" },
            { time: "14:50", text: "[转人工] \"风扇不转了要退货\" → 涉及售后，转人工处理" },
            { time: "14:30", text: "[自动回复] \"能开发票吗\" → 已自动发送 (置信度 0.92)" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">客户咨询列表——按置信度排序，低置信度优先处理：</div>
          {CONVERSATIONS.sort((a, b) => a.confidence - b.confidence).map((conv, i) => (
            <div key={i} className="rounded-xl border border-border/50 p-4">
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
              <div className="bg-card/50 rounded-lg p-3 mb-2">
                <p className="text-sm"><span className="text-muted-foreground">客户：</span>{conv.question}</p>
              </div>
              {conv.reply ? (
                <div className="bg-cyan-500/5 border border-cyan-500/10 rounded-lg p-3">
                  <p className="text-sm"><span className="text-muted-foreground">AI回复：</span>{conv.reply}</p>
                </div>
              ) : (
                <div className="bg-red-500/5 border border-red-500/10 rounded-lg p-3 flex items-center gap-2">
                  <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
                  <p className="text-sm text-red-400">需要人工处理（涉及售后/投诉）</p>
                </div>
              )}
              {!conv.autoSent && conv.reply && (
                <div className="mt-2 flex gap-2">
                  <button className="text-xs border border-green-500/30 text-green-400 rounded-lg px-3 py-1.5 hover:bg-green-500/10">
                    确认发送
                  </button>
                  <button className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50">
                    编辑后发送
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      }
    />
  );
}
