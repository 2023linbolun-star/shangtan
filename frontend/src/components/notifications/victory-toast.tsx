"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, PartyPopper, AlertTriangle } from "lucide-react";
import { useNotificationStore, type NotificationType } from "@/stores/notification-store";

const STYLE_MAP: Record<NotificationType, { bg: string; border: string; icon: typeof PartyPopper; iconColor: string }> = {
  victory: {
    bg: "bg-green-500/10",
    border: "border-green-500/30",
    icon: PartyPopper,
    iconColor: "text-green-400",
  },
  warning: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    icon: AlertTriangle,
    iconColor: "text-amber-400",
  },
  action: {
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30",
    icon: PartyPopper,
    iconColor: "text-cyan-400",
  },
};

export function VictoryToastContainer() {
  const { notifications, dismiss } = useNotificationStore();
  const [visibleIds, setVisibleIds] = useState<Set<string>>(new Set());

  // Show new toast notifications (victory + warning only)
  useEffect(() => {
    const toastable = notifications.filter(
      (n) => (n.type === "victory" || n.type === "warning") && !n.read
    );
    const newIds = new Set(toastable.map((n) => n.id));
    setVisibleIds(newIds);

    // Auto-dismiss victory after 5s
    toastable
      .filter((n) => n.type === "victory")
      .forEach((n) => {
        setTimeout(() => {
          setVisibleIds((prev) => {
            const next = new Set(prev);
            next.delete(n.id);
            return next;
          });
        }, 5000);
      });
  }, [notifications]);

  const visibleToasts = notifications.filter((n) => visibleIds.has(n.id));

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
      <AnimatePresence>
        {visibleToasts.slice(0, 5).map((n) => {
          const style = STYLE_MAP[n.type] || STYLE_MAP.victory;
          const Icon = style.icon;
          return (
            <motion.div
              key={n.id}
              initial={{ opacity: 0, x: 80, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 80, scale: 0.95 }}
              className={`rounded-lg border ${style.border} ${style.bg} backdrop-blur-sm p-4`}
            >
              <div className="flex items-start gap-3">
                <Icon className={`h-5 w-5 mt-0.5 shrink-0 ${style.iconColor}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{n.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{n.message}</p>
                </div>
                <button
                  onClick={() => {
                    setVisibleIds((prev) => {
                      const next = new Set(prev);
                      next.delete(n.id);
                      return next;
                    });
                    dismiss(n.id);
                  }}
                  className="text-muted-foreground hover:text-foreground shrink-0"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
