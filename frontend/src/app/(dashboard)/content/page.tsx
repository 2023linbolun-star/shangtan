"use client";

import { useState, useCallback } from "react";
import {
  FileText, Sparkles, Settings2, Palette, FolderOpen, Image as ImageIcon,
  Brain, ThumbsUp, ThumbsDown, Loader2, X, ChevronDown, ChevronUp,
  ArrowLeft, Copy, Send, Check, Paperclip, Video,
} from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { CreationCards, type CreationType } from "@/components/content/creation-cards";
import { ContentLibrary } from "@/components/content/content-library";
import { AssetLibrary } from "@/components/content/asset-library";
import { MainImagePanel } from "@/components/content/main-image-panel";
import { PromoVideoPanel } from "@/components/content/promo-video-panel";
import { SmartPlanPanel } from "@/components/content/smart-plan-panel";
import {
  getContentStyles, getPreferences, updatePreferences, getMemoryStats,
  generateContent, submitFeedback, getSmartPlan,
} from "@/lib/api";
import { useEffect } from "react";

// ── Types ──

interface StyleConfig {
  id: string; name: string; platform: string; category: string;
  description: string; tags: string[];
  customizable_fields: Array<{ key: string; label: string; type: string; options?: string[]; default?: string; }>;
}

interface MemoryStats {
  days_learning: number; interaction_count: number; preference_count: number;
  few_shot_count: number; guardrail_count: number; adoption_rate: number;
  learned_preferences: Array<{ key: string; label: string; value: string; source: string }>;
}

// ══════════════════════════════════════════════════════════════
//  AI记忆面板
// ══════════════════════════════════════════════════════════════

