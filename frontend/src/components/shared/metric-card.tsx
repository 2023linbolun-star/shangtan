"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string | number;
  prefix?: string;
  trend?: number; // percentage change
  className?: string;
}

export function MetricCard({ label, value, prefix, trend, className }: MetricCardProps) {
  const trendColor = trend === undefined ? "" : trend > 0 ? "text-green-400" : trend < 0 ? "text-red-400" : "text-muted-foreground";
  const TrendIcon = trend === undefined ? null : trend > 0 ? TrendingUp : trend < 0 ? TrendingDown : Minus;

  return (
    <div className={cn(
      "rounded-xl border border-border/50 bg-card p-4 transition-colors hover:bg-card/80",
      className
    )}>
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <div className="flex items-baseline gap-1.5">
        {prefix && <span className="text-sm text-muted-foreground">{prefix}</span>}
        <span className="text-2xl font-bold font-mono tabular-nums">{value}</span>
      </div>
      {trend !== undefined && (
        <div className={cn("flex items-center gap-1 mt-1 text-xs", trendColor)}>
          {TrendIcon && <TrendIcon className="h-3 w-3" />}
          <span>{trend > 0 ? "+" : ""}{trend.toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}
