"use client";

export function ChartSkeleton({ height = "h-56" }: { height?: string }) {
  return (
    <div className={`${height} w-full flex items-center justify-center bg-muted/30 rounded-lg animate-pulse`}>
      <div className="text-sm text-muted-foreground">加载图表中...</div>
    </div>
  );
}