function MemoryPanel() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    getMemoryStats().then((res) => setStats(res.data)).catch(() => {});
  }, []);

  if (!stats) return null;

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3 mb-4">
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-cyan-400" />
          <span className="text-cyan-400 font-medium">你的内容AI</span>
          <span className="text-muted-foreground text-xs">
            · 已学习{stats.days_learning}天 · 记住{stats.preference_count + stats.few_shot_count}条偏好
            {stats.adoption_rate > 0 && ` · 采纳率${stats.adoption_rate}%`}
          </span>
        </div>
        {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
      </button>
      {expanded && (
        <div className="mt-3 pt-3 border-t border-cyan-500/10 space-y-3">
          <div className="grid grid-cols-4 gap-3">
            {[
              { v: stats.few_shot_count, l: "优秀案例", c: "text-cyan-400" },
              { v: stats.guardrail_count, l: "已学教训", c: "text-amber-400" },
              { v: `${stats.adoption_rate}%`, l: "采纳率", c: "text-green-400" },
              { v: stats.interaction_count, l: "总交互", c: "" },
            ].map((m, i) => (
              <div key={i} className="text-center">
                <div className={`text-lg font-bold font-tabular ${m.c}`}>{m.v}</div>
                <div className="text-[10px] text-muted-foreground">{m.l}</div>
              </div>
            ))}
          </div>
          {stats.learned_preferences.length > 0 && (
            <div>
              <div className="text-xs text-muted-foreground mb-2">已学习的偏好：</div>
              <div className="flex flex-wrap gap-1.5">
                {stats.learned_preferences.map((p, i) => (
                  <span key={i} className={`text-[10px] px-2 py-0.5 rounded-full border ${
                    p.source === "learned" ? "border-amber-500/30 text-amber-400" : "border-cyan-500/30 text-cyan-400"
                  }`}>
                    {p.label}: {p.value}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
//  风格选择器
// ══════════════════════════════════════════════════════════════

function StyleSelector({ platform, selectedStyle, onSelect }: {
  platform: string; selectedStyle: string; onSelect: (id: string) => void;
}) {
  const [styles, setStyles] = useState<StyleConfig[]>([]);
  useEffect(() => {
    getContentStyles(platform).then((res) => setStyles(res.data?.styles || [])).catch(() => {});
  }, [platform]);

  if (styles.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="text-xs text-muted-foreground flex items-center gap-1.5">
        <Palette className="h-3 w-3" /> 选择风格
      </div>
      <div className="grid grid-cols-2 gap-2">
        {styles.map((s) => (
          <button key={s.id} onClick={() => onSelect(s.id)}
            className={`text-left p-3 rounded-lg border transition-all ${
              selectedStyle === s.id
                ? "border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_12px_rgba(6,182,212,0.1)]"
                : "border-border/50 hover:border-border"
            }`}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">{s.name}</span>
              <div className="flex gap-1">
                {s.tags.map((t) => (
                  <span key={t} className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                    t === "推荐" ? "bg-cyan-500/20 text-cyan-400" :
                    t === "涨粉" ? "bg-green-500/20 text-green-400" :
                    t === "去AI味" ? "bg-purple-500/20 text-purple-400" :
                    "bg-muted text-muted-foreground"
                  }`}>{t}</span>
                ))}
              </div>
            </div>
            <p className="text-[11px] text-muted-foreground leading-relaxed">{s.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
//  创作面板（通用）
// ══════════════════════════════════════════════════════════════

function CreatePanel({ creationType, onBack }: { creationType: CreationType; onBack: () => void }) {
  const defaultPlatform = creationType.platforms[0] === "any" ? "douyin" : creationType.platforms[0];
  const [platform, setPlatform] = useState(defaultPlatform);
  const [styleId, setStyleId] = useState("");
  const [productInfo, setProductInfo] = useState("");
  const [generating, setGenerating] = useState(false);
  const [attributionSteps, setAttributionSteps] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  const [feedbackMsg, setFeedbackMsg] = useState("");
  const [selectedAssets, setSelectedAssets] = useState<string[]>([]);
  const [assetsExpanded, setAssetsExpanded] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [contentSaved, setContentSaved] = useState(false);
  const [modifyInstruction, setModifyInstruction] = useState("");
  const [previousResult, setPreviousResult] = useState<any>(null);
  const [modifying, setModifying] = useState(false);
  const [copied, setCopied] = useState(false);
  const [queued, setQueued] = useState(false);
  const [aiRecommending, setAiRecommending] = useState(false);
  const [aiRecommended, setAiRecommended] = useState(false);
  const [realAssets, setRealAssets] = useState<Array<{ id: string; file_type: string; name: string; category: string; file_url?: string }>>([]);

  useEffect(() => {
    import("@/lib/api").then(({ listAssets }) =>
      listAssets().then(resp => {
        const raw = resp?.data ?? resp ?? {};
        const data = Array.isArray(raw) ? raw : (raw.assets ?? raw.items ?? []);
        setRealAssets(Array.isArray(data) ? data : []);
      }).catch(() => {})
    );
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!productInfo.trim()) return;
    setGenerating(true);
    setResult(null);
    setPreviousResult(null);
    setFeedbackMsg("");
    setEditedContent("");
    setContentSaved(false);
    setAttributionSteps(["正在加载你的偏好设置..."]);
    await new Promise((r) => setTimeout(r, 500));
    setAttributionSteps((p) => [...p, "正在加载历史优秀案例..."]);

    try {
      const res = await generateContent({
        product_info: productInfo,
        platform,
        style_id: styleId || undefined,
        asset_ids: selectedAssets.length > 0 ? selectedAssets : undefined,
      });
      const applied = res.data?.applied_preferences || [];
      setAttributionSteps(applied.length > 0 ? applied.map((a: string) => `✓ ${a}`) : ["✓ 已使用默认设置"]);
      setResult(res.data);
      const content = typeof res.data?.content === "string" ? res.data.content : JSON.stringify(res.data?.content, null, 2);
      setEditedContent(content);
    } catch (e: any) {
      setResult({ error: e.message });
    } finally {
      setGenerating(false);
    }
  }, [productInfo, platform, styleId, selectedAssets]);

  const handleModify = useCallback(async () => {
    if (!modifyInstruction.trim() || !result) return;
    setModifying(true);
    setPreviousResult(result);
    try {
      const combinedInfo = `${productInfo}\n\n--- 修改指令 ---\n原内容：\n${editedContent}\n\n修改要求：${modifyInstruction}`;
      const res = await generateContent({
        product_info: combinedInfo,
        platform,
        style_id: styleId || undefined,
        asset_ids: selectedAssets.length > 0 ? selectedAssets : undefined,
      });
      setResult(res.data);
      const content = typeof res.data?.content === "string" ? res.data.content : JSON.stringify(res.data?.content, null, 2);
      setEditedContent(content);
      setModifyInstruction("");
      setContentSaved(false);
    } catch (e: any) {
      setResult({ error: e.message });
    } finally {
      setModifying(false);
    }
  }, [modifyInstruction, result, productInfo, editedContent, platform, styleId, selectedAssets]);

  const handleCopyContent = useCallback(() => {
    navigator.clipboard.writeText(editedContent).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [editedContent]);

  const handleQueue = useCallback(() => {
    setQueued(true);
    setTimeout(() => setQueued(false), 2000);
  }, []);

  const handleFeedback = useCallback(async (vote: number) => {
    if (!result?.id) return;
    try {
      const res = await submitFeedback(result.id, vote);
      setFeedbackMsg(res.data?.learned?.message || "反馈已记录");
    } catch {}
  }, [result]);

  // Route to specialized panels for visual design
  if (creationType.id === "product_main_image") {
    return <MainImagePanel onBack={onBack} />;
  }
  if (creationType.id === "promo_video") {
    return <PromoVideoPanel onBack={onBack} />;
  }

  const Icon = creationType.icon;

  return (
    <div className="space-y-4">
      {/* 返回+标题 */}
      <div className="flex items-center gap-3">
        <button onClick={onBack} className="p-1.5 rounded-lg hover:bg-muted/50 transition-colors">
          <ArrowLeft className="h-4 w-4" />
        </button>
        <Icon className="h-5 w-5" />
        <div>
          <h3 className="text-sm font-medium">{creationType.title}</h3>
          <p className="text-[10px] text-muted-foreground">{creationType.subtitle}</p>
        </div>
      </div>

      {/* 平台选择（多平台类型才显示） */}
      {creationType.platforms.length > 1 || creationType.platforms[0] === "any" ? (
        <div className="flex gap-2">
          {["douyin", "xiaohongshu", "taobao", "pinduoduo"].map((p) => (
            <button key={p} onClick={() => setPlatform(p)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                platform === p ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-400" : "border-border/50 text-muted-foreground"
              }`}>
              {{ douyin: "抖音", xiaohongshu: "小红书", taobao: "淘宝", pinduoduo: "拼多多" }[p]}
            </button>
          ))}
        </div>
      ) : null}

      {/* 风格选择 */}
      <StyleSelector platform={platform} selectedStyle={styleId} onSelect={setStyleId} />

      {/* 附加素材 M3-A1 */}
      <div className="space-y-2">
        <button
          onClick={() => setAssetsExpanded(!assetsExpanded)}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <Paperclip className="h-3 w-3" />
          <span>附加素材</span>
          {selectedAssets.length > 0 && (
            <Badge variant="outline" className="text-[9px] px-1.5 py-0 border-cyan-500/30 text-cyan-400">
              {selectedAssets.length}
            </Badge>
          )}
          {assetsExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
        {assetsExpanded && (
          <div className="grid grid-cols-3 gap-2 p-2 rounded-lg border border-border/30 bg-muted/10">
            {realAssets.map((asset) => {
              const isSelected = selectedAssets.includes(asset.id);
              return (
                <button
                  key={asset.id}
                  onClick={() =>
                    setSelectedAssets((prev) =>
                      isSelected ? prev.filter((id) => id !== asset.id) : [...prev, asset.id]
                    )
                  }
                  className={`flex flex-col items-center gap-1 p-2 rounded-lg border transition-all text-center ${
                    isSelected
                      ? "border-cyan-500/50 bg-cyan-500/10"
                      : "border-border/30 hover:border-border/50"
                  }`}
                >
                  <div className={`h-8 w-8 rounded flex items-center justify-center ${
                    isSelected ? "bg-cyan-500/20" : "bg-muted/30"
                  }`}>
                    {asset.file_type === "video" ? (
                      <Video className={`h-4 w-4 ${isSelected ? "text-cyan-400" : "text-muted-foreground"}`} />
                    ) : (
                      <ImageIcon className={`h-4 w-4 ${isSelected ? "text-cyan-400" : "text-muted-foreground"}`} />
                    )}
                  </div>
                  <span className={`text-[10px] leading-tight line-clamp-2 ${isSelected ? "text-cyan-400" : "text-muted-foreground"}`}>
                    {asset.name}
                  </span>
                </button>
              );
            })}
          </div>
        )}
        {selectedAssets.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {selectedAssets.map((id) => {
              const asset = realAssets.find((a) => a.id === id);
              if (!asset) return null;
              return (
                <span key={id} className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-cyan-400">
                  {asset.file_type === "video" ? <Video className="h-2.5 w-2.5" /> : <ImageIcon className="h-2.5 w-2.5" />}
                  {asset.name}
                  <button onClick={() => setSelectedAssets((prev) => prev.filter((i) => i !== id))}>
                    <X className="h-2.5 w-2.5" />
                  </button>
                </span>
              );
            })}
          </div>
        )}
      </div>

      {/* 产品信息 */}
      <div className="space-y-1.5">
        <div className="text-xs text-muted-foreground">产品/内容信息</div>
        <Textarea
          placeholder={
            creationType.id === "promo_image"
              ? "描述你要做的海报/宣传图，如：冰丝防晒衣夏季促销海报，突出29.9特价，清爽蓝色调"
              : creationType.id === "free_create"
              ? "描述你想要的任何内容，AI会帮你生成"
              : "输入产品信息，如：冰丝防晒衣，29.9元，UPF50+，冰丝面料，9色可选"
          }
          value={productInfo}
          onChange={(e) => setProductInfo(e.target.value)}
          className="min-h-[80px] bg-muted/20 border-border/50 text-sm"
        />
      </div>

      {/* AI推荐按钮 */}
      <button
        onClick={async () => {
          if (!productInfo.trim()) return;
          setAiRecommending(true);
          try {
            const focusMap: Record<string, string> = {
              short_video: "short_video", xhs_note: "xhs_note",
              ecommerce: "ecommerce", product_main_image: "product_main_image",
              promo_video: "promo_video",
            };
            const focusType = focusMap[creationType.id] || undefined;
            const res = await getSmartPlan({ product_info: productInfo, focus_type: focusType });
            const rec = res.data?.plan;
            if (rec?.recommended_style_id) setStyleId(rec.recommended_style_id);
            if (rec?.platform) setPlatform(rec.platform);
            setAiRecommended(true);
            setTimeout(() => setAiRecommended(false), 3000);
          } catch {}
          setAiRecommending(false);
        }}
        disabled={!productInfo.trim() || aiRecommending}
        className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 disabled:opacity-50 transition-colors"
      >
        {aiRecommending ? (
          <><Loader2 className="h-3 w-3 animate-spin" /> AI分析中...</>
        ) : aiRecommended ? (
          <><Check className="h-3 w-3 text-green-400" /> <span className="text-green-400">AI已推荐</span></>
        ) : (
          <><Sparkles className="h-3 w-3" /> AI推荐最佳参数</>
        )}
      </button>

      {/* 生成按钮 */}
      <Button onClick={handleGenerate} disabled={generating || !productInfo.trim()}
        className="w-full bg-cyan-600 hover:bg-cyan-700 text-white">
        {generating ? <><Loader2 className="h-4 w-4 animate-spin mr-2" />AI生成中...</>
          : <><Sparkles className="h-4 w-4 mr-2" />开始生成</>}
      </Button>

      {/* 归因流 */}
      {attributionSteps.length > 0 && (generating || result) && (
        <div className="rounded-lg border border-border/30 bg-muted/10 p-3 space-y-1">
          <div className="text-[10px] text-muted-foreground flex items-center gap-1">
            <Brain className="h-3 w-3 text-cyan-400" /> AI生成依据
          </div>
          {attributionSteps.map((s, i) => (
            <div key={i} className="text-xs text-cyan-400/80">→ {s}</div>
          ))}
        </div>
      )}

      {/* 对比：上一版结果 M3-B1 */}
      {previousResult && !previousResult.error && (
        <div className="rounded-xl border border-border/30 p-3 space-y-2 opacity-60">
          <div className="text-[10px] text-muted-foreground flex items-center gap-1">
            <ArrowLeft className="h-3 w-3" /> 上一版本
          </div>
          <pre className="text-xs text-foreground/60 whitespace-pre-wrap max-h-[150px] overflow-y-auto bg-muted/10 rounded-lg p-2 border border-border/20">
            {typeof previousResult.content === "string" ? previousResult.content : JSON.stringify(previousResult.content, null, 2)}
          </pre>
        </div>
      )}

      {/* 生成结果 */}
      {result && !result.error && (
        <div className="rounded-xl border border-border/50 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px]">{result.platform}</Badge>
              <Badge variant="outline" className="text-[10px]">{result.ai_model}</Badge>
              <span className="text-[10px] text-muted-foreground">${result.cost_usd}</span>
            </div>
            <div className="flex items-center gap-1">
              {/* M3-C1: 发布入口 */}
              <button onClick={handleCopyContent}
                className="p-1.5 rounded-lg border border-border/50 hover:border-cyan-500/30 hover:bg-cyan-500/10 transition-all"
                title="复制文案">
                {copied ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5 text-muted-foreground" />}
              </button>
              <button onClick={handleQueue}
                className={`p-1.5 rounded-lg border transition-all ${
                  queued ? "border-green-500/30 bg-green-500/10" : "border-border/50 hover:border-cyan-500/30 hover:bg-cyan-500/10"
                }`}
                title="加入发布队列">
                {queued ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Send className="h-3.5 w-3.5 text-muted-foreground" />}
              </button>
              <div className="w-px h-4 bg-border/30 mx-0.5" />
              <button onClick={() => handleFeedback(1)}
                className="p-1.5 rounded-lg border border-border/50 hover:border-green-500/30 hover:bg-green-500/10">
                <ThumbsUp className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
              <button onClick={() => handleFeedback(-1)}
                className="p-1.5 rounded-lg border border-border/50 hover:border-red-500/30 hover:bg-red-500/10">
                <ThumbsDown className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            </div>
          </div>
          {feedbackMsg && (
            <div className="flex items-center gap-2 text-xs text-cyan-400 bg-cyan-500/5 rounded-lg px-3 py-2 border border-cyan-500/20">
              <Brain className="h-3.5 w-3.5 flex-shrink-0" /> {feedbackMsg}
              <button onClick={() => setFeedbackMsg("")} className="ml-auto"><X className="h-3 w-3" /></button>
            </div>
          )}
          {result.violation_check && (
            <div className={`text-[11px] px-2 py-1 rounded ${
              result.violation_check.risk_level === "green" ? "text-green-400 bg-green-500/5" :
              result.violation_check.risk_level === "yellow" ? "text-amber-400 bg-amber-500/5" :
              "text-red-400 bg-red-500/5"
            }`}>
              违规检测: {result.violation_check.risk_level === "green" ? "✓ 通过" : `⚠ ${result.violation_check.risk_level}`}
            </div>
          )}
          {/* M3-B2: 结果可编辑 */}
          <div className="space-y-2">
            <Textarea
              value={editedContent}
              onChange={(e) => { setEditedContent(e.target.value); setContentSaved(false); }}
              className="text-xs text-foreground/80 min-h-[200px] max-h-[300px] bg-muted/20 border-border/30 font-mono"
            />
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-muted-foreground">
                {editedContent !== (typeof result.content === "string" ? result.content : JSON.stringify(result.content, null, 2))
                  ? "已修改，点击保存"
                  : "可直接编辑内容"}
              </span>
              <Button
                size="sm"
                variant={contentSaved ? "default" : "outline"}
                className="h-7 text-xs"
                onClick={() => { setContentSaved(true); setTimeout(() => setContentSaved(false), 2000); }}
              >
                {contentSaved ? <><Check className="h-3 w-3 mr-1" />已保存</> : "保存修改"}
              </Button>
            </div>
          </div>

          {/* M3-B1: 迭代修改 */}
          <div className="space-y-2 pt-2 border-t border-border/30">
            <div className="text-xs text-muted-foreground">修改指令</div>
            <Textarea
              placeholder="输入修改要求，如：开头更吸引人、语气更活泼、加入价格对比..."
              value={modifyInstruction}
              onChange={(e) => setModifyInstruction(e.target.value)}
              className="min-h-[60px] bg-muted/20 border-border/50 text-xs"
            />
            <Button
              onClick={handleModify}
              disabled={modifying || !modifyInstruction.trim()}
              variant="outline"
              className="w-full text-xs"
            >
              {modifying ? <><Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />修改中...</>
                : <><Sparkles className="h-3.5 w-3.5 mr-1.5" />按要求修改</>}
            </Button>
          </div>
        </div>
      )}
      {result?.error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-400">{result.error}</div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
//  偏好设置
// ══════════════════════════════════════════════════════════════

function PreferencesPanel() {
  const [prefs, setPrefs] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getPreferences().then((res) => setPrefs(res.data?.preferences || {})).catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try { await updatePreferences(prefs); setSaved(true); setTimeout(() => setSaved(false), 2000); } catch {}
    setSaving(false);
  };

  const fields = [
    { key: "voice_style", label: "语气风格", options: ["闺蜜聊天", "专业测评", "轻幽默", "真诚推荐", "吐槽风"] },
    { key: "visual_preference", label: "视觉风格", options: ["日系清透", "极简白底", "真人手机拍", "高级感", "生活感"] },
    { key: "hook_preference", label: "开头偏好", options: ["冲突反差", "提问悬念", "数据冲击", "共鸣代入", "反常识"] },
    { key: "selling_intensity", label: "推销强度", options: ["纯测评", "软种草", "中等推荐", "强力带货"] },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm">
        <Settings2 className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">内容偏好设置</span>
      </div>
      {fields.map((f) => (
        <div key={f.key} className="space-y-1.5">
          <label className="text-xs text-muted-foreground">{f.label}</label>
          <div className="flex flex-wrap gap-1.5">
            {f.options.map((opt) => (
              <button key={opt} onClick={() => setPrefs({ ...prefs, [f.key]: opt })}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  prefs[f.key] === opt ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-400" : "border-border/50 text-muted-foreground"
                }`}>{opt}</button>
            ))}
          </div>
        </div>
      ))}
      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground">明确不喜欢的</label>
        <Textarea placeholder="例如：过度感叹号、网络烂梗..."
          value={(prefs.avoid_patterns || []).join("、")}
          onChange={(e) => setPrefs({ ...prefs, avoid_patterns: e.target.value.split(/[、,，\n]/).map((s: string) => s.trim()).filter(Boolean) })}
          className="min-h-[50px] bg-muted/20 border-border/50 text-xs" />
      </div>
      <Button onClick={handleSave} disabled={saving} className="w-full" variant={saved ? "default" : "outline"}>
        {saving ? "保存中..." : saved ? "✓ 已保存" : "保存偏好"}
      </Button>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
//  主页面
// ══════════════════════════════════════════════════════════════

export default function ContentPage() {
  const [activeTab, setActiveTab] = useState("smart-plan");
  const [selectedCreationType, setSelectedCreationType] = useState<CreationType | null>(null);

  return (
    <ModulePageLayout
      moduleId="content"
      title="内容工厂"
      autoView={
        <AutoModePanel
          moduleId="content"
          icon={<FileText className="h-5 w-5" />}
          description="AI自动为每个商品生成多平台内容（短视频/图文/Listing），含违规检测和质量审核"
          metrics={[
            { label: "今日生成", value: 8 },
            { label: "待审核", value: 2 },
            { label: "已发布", value: 5 },
            { label: "违规拦截", value: 0 },
          ]}
          recentActions={[
            { time: "14:35", text: "已生成: 冰丝防晒衣 × 3条抖音脚本 (A/B测试)" },
            { time: "14:33", text: "已生成: 冰丝防晒衣 × 1篇小红书笔记 (800字)" },
            { time: "14:30", text: "质量审核通过: 评分8.2/10 ✓ 可发布" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          <MemoryPanel />

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-muted/30 w-full">
              <TabsTrigger value="smart-plan" className="text-xs flex-1">
                <Sparkles className="h-3 w-3 mr-1" /> AI方案
              </TabsTrigger>
              <TabsTrigger value="create" className="text-xs flex-1">
                <Sparkles className="h-3 w-3 mr-1" /> 创作中心
              </TabsTrigger>
              <TabsTrigger value="library" className="text-xs flex-1">
                <FolderOpen className="h-3 w-3 mr-1" /> 内容库
              </TabsTrigger>
              <TabsTrigger value="assets" className="text-xs flex-1">
                <ImageIcon className="h-3 w-3 mr-1" /> 素材库
              </TabsTrigger>
              <TabsTrigger value="preferences" className="text-xs flex-1">
                <Settings2 className="h-3 w-3 mr-1" /> 偏好
              </TabsTrigger>
            </TabsList>

            <TabsContent value="smart-plan" className="mt-4">
              <SmartPlanPanel />
            </TabsContent>

            <TabsContent value="create" className="mt-4">
              {selectedCreationType ? (
                <CreatePanel creationType={selectedCreationType} onBack={() => setSelectedCreationType(null)} />
              ) : (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">选择你要创作的内容类型：</div>
                  <CreationCards onSelect={setSelectedCreationType} />
                </div>
              )}
            </TabsContent>

            <TabsContent value="library" className="mt-4">
              <ContentLibrary />
            </TabsContent>

            <TabsContent value="assets" className="mt-4">
              <AssetLibrary />
            </TabsContent>

            <TabsContent value="preferences" className="mt-4">
              <PreferencesPanel />
            </TabsContent>
          </Tabs>
        </div>
      }
    />
  );
}
