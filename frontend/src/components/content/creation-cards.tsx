"use client";

import { Video, Image, BookOpen, ShoppingBag, Wand2, Layers, Camera, Film } from "lucide-react";

export interface CreationType {
  id: string;
  icon: any;
  title: string;
  subtitle: string;
  description: string;
  color: string;
  platforms: string[];
}

export const CREATION_TYPES: CreationType[] = [
  {
    id: "short_video",
    icon: Video,
    title: "短视频",
    subtitle: "抖音 / 快手",
    description: "AI生成带货脚本+场景图+配音+字幕，自动合成视频",
    color: "from-pink-500/20 to-pink-600/5 border-pink-500/20 hover:border-pink-500/40",
    platforms: ["douyin", "kuaishou"],
  },
  {
    id: "xhs_note",
    icon: BookOpen,
    title: "小红书图文",
    subtitle: "种草笔记 / 测评",
    description: "AI生成文案+真人风配图，完全去AI味",
    color: "from-red-500/20 to-red-600/5 border-red-500/20 hover:border-red-500/40",
    platforms: ["xiaohongshu"],
  },
  {
    id: "promo_image",
    icon: Image,
    title: "宣传图 / 海报",
    subtitle: "任意尺寸",
    description: "产品海报、活动Banner、社媒配图，AI一键生成",
    color: "from-purple-500/20 to-purple-600/5 border-purple-500/20 hover:border-purple-500/40",
    platforms: ["general"],
  },
  {
    id: "ecommerce",
    icon: ShoppingBag,
    title: "电商文案",
    subtitle: "淘宝 / 拼多多",
    description: "商品标题+卖点+详情页文案，平台规则自动适配",
    color: "from-orange-500/20 to-orange-600/5 border-orange-500/20 hover:border-orange-500/40",
    platforms: ["taobao", "pinduoduo"],
  },
  {
    id: "product_main_image",
    icon: Camera,
    title: "商品主图",
    subtitle: "淘宝 / 天猫",
    description: "AI生成电商5张主图：白底图、场景图、细节图、卖点图、模特图",
    color: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/20 hover:border-emerald-500/40",
    platforms: ["taobao", "tmall"],
  },
  {
    id: "promo_video",
    icon: Film,
    title: "商品宣传视频",
    subtitle: "商品详情页",
    description: "15-30秒商品展示视频，AI配音+BGM，适合商品详情页顶部展示",
    color: "from-rose-500/20 to-rose-600/5 border-rose-500/20 hover:border-rose-500/40",
    platforms: ["taobao", "tmall", "douyin"],
  },
  {
    id: "free_create",
    icon: Wand2,
    title: "自由创作",
    subtitle: "任意平台",
    description: "描述你的需求，AI帮你生成任何类型的内容",
    color: "from-cyan-500/20 to-cyan-600/5 border-cyan-500/20 hover:border-cyan-500/40",
    platforms: ["any"],
  },
  {
    id: "batch",
    icon: Layers,
    title: "批量生成",
    subtitle: "多产品 × 多平台",
    description: "选择多个产品和平台，一键批量生成全套内容",
    color: "from-indigo-500/20 to-indigo-600/5 border-indigo-500/20 hover:border-indigo-500/40",
    platforms: ["all"],
  },
];

export function CreationCards({ onSelect }: { onSelect: (type: CreationType) => void }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
      {CREATION_TYPES.map((type) => {
        const Icon = type.icon;
        return (
          <button
            key={type.id}
            onClick={() => onSelect(type)}
            className={`text-left p-4 rounded-xl border bg-gradient-to-br transition-all ${type.color} hover:shadow-lg group`}
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-background/50">
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">{type.title}</div>
                <div className="text-[10px] text-muted-foreground">{type.subtitle}</div>
              </div>
            </div>
            <p className="text-[11px] text-muted-foreground mt-2 leading-relaxed">{type.description}</p>
          </button>
        );
      })}
    </div>
  );
}
