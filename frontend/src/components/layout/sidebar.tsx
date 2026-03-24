"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSidebarStore } from "@/stores/sidebar-store";
import { useAutopilotStore } from "@/stores/autopilot-store";
import {
  Gauge,
  Search,
  Package,
  FileText,
  Send,
  Truck,
  Headphones,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  OctagonX,
} from "lucide-react";

interface NavItem {
  id: string; // matches autopilot module id
  label: string;
  href: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { id: "cockpit", label: "驾驶舱", href: "/cockpit", icon: Gauge },
  { id: "discovery", label: "趋势发现", href: "/discovery", icon: Search },
  { id: "products", label: "在管商品", href: "/products", icon: Package },
  { id: "content", label: "内容工厂", href: "/content", icon: FileText },
  { id: "publishing", label: "发布中心", href: "/publishing", icon: Send },
  { id: "orders", label: "订单履约", href: "/orders", icon: Truck },
  { id: "customer_service", label: "AI客服", href: "/cs", icon: Headphones },
  { id: "analytics", label: "数据分析", href: "/analytics", icon: BarChart3 },
  { id: "settings", label: "设置", href: "/settings", icon: Settings },
];

// 模块状态指示点颜色
function StatusDot({ moduleId }: { moduleId: string }) {
  const modules = useAutopilotStore((s) => s.modules);
  const mod = modules.find((m) => m.id === moduleId);
  if (!mod || moduleId === "cockpit" || moduleId === "settings") return null;

  let color = "bg-muted-foreground/30"; // idle = gray
  if (mod.status === "running") color = "bg-green-400";
  if (mod.status === "awaiting_review") color = "bg-amber-400";
  if (mod.status === "error") color = "bg-red-400";

  return (
    <span className="relative flex h-2 w-2 shrink-0">
      {mod.status === "running" && (
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${color} opacity-75`} />
      )}
      <span className={`relative inline-flex rounded-full h-2 w-2 ${color}`} />
    </span>
  );
}

// 待审核徽章
function PendingBadge({ moduleId }: { moduleId: string }) {
  const modules = useAutopilotStore((s) => s.modules);
  const mod = modules.find((m) => m.id === moduleId);
  if (!mod || mod.pendingReviewCount === 0) return null;

  return (
    <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-medium px-1">
      {mod.pendingReviewCount}
    </span>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const { collapsed, toggle } = useSidebarStore();

  return (
    <aside
      className={cn(
        "flex h-screen flex-col border-r border-border/30 bg-sidebar/80 backdrop-blur-xl text-sidebar-foreground transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-border/30 px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-600 to-indigo-600 text-white text-sm font-bold shadow-[0_0_15px_oklch(0.65_0.2_220/0.3)]">
          商
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-wide">商探AI</span>
            <span className="text-[10px] text-cyan-400/70 font-mono">Autopilot</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3 scrollbar-thin">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          const isRunning = false; // Will be enhanced when connected to store

          return (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all",
                active
                  ? "bg-sidebar-accent text-sidebar-primary-foreground font-medium shadow-[0_0_10px_oklch(0.75_0.15_195/0.1)]"
                  : "text-sidebar-foreground/60 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!collapsed && (
                <>
                  <span className="flex-1">{item.label}</span>
                  <StatusDot moduleId={item.id} />
                  <PendingBadge moduleId={item.id} />
                </>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border/30 p-2">
        <button
          onClick={toggle}
          className="flex w-full items-center justify-center rounded-lg p-2 text-sidebar-foreground/40 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
