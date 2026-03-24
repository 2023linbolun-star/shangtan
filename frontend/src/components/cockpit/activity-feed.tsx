"use client";

import { useActivityStore, type ActivityEntry } from "@/stores/activity-store";
import { cn } from "@/lib/utils";

const MODULE_COLORS: Record<string, string> = {
  discovery: "text-cyan-400 bg-cyan-400/10",
  evaluation: "text-blue-400 bg-blue-400/10",
  sourcing: "text-purple-400 bg-purple-400/10",
  content: "text-pink-400 bg-pink-400/10",
  publishing: "text-green-400 bg-green-400/10",
  customer_service: "text-amber-400 bg-amber-400/10",
  analytics: "text-indigo-400 bg-indigo-400/10",
};

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function EntryRow({ entry }: { entry: ActivityEntry }) {
  const colorClass = MODULE_COLORS[entry.module] || "text-muted-foreground bg-muted/10";
  return (
    <div className="flex items-start gap-3 py-2 px-3 text-sm animate-[fade-slide-in_0.3s_ease-out]">
      <span className="font-mono text-xs text-muted-foreground whitespace-nowrap mt-0.5">
        {formatTime(entry.timestamp)}
      </span>
      <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap", colorClass)}>
        {entry.moduleName}
      </span>
      <span className="text-foreground/80 leading-relaxed">{entry.message}</span>
    </div>
  );
}

export function ActivityFeed() {
  const entries = useActivityStore((s) => s.entries);

  if (entries.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground text-sm">
        AI 系统就绪，等待启动...
      </div>
    );
  }

  return (
    <div className="max-h-[320px] overflow-y-auto space-y-0.5 scrollbar-thin">
      {entries.map((entry) => (
        <EntryRow key={entry.id} entry={entry} />
      ))}
    </div>
  );
}
