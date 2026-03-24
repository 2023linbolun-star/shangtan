"use client";

import { Search, TrendingUp, Zap, Filter } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

export default function DiscoveryPage() {
  return (
    <ModulePageLayout
      moduleId="discovery"
      title="趋势发现"
      autoView={
        <AutoModePanel
          moduleId="discovery"
          icon={<Search className="h-5 w-5" />}
          description="每4小时自动扫描抖音热搜、百度指数、淘宝搜索趋势，发现商品机会"
          metrics={[
            { label: "今日扫描", value: "3 次" },
            { label: "发现趋势", value: 12 },
            { label: "已送评估", value: 5 },
            { label: "下次扫描", value: "2h后" },
          ]}
          recentActions={[
            { time: "14:32", text: "发现上升品类: 冰丝防晒衣 (+340% 搜索量)" },
            { time: "14:31", text: "发现上升品类: 便携风扇 (+180% 搜索量)" },
            { time: "10:15", text: "扫描完成: 12个上升趋势，3个送入评估" },
            { time: "06:12", text: "定时扫描: 抖音热搜 + 百度指数 + 季节性日历" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          {/* Trend cards for review */}
          <div className="text-sm text-muted-foreground">
            系统发现的趋势机会，选择要送入评估的品类：
          </div>
          {[
            { keyword: "冰丝防晒衣", score: 92, growth: "+340%", source: "抖音热搜", platforms: ["douyin", "xhs"] },
            { keyword: "便携风扇", score: 78, growth: "+180%", source: "百度指数", platforms: ["taobao", "pdd"] },
            { keyword: "遮阳帽女", score: 71, growth: "+120%", source: "季节性日历", platforms: ["douyin", "xhs", "taobao"] },
            { keyword: "防蚊手环", score: 65, growth: "+95%", source: "淘宝趋势", platforms: ["pdd", "taobao"] },
          ].map((trend) => (
            <div
              key={trend.keyword}
              className="rounded-xl border border-border/50 p-4 flex items-center gap-4 hover:border-cyan-500/30 transition-colors"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-cyan-500/10">
                <TrendingUp className="h-5 w-5 text-cyan-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{trend.keyword}</span>
                  <Badge variant="outline" className="text-xs text-green-400 border-green-500/30">
                    {trend.growth}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-muted-foreground">{trend.source}</span>
                  <span className="text-xs text-muted-foreground">·</span>
                  <span className="text-xs text-muted-foreground">机会评分 {trend.score}/100</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 transition-colors">
                  送入评估
                </button>
                <button className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50 transition-colors">
                  跳过
                </button>
              </div>
            </div>
          ))}
        </div>
      }
    />
  );
}
