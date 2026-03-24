"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, ChevronLeft, Zap, Shield, Scale, Bot, Handshake, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LaunchButton } from "./launch-button";

// ── Types ──

interface OnboardingData {
  platforms: string[];
  riskLevel: "conservative" | "balanced" | "aggressive";
  categories: string[];
  automationLevel: "full_auto" | "guided" | "manual_ai";
}

interface WizardProps {
  onComplete: (data: OnboardingData) => void;
}

// ── Platform options ──

const PLATFORMS = [
  { id: "douyin", name: "抖音", icon: "🎵", desc: "短视频+电商" },
  { id: "xiaohongshu", name: "小红书", icon: "📕", desc: "种草笔记" },
  { id: "taobao", name: "淘宝", icon: "🛒", desc: "搜索电商" },
  { id: "pinduoduo", name: "拼多多", icon: "🍊", desc: "价格电商" },
  { id: "wechat_mp", name: "公众号", icon: "💬", desc: "私域沉淀" },
  { id: "1688", name: "1688", icon: "🏭", desc: "供应链" },
];

const RISK_OPTIONS = [
  { id: "conservative" as const, name: "保守", icon: Shield, desc: "低风险，稳扎稳打", color: "text-green-400 border-green-500/30" },
  { id: "balanced" as const, name: "平衡", icon: Scale, desc: "适度风险，兼顾增长", color: "text-cyan-400 border-cyan-500/30" },
  { id: "aggressive" as const, name: "激进", icon: Zap, desc: "高风险高回报，快速扩张", color: "text-amber-400 border-amber-500/30" },
];

const AUTOMATION_OPTIONS = [
  { id: "full_auto" as const, name: "全自动", icon: Bot, desc: "系统自主决策+执行，你只管收钱", color: "border-cyan-500/30 shadow-[0_0_15px_oklch(0.75_0.15_195/0.15)]" },
  { id: "guided" as const, name: "有引导", icon: Handshake, desc: "系统做完推给你审核，关键步骤你来确认", color: "border-indigo-500/30" },
  { id: "manual_ai" as const, name: "手动+AI辅助", icon: Wrench, desc: "你来操作，AI 提供建议和优化", color: "border-border/50" },
];

const CATEGORY_SUGGESTIONS = [
  "服饰鞋包", "美妆护肤", "家居日用", "数码3C", "食品零食",
  "母婴用品", "运动户外", "宠物用品", "文具办公", "汽车用品",
];

// ── Steps ──

const TOTAL_STEPS = 5; // welcome, platforms, risk, categories, automation + launch

