"use client";

import { useState, useEffect, useCallback } from "react";
import {
  FileText, Video, BookOpen, AlertTriangle, CheckCircle2, Edit3,
  Brain, ThumbsUp, ThumbsDown, Sparkles, ChevronDown, ChevronUp,
  Palette, Settings2, Loader2, Zap, X,
} from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  getContentStyles, getPreferences, updatePreferences, getMemoryStats,
  generateContent, submitFeedback, listContents,
} from "@/lib/api";

// ── Types ──

interface StyleConfig {
  id: string;
  name: string;
  platform: string;
  category: string;
  description: string;
  tags: string[];
  customizable_fields: Array<{
    key: string; label: string; type: string;
    options?: string[]; default?: string;
  }>;
}

interface MemoryStats {
  days_learning: number;
  interaction_count: number;
  preference_count: number;
  few_shot_count: number;
  guardrail_count: number;
  adoption_rate: number;
  learned_preferences: Array<{ key: string; label: string; value: string; source: string }>;
}

interface ContentItem {
  id: string;
  type: string;
  platform: string;
  content: any;
  status: string;
  feedback: number | null;
  ai_model: string;
  created_at: string;
}

// ── Status Map ──

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  generating: { label: "生成中", color: "text-cyan-400 border-cyan-500/30" },
  draft: { label: "待审核", color: "text-amber-400 border-amber-500/30" },
  pending: { label: "待审核", color: "text-amber-400 border-amber-500/30" },
  approved: { label: "已通过", color: "text-green-400 border-green-500/30" },
  rejected: { label: "已拒绝", color: "text-red-400 border-red-500/30" },
  published: { label: "已发布", color: "text-blue-400 border-blue-500/30" },
};

const PLATFORM_COLORS: Record<string, string> = {
  douyin: "text-pink-400 border-pink-500/30",
  xiaohongshu: "text-red-400 border-red-500/30",
  taobao: "text-orange-400 border-orange-500/30",
  pinduoduo: "text-yellow-400 border-yellow-500/30",
};

// ══════════════════════════════════════════════════════════════
//  AI 记忆面板组件
// ══════════════════════════════════════════════════════════════

