"use client";

import { Package, TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

const MOCK_PRODUCTS = [
  { name: "冰丝防晒衣", platform: "抖音", status: "active", stage: "加量", sales: 47, revenue: 3290, margin: "42%", daysListed: 14 },
  { name: "便携风扇USB", platform: "拼多多", status: "active", stage: "维持", sales: 8, revenue: 320, margin: "35%", daysListed: 7 },
  { name: "瑜伽裤高腰", platform: "小红书", status: "content_ready", stage: "内容就绪", sales: 0, revenue: 0, margin: "48%", daysListed: 0 },
  { name: "运动水壶", platform: "淘宝", status: "declining", stage: "待淘汰", sales: 1, revenue: 39, margin: "12%", daysListed: 14 },
];

const STAGE_COLORS: Record<string, string> = {
  "加量": "text-green-400 border-green-500/30 bg-green-500/10",
  "维持": "text-cyan-400 border-cyan-500/30 bg-cyan-500/10",
  "内容就绪": "text-indigo-400 border-indigo-500/30 bg-indigo-500/10",
  "待淘汰": "text-red-400 border-red-500/30 bg-red-500/10",
};

export default function ProductsPage() {
  return (
    <ModulePageLayout
      moduleId="evaluation"
      title="在管商品"
      autoView={
        <AutoModePanel
          moduleId="evaluation"
          icon={<Package className="h-5 w-5" />}
          description="自动监控所有在管商品表现，7天后自动做出加量/维持/淘汰决策"
          metrics={[
            { label: "在管商品", value: 4 },
            { label: "今日营收", value: "¥3,649" },
            { label: "加量中", value: 1 },
            { label: "待淘汰", value: 1 },
          ]}
          recentActions={[
            { time: "14:00", text: "\"冰丝防晒衣\" 7天47单，净利率42%，决策: 加量" },
            { time: "14:00", text: "\"运动水壶\" 7天1单，净利率12%，决策: 待淘汰" },
            { time: "13:30", text: "\"便携风扇USB\" 数据采集完成，7天后评估" },
            { time: "10:00", text: "\"瑜伽裤高腰\" 内容生成完成，等待发布" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">所有在管商品及其生命周期状态：</div>
          {MOCK_PRODUCTS.map((p) => (
            <div key={p.name} className="rounded-xl border border-border/50 p-4 flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{p.name}</span>
                  <Badge variant="outline" className="text-[10px]">{p.platform}</Badge>
                  <Badge variant="outline" className={`text-[10px] ${STAGE_COLORS[p.stage] || ""}`}>
                    {p.stage}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span>销量 {p.sales}</span>
                  <span>营收 ¥{p.revenue}</span>
                  <span>利润率 {p.margin}</span>
                  <span>{p.daysListed > 0 ? `上架 ${p.daysListed} 天` : "未上架"}</span>
                </div>
              </div>
              {p.stage === "待淘汰" && (
                <div className="flex gap-2">
                  <button className="text-xs border border-red-500/30 text-red-400 rounded-lg px-3 py-1.5 hover:bg-red-500/10">
                    确认淘汰
                  </button>
                  <button className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50">
                    再观察
                  </button>
                </div>
              )}
              {p.stage === "加量" && (
                <button className="text-xs border border-green-500/30 text-green-400 rounded-lg px-3 py-1.5 hover:bg-green-500/10">
                  查看加量计划
                </button>
              )}
            </div>
          ))}
        </div>
      }
    />
  );
}
