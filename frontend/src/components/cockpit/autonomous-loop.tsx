"use client";

import { useAutopilotStore, type ModuleState } from "@/stores/autopilot-store";
import {
  Search, BarChart3, Truck, FileText, Send, Headphones, TrendingUp,
} from "lucide-react";
import React from "react";

const MODULE_ICONS: Record<string, React.ElementType> = {
  discovery: Search,
  evaluation: BarChart3,
  sourcing: Truck,
  content: FileText,
  publishing: Send,
  customer_service: Headphones,
  analytics: TrendingUp,
};

// Positions on an elliptical orbit (cx, cy as percentages of viewBox)
const NODE_POSITIONS: Record<string, { x: number; y: number }> = {
  discovery:        { x: 250, y: 40 },
  evaluation:       { x: 100, y: 120 },
  sourcing:         { x: 400, y: 120 },
  content:          { x: 400, y: 240 },
  publishing:       { x: 250, y: 320 },
  customer_service: { x: 100, y: 240 },
  analytics:        { x: 250, y: 180 },
};

const CONNECTIONS = [
  ["discovery", "evaluation"],
  ["discovery", "sourcing"],
  ["evaluation", "customer_service"],
  ["sourcing", "content"],
  ["content", "publishing"],
  ["publishing", "customer_service"],
  ["customer_service", "analytics"],
  ["analytics", "discovery"],
];

function ModuleNode({ module }: { module: ModuleState }) {
  const pos = NODE_POSITIONS[module.id] || { x: 250, y: 180 };
  const Icon = MODULE_ICONS[module.id] || Search;
  const isRunning = module.status === "running";
  const isReview = module.status === "awaiting_review";

  const glowColor = isRunning
    ? "drop-shadow(0 0 8px oklch(0.75 0.15 195 / 0.6))"
    : isReview
    ? "drop-shadow(0 0 8px oklch(0.78 0.18 80 / 0.6))"
    : "none";

  const ringColor = isRunning
    ? "#67e8f9"
    : isReview
    ? "#fbbf24"
    : "#444";

  return (
    <g transform={`translate(${pos.x - 28}, ${pos.y - 28})`} style={{ filter: glowColor }}>
      <rect
        width="56" height="56" rx="14"
        fill="oklch(0.17 0.02 260)"
        stroke={ringColor}
        strokeWidth={isRunning || isReview ? 2 : 1}
        className={isRunning ? "animate-[glow-pulse_2s_ease-in-out_infinite]" : ""}
      />
      <foreignObject x="14" y="10" width="28" height="28">
        <Icon className="h-7 w-7 text-foreground/70" />
      </foreignObject>
      <text
        x="28" y="52"
        textAnchor="middle"
        className="fill-muted-foreground text-[8px]"
      >
        {module.name}
      </text>
      {module.pendingReviewCount > 0 && (
        <>
          <circle cx="48" cy="8" r="8" fill="#f59e0b" />
          <text x="48" y="11" textAnchor="middle" className="fill-white text-[8px] font-bold">
            {module.pendingReviewCount}
          </text>
        </>
      )}
    </g>
  );
}

export function AutonomousLoopViz() {
  const modules = useAutopilotStore((s) => s.modules);

  return (
    <div className="w-full max-w-lg mx-auto">
      <svg viewBox="0 0 500 360" className="w-full h-auto">
        {/* Connection lines */}
        {CONNECTIONS.map(([from, to]) => {
          const a = NODE_POSITIONS[from];
          const b = NODE_POSITIONS[to];
          if (!a || !b) return null;
          return (
            <line
              key={`${from}-${to}`}
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke="oklch(0.25 0.02 260)"
              strokeWidth="1"
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Module nodes */}
        {modules.map((m) => (
          <ModuleNode key={m.id} module={m} />
        ))}

        {/* Center metric */}
        <text x="250" y="175" textAnchor="middle" className="fill-foreground text-3xl font-bold font-mono">
          0
        </text>
        <text x="250" y="195" textAnchor="middle" className="fill-muted-foreground text-[10px]">
          在管商品
        </text>
      </svg>
    </div>
  );
}
