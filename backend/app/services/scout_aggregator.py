"""
Scout Aggregator — 选品数据聚合服务

多平台数据统一搜索、聚合、分析。
将淘宝联盟、多多进宝、京东联盟、抖音精选联盟的商品数据 + 小红书种草热度
汇总为标准化的选品分析数据，再交给 AI 做综合分析。

数据源策略：
  - VEAPI_KEY 已配置 → 通过维易 API 聚合中间层获取数据
  - VEAPI_KEY 未配置 → 回退到各平台官方 API
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from app.core.config import VEAPI_KEY

logger = logging.getLogger("shangtanai.scout_aggregator")
from app.services.platforms.base import PlatformProduct, PlatformSearchResult

# 官方适配器
from app.services.platforms.taobao import TaobaoAdapter
from app.services.platforms.pinduoduo import PinduoduoAdapter
from app.services.platforms.douyin import DouyinAdapter
from app.services.platforms.xiaohongshu import XiaohongshuAdapter, XhsNoteData

# 维易 API 适配器
from app.services.platforms.veapi import (
    VeapiTaobaoAdapter,
    VeapiPinduoduoAdapter,
    VeapiJingdongAdapter,
    VeapiDouyinAdapter,
)


@dataclass
class AggregatedData:
    """多平台聚合数据。"""

    keyword: str
    platforms: dict[str, PlatformSearchResult] = field(default_factory=dict)
    xhs_data: Optional[XhsNoteData] = None
    total_products: int = 0
    configured_platforms: list[str] = field(default_factory=list)
    unconfigured_platforms: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)

    def price_summary(self) -> dict:
        """价格统计摘要。"""
        all_products = self._all_products()
        if not all_products:
            return {"min": 0, "max": 0, "avg": 0, "median": 0}
        prices = sorted(p.price for p in all_products if p.price > 0)
        if not prices:
            return {"min": 0, "max": 0, "avg": 0, "median": 0}
        return {
            "min": round(prices[0], 2),
            "max": round(prices[-1], 2),
            "avg": round(sum(prices) / len(prices), 2),
            "median": round(prices[len(prices) // 2], 2),
        }

    def sales_summary(self) -> dict:
        """销量统计摘要。"""
        all_products = self._all_products()
        sales = [p.sales_volume for p in all_products if p.sales_volume is not None and p.sales_volume > 0]
        if not sales:
            return {"total": 0, "avg": 0, "max": 0}
        return {
            "total": sum(sales),
            "avg": round(sum(sales) / len(sales)),
            "max": max(sales),
        }

    def commission_summary(self) -> dict:
        """佣金统计摘要。"""
        all_products = self._all_products()
        rates = [p.commission_rate for p in all_products if p.commission_rate is not None and p.commission_rate > 0]
        if not rates:
            return {"avg_rate": 0, "max_rate": 0, "min_rate": 0}
        return {
            "avg_rate": round(sum(rates) / len(rates) * 100, 1),
            "max_rate": round(max(rates) * 100, 1),
            "min_rate": round(min(rates) * 100, 1),
        }

    def price_bands(self) -> list[dict]:
        """价格带分布。"""
        bands = [
            ("0-50元", 0, 50),
            ("50-100元", 50, 100),
            ("100-200元", 100, 200),
            ("200-500元", 200, 500),
            ("500元+", 500, float("inf")),
        ]
        all_products = self._all_products()
        result = []
        for label, low, high in bands:
            count = sum(1 for p in all_products if low <= p.price < high)
            result.append({"range": label, "count": count})
        return result

    def platform_breakdown(self) -> list[dict]:
        """各平台商品数量占比。"""
        result = []
        for platform, search_result in self.platforms.items():
            if search_result.products:
                result.append({
                    "platform": platform,
                    "count": len(search_result.products),
                    "total": search_result.total_count,
                })
        return result

    def top_products(self, limit: int = 10) -> list[dict]:
        """跨平台综合评分 Top N 商品。"""
        all_products = self._all_products()
        scored = []
        for p in all_products:
            score = 0
            if p.sales_volume and p.sales_volume > 0:
                score += min(p.sales_volume / 1000, 40)  # 销量占 40 分
            if p.commission_rate and p.commission_rate > 0:
                score += p.commission_rate * 100 * 0.3  # 佣金率占 30 分
            if p.price > 0:
                score += min(p.price / 10, 30)  # 价格因子占 30 分
            scored.append((p, round(score, 1)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {
                "platform": p.platform,
                "product_id": p.product_id,
                "title": p.title,
                "price": p.price,
                "sales_volume": p.sales_volume,
                "commission_rate": round(p.commission_rate * 100, 1) if p.commission_rate else None,
                "shop_name": p.shop_name,
                "image_url": p.image_url,
                "score": s,
            }
            for p, s in scored[:limit]
        ]

    def to_ai_context(self) -> str:
        """生成 AI 分析用的上下文文本（基于真实数据）。"""
        lines = [f"关键词：{self.keyword}", ""]

        price = self.price_summary()
        sales = self.sales_summary()
        commission = self.commission_summary()

        lines.append(f"## 数据概览（来自 {', '.join(self.configured_platforms)} 联盟API真实数据）")
        lines.append(f"- 搜索到商品总数：{self.total_products}")
        lines.append(f"- 价格范围：¥{price['min']} - ¥{price['max']}，均价 ¥{price['avg']}，中位价 ¥{price['median']}")
        lines.append(f"- 销量数据：总销量 {sales['total']}，平均 {sales['avg']}，最高 {sales['max']}")
        lines.append(f"- 佣金率：平均 {commission['avg_rate']}%，范围 {commission['min_rate']}%-{commission['max_rate']}%")
        lines.append("")

        # 各平台数据
        for platform, result in self.platforms.items():
            if result.products:
                lines.append(f"### {platform} 平台（{len(result.products)} 件商品，总计 {result.total_count} 件）")
                for p in result.products[:5]:
                    vol = f"月销 {p.sales_volume}" if p.sales_volume else "销量未知"
                    comm = f"佣金 {round(p.commission_rate * 100, 1)}%" if p.commission_rate else ""
                    lines.append(f"  - {p.title[:40]} | ¥{p.price} | {vol} | {comm}")
                lines.append("")

        # 价格带
        lines.append("### 价格带分布")
        for band in self.price_bands():
            lines.append(f"  - {band['range']}: {band['count']} 件")
        lines.append("")

        # 小红书种草热度
        if self.xhs_data:
            lines.append("### 小红书种草热度")
            lines.append(f"  - 相关笔记数：{self.xhs_data.note_count}")
            lines.append(f"  - 平均点赞：{self.xhs_data.avg_likes}")
            lines.append(f"  - 平均收藏：{self.xhs_data.avg_collects}")
            lines.append(f"  - 种草热度评分：{self.xhs_data.buzz_score}/100")
            lines.append("")

        if self.unconfigured_platforms:
            lines.append(f"（未配置平台：{', '.join(self.unconfigured_platforms)}，数据不完整）")

        return "\n".join(lines)

    def _all_products(self) -> list[PlatformProduct]:
        products = []
        for result in self.platforms.values():
            products.extend(result.products)
        return products


class ScoutAggregator:
    """选品数据聚合器。

    数据源优先级：
      VEAPI_KEY 已配置 → 维易 API（淘宝+拼多多+京东+抖音）
      VEAPI_KEY 未配置 → 各平台官方 API
    """

    def __init__(self):
        use_veapi = bool(VEAPI_KEY)

        # 拼多多：官方 API 已接通，始终用官方适配器
        self.pinduoduo = PinduoduoAdapter()

        if use_veapi:
            self.taobao = VeapiTaobaoAdapter()
            self.douyin = VeapiDouyinAdapter()
            self.jingdong = VeapiJingdongAdapter()
        else:
            self.taobao = TaobaoAdapter()
            self.douyin = DouyinAdapter()
            self.jingdong = None  # 官方京东适配器暂未实现

        self.xiaohongshu = XiaohongshuAdapter()
        self._use_veapi = use_veapi

    async def search(
        self,
        keyword: str,
        platforms: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> AggregatedData:
        """多平台并发搜索，聚合结果。"""
        all_adapters = {
            "taobao": self.taobao,
            "pinduoduo": self.pinduoduo,
            "douyin": self.douyin,
        }
        # 京东仅在 veapi 模式下可用
        if self.jingdong:
            all_adapters["jingdong"] = self.jingdong

        # 筛选要查询的平台
        if platforms:
            adapters = {k: v for k, v in all_adapters.items() if k in platforms}
        else:
            adapters = all_adapters

        result = AggregatedData(keyword=keyword)

        # 检查各平台配置状态
        for name, adapter in adapters.items():
            if adapter.is_configured():
                result.configured_platforms.append(name)
            else:
                result.unconfigured_platforms.append(name)

        # 并发搜索所有已配置的平台 + 小红书笔记
        tasks = []
        task_names = []

        for name, adapter in adapters.items():
            tasks.append(adapter.search_products(keyword, page, page_size, sort))
            task_names.append(name)

        # 小红书种草热度（始终查询，如果已配置）
        if self.xiaohongshu.is_configured():
            tasks.append(self.xiaohongshu.search_notes(keyword))
            task_names.append("xhs_notes")
            result.configured_platforms.append("xiaohongshu")
        else:
            result.unconfigured_platforms.append("xiaohongshu")

        # 并发执行
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for name, resp in zip(task_names, responses):
            if isinstance(resp, Exception):
                logger.error("[%s] 平台 %s 搜索异常: %s", keyword, name, resp)
                result.errors[name] = str(resp)
            elif name == "xhs_notes":
                result.xhs_data = resp
            elif isinstance(resp, PlatformSearchResult):
                result.platforms[name] = resp
                if resp.error:
                    logger.warning("[%s] 平台 %s 返回错误: %s", keyword, name, resp.error)
                    result.errors[name] = resp.error
                if resp.products:
                    logger.info("[%s] 平台 %s 返回 %d 条商品", keyword, name, len(resp.products))
                else:
                    logger.warning("[%s] 平台 %s 返回 0 条商品", keyword, name)
                result.total_products += len(resp.products)

        if result.errors:
            logger.warning("[%s] 聚合完成，%d 个平台有错误: %s", keyword, len(result.errors), result.errors)
        logger.info("[%s] 聚合完成: %d 条商品, 已配置平台=%s, 未配置=%s",
                     keyword, result.total_products, result.configured_platforms, result.unconfigured_platforms)

        return result