export function OnboardingWizard({ onComplete }: WizardProps) {
  const [step, setStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    platforms: [],
    riskLevel: "balanced",
    categories: [],
    automationLevel: "guided",
  });

  const canNext =
    step === 0 ||
    (step === 1 && data.platforms.length > 0) ||
    step === 2 ||
    step === 3 ||
    step === 4;

  const togglePlatform = (id: string) => {
    setData((d) => ({
      ...d,
      platforms: d.platforms.includes(id)
        ? d.platforms.filter((p) => p !== id)
        : [...d.platforms, id],
    }));
  };

  const toggleCategory = (cat: string) => {
    setData((d) => ({
      ...d,
      categories: d.categories.includes(cat)
        ? d.categories.filter((c) => c !== cat)
        : [...d.categories, cat],
    }));
  };

  const handleLaunch = () => {
    onComplete(data);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
      {/* Progress */}
      {step > 0 && step < TOTAL_STEPS && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 flex gap-2">
          {Array.from({ length: TOTAL_STEPS - 1 }).map((_, i) => (
            <div
              key={i}
              className={`h-1 w-12 rounded-full transition-colors ${
                i < step ? "bg-cyan-500" : "bg-border/50"
              }`}
            />
          ))}
        </div>
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="w-full max-w-2xl"
        >
          {/* Step 0: Welcome */}
          {step === 0 && (
            <div className="text-center space-y-8">
              <div className="flex h-20 w-20 mx-auto items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-600 to-indigo-600 text-3xl font-bold text-white shadow-[0_0_40px_oklch(0.65_0.2_220/0.3)]">
                商
              </div>
              <div>
                <h1 className="text-3xl font-bold mb-3">欢迎来到商探AI</h1>
                <p className="text-muted-foreground text-lg">AI 替你做电商，你只管收钱</p>
              </div>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                接下来几个问题帮我了解你的情况，然后系统就会自动开始工作。
              </p>
            </div>
          )}

          {/* Step 1: Platform Selection */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">选择目标平台</h2>
                <p className="text-muted-foreground">你想在哪些平台上卖货？</p>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {PLATFORMS.map((p) => {
                  const selected = data.platforms.includes(p.id);
                  return (
                    <button
                      key={p.id}
                      onClick={() => togglePlatform(p.id)}
                      className={`rounded-xl border p-4 text-left transition-all ${
                        selected
                          ? "border-cyan-500/50 bg-cyan-500/5 shadow-[0_0_20px_oklch(0.75_0.15_195/0.15)]"
                          : "border-border/50 hover:border-border"
                      }`}
                    >
                      <div className="text-2xl mb-2">{p.icon}</div>
                      <div className="font-medium text-sm">{p.name}</div>
                      <div className="text-xs text-muted-foreground">{p.desc}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 2: Risk Level */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">风险偏好</h2>
                <p className="text-muted-foreground">你希望系统用什么策略来运营？</p>
              </div>
              <div className="space-y-3">
                {RISK_OPTIONS.map((opt) => {
                  const selected = data.riskLevel === opt.id;
                  const Icon = opt.icon;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => setData((d) => ({ ...d, riskLevel: opt.id }))}
                      className={`w-full rounded-xl border p-5 text-left transition-all flex items-center gap-4 ${
                        selected ? opt.color + " bg-card/80" : "border-border/50 hover:border-border"
                      }`}
                    >
                      <Icon className={`h-8 w-8 ${selected ? "" : "text-muted-foreground"}`} />
                      <div>
                        <div className="font-medium">{opt.name}</div>
                        <div className="text-sm text-muted-foreground">{opt.desc}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 3: Category Preferences */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">品类偏好</h2>
                <p className="text-muted-foreground">有感兴趣的品类吗？可以跳过让 AI 自己发现</p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center">
                {CATEGORY_SUGGESTIONS.map((cat) => {
                  const selected = data.categories.includes(cat);
                  return (
                    <button
                      key={cat}
                      onClick={() => toggleCategory(cat)}
                      className={`rounded-full px-4 py-2 text-sm border transition-all ${
                        selected
                          ? "border-cyan-500/50 bg-cyan-500/10 text-cyan-300"
                          : "border-border/50 text-muted-foreground hover:border-border hover:text-foreground"
                      }`}
                    >
                      {cat}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Step 4: Automation Level + Launch */}
          {step === 4 && (
            <div className="space-y-8">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-2">自动化级别</h2>
                <p className="text-muted-foreground">选择 AI 的自主程度，随时可调</p>
              </div>
              <div className="space-y-3">
                {AUTOMATION_OPTIONS.map((opt) => {
                  const selected = data.automationLevel === opt.id;
                  const Icon = opt.icon;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => setData((d) => ({ ...d, automationLevel: opt.id }))}
                      className={`w-full rounded-xl border p-5 text-left transition-all flex items-center gap-4 ${
                        selected ? opt.color + " bg-card/80" : "border-border/50 hover:border-border"
                      }`}
                    >
                      <Icon className={`h-8 w-8 ${selected ? "text-cyan-400" : "text-muted-foreground"}`} />
                      <div>
                        <div className="font-medium">{opt.name}</div>
                        <div className="text-sm text-muted-foreground">{opt.desc}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
              <div className="flex justify-center pt-4">
                <LaunchButton onLaunch={handleLaunch} />
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      {step < 4 && (
        <div className="fixed bottom-8 flex items-center gap-4">
          {step > 0 && (
            <Button variant="ghost" onClick={() => setStep((s) => s - 1)}>
              <ChevronLeft className="h-4 w-4 mr-1" />
              上一步
            </Button>
          )}
          <Button
            onClick={() => setStep((s) => s + 1)}
            disabled={!canNext}
            className={step === 0 ? "px-8" : ""}
          >
            {step === 0 ? "开始设置" : step === 3 ? (data.categories.length === 0 ? "跳过" : "下一步") : "下一步"}
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}
