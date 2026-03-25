"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, MessageSquare, Loader2, ArrowRight, Sparkles, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { MetricCard } from "@/components/shared/metric-card";

const ACTIONABLE_INSIGHTS: Array<{ text: string; action: { label: string; route: string } | null }> = [];

function AiQuestionInput() {
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiAsking, setAiAsking] = useState(false);
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);

  const handleAskAI = () => {
    if (!aiQuestion.trim()) return;
    setAiAsking(true);
    setAiAnswer(null);
    setTimeout(() => {
      setAiAnswer("暂无数据，请先录入商品并产生销售数据后再进行分析。");
      setAiAsking(false);
    }, 500);
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 rounded-lg border border-border/50 bg-background/50 px-3 py-2 text-xs placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
          placeholder="问AI：为什么转化率下降了？"
          value={aiQuestion}
          onChange={(e) => setAiQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAskAI()}
          disabled={aiAsking}
        />
        <Button
          size="sm"
          className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs px-4"
          onClick={handleAskAI}
          disabled={aiAsking || !aiQuestion.trim()}
        >
          {aiAsking ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "提问"}
        </Button>
      </div>
      {aiAsking && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>AI 正在分析数据...</span>
        </div>
      )}
      {aiAnswer && (
        <div className="rounded-lg border border-cyan-500/20 bg-cyan-950/30 p-3">
          <div className="flex items-start gap-2">
            <Sparkles className="h-3.5 w-3.5 text-cyan-400 mt-0.5 shrink-0" />
            <p className="text-xs leading-relaxed text-foreground/90">{aiAnswer}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const router = useRouter();

  return (
    <ModulePageLayout
      moduleId="analytics"
      title="数据分析"
      autoView={
        <AutoModePanel
          moduleId="analytics"
          icon={<BarChart3 className="h-5 w-5" />}
          description="每日自动汇总销售数据，计算单品经济模型，生成加量/淘汰建议"
          quickActions={<AiQuestionInput />}
          metrics={[
            { label: "本周营收", value: "¥0" },
            { label: "本周利润", value: "¥0" },
            { label: "平均利润率", value: "-" },
            { label: "退货率", value: "-" },
          ]}
          recentActions={[]}
        />
      }
      reviewView={
        <div className="space-y-5">
          {/* M7-A2: AI Data Q&A */}
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-4">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="h-4 w-4 text-cyan-400" />
              <h3 className="text-sm font-medium text-cyan-300">AI 数据问答</h3>
            </div>
            <AiQuestionInput />
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="总营收" value="¥0" />
            <MetricCard label="总利润" value="¥0" />
            <MetricCard label="订单数" value="0" />
            <MetricCard label="退货率" value="-" />
          </div>

          {/* Per-product economics */}
          <div className="rounded-xl border border-border/50 p-4">
            <h3 className="text-sm font-medium mb-3">单品经济模型</h3>
            <div className="text-center py-6 text-sm text-muted-foreground">
              暂无商品数据，请先录入商品并产生销售数据
            </div>
          </div>

          {/* M7-B2 & M7-C1: AI Insights with actionable buttons */}
          <div className="rounded-xl border border-border/50 p-4">
            <h3 className="text-sm font-medium mb-3">AI 周报摘要</h3>
            <div className="space-y-2.5">
              {ACTIONABLE_INSIGHTS.map((insight, i) => (
                <div key={i} className="flex items-start justify-between gap-3">
                  <p className="text-xs text-muted-foreground leading-relaxed">- {insight.text}</p>
                  {insight.action && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="shrink-0 h-6 px-2 text-[11px] text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/30 gap-1"
                      onClick={() => router.push(insight.action!.route)}
                    >
                      {insight.action.label}
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      }
    />
  );
}
