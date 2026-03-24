"use client";

import { cn } from "@/lib/utils";

interface AutoReviewToggleProps {
  mode: "auto" | "review";
  onChange: (mode: "auto" | "review") => void;
  size?: "sm" | "md";
  className?: string;
}

export function AutoReviewToggle({ mode, onChange, size = "md", className }: AutoReviewToggleProps) {
  const isAuto = mode === "auto";
  const sizeClasses = size === "sm" ? "text-xs h-7" : "text-sm h-9";

  return (
    <div
      className={cn(
        "inline-flex rounded-lg p-0.5 border border-border/50",
        isAuto ? "bg-cyan-950/30" : "bg-amber-950/30",
        className
      )}
    >
      <button
        onClick={() => onChange("auto")}
        className={cn(
          "px-3 rounded-md font-medium transition-all duration-200",
          sizeClasses,
          isAuto
            ? "bg-cyan-500/20 text-cyan-400 shadow-[0_0_12px_oklch(0.75_0.15_195/0.3)]"
            : "text-muted-foreground hover:text-foreground"
        )}
      >
        自动
      </button>
      <button
        onClick={() => onChange("review")}
        className={cn(
          "px-3 rounded-md font-medium transition-all duration-200",
          sizeClasses,
          !isAuto
            ? "bg-amber-500/20 text-amber-400 shadow-[0_0_12px_oklch(0.78_0.18_80/0.3)]"
            : "text-muted-foreground hover:text-foreground"
        )}
      >
        审核
      </button>
    </div>
  );
}
