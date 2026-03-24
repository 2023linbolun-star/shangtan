"use client";

import { Truck, Package, AlertTriangle, CheckCircle2 } from "lucide-react";
import { ModulePageLayout, AutoModePanel } from "@/components/shared/module-page-layout";
import { Badge } from "@/components/ui/badge";

const MOCK_ORDERS = [
  { id: "DY20260324001", product: "冰丝防晒衣", platform: "抖音", status: "shipped", logistics: "圆通 YT9876543210", supplier: "广州XX工厂", cost: 15.8 },
  { id: "DY20260324002", product: "冰丝防晒衣", platform: "抖音", status: "forwarded", logistics: "待发货", supplier: "广州XX工厂", cost: 15.8 },
  { id: "PDD20260323005", product: "便携风扇USB", platform: "拼多多", status: "pending", logistics: "—", supplier: "义乌YY电器", cost: 12.5 },
];

const STATUS_MAP: Record<string, { label: string; color: string }> = {
  pending: { label: "待转发", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
  forwarded: { label: "已转发供应商", color: "text-cyan-400 border-cyan-500/30 bg-cyan-500/10" },
  shipped: { label: "已发货", color: "text-green-400 border-green-500/30 bg-green-500/10" },
  delivered: { label: "已签收", color: "text-green-400 border-green-500/30 bg-green-500/10" },
};

export default function OrdersPage() {
  return (
    <ModulePageLayout
      moduleId="orders"
      title="订单履约"
      autoView={
        <AutoModePanel
          moduleId="orders"
          icon={<Truck className="h-5 w-5" />}
          description="订单自动转发给1688供应商一件代发，物流自动追踪"
          metrics={[
            { label: "待处理订单", value: 1 },
            { label: "运输中", value: 2 },
            { label: "今日成交", value: 5 },
            { label: "平均发货时间", value: "18h" },
          ]}
          recentActions={[
            { time: "15:30", text: "订单 DY...001 已发货，圆通 YT9876543210" },
            { time: "14:20", text: "订单 DY...002 已转发给 广州XX工厂" },
            { time: "13:00", text: "新订单 PDD...005 收到，准备转发供应商" },
            { time: "10:00", text: "物流更新: 3个包裹在途" },
          ]}
        />
      }
      reviewView={
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground">订单列表——系统自动转发给供应商一件代发：</div>
          {MOCK_ORDERS.map((order) => {
            const st = STATUS_MAP[order.status] || STATUS_MAP.pending;
            return (
              <div key={order.id} className="rounded-xl border border-border/50 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">{order.product}</span>
                    <Badge variant="outline" className="text-[10px]">{order.platform}</Badge>
                    <Badge variant="outline" className={`text-[10px] ${st.color}`}>{st.label}</Badge>
                  </div>
                  <span className="text-xs text-muted-foreground font-mono">{order.id}</span>
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span>供应商: {order.supplier}</span>
                  <span>采购成本: ¥{order.cost}</span>
                  <span>物流: {order.logistics}</span>
                </div>
                {order.status === "pending" && (
                  <div className="mt-3 flex gap-2">
                    <button className="text-xs border border-cyan-500/30 text-cyan-400 rounded-lg px-3 py-1.5 hover:bg-cyan-500/10">
                      确认转发供应商
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      }
    />
  );
}
