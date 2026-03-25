"use client";

import { useState, useRef } from "react";
import { Upload, Image as ImageIcon, Video, Palette, Trash2, Tag, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

// Mock素材数据
const MOCK_ASSETS = [
  { id: "a1", type: "image", name: "防晒衣正面实拍.jpg", size: "3.2MB", category: "product", product: "冰丝防晒衣", refs: 3, date: "3月24日" },
  { id: "a2", type: "image", name: "防晒衣场景图.jpg", size: "1.8MB", category: "product", product: "冰丝防晒衣", refs: 1, date: "3月24日" },
  { id: "a3", type: "video", name: "使用演示.mp4", size: "12MB", category: "product", product: "冰丝防晒衣", refs: 0, duration: "0:23", date: "3月23日" },
  { id: "a4", type: "image", name: "品牌logo.png", size: "200KB", category: "brand", product: "通用", refs: 8, date: "3月1日" },
  { id: "a5", type: "image", name: "手持产品照.jpg", size: "4.1MB", category: "person", product: "通用", refs: 2, date: "3月20日" },
];

const CATEGORY_LABELS: Record<string, string> = {
  product: "商品素材",
  brand: "品牌素材",
  person: "通用素材",
  reference: "参考素材",
};

export function AssetLibrary() {
  const [category, setCategory] = useState("all");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredAssets = category === "all"
    ? MOCK_ASSETS
    : MOCK_ASSETS.filter((a) => a.category === category);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    // TODO: 处理文件上传
    const files = Array.from(e.dataTransfer.files);
    console.log("Dropped files:", files);
  };

  return (
    <div className="space-y-4">
      {/* 上传区域 */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-all ${
          dragOver
            ? "border-cyan-500/50 bg-cyan-500/5"
            : "border-border/50 hover:border-border"
        }`}
      >
        <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">拖拽文件到此处上传，或点击选择文件</p>
        <p className="text-[10px] text-muted-foreground mt-1">支持 JPG/PNG/WebP/MP4/MOV，图片≤20MB，视频≤500MB</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            console.log("Selected files:", files);
          }}
        />
      </div>

      {/* 分类筛选 */}
      <div className="flex items-center gap-2">
        {[
          { key: "all", label: "全部" },
          { key: "product", label: "商品素材" },
          { key: "brand", label: "品牌素材" },
          { key: "person", label: "通用素材" },
        ].map((c) => (
          <button
            key={c.key}
            onClick={() => setCategory(c.key)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
              category === c.key
                ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-400"
                : "border-border/50 text-muted-foreground hover:border-border"
            }`}
          >
            {c.label}
            {c.key !== "all" && (
              <span className="ml-1 text-[10px]">
                ({MOCK_ASSETS.filter((a) => a.category === c.key).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* 素材网格 */}
      {filteredAssets.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground text-sm">
          暂无素材，上传一些吧
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredAssets.map((asset) => (
            <div key={asset.id} className="rounded-xl border border-border/50 overflow-hidden group hover:border-border transition-colors">
              {/* 预览区 */}
              <div className="aspect-square bg-muted/20 flex items-center justify-center relative">
                {asset.type === "image" ? (
                  <ImageIcon className="h-10 w-10 text-muted-foreground/30" />
                ) : (
                  <div className="relative">
                    <Video className="h-10 w-10 text-muted-foreground/30" />
                    {asset.duration && (
                      <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[10px] bg-black/60 text-white px-1.5 py-0.5 rounded">
                        {asset.duration}
                      </span>
                    )}
                  </div>
                )}
                {/* 悬浮操作 */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <Button variant="ghost" size="sm" className="h-7 text-xs text-white hover:text-white hover:bg-white/20">
                    用于生成
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/20">
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              {/* 信息区 */}
              <div className="p-2.5">
                <div className="text-xs font-medium truncate">{asset.name}</div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] text-muted-foreground">{asset.size}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {asset.refs > 0 ? `被引用${asset.refs}次` : "未使用"}
                  </span>
                </div>
                <div className="flex items-center gap-1 mt-1.5">
                  <Badge variant="outline" className="text-[9px] px-1.5 py-0">
                    {CATEGORY_LABELS[asset.category] || asset.category}
                  </Badge>
                  <Badge variant="outline" className="text-[9px] px-1.5 py-0">
                    {asset.product}
                  </Badge>
                </div>
              </div>
            </div>
          ))}

          {/* 添加更多按钮 */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="rounded-xl border-2 border-dashed border-border/50 aspect-square flex flex-col items-center justify-center gap-2 hover:border-border transition-colors"
          >
            <Plus className="h-8 w-8 text-muted-foreground/30" />
            <span className="text-xs text-muted-foreground">上传素材</span>
          </button>
        </div>
      )}
    </div>
  );
}