function MemoryPanel() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    getMemoryStats()
      .then((res) => setStats(res.data))
      .catch(() => {});
  }, []);

  if (!stats) return null;

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3 mb-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-sm"
      >
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-cyan-400" />
          <span className="text-cyan-400 font-medium">你的内容AI</span>
          <span className="text-muted-foreground">·</span>
          <span className="text-muted-foreground text-xs">
            已学习{stats.days_learning}天 · 记住{stats.preference_count + stats.few_shot_count}条偏好
            {stats.adoption_rate > 0 && ` · 采纳率${stats.adoption_rate}%`}
          </span>
        </div>
        {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
      </button>

      {expanded && (
        <div className="mt-3 pt-3 border-t border-cyan-500/10 space-y-3">
          {/* 统计数据 */}
          <div className="grid grid-cols-4 gap-3">
            <div className="text-center">
              <div className="text-lg font-bold font-tabular text-cyan-400">{stats.few_shot_count}</div>
              <div className="text-[10px] text-muted-foreground">优秀案例</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold font-tabular text-amber-400">{stats.guardrail_count}</div>
              <div className="text-[10px] text-muted-foreground">已学教训</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold font-tabular text-green-400">{stats.adoption_rate}%</div>
              <div className="text-[10px] text-muted-foreground">采纳率</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-bold font-tabular">{stats.interaction_count}</div>
              <div className="text-[10px] text-muted-foreground">总交互</div>
            </div>
          </div>

          {/* 已学习的偏好 */}
          {stats.learned_preferences.length > 0 && (
            <div>
              <div className="text-xs text-muted-foreground mb-2">已学习的偏好：</div>
              <div className="flex flex-wrap gap-1.5">
                {stats.learned_preferences.map((p, i) => (
                  <span
                    key={i}
                    className={`text-[10px] px-2 py-0.5 rounded-full border ${
                      p.source === "learned"
                        ? "border-amber-500/30 text-amber-400 bg-amber-500/5"
                        : "border-cyan-500/30 text-cyan-400 bg-cyan-500/5"
                    }`}
                  >
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
//  风格选择器组件
// ══════════════════════════════════════════════════════════════

function StyleSelector({
  platform,
  selectedStyle,
  onSelect,
}: {
  platform: string;
  selectedStyle: string;
  onSelect: (styleId: string) => void;
}) {
  const [styles, setStyles] = useState<StyleConfig[]>([]);

  useEffect(() => {
    getContentStyles(platform)
      .then((res) => setStyles(res.data?.styles || []))
      .catch(() => {});
  }, [platform]);

  if (styles.length === 0) return null;

  return (
    <div className="space-y-2">
      <div className="text-xs text-muted-foreground flex items-center gap-1.5">
        <Palette className="h-3 w-3" />
        选择内容风格
      </div>
      <div className="grid grid-cols-2 gap-2">
        {styles.map((s) => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`text-left p-3 rounded-lg border transition-all ${
              selectedStyle === s.id
                ? "border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_12px_rgba(6,182,212,0.1)]"
                : "border-border/50 hover:border-border"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium">{s.name}</span>
              <div className="flex gap-1">
                {s.tags.map((tag) => (
                  <span
                    key={tag}
                    className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                      tag === "推荐" ? "bg-cyan-500/20 text-cyan-400" :
                      tag === "涨粉" ? "bg-green-500/20 text-green-400" :
                      tag === "去AI味" ? "bg-purple-500/20 text-purple-400" :
                      "bg-muted text-muted-foreground"
                    }`}
                  >
                    {tag}
                  </span>
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
//  内容生成面板
// ══════════════════════════════════════════════════════════════

function GeneratePanel() {
  const [platform, setPlatform] = useState("douyin");
  const [styleId, setStyleId] = useState("douyin_3act_drama");
  const [productInfo, setProductInfo] = useState("");
  const [generating, setGenerating] = useState(false);
  const [attributionSteps, setAttributionSteps] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  const [feedbackMsg, setFeedbackMsg] = useState("");

  const handleGenerate = useCallback(async () => {
    if (!productInfo.trim()) return;
    setGenerating(true);
    setResult(null);
    setFeedbackMsg("");

    // 模拟归因流
    setAttributionSteps(["正在加载你的偏好设置..."]);
    await new Promise((r) => setTimeout(r, 600));
    setAttributionSteps((prev) => [...prev, "正在加载历史优秀案例..."]);
    await new Promise((r) => setTimeout(r, 400));
    setAttributionSteps((prev) => [...prev, "正在检查回避模式..."]);

    try {
      const res = await generateContent({
        product_info: productInfo,
        platform,
        style_id: styleId,
      });

      // 显示实际归因
      const applied = res.data?.applied_preferences || [];
      if (applied.length > 0) {
        setAttributionSteps(applied.map((a: string) => `✓ ${a}`));
      }

      setResult(res.data);
    } catch (e: any) {
      setResult({ error: e.message });
    } finally {
      setGenerating(false);
    }
  }, [productInfo, platform, styleId]);

  const handleFeedback = useCallback(async (vote: number) => {
    if (!result?.id) return;
    try {
      const res = await submitFeedback(result.id, vote);
      const learned = res.data?.learned;
      if (learned?.message) {
        setFeedbackMsg(learned.message);
      }
    } catch {}
  }, [result]);

  const handlePlatformChange = (p: string) => {
    setPlatform(p);
    setStyleId(p === "douyin" ? "douyin_3act_drama" : "xhs_review");
  };

  return (
    <div className="space-y-4">
      {/* 平台切换 */}
      <Tabs value={platform} onValueChange={handlePlatformChange}>
        <TabsList className="bg-muted/30">
          <TabsTrigger value="douyin" className="text-xs">抖音</TabsTrigger>
          <TabsTrigger value="xiaohongshu" className="text-xs">小红书</TabsTrigger>
          <TabsTrigger value="taobao" className="text-xs">淘宝</TabsTrigger>
          <TabsTrigger value="pinduoduo" className="text-xs">拼多多</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* 风格选择 */}
      <StyleSelector platform={platform} selectedStyle={styleId} onSelect={setStyleId} />

      {/* 产品信息输入 */}
      <div className="space-y-2">
        <div className="text-xs text-muted-foreground">产品信息</div>
        <Textarea
          placeholder="输入产品信息，如：冰丝防晒衣，价格29.9元，UPF50+，冰丝面料，9色可选"
          value={productInfo}
          onChange={(e) => setProductInfo(e.target.value)}
          className="min-h-[80px] bg-muted/20 border-border/50 text-sm"
        />
      </div>

      {/* 生成按钮 */}
      <Button
        onClick={handleGenerate}
        disabled={generating || !productInfo.trim()}
        className="w-full bg-cyan-600 hover:bg-cyan-700 text-white"
      >
        {generating ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
            AI生成中...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4 mr-2" />
            生成内容
          </>
        )}
      </Button>

      {/* 归因流 */}
      {attributionSteps.length > 0 && (generating || result) && (
        <div className="rounded-lg border border-border/30 bg-muted/10 p-3 space-y-1.5">
          <div className="text-[10px] text-muted-foreground flex items-center gap-1">
            <Brain className="h-3 w-3 text-cyan-400" />
            AI生成依据
          </div>
          {attributionSteps.map((step, i) => (
            <div key={i} className="text-xs text-cyan-400/80 flex items-start gap-1.5">
              <span className="text-cyan-500 mt-0.5">→</span>
              {step}
            </div>
          ))}
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
            {/* 反馈按钮 */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleFeedback(1)}
                className="p-1.5 rounded-lg border border-border/50 hover:border-green-500/30 hover:bg-green-500/10 transition-colors"
              >
                <ThumbsUp className="h-3.5 w-3.5 text-muted-foreground hover:text-green-400" />
              </button>
              <button
                onClick={() => handleFeedback(-1)}
                className="p-1.5 rounded-lg border border-border/50 hover:border-red-500/30 hover:bg-red-500/10 transition-colors"
              >
                <ThumbsDown className="h-3.5 w-3.5 text-muted-foreground hover:text-red-400" />
              </button>
            </div>
          </div>

          {/* 反馈学习提示 */}
          {feedbackMsg && (
            <div className="flex items-center gap-2 text-xs text-cyan-400 bg-cyan-500/5 rounded-lg px-3 py-2 border border-cyan-500/20">
              <Brain className="h-3.5 w-3.5 flex-shrink-0" />
              {feedbackMsg}
              <button onClick={() => setFeedbackMsg("")} className="ml-auto">
                <X className="h-3 w-3 text-muted-foreground" />
              </button>
            </div>
          )}

          {/* 违规检测 */}
          {result.violation_check && (
            <div className={`text-[11px] px-2 py-1 rounded ${
              result.violation_check.risk_level === "green"
                ? "text-green-400 bg-green-500/5"
                : result.violation_check.risk_level === "yellow"
                ? "text-amber-400 bg-amber-500/5"
                : "text-red-400 bg-red-500/5"
            }`}>
              违规检测: {result.violation_check.risk_level === "green" ? "✓ 通过" : `⚠ ${result.violation_check.risk_level}`}
            </div>
          )}

          {/* 内容预览 */}
          <pre className="text-xs text-foreground/80 whitespace-pre-wrap max-h-[300px] overflow-y-auto bg-muted/20 rounded-lg p-3 border border-border/30">
            {typeof result.content === "string" ? result.content : JSON.stringify(result.content, null, 2)}
          </pre>
        </div>
      )}

      {result?.error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-3 text-sm text-red-400">
          {result.error}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
//  偏好设置面板
// ══════════════════════════════════════════════════════════════

function PreferencesPanel() {
  const [prefs, setPrefs] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getPreferences()
      .then((res) => setPrefs(res.data?.preferences || {}))
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updatePreferences(prefs);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {}
    setSaving(false);
  };

  const fields = [
    { key: "voice_style", label: "语气风格", options: ["闺蜜聊天", "专业测评", "轻幽默", "真诚推荐", "吐槽风"] },
    { key: "visual_preference", label: "视觉风格", options: ["日系清透", "极简白底", "真人手机拍", "高级感", "生活感"] },
    { key: "hook_preference", label: "开头偏好", options: ["冲突反差", "提问悬念", "数据冲击", "共鸣代入", "反常识"] },
    { key: "selling_intensity", label: "推销强度", options: ["纯测评不推荐", "软种草", "中等推荐", "强力带货"] },
    { key: "content_length", label: "内容长度", options: ["极短(15秒)", "短(20秒)", "中(30秒)", "长(45秒)", "详细(60秒)"] },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm">
        <Settings2 className="h-4 w-4 text-muted-foreground" />
        <span className="font-medium">内容偏好设置</span>
        <span className="text-[10px] text-muted-foreground">AI会根据这些偏好调整生成内容</span>
      </div>

      {fields.map((field) => (
        <div key={field.key} className="space-y-1.5">
          <label className="text-xs text-muted-foreground">{field.label}</label>
          <div className="flex flex-wrap gap-1.5">
            {field.options.map((opt) => (
              <button
                key={opt}
                onClick={() => setPrefs({ ...prefs, [field.key]: opt })}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  prefs[field.key] === opt
                    ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-400"
                    : "border-border/50 text-muted-foreground hover:border-border"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}

      {/* 回避模式 */}
      <div className="space-y-1.5">
        <label className="text-xs text-muted-foreground">明确不喜欢的（AI会自动回避）</label>
        <Textarea
          placeholder="例如：过度使用感叹号、网络烂梗、太长的铺垫..."
          value={(prefs.avoid_patterns || []).join("、")}
          onChange={(e) => setPrefs({
            ...prefs,
            avoid_patterns: e.target.value.split(/[、,，\n]/).map((s: string) => s.trim()).filter(Boolean),
          })}
          className="min-h-[60px] bg-muted/20 border-border/50 text-xs"
        />
      </div>

      <Button
        onClick={handleSave}
        disabled={saving}
        className="w-full"
        variant={saved ? "default" : "outline"}
      >
        {saving ? "保存中..." : saved ? "✓ 已保存" : "保存偏好"}
      </Button>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
//  主页面
// ══════════════════════════════════════════════════════════════

export default function ContentPage() {
  const [activeTab, setActiveTab] = useState("generate");

  return (
    <ModulePageLayout
      moduleId="content"
      title="内容工厂"
      autoView={
        <AutoModePanel
          moduleId="content"
          icon={<FileText className="h-5 w-5" />}
          description="为每个通过评估的商品自动生成多平台内容（抖音脚本/小红书笔记/Listing），含违规检测和质量审核"
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
            { time: "13:00", text: "已生成: 便携风扇USB × 淘宝Listing (标题+五点卖点)" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          {/* AI记忆面板 */}
          <MemoryPanel />

          {/* 三个标签：生成 / 偏好 / 历史 */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-muted/30 w-full">
              <TabsTrigger value="generate" className="text-xs flex-1">
                <Sparkles className="h-3 w-3 mr-1" />
                生成内容
              </TabsTrigger>
              <TabsTrigger value="preferences" className="text-xs flex-1">
                <Settings2 className="h-3 w-3 mr-1" />
                偏好设置
              </TabsTrigger>
              <TabsTrigger value="styles" className="text-xs flex-1">
                <Palette className="h-3 w-3 mr-1" />
                风格库
              </TabsTrigger>
            </TabsList>

            <TabsContent value="generate" className="mt-4">
              <GeneratePanel />
            </TabsContent>

            <TabsContent value="preferences" className="mt-4">
              <PreferencesPanel />
            </TabsContent>

            <TabsContent value="styles" className="mt-4">
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  所有可用风格（按平台筛选）：
                </div>
                <StyleSelector platform="douyin" selectedStyle="" onSelect={() => {}} />
                <div className="border-t border-border/30 pt-4">
                  <StyleSelector platform="xiaohongshu" selectedStyle="" onSelect={() => {}} />
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      }
    />
  );
}
