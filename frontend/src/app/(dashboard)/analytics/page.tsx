"use client";

import { BarChart3, TrendingUp, TrendingDown, DollarSign } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { MetricCard } from "@/components/shared/metric-card";

export default function AnalyticsPage() {
  return (
    <ModulePageLayout
      moduleId="analytics"
      title="数据分析"
      autoView={
        <AutoModePanel
          moduleId="analytics"
          icon={<BarChart3 className="h-5 w-5" />}
          description="每日自动汇总销售数据，计算单品经济模型，生成加量/淘汰建议"
          metrics={[
            { label: "本周营收", value: "¥8,420" },
            { label: "本周利润", value: "¥3,280" },
            { label: "平均利润率", value: "38.9%" },
            { label: "退货率", value: "8.2%" },
          ]}
          recentActions={[
            { time: "03:00", text: "每日数据同步完成，5个商品数据已更新" },
            { time: "03:01", text: "生成日报: 营收¥1,680, 利润¥654, 新增订单12" },
            { time: "03:02", text: "决策建议: 冰丝防晒衣→加量, 运动水壶→淘汰" },
            { time: "03:03", text: "反馈闭环: 2条AI决策结果已回流学习引擎" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-5">
          {/* Key metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard label="总营收" value="¥8,420" trend={12.3} />
            <MetricCard label="总利润" value="¥3,280" trend={8.5} />
            <MetricCard label="订单数" value="56" trend={15.2} />
            <MetricCard label="退货率" value="8.2%" trend={-2.1} />
          </div>

          {/* Per-product economics */}
          <div className="rounded-xl border border-border/50 p-4">
            <h3 className="text-sm font-medium mb-3">单品经济模型</h3>
            <div className="space-y-3">
              {[
                { name: "冰丝防晒衣", revenue: 3290, cost: 742, shipping: 235, commission: 329, returns: 165, profit: 1819, decision: "加量" },
                { name: "便携风扇USB", revenue: 320, cost: 100, shipping: 32, commission: 32, returns: 0, profit: 156, decision: "维持" },
                { name: "运动水壶", revenue: 39, cost: 18, shipping: 6, commission: 4, returns: 0, profit: 11, decision: "淘汰" },
              ].map((p) => (
                <div key={p.name} className="flex items-center gap-4 text-xs">
                  <span className="w-24 font-medium text-sm">{p.name}</span>
                  <span className="text-muted-foreground">营收 ¥{p.revenue}</span>
                  <span className="text-muted-foreground">- 采购 ¥{p.cost}</span>
                  <span className="text-muted-foreground">- 运费 ¥{p.shipping}</span>
                  <span className="text-muted-foreground">- 佣金 ¥{p.commission}</span>
                  <span className="text-muted-foreground">- 退货 ¥{p.returns}</span>
                  <span className="text-muted-foreground">=</span>
                  <span className={`font-medium ${p.profit > 100 ? "text-green-400" : p.profit > 0 ? "text-cyan-400" : "text-red-400"}`}>
                    净利 ¥{p.profit}
                  </span>
                  <span className={`ml-auto font-medium ${p.decision === "加量" ? "text-green-400" : p.decision === "淘汰" ? "text-red-400" : "text-cyan-400"}`}>
                    {p.decision}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* AI Insights */}
          <div className="rounded-xl border border-border/50 p-4">
            <h3 className="text-sm font-medium mb-3">AI 周报摘要</h3>
            <div className="text-xs text-muted-foreground space-y-1.5">
              <p>- 冰丝防晒衣表现优异，建议增加抖音视频发布频率至每日2条</p>
              <p>- 运动水壶14天仅1单，净利率12%低于阈值15%，建议淘汰</p>
              <p>- 本周AI内容生成18条，用户修改率5.6%（低），内容质量稳定</p>
              <p>- 建议下周关注品类：防蚊用品（季节性上升 +200%）</p>
            </div>
          </div>
        </div>
      }
    />
  );
}
