"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Upload, Image as ImageIcon, Video, Trash2, Plus, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { uploadAsset, listAssets, deleteAsset } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function assetUrl(fileUrl: string | undefined): string | undefined {
  if (!fileUrl) return undefined;
  if (fileUrl.startsWith("http")) return fileUrl;
  return `${API_BASE}${fileUrl}`;
}

interface AssetItem {
  id: string;
  name: string;
  file_type: string;
  file_url: string;
  file_size: number;
  category: string;
  product_id?: string;
  ref_count?: number;
  created_at?: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  product: "商品素材",
  brand: "品牌素材",
  general: "通用素材",
  reference: "参考素材",
  ai_model: "AI模特",
  generated_main: "生成主图",
  generated_video: "生成视频",
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

export function AssetLibrary() {
  const [category, setCategory] = useState("all");
  const [dragOver, setDragOver] = useState(false);
  const [assets, setAssets] = useState<AssetItem[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadingCount, setUploadingCount] = useState({ done: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchAssets = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      const resp = await listAssets();

      const raw = resp?.data ?? resp ?? {};
      const data = Array.isArray(raw) ? raw : (raw.assets ?? raw.items ?? []);
      setAssets(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("[素材库] 加载失败:", err);
      setAssets([]);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAssets(); }, [fetchAssets]);

  const filteredAssets = category === "all"
    ? assets
    : assets.filter((a) => a.category === category);

  const handleUpload = async (files: File[]) => {

    if (files.length === 0) return;
    setError(null);
    setUploading(true);
    setUploadingCount({ done: 0, total: files.length });

    let failed = 0;
    let lastErr = "";
    for (let i = 0; i < files.length; i++) {
      try {
        const uploadCategory = category === "all" ? "product" : category;
        await uploadAsset(files[i], uploadCategory);
      } catch (err: any) {
        failed++;
        lastErr = err?.message || "未知错误";
        console.error("[素材上传] 上传失败:", files[i].name, err);
      }
      setUploadingCount({ done: i + 1, total: files.length });
    }

    setUploading(false);
    if (failed > 0) {
      setError(`${failed}/${files.length} 个文件上传失败: ${lastErr}`);
    } else {
      setError(null);
    }
    await fetchAssets(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files).filter(
      (f) => f.type.startsWith("image/") || f.type.startsWith("video/")
    );
    handleUpload(files);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;
    await handleUpload(files);
    e.target.value = "";
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await deleteAsset(id);
      setAssets((prev) => prev.filter((a) => a.id !== id));
    } catch {
      setError("删除失败");
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* 上传区域 */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        className={`rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-all ${
          dragOver
            ? "border-cyan-500/50 bg-cyan-500/5"
            : "border-border/50 hover:border-border"
        }`}
      >
        {uploading ? (
          <>
            <Loader2 className="h-8 w-8 mx-auto mb-2 text-cyan-400 animate-spin" />
            <p className="text-sm text-cyan-400">
              上传中 {uploadingCount.done}/{uploadingCount.total}...
            </p>
          </>
        ) : (
          <>
            <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">拖拽文件到此处上传，或点击选择文件</p>
            <p className="text-[10px] text-muted-foreground mt-1">支持 JPG/PNG/WebP/MP4/MOV，图片≤20MB，视频≤500MB</p>
          </>
        )}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*,video/*"
          className="hidden"
          onClick={(e) => e.stopPropagation()}
          onChange={handleFileSelect}
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {/* 分类筛选 */}
      <div className="flex items-center gap-2 flex-wrap">
        {[
          { key: "all", label: "全部" },
          { key: "product", label: "商品素材" },
          { key: "brand", label: "品牌素材" },
          { key: "general", label: "通用素材" },
          { key: "ai_model", label: "AI模特" },
          { key: "generated_main", label: "生成主图" },
          { key: "generated_video", label: "生成视频" },
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
                ({assets.filter((a) => a.category === c.key).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* 素材网格 */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="h-6 w-6 mx-auto animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground mt-2">加载中...</p>
        </div>
      ) : filteredAssets.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground text-sm">
          暂无素材，上传一些吧
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredAssets.map((asset) => (
            <div key={asset.id} className="rounded-xl border border-border/50 overflow-hidden group hover:border-border transition-colors">
              {/* 预览区 */}
              <div className="aspect-square bg-muted/20 flex items-center justify-center relative">
                {asset.file_type === "image" ? (
                  asset.file_url ? (
                    <img src={assetUrl(asset.file_url)} alt={asset.name} className="w-full h-full object-cover" />
                  ) : (
                    <ImageIcon className="h-10 w-10 text-muted-foreground/30" />
                  )
                ) : (
                  <div className="relative">
                    <Video className="h-10 w-10 text-muted-foreground/30" />
                  </div>
                )}
                {/* 悬浮操作 */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/20"
                    disabled={deleting === asset.id}
                    onClick={(e) => { e.stopPropagation(); handleDelete(asset.id); }}
                  >
                    {deleting === asset.id ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Trash2 className="h-3 w-3" />
                    )}
                    <span className="ml-1">删除</span>
                  </Button>
                </div>
              </div>
              {/* 信息区 */}
              <div className="p-2.5">
                <div className="text-xs font-medium truncate">{asset.name}</div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] text-muted-foreground">{formatSize(asset.file_size)}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {(asset.ref_count ?? 0) > 0 ? `被引用${asset.ref_count}次` : "未使用"}
                  </span>
                </div>
                <div className="flex items-center gap-1 mt-1.5">
                  <Badge variant="outline" className="text-[9px] px-1.5 py-0">
                    {CATEGORY_LABELS[asset.category] || asset.category}
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
