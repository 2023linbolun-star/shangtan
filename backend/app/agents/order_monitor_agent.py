"""
OrderMonitorAgent — 订单履约监控。
追踪订单状态，生成一件代发转发指令。
"""
from app.agents.base import BaseAgent, AgentContext
import logging

logger = logging.getLogger("shangtanai.agent.order_monitor")


class OrderMonitorAgent(BaseAgent):
    agent_type = "order_monitor"

    async def observe(self, ctx: AgentContext) -> dict:
        """Collect order data. Initially from manual input, later from platform APIs."""
        orders = ctx.task_input.get("orders", [])
        return {
            "order_count": len(orders),
            "orders": orders,
            "store_id": ctx.task_input.get("store_id"),
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        count = observation["order_count"]
        return {
            "reasoning": f"收到 {count} 笔订单待处理" if count > 0 else "无新订单",
            "strategy": "process_orders" if count > 0 else "idle",
        }

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        orders = observation["orders"]

        if not orders:
            return {"processed": 0, "forwarding_instructions": [], "message": "无新订单"}

        # Generate forwarding instructions for each order
        instructions = []
        for order in orders:
            instructions.append({
                "order_id": order.get("order_id", ""),
                "product_name": order.get("product_name", ""),
                "quantity": order.get("quantity", 1),
                "customer_address": order.get("address", ""),
                "supplier_name": order.get("supplier_name", ""),
                "supplier_url": order.get("supplier_url", ""),
                "action": "forward_to_supplier",
                "instruction": (
                    f"在1688供应商 [{order.get('supplier_name', '')}] 处下单，"
                    f"商品：{order.get('product_name', '')}，"
                    f"数量：{order.get('quantity', 1)}，"
                    f"收件地址：{order.get('address', '')}"
                ),
            })

        return {
            "processed": len(instructions),
            "forwarding_instructions": instructions,
            "message": f"已生成 {len(instructions)} 笔订单转发指令",
        }

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        processed = output.get("processed", 0)
        return {
            "confidence": 0.9 if processed > 0 else 0.5,
            "issues": [],
        }
