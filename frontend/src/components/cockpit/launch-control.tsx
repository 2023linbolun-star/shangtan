"use client";

import { useState } from "react";
import { Rocket, Pause, Play, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAutopilotStore } from "@/stores/autopilot-store";

export function LaunchControl() {
  const { globalMode, setGlobalMode } = useAutopilotStore();
  const [loading, setLoading] = useState(false);
  const isRunning = globalMode === "auto";

  const handleToggle = async () => {
    setLoading(true);
    try {
      setGlobalMode(isRunning ? "review" : "auto");
    } finally {
      setTimeout(() => setLoading(false), 500);
    }
  };

  if (isRunning) {
    return (
      <div className="rounded-2xl border border-cyan-500/30 bg-cyan-500/5 p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="h-3 w-3 rounded-full bg-cyan-400" />
              <div className="absolute inset-0 h-3 w-3 rounded-full bg-cyan-400 animate-ping opacity-30" />
            </div>
            <div>
              <div className="text-sm font-medium text-cyan-400">AI 自动驾驶运行中</div>
              <div className="text-xs text-muted-foreground">系统正在自动扫描趋势、生成内容、处理订单...</div>
            </div>
          </div>
          <Button
            onClick={handleToggle}
            disabled={loading}
            variant="outline"
            className="border-amber-500/30 text-amber-400 hover:bg-amber-500/10 hover:text-amber-300"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Pause className="h-4 w-4 mr-2" />}
            暂停全部
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border/50 bg-gradient-to-r from-cyan-500/5 to-indigo-500/5 p-6 mb-6">
      <div className="flex flex-col items-center gap-4">
        <div className="text-center">
          <h2 className="text-lg font-bold mb-1">AI 自动驾驶</h2>
          <p className="text-sm text-muted-foreground">一键启动，AI自动完成选品、内容、发布全流程</p>
        </div>
        <Button
          onClick={handleToggle}
          disabled={loading}
          size="lg"
          className="bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white px-8 py-3 text-base shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] transition-all"
        >
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
          ) : (
            <Rocket className="h-5 w-5 mr-2" />
          )}
          启动 AI 自动驾驶
        </Button>
      </div>
    </div>
  );
}
