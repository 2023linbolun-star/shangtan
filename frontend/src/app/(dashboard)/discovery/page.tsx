"use client";

import { useState } from "react";
import { Search, TrendingUp, Zap, Filter, Loader2 } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { createPipeline } from "@/lib/api";

interface TrendItem {
  keyword: string;
  score: number;
  growth: string;
  source: string;
  platforms: string[];
}

const mockTrends: TrendItem[] = [];

function TrendCard({ trend }: { trend: TrendItem }) {
  return (
    <div className="rounded-xl border border-border/50 p-4 flex items-center gap-4 hover:border-cyan-500/30 transition-colors">
      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-cyan-500/10">
        <TrendingUp className="h-5 w-5 text-cyan-400" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="font-medium">{trend.keyword}</span>
          <Badge variant="outline" className="text-xs text-green-400 border-green-500/30">
            {trend.growth}
          </Badge>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-muted-foreground">{trend.source}</span>
          <span className="text-xs text-muted-foreground">·</span>
          <span className="text-xs text-muted-foreground">机会评分 {trend.score}/100</span>
        </div>
      </div>
      <div className="flex gap-2">
        <button className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10 transition-colors">
          送入评估
        </button>
        <button className="text-xs border border-border/50 text-muted-foreground rounded-lg px-3 py-1.5 hover:bg-muted/50 transition-colors">
          跳过
        </button>
      </div>
    </div>
  );
}

function KeywordSearchBar() {
  const [keyword, setKeyword] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<TrendItem | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  async function handleSearch() {
    const trimmed = keyword.trim();
    if (!trimmed || searching) return;

    setSearching(true);
    setSearchResult(null);
    setSearchError(null);

    try {
      const res = await createPipeline(trimmed, ["douyin", "xiaohongshu"]);
      const data = res?.data || res;
      setSearchResult({
        keyword: trimmed,
        score: data?.score ?? 0,
        growth: data?.growth ?? "分析中",
        source: "手动分析",
        platforms: ["douyin", "xiaohongshu"],
      });
    } catch (err: any) {
      setSearchError(err?.message || "分析失败，请稍后重试");
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="输入关键词，如：冰丝防晒衣"
          disabled={searching}
          className="flex-1"
          aria-label="分析关键词"
        />
        <button
          onClick={handleSearch}
          disabled={!keyword.trim() || searching}
          className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-4 py-1.5 hover:bg-cyan-500/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 whitespace-nowrap"
        >
          {searching ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              分析中
            </>
          ) : (
            "分析"
          )}
        </button>
      </div>
      {searchError && <div className="text-xs text-red-400 px-1">{searchError}</div>}
      {searchResult && <TrendCard trend={searchResult} />}
    </div>
  );
}

function ReviewView() {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border/50 p-4 space-y-3">
        <div className="text-sm font-medium flex items-center gap-2">
          <Search className="h-4 w-4 text-cyan-400" />
          手动分析关键词
        </div>
        <KeywordSearchBar />
      </div>

      <div className="text-sm text-muted-foreground">
        系统发现的趋势机会，选择要送入评估的品类：
      </div>
      {mockTrends.length === 0 ? (
        <div className="text-center py-8 text-sm text-muted-foreground">暂无系统推荐趋势，请手动搜索关键词分析</div>
      ) : (
        mockTrends.map((trend) => (
          <TrendCard key={trend.keyword} trend={trend} />
        ))
      )}
    </div>
  );
}

export default function DiscoveryPage() {
  return (
    <ModulePageLayout
      moduleId="discovery"
      title="趋势发现"
      autoView={
        <AutoModePanel
          moduleId="discovery"
          icon={<Search className="h-5 w-5" />}
          description="每4小时自动扫描抖音热搜、百度指数、淘宝搜索趋势，发现商品机会"
          quickActions={<KeywordSearchBar />}
          metrics={[
            { label: "今日扫描", value: 0 },
            { label: "发现趋势", value: 0 },
            { label: "已送评估", value: 0 },
            { label: "下次扫描", value: "-" },
          ]}
          recentActions={[]}
        />
      }
      reviewView={<ReviewView />}
    />
  );
}
