"use client";

import { FileText, Video, BookOpen, AlertTriangle, CheckCircle2, Edit3 } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

const CONTENT_QUEUE = [
  { product: "冰丝防晒衣", type: "抖音视频脚本", platform: "抖音", status: "approved", variants: 3 },
  { product: "冰丝防晒衣", type: "种草笔记", platform: "小红书", status: "pending", variants: 1 },
  { product: "便携风扇USB", type: "商品Listing", platform: "淘宝", status: "pending", variants: 1 },
  { product: "便携风扇USB", type: "短视频脚本", platform: "抖音", status: "generating", variants: 0 },
];

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  generating: { label: "生成中", color: "text-cyan-400 border-cyan-500/30" },
  pending: { label: "待审核", color: "text-amber-400 border-amber-500/30" },
  approved: { label: "已通过", color: "text-green-400 border-green-500/30" },
  rejected: { label: "已拒绝", color: "text-red-400 border-red-500/30" },
};

export default function ContentPage() {
  return (
    <ModulePageLayout
      moduleId="content"
      title="内容工厂"
      autoView={
        <AutoModePanel
          moduleId="content"
          icon={<FileText className="h-5 w-5" />}
          description="为每个通过评估的商品自动生成多平台内容（抖音脚本/小红书笔记/Listing），含违规检测"
          metrics={[
            { label: "今日生成", value: 8 },
            { label: "待审核", value: 2 },
            { label: "已发布", value: 5 },
            { label: "违规拦截", value: 0 },
          ]}
          recentActions={[
            { time: "14:35", text: "已生成: 冰丝防晒衣 × 3条抖音脚本 (A/B测试)" },
            { time: "14:33", text: "已生成: 冰丝防晒衣 × 1篇小红书笔记 (800字)" },
            { time: "14:30", text: "违规检测通过: 所有内容 ✓ 绿色" },
            { time: "13:00", text: "已生成: 便携风扇USB × 淘宝Listing (标题+五点卖点)" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">AI 生成的内容，审核后进入发布队列：</div>
          {CONTENT_QUEUE.map((item, i) => {
            const st = STATUS_MAP[item.status] || STATUS_MAP.pending;
            return (
              <div key={i} className="rounded-xl border border-border/50 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{item.product}</span>
                    <Badge variant="outline" className="text-[10px]">{item.type}</Badge>
                    <Badge variant="outline" className="text-[10px]">{item.platform}</Badge>
                    <Badge variant="outline" className={`text-[10px] ${st.color}`}>{st.label}</Badge>
                    {item.variants > 1 && (
                      <span className="text-[10px] text-muted-foreground">{item.variants}个变体</span>
                    )}
                  </div>
                  {item.status === "pending" && (
                    <div className="flex gap-2">
                      <button className="flex items-center gap-1 text-xs border border-green-500/30 text-green-400 rounded-lg px-3 py-1.5 hover:bg-green-500/10">
                        <CheckCircle2 className="h-3 w-3" />
                        通过
                      </button>
                      <button className="flex items-center gap-1 text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50">
                        <Edit3 className="h-3 w-3" />
                        编辑
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      }
    />
  );
}
