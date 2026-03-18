"""
抖音精选联盟 API 适配器（通过聚推客）

通过聚推客（jutuike.com）API 间接获取抖音精选联盟商品数据。
聚推客聚合了抖音精选联盟的商品搜索和佣金数据。

API 文档：https://www.jutuike.com/doc/104
核心接口：商品搜索 /dyfx/product_search

需要：聚推客 pub_id（在聚推客个人中心获取）
"""

from __future__ import annotations

from typing import Optional

import httpx

from app.core.config import JUTUIKE_PUB_ID
from app.services.platforms.base import (
    PlatformAdapter,
    PlatformProduct,
    PlatformSearchResult,
)

JUTUIKE_API_URL = "https://api.act.jutuike.com"


class DouyinAdapter(PlatformAdapter):
    """抖音精选联盟适配器（通过聚推客 API）。"""

    platform_name = "douyin"

    def is_configured(self) -> bool:
        return bool(JUTUIKE_PUB_ID)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        if not self.is_configured():
            return self._empty_result(keyword, "聚推客 API 未配置")

        # search_type: 0-综合 1-销量 2-价格 3-佣金金额 4-佣金比例
        # sort_type: 0-升序 1-降序
        search_type_map = {
            "default": (0, 1),
            "sales": (1, 1),
            "price_asc": (2, 0),
            "price_desc": (2, 1),
            "commission": (4, 1),
        }
        search_type, sort_type = search_type_map.get(sort, (0, 1))

        params = {
            "pub_id": JUTUIKE_PUB_ID,
            "title": keyword,
            "page": page,
            "page_size": min(page_size, 20),
            "search_type": search_type,
            "sort_type": sort_type,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{JUTUIKE_API_URL}/dyfx/product_search",
                    params=params,
                    timeout=15,
                )
                data = resp.json()

            if data.get("code") != 0 or data.get("msg") not in ("success", "ok", None):
                if data.get("msg") and data.get("msg") not in ("success", "ok"):
                    return self._empty_result(
                        keyword, f"聚推客 API 错误: {data.get('msg', '未知错误')}"
                    )

            goods_list = data.get("data", [])
            if isinstance(goods_list, dict):
                goods_list = goods_list.get("list", [])
            total = len(goods_list)

            products = []
            for item in goods_list:
                price = item.get("price", 0) / 100  # 分→元
                cos_ratio = item.get("cos_ratio", 0) / 100  # 百分比→小数
                cos_fee = item.get("cos_fee", 0) / 100  # 分→元
                coupon_price = item.get("coupon_price", 0) / 100  # 分→元
                products.append(
                    PlatformProduct(
                        platform="douyin",
                        product_id=str(item.get("product_id", "")),
                        title=item.get("title", ""),
                        price=price,
                        sales_volume=item.get("sales", None),
                        commission_rate=cos_ratio,
                        commission_amount=cos_fee,
                        shop_name=item.get("shop_name", ""),
                        category="",
                        image_url=item.get("cover", ""),
                        detail_url=item.get("detail_url", ""),
                        coupon_amount=max(price - coupon_price, 0) if coupon_price > 0 else 0,
                        coupon_price=coupon_price if coupon_price > 0 else price,
                        extra={
                            "shop_id": item.get("shop_id", ""),
                            "in_stock": item.get("in_stock", True),
                            "first_cid": item.get("first_cid", ""),
                            "second_cid": item.get("second_cid", ""),
                        },
                    )
                )

            return PlatformSearchResult(
                platform="douyin",
                keyword=keyword,
                total_count=total,
                products=products,
                raw_response=data,
            )

        except Exception as e:
            return self._empty_result(keyword, f"聚推客 API 请求失败: {e}")

    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        if not self.is_configured():
            return None

        params = {
            "pub_id": JUTUIKE_PUB_ID,
            "product_id": product_id,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{JUTUIKE_API_URL}/dyfx/product_detail",
                    params=params,
                    timeout=15,
                )
                data = resp.json()

            if data.get("code") != 0:
                return None

            item = data.get("data", {})
            if isinstance(item, list) and item:
                item = item[0]
            if not item:
                return None

            price = item.get("price", 0) / 100
            return PlatformProduct(
                platform="douyin",
                product_id=str(item.get("product_id", "")),
                title=item.get("title", ""),
                price=price,
                sales_volume=item.get("sales", None),
                commission_rate=item.get("cos_ratio", 0) / 100,
                image_url=item.get("cover", ""),
            )
        except Exception:
            return None
