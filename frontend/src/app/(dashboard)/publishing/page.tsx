"use client";

import { Send, Video, FileText, Copy, CheckCircle2 } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

const PUBLISH_QUEUE = [
  { title: "冰丝防晒衣 - 抖音视频脚本 #1", platform: "抖音", method: "API自动发布", status: "scheduled", time: "今天 18:00" },
  { title: "冰丝防晒衣 - 种草笔记", platform: "小红书", method: "一键复制包", status: "ready", time: "待你复制发布" },
  { title: "冰丝防晒衣 - 抖音视频脚本 #2", platform: "抖音", method: "API自动发布", status: "scheduled", time: "明天 12:00" },
  { title: "便携风扇 - 商品Listing", platform: "淘宝", method: "CSV数据包", status: "ready", time: "待你上传" },
];

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
            { label: "今日已发布", value: 3 },
            { label: "排期中", value: 5 },
            { label: "待手动发布", value: 2 },
            { label: "本周总发布", value: 18 },
          ]}
          recentActions={[
            { time: "18:00", text: "[抖音] 已自动发布: 冰丝防晒衣视频脚本 #1" },
            { time: "15:30", text: "[公众号] 已自动发布: 夏季防晒好物推荐长文" },
            { time: "14:00", text: "[小红书] 一键复制包已生成，等待手动发布" },
            { time: "12:00", text: "[抖音] 已自动发布: 便携风扇开箱测评" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">发布队列——API平台自动发布，手动平台需你操作：</div>
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
