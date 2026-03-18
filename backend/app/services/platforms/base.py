"""
Platform Adapter Base — 平台适配器基类

所有联盟 API 平台适配器的统一接口。
每个平台返回标准化的 PlatformProduct 列表，由 scout_aggregator 聚合。
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlatformProduct:
    """标准化商品数据结构，各平台适配器统一输出此格式。"""

    platform: str  # taobao / pinduoduo / douyin / xiaohongshu
    product_id: str
    title: str
    price: float  # 售价（元）
    sales_volume: Optional[int] = None  # 月销量（部分平台可能无此字段）
    commission_rate: Optional[float] = None  # 佣金比例 0-1
    commission_amount: Optional[float] = None  # 佣金金额（元）
    shop_name: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    detail_url: Optional[str] = None
    coupon_amount: Optional[float] = None  # 优惠券金额
    coupon_price: Optional[float] = None  # 券后价
    extra: dict = field(default_factory=dict)  # 平台特有字段


@dataclass
class PlatformSearchResult:
    """平台搜索结果。"""

    platform: str
    keyword: str
    total_count: int  # 搜索结果总数
    products: list[PlatformProduct]
    raw_response: Optional[dict] = None  # 原始响应（调试用）
    error: Optional[str] = None


class PlatformAdapter(abc.ABC):
    """平台适配器抽象基类。"""

    platform_name: str = ""

    @abc.abstractmethod
    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        """搜索商品，返回标准化结果。"""
        ...

    @abc.abstractmethod
    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        """获取单个商品详情。"""
        ...

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """检查该平台 API 是否已配置（有 API Key）。"""
        ...

    def _empty_result(self, keyword: str, error: str) -> PlatformSearchResult:
        """返回空结果（用于 API 未配置或请求失败时）。"""
        return PlatformSearchResult(
            platform=self.platform_name,
            keyword=keyword,
            total_count=0,
            products=[],
            error=error,
        )
