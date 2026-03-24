"use client";

import { AutoReviewToggle } from "./auto-review-toggle";
import { Badge } from "@/components/ui/badge";

interface ModuleHeaderProps {
  title: string;
  subtitle: string;
  mode: "auto" | "review";
  onModeChange: (mode: "auto" | "review") => void;
  stats?: { label: string; value: number | string }[];
}

export function ModuleHeader({ title, subtitle, mode, onModeChange, stats }: ModuleHeaderProps) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-muted-foreground text-sm mt-1">{subtitle}</p>
        {stats && stats.length > 0 && (
          <div className="flex gap-3 mt-3">
            {stats.map((s) => (
              <Badge key={s.label} variant="outline" className="text-xs gap-1.5 py-1 px-2.5">
                <span className="text-muted-foreground">{s.label}</span>
                <span className="font-mono font-medium">{s.value}</span>
              </Badge>
            ))}
          </div>
        )}
      </div>
      <AutoReviewToggle mode={mode} onChange={onModeChange} />
    </div>
  );
}
