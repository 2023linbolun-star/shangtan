"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search, Package, FileText, Send, Truck, Headphones, BarChart3,
  ArrowRight, AlertCircle, ChevronRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/shared/metric-card";
import { AutoReviewToggle } from "@/components/shared/auto-review-toggle";
import { AutonomousLoopViz } from "@/components/cockpit/autonomous-loop";
import { ActivityFeed } from "@/components/cockpit/activity-feed";
import { ReviewQueue, type ReviewItem } from "@/components/cockpit/review-queue";
import { LaunchControl } from "@/components/cockpit/launch-control";
import { useAutopilotStore } from "@/stores/autopilot-store";

// 模块快捷操作配置
const MODULE_ACTIONS: Record<string, {
  icon: any; label: string; href: string;
  action: string; actionHref: string;
}> = {
  discovery: {
    icon: Search, label: "趋势发现", href: "/discovery",
    action: "查看待确认", actionHref: "/discovery",
  },
  evaluation: {
    icon: Package, label: "在管商品", href: "/products",
    action: "审核商品", actionHref: "/products",
  },
  content: {
    icon: FileText, label: "内容工厂", href: "/content",
    action: "创作内容", actionHref: "/content",
  },
  publishing: {
    icon: Send, label: "发布中心", href: "/publishing",
    action: "查看排期", actionHref: "/publishing",
  },
  sourcing: {
    icon: Truck, label: "订单履约", href: "/orders",
    action: "处理异常", actionHref: "/orders",
  },
  customer_service: {
    icon: Headphones, label: "AI客服", href: "/cs",
    action: "查看对话", actionHref: "/cs",
  },
  analytics: {
    icon: BarChart3, label: "数据分析", href: "/analytics",
    action: "查看报表", actionHref: "/analytics",
  },
};

export default function CockpitPage() {
  const router = useRouter();
  const { globalMode, setGlobalMode, modules, setModuleMode } = useAutopilotStore();
  const [reviewItems] = useState<ReviewItem[]>([]);

  const totalPendingReviews = modules.reduce((sum, m) => sum + m.pendingReviewCount, 0);
  const runningCount = modules.filter((m) => m.status === "running").length;

  return (
    <div className="space-y-6">
      {/* 启动/暂停控制 */}
      <LaunchControl />

      {/* Status Bar */}
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${globalMode === 'auto' ? 'bg-green-400' : 'bg-gray-400'} opacity-75`} />
            <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${globalMode === 'auto' ? 'bg-green-500' : 'bg-gray-500'}`} />
          </span>
          <span className="text-muted-foreground">{globalMode === 'auto' ? 'AI 运行中' : 'AI 已暂停'}</span>
        </div>
        <span className="text-muted-foreground">|</span>
        <span className="text-muted-foreground">{runningCount} 个进程运行中</span>
        <span className="text-muted-foreground">|</span>
        <span className="text-green-400 font-mono">&yen;0 <span className="text-xs text-muted-foreground">今日营收</span></span>
        {totalPendingReviews > 0 && (
          <>
            <span className="text-muted-foreground">|</span>
            <span className="text-amber-400">{totalPendingReviews} 项待审核</span>
          </>
        )}
      </div>

      {/* Autonomous Loop Visualization */}
      <Card className="border-border/50">
        <CardContent className="pt-6">
          <AutonomousLoopViz />
        </CardContent>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard label="今日营收" value="0" prefix="¥" trend={0} />
        <MetricCard label="今日利润" value="0" prefix="¥" trend={0} />
        <MetricCard label="在管商品" value="0" />
        <MetricCard label="已发内容" value="0" />
        <MetricCard label="订单数" value="0" />
        <MetricCard label="转化率" value="0%" />
      </div>

      {/* 模块控制网格 — 带操作入口 */}
      <Card className="border-border/50">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">模块控制</CardTitle>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground">全局模式</span>
              <AutoReviewToggle mode={globalMode} onChange={setGlobalMode} size="sm" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {modules.map((m) => {
              const config = MODULE_ACTIONS[m.id];
              if (!config) return null;

              const Icon = config.icon;
              const isRunning = m.status === "running";
              const isReview = m.status === "awaiting_review";

              return (
                <div
                  key={m.id}
                  className={`rounded-xl border p-4 transition-all group ${
                    isRunning
                      ? "border-cyan-500/30 shadow-[0_0_15px_oklch(0.75_0.15_195/0.15)]"
                      : isReview
                      ? "border-amber-500/30 shadow-[0_0_15px_oklch(0.78_0.18_80/0.15)]"
                      : "border-border/50"
                  }`}
                >
                  {/* 顶部：图标+名称+状态 */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Icon className={`h-4 w-4 ${isRunning ? 'text-cyan-400' : 'text-muted-foreground'}`} />
                      <span className="text-sm font-medium">{config.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {m.pendingReviewCount > 0 && (
                        <span className="flex items-center justify-center h-5 min-w-[20px] px-1 rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-bold">
                          {m.pendingReviewCount}
                        </span>
                      )}
                      <AutoReviewToggle
                        mode={m.mode}
                        onChange={(mode) => setModuleMode(m.id, mode)}
                        size="sm"
                      />
                    </div>
                  </div>

                  {/* 状态文字 */}
                  <p className="text-xs text-muted-foreground mb-3">{m.statusText}</p>

                  {/* 操作按钮 */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs h-7 flex-1 border-border/50 hover:border-cyan-500/30 hover:text-cyan-400"
                      onClick={() => router.push(config.actionHref)}
                    >
                      {config.action}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs h-7 px-2 text-muted-foreground hover:text-foreground"
                      onClick={() => router.push(config.href)}
                    >
                      <ChevronRight className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Activity Feed + Review Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">实时活动</CardTitle>
          </CardHeader>
          <CardContent>
            <ActivityFeed />
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">待审核</CardTitle>
              {totalPendingReviews > 0 && (
                <Badge className="bg-amber-500/20 text-amber-400 text-xs">
                  {totalPendingReviews}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <ReviewQueue items={reviewItems} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
