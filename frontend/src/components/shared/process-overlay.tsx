"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Check, Loader2, Circle } from "lucide-react";

export type StepState = "completed" | "running" | "pending";

export interface ProcessStep {
  id: string;
  label: string;
  state: StepState;
  detail?: string;
}

interface ProcessOverlayProps {
  steps: ProcessStep[];
  title?: string;
  visible?: boolean;
}

export function ProcessOverlay({ steps, title, visible = true }: ProcessOverlayProps) {
  if (!visible) return null;

  return (
    <div className="rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm p-5">
      {title && (
        <div className="flex items-center gap-2 mb-4">
          <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
          <span className="text-sm font-medium text-cyan-400">{title}</span>
        </div>
      )}
      <div className="space-y-1">
        <AnimatePresence>
          {steps.map((step, i) => {
            const isLast = i === steps.length - 1;
            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
              >
                <div className="flex items-start gap-3 py-1.5">
                  {/* Icon */}
                  <div className="mt-0.5 shrink-0">
                    {step.state === "completed" && (
                      <Check className="h-4 w-4 text-green-400" />
                    )}
                    {step.state === "running" && (
                      <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                    )}
                    {step.state === "pending" && (
                      <Circle className="h-4 w-4 text-muted-foreground/40" />
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <span
                      className={`text-sm ${
                        step.state === "completed"
                          ? "text-foreground/70"
                          : step.state === "running"
                          ? "text-foreground"
                          : "text-muted-foreground/50"
                      }`}
                    >
                      {step.label}
                    </span>
                    {step.detail && step.state !== "pending" && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        → {step.detail}
                      </p>
                    )}
                  </div>
                </div>

                {/* Connector line */}
                {!isLast && (
                  <div className="ml-[7px] h-3 w-px bg-border/30" />
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
