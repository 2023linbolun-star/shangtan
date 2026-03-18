"""
淘宝联盟 API 适配器

对接淘宝联盟（阿里妈妈）开放 API，获取淘宝/天猫商品搜索、价格、销量、佣金数据。

API 文档：https://open.taobao.com/api.htm?docId=48417&docType=2
核心接口：taobao.tbk.dg.material.optional（物料搜索）

需要：App Key + App Secret（在淘宝联盟开放平台申请）
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional
from urllib.parse import quote_plus

import httpx

from app.core.config import TAOBAO_APP_KEY, TAOBAO_APP_SECRET
from app.services.platforms.base import (
    PlatformAdapter,
    PlatformProduct,
    PlatformSearchResult,
)

TAOBAO_API_URL = "https://eco.taobao.com/router/rest"


class TaobaoAdapter(PlatformAdapter):
    """淘宝联盟 API 适配器。"""

    platform_name = "taobao"

    def is_configured(self) -> bool:
        return bool(TAOBAO_APP_KEY and TAOBAO_APP_SECRET)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        if not self.is_configured():
            return self._empty_result(keyword, "淘宝联盟 API 未配置")

        sort_map = {
            "default": "tk_rate_des",  # 默认按佣金率降序
            "sales": "total_sales_des",
            "price_asc": "price_asc",
            "price_desc": "price_des",
            "commission": "tk_rate_des",
        }

        params = {
            "method": "taobao.tbk.dg.material.optional",
            "app_key": TAOBAO_APP_KEY,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": "2.0",
            "sign_method": "hmac",
            "q": keyword,
            "page_no": str(page),
            "page_size": str(min(page_size, 100)),
            "sort": sort_map.get(sort, "tk_rate_des"),
            "has_coupon": "false",
            "adzone_id": "0",  # 需要替换为实际推广位 ID
        }

        params["sign"] = self._sign(params)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(TAOBAO_API_URL, params=params, timeout=15)
                data = resp.json()

            result_data = (
                data.get("tbk_dg_material_optional_response", {})
                .get("result_list", {})
                .get("map_data", [])
            )
            total = data.get("tbk_dg_material_optional_response", {}).get(
                "total_results", 0
            )

            products = []
            for item in result_data:
                products.append(
                    PlatformProduct(
                        platform="taobao",
                        product_id=str(item.get("num_iid", "")),
                        title=item.get("title", ""),
                        price=float(item.get("zk_final_price", 0)),
                        sales_volume=int(item.get("volume", 0)),
                        commission_rate=float(item.get("commission_rate", "0"))
                        / 100,
                        commission_amount=float(
                            item.get("tk_total_commi", "0")
                        ),
                        shop_name=item.get("nick", ""),
                        category=item.get("category_name", ""),
                        image_url=item.get("pict_url", ""),
                        detail_url=item.get("url", ""),
                        coupon_amount=float(
                            item.get("coupon_amount", "0")
                        ),
                        coupon_price=float(
                            item.get("zk_final_price", 0)
                        )
                        - float(item.get("coupon_amount", "0")),
                        extra={
                            "item_url": item.get("item_url", ""),
                            "seller_id": item.get("seller_id", ""),
                            "user_type": item.get("user_type", 0),  # 0=淘宝 1=天猫
                        },
                    )
                )

            return PlatformSearchResult(
                platform="taobao",
                keyword=keyword,
                total_count=total,
                products=products,
                raw_response=data,
            )

        except Exception as e:
            return self._empty_result(keyword, f"淘宝联盟 API 请求失败: {e}")

    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        if not self.is_configured():
            return None

        params = {
            "method": "taobao.tbk.item.info.get",
            "app_key": TAOBAO_APP_KEY,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "format": "json",
            "v": "2.0",
            "sign_method": "hmac",
            "num_iids": product_id,
        }
        params["sign"] = self._sign(params)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(TAOBAO_API_URL, params=params, timeout=15)
                data = resp.json()

            items = (
                data.get("tbk_item_info_get_response", {})
                .get("results", {})
                .get("n_tbk_item", [])
            )
            if not items:
                return None

            item = items[0]
            return PlatformProduct(
                platform="taobao",
                product_id=str(item.get("num_iid", "")),
                title=item.get("title", ""),
                price=float(item.get("zk_final_price", 0)),
                sales_volume=int(item.get("volume", 0)),
                image_url=item.get("pict_url", ""),
                detail_url=item.get("item_url", ""),
            )
        except Exception:
            return None

    def _sign(self, params: dict) -> str:
        """生成淘宝 API HMAC 签名。"""
        sorted_params = sorted(params.items())
        sign_str = "".join(f"{k}{v}" for k, v in sorted_params)
        return (
            hmac.new(
                TAOBAO_APP_SECRET.encode("utf-8"),
                sign_str.encode("utf-8"),
                hashlib.md5,
            )
            .hexdigest()
            .upper()
        )
