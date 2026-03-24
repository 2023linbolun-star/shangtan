"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Rocket } from "lucide-react";

interface LaunchButtonProps {
  onLaunch: () => void;
  disabled?: boolean;
}

const INIT_STEPS = [
  "连接平台API...",
  "加载市场数据模型...",
  "初始化发现引擎...",
  "内容生成就绪...",
  "客服AI上线...",
  "所有系统就绪。",
];

export function LaunchButton({ onLaunch, disabled }: LaunchButtonProps) {
  const [phase, setPhase] = useState<"idle" | "launching" | "done">("idle");
  const [visibleSteps, setVisibleSteps] = useState<number>(0);

  const handleClick = async () => {
    if (phase !== "idle" || disabled) return;
    setPhase("launching");
    setVisibleSteps(0);

    for (let i = 0; i < INIT_STEPS.length; i++) {
      await new Promise((r) => setTimeout(r, 600 + Math.random() * 400));
      setVisibleSteps(i + 1);
    }

    await new Promise((r) => setTimeout(r, 800));
    setPhase("done");
    onLaunch();
  };

  if (phase === "launching" || phase === "done") {
    return (
      <div className="flex flex-col items-center gap-6 w-full max-w-md mx-auto">
        <div className="w-full space-y-3">
          {INIT_STEPS.map((step, i) => (
            <AnimatePresence key={i}>
              {i < visibleSteps && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-3 text-sm font-mono"
                >
                  <span className="text-green-400">✓</span>
                  <span className="text-foreground/80">{step}</span>
                </motion.div>
              )}
            </AnimatePresence>
          ))}
        </div>
        {phase === "done" && (
          <motion.p
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-cyan-400 text-lg font-medium"
          >
            系统已启动
          </motion.p>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className="group relative px-16 py-6 rounded-2xl text-xl font-bold tracking-wide
        bg-gradient-to-r from-cyan-600 to-indigo-600 text-white
        shadow-[0_0_30px_oklch(0.65_0.2_220/0.4)]
        hover:shadow-[0_0_50px_oklch(0.65_0.2_220/0.6)]
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-all duration-300"
    >
      <span className="absolute inset-0 rounded-2xl animate-[glow-pulse_2s_ease-in-out_infinite] bg-gradient-to-r from-cyan-500/20 to-indigo-500/20" />
      <span className="relative flex items-center gap-3">
        <Rocket className="h-6 w-6" />
        LAUNCH AI
      </span>
    </button>
  );
}
