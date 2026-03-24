"use client";

import { AutoReviewToggle } from "@/components/shared/auto-review-toggle";
import { useAutopilotStore, type ModuleMode } from "@/stores/autopilot-store";
import { Loader2, Clock } from "lucide-react";

interface ModulePageLayoutProps {
  moduleId: string;
  title: string;
  autoView: React.ReactNode;
  reviewView: React.ReactNode;
}

/**
 * v2.0 模块页面统一布局：自动/审核双视图。
 * - 自动模式：监控面板（AI正在运行 + 最近动作日志 + 指标）
 * - 审核模式：交互面板（审核队列 + 操作UI）
 */
export function ModulePageLayout({ moduleId, title, autoView, reviewView }: ModulePageLayoutProps) {
  const modules = useAutopilotStore((s) => s.modules);
  const setModuleMode = useAutopilotStore((s) => s.setModuleMode);

  const mod = modules.find((m) => m.id === moduleId);
  const mode: ModuleMode = mod?.mode || "review";
  const isRunning = mod?.status === "running";

  return (
    <div className="space-y-5">
      {/* Header: title + mode toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold">{title}</h1>
          {isRunning && (
            <div className="flex items-center gap-1.5 text-cyan-400 text-xs">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>运行中</span>
            </div>
          )}
          {!isRunning && mod?.statusText && (
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {mod.statusText}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            {mode === "auto" ? "AI 自主运行" : "需审核确认"}
          </span>
          <AutoReviewToggle
            mode={mode}
            onChange={(m) => setModuleMode(moduleId, m)}
            size="sm"
          />
        </div>
      </div>

      {/* Content: auto or review view */}
      {mode === "auto" ? autoView : reviewView}
    </div>
  );
}

/**
 * 自动模式的通用监控面板。
 */
export function AutoModePanel({
  moduleId,
  icon,
  description,
  metrics,
  recentActions,
  onManualTrigger,
}: {
  moduleId: string;
  icon: React.ReactNode;
  description: string;
  metrics?: { label: string; value: string | number }[];
  recentActions?: { time: string; text: string }[];
  onManualTrigger?: () => void;
}) {
  return (
    <div className="space-y-4">
      {/* Status card */}
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-5 flex items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400">
          {icon}
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium">AI 正在自主运行此模块</p>
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        </div>
        {onManualTrigger && (
          <button
            onClick={onManualTrigger}
            className="text-xs text-cyan-400 hover:text-cyan-300 border border-cyan-500/30 rounded-lg px-3 py-1.5 transition-colors"
          >
            手动触发
          </button>
        )}
      </div>

      {/* Metrics */}
      {metrics && metrics.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {metrics.map((m) => (
            <div key={m.label} className="rounded-lg border border-border/50 p-3">
              <p className="text-xs text-muted-foreground">{m.label}</p>
              <p className="text-lg font-bold font-mono tabular-nums mt-0.5">{m.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Recent actions log */}
      {recentActions && recentActions.length > 0 && (
        <div className="rounded-xl border border-border/50 p-4">
          <h3 className="text-sm font-medium mb-3">最近 AI 动作</h3>
          <div className="space-y-2">
            {recentActions.map((action, i) => (
              <div key={i} className="flex items-start gap-3 text-xs">
                <span className="text-muted-foreground font-mono shrink-0">{action.time}</span>
                <span className="text-foreground/80">{action.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
