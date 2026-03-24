"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/shared/metric-card";
import { AutoReviewToggle } from "@/components/shared/auto-review-toggle";
import { AutonomousLoopViz } from "@/components/cockpit/autonomous-loop";
import { ActivityFeed } from "@/components/cockpit/activity-feed";
import { ReviewQueue, type ReviewItem } from "@/components/cockpit/review-queue";
import { useAutopilotStore } from "@/stores/autopilot-store";

export default function CockpitPage() {
  const { globalMode, setGlobalMode, modules, setModuleMode } = useAutopilotStore();

  // Mock review items for now
  const [reviewItems] = useState<ReviewItem[]>([]);

  const totalPendingReviews = modules.reduce((sum, m) => sum + m.pendingReviewCount, 0);
  const runningCount = modules.filter((m) => m.status === "running").length;

  return (
    <div className="space-y-6">
      {/* Status Bar */}
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
          </span>
          <span className="text-muted-foreground">AI 运行中</span>
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

      {/* Module Grid with Auto/Review Toggles */}
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
              const isRunning = m.status === "running";
              const isReview = m.status === "awaiting_review";
              return (
                <div
                  key={m.id}
                  className={`rounded-lg border p-3 transition-all ${
                    isRunning
                      ? "border-cyan-500/30 shadow-[0_0_15px_oklch(0.75_0.15_195/0.15)]"
                      : isReview
                      ? "border-amber-500/30 shadow-[0_0_15px_oklch(0.78_0.18_80/0.15)]"
                      : "border-border/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{m.name}</span>
                    <AutoReviewToggle
                      mode={m.mode}
                      onChange={(mode) => setModuleMode(m.id, mode)}
                      size="sm"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">{m.statusText}</p>
                  {m.pendingReviewCount > 0 && (
                    <Badge variant="outline" className="mt-2 text-xs text-amber-400 border-amber-500/30">
                      {m.pendingReviewCount} 项待审核
                    </Badge>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Activity Feed + Review Queue side by side on large screens */}
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
