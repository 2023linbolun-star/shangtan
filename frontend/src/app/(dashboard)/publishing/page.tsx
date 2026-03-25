"use client";

import { Send, Video, FileText, Copy, CheckCircle2 } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

const PUBLISH_QUEUE: Array<{ title: string; platform: string; method: string; status: string; time: string }> = [];

const METHOD_COLORS: Record<string, string> = {
  "API自动发布": "text-green-400 border-green-500/30",
  "一键复制包": "text-amber-400 border-amber-500/30",
  "CSV数据包": "text-amber-400 border-amber-500/30",
};

export default function PublishingPage() {
  return (
    <ModulePageLayout
      moduleId="publishing"
      title="发布中心"
      autoView={
        <AutoModePanel
          moduleId="publishing"
          icon={<Send className="h-5 w-5" />}
          description="API平台（抖音/公众号）自动发布，手动平台生成一键复制包并推送通知"
          metrics={[
            { label: "今日已发布", value: 0 },
            { label: "排期中", value: 0 },
            { label: "待手动发布", value: 0 },
            { label: "本周总发布", value: 0 },
          ]}
          recentActions={[]}
        />
      }
      reviewView={
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">发布队列——API平台自动发布，手动平台需你操作：</div>
          {PUBLISH_QUEUE.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">暂无待发布内容</div>
          ) : null}
          {PUBLISH_QUEUE.map((item, i) => (
            <div key={i} className="rounded-xl border border-border/50 p-4 flex items-center gap-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-card">
                {item.platform === "抖音" ? <Video className="h-4 w-4 text-muted-foreground" /> : <FileText className="h-4 w-4 text-muted-foreground" />}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">{item.title}</p>
                <div className="flex items-center gap-2 mt-1">
                  <Badge variant="outline" className="text-[10px]">{item.platform}</Badge>
                  <Badge variant="outline" className={`text-[10px] ${METHOD_COLORS[item.method] || ""}`}>
                    {item.method}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{item.time}</span>
                </div>
              </div>
              {item.method === "一键复制包" && (
                <button className="flex items-center gap-1.5 text-xs border border-amber-500/30 text-amber-400 rounded-lg px-3 py-1.5 hover:bg-amber-500/10 transition-colors">
                  <Copy className="h-3 w-3" />
                  复制内容
                </button>
              )}
              {item.method === "CSV数据包" && (
                <button className="flex items-center gap-1.5 text-xs border border-amber-500/30 text-amber-400 rounded-lg px-3 py-1.5 hover:bg-amber-500/10 transition-colors">
                  下载数据包
                </button>
              )}
              {item.method === "API自动发布" && item.status === "scheduled" && (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <CheckCircle2 className="h-3 w-3" />
                  已排期
                </span>
              )}
            </div>
          ))}
        </div>
      }
    />
  );
}
