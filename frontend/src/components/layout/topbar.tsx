"use client";

import { useRouter } from "next/navigation";
import { Bell, ChevronDown, Store } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAppStore } from "@/stores/app-store";
import { useAutopilotStore } from "@/stores/autopilot-store";
import { useNotificationStore } from "@/stores/notification-store";
import { clearToken } from "@/lib/api";

export function Topbar() {
  const router = useRouter();
  const currentStore = useAppStore((s) => s.currentStore);
  const modules = useAutopilotStore((s) => s.modules);

  const runningCount = modules.filter((m) => m.status === "running").length;
  const pendingCount = modules.reduce((sum, m) => sum + m.pendingReviewCount, 0);

  return (
    <header className="flex h-12 items-center justify-between border-b border-border/30 bg-card/50 backdrop-blur-xl px-6">
      {/* Left: AI status */}
      <div className="flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500" />
          </span>
          <span className="text-muted-foreground text-xs">AI 运行中</span>
        </div>
        {runningCount > 0 && (
          <>
            <span className="text-border/50">|</span>
            <span className="text-xs text-cyan-400 font-mono">{runningCount} 进程</span>
          </>
        )}
        {pendingCount > 0 && (
          <>
            <span className="text-border/50">|</span>
            <span className="text-xs text-amber-400">{pendingCount} 项待审核</span>
          </>
        )}
      </div>

      {/* Right: Store + Notifications + Profile */}
      <div className="flex items-center gap-3">
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs hover:bg-muted/50 transition-colors">
            <Store className="h-3.5 w-3.5" />
            {currentStore}
            <ChevronDown className="h-3 w-3" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem className="text-xs text-muted-foreground">
              暂无店铺，请在设置中添加
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <NotificationBell />

        <DropdownMenu>
          <DropdownMenuTrigger className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-cyan-600 to-indigo-600 text-white text-[10px] cursor-pointer">
            用
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>个人信息</DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => {
                clearToken();
                router.push("/login");
              }}
            >
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

function NotificationBell() {
  const { notifications, unreadCount, markAllRead, dismiss } = useNotificationStore();
  const recent = notifications.slice(0, 5);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger className="relative inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-muted/50 transition-colors">
        <Bell className="h-3.5 w-3.5" />
        {unreadCount > 0 && (
          <Badge className="absolute -right-1 -top-1 h-3.5 w-3.5 rounded-full p-0 text-[9px] flex items-center justify-center bg-amber-500">
            {unreadCount}
          </Badge>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>通知</span>
          {unreadCount > 0 && (
            <button onClick={markAllRead} className="text-xs text-muted-foreground hover:text-foreground">
              全部已读
            </button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {recent.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-muted-foreground">暂无通知</div>
        ) : (
          recent.map((n) => (
            <DropdownMenuItem key={n.id} className="flex-col items-start gap-0.5 cursor-pointer" onClick={() => dismiss(n.id)}>
              <span className={`text-xs font-medium ${!n.read ? "text-foreground" : "text-muted-foreground"}`}>
                {n.title}
              </span>
              <span className="text-[10px] text-muted-foreground">{n.message}</span>
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
