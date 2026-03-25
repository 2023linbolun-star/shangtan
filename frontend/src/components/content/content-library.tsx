"use client";

import { useState, useEffect, useCallback } from "react";
import { Copy, Download, RotateCcw, Check, Eye, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { listContents } from "@/lib/api";

interface ContentItem {
  id: string;
  title: string;
  type: string;
  platform: string;
  status: string;
  feedback: number | null;
  model: string;
  created_at: string;
  preview_text: string;
  metrics?: { views: number; likes: number } | null;
}

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  draft: { label: "草稿", color: "text-muted-foreground border-border/50" },
  approved: { label: "已通过", color: "text-green-400 border-green-500/30" },
  published: { label: "已发布", color: "text-blue-400 border-blue-500/30" },
  archived: { label: "已归档", color: "text-gray-400 border-gray-500/30" },
};

const PLATFORM_MAP: Record<string, string> = {
  douyin: "抖音",
  xiaohongshu: "小红书",
  taobao: "淘宝",
  pinduoduo: "拼多多",
};

export function ContentLibrary() {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchContents = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await listContents();
      const raw = resp?.data ?? resp ?? {};
      const data = Array.isArray(raw) ? raw : (raw.contents ?? raw.items ?? []);
      setContents(Array.isArray(data) ? data : []);
    } catch {
      setContents([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchContents(); }, [fetchContents]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredContents = contents.filter((c) => {
    if (platformFilter !== "all" && c.platform !== platformFilter) return false;
    if (statusFilter !== "all" && c.status !== statusFilter) return false;
    if (searchQuery && !c.title?.includes(searchQuery) && !c.preview_text?.includes(searchQuery)) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* 搜索和筛选 */}
      <div className="flex items-center gap-3">
        <Input
          placeholder="搜索内容..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="flex-1 h-8 text-xs bg-muted/20"
        />
        <Select value={platformFilter} onValueChange={(v) => v && setPlatformFilter(v)}>
          <SelectTrigger className="w-[100px] h-8 text-xs">
            <SelectValue placeholder="平台" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部平台</SelectItem>
            <SelectItem value="douyin">抖音</SelectItem>
            <SelectItem value="xiaohongshu">小红书</SelectItem>
            <SelectItem value="taobao">淘宝</SelectItem>
            <SelectItem value="pinduoduo">拼多多</SelectItem>
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={(v) => v && setStatusFilter(v)}>
          <SelectTrigger className="w-[100px] h-8 text-xs">
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="draft">草稿</SelectItem>
            <SelectItem value="approved">已通过</SelectItem>
            <SelectItem value="published">已发布</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 内容卡片列表 */}
      {loading ? (
        <div className="text-center py-12">
          <Loader2 className="h-6 w-6 mx-auto animate-spin text-muted-foreground" />
          <p className="text-sm text-muted-foreground mt-2">加载中...</p>
        </div>
      ) : filteredContents.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground text-sm">
          暂无内容，去创作中心生成吧
        </div>
      ) : (
        <div className="space-y-3">
          {filteredContents.map((c) => {
            const st = STATUS_MAP[c.status] || STATUS_MAP.draft;
            return (
              <div key={c.id} className="rounded-xl border border-border/50 p-4 hover:border-border transition-colors">
                {/* 顶部：标题+标签 */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{c.title}</span>
                    <Badge variant="outline" className="text-[10px]">{PLATFORM_MAP[c.platform] || c.platform}</Badge>
                    <Badge variant="outline" className={`text-[10px] ${st.color}`}>{st.label}</Badge>
                  </div>
                  <span className="text-[10px] text-muted-foreground">{c.created_at}</span>
                </div>

                {/* 文案预览 */}
                <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{c.preview_text}</p>

                {/* 数据指标（已发布的内容） */}
                {c.metrics && (
                  <div className="flex items-center gap-4 mb-3 text-[10px] text-muted-foreground">
                    <span>播放 {(c.metrics.views / 1000).toFixed(1)}k</span>
                    <span>点赞 {c.metrics.likes}</span>
                  </div>
                )}

                {/* 操作按钮 */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs border-border/50"
                    onClick={() => handleCopy(c.id, c.preview_text)}
                  >
                    {copiedId === c.id ? (
                      <><Check className="h-3 w-3 mr-1 text-green-400" /> 已复制</>
                    ) : (
                      <><Copy className="h-3 w-3 mr-1" /> 复制文案</>
                    )}
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-xs border-border/50">
                    <Download className="h-3 w-3 mr-1" /> 下载
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 text-xs">
                    <Eye className="h-3 w-3 mr-1" /> 预览
                  </Button>
                  <Button variant="ghost" size="sm" className="h-7 text-xs">
                    <RotateCcw className="h-3 w-3 mr-1" /> 复用
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
