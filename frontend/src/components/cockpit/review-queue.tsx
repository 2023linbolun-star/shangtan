"use client";

import { Button } from "@/components/ui/button";
import { CheckCircle2, Eye, X, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ReviewItem {
  id: string;
  type: string;
  title: string;
  description: string;
  module: string;
  urgency: "low" | "medium" | "high";
  createdAt: string;
}

interface ReviewQueueProps {
  items: ReviewItem[];
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onPreview?: (id: string) => void;
}

const URGENCY_BORDER: Record<string, string> = {
  low: "border-l-green-500/50",
  medium: "border-l-amber-500/50",
  high: "border-l-red-500/50",
};

export function ReviewQueue({ items, onApprove, onReject, onPreview }: ReviewQueueProps) {
  if (items.length === 0) {
    return (
      <div className="text-center py-6 text-muted-foreground text-sm">
        没有待审核项目
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className={cn(
            "rounded-lg border border-border/50 bg-card p-4 border-l-4",
            URGENCY_BORDER[item.urgency]
          )}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {item.type}
                </span>
                <Clock className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  {new Date(item.createdAt).toLocaleString("zh-CN")}
                </span>
              </div>
              <p className="text-sm font-medium">{item.title}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{item.description}</p>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {onPreview && (
                <Button size="sm" variant="ghost" onClick={() => onPreview(item.id)} className="h-8 w-8 p-0">
                  <Eye className="h-3.5 w-3.5" />
                </Button>
              )}
              {onApprove && (
                <Button size="sm" variant="ghost" onClick={() => onApprove(item.id)} className="h-8 w-8 p-0 text-green-400 hover:text-green-300">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                </Button>
              )}
              {onReject && (
                <Button size="sm" variant="ghost" onClick={() => onReject(item.id)} className="h-8 w-8 p-0 text-red-400 hover:text-red-300">
                  <X className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
