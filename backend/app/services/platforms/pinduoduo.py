"""
多多进宝 API 适配器

对接拼多多开放平台（多多进宝），获取拼多多商品搜索、价格、销量、佣金数据。

API 文档：https://open.pinduoduo.com/application/document/api?id=pdd.ddk.goods.search
核心接口：pdd.ddk.goods.search（商品搜索）

需要：Client ID + Client Secret + PID（在拼多多开放平台申请）
"""

from __future__ import annotations

import hashlib
import time
from typing import Optional

import httpx

from app.core.config import PDD_CLIENT_ID, PDD_CLIENT_SECRET, PDD_PID
from app.services.platforms.base import (
    PlatformAdapter,
    PlatformProduct,
    PlatformSearchResult,
)

PDD_API_URL = "https://gw-api.pinduoduo.com/api/router"


class PinduoduoAdapter(PlatformAdapter):
    """多多进宝 API 适配器。"""

    platform_name = "pinduoduo"

    def is_configured(self) -> bool:
        return bool(PDD_CLIENT_ID and PDD_CLIENT_SECRET and PDD_PID)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        if not self.is_configured():
            return self._empty_result(keyword, "多多进宝 API 未配置")

        # sort_type: 0-综合 1-销量 2-价格升 3-价格降 4-佣金升 5-佣金降
        sort_map = {
            "default": 0,
            "sales": 1,
            "price_asc": 2,
            "price_desc": 3,
            "commission": 5,
        }

        params = {
            "type": "pdd.ddk.goods.search",
            "client_id": PDD_CLIENT_ID,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "keyword": keyword,
            "page": page,
            "page_size": max(min(page_size, 100), 10),  # 拼多多要求 10-100
            "sort_type": sort_map.get(sort, 0),
            "pid": PDD_PID,
            "custom_parameters": '{"uid":"shangtanai","new":1}',
        }

        params["sign"] = self._sign(params)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(PDD_API_URL, json=params, timeout=15)
                data = resp.json()

            if "error_response" in data:
                error_msg = data["error_response"].get(
                    "sub_msg", data["error_response"].get("error_msg", "未知错误")
                )
                return self._empty_result(keyword, f"多多进宝 API 错误: {error_msg}")

            search_resp = data.get("goods_search_response", {})
            goods_list = search_resp.get("goods_list", [])
            total = search_resp.get("total_count", 0)

            products = []
            for item in goods_list:
                price = item.get("min_group_price", 0) / 100  # 分→元
                coupon = item.get("coupon_discount", 0) / 100
                products.append(
                    PlatformProduct(
                        platform="pinduoduo",
                        product_id=str(item.get("goods_id", "")),
                        title=item.get("goods_name", ""),
                        price=price,
                        sales_volume=self._parse_sales(item),
                        commission_rate=(
                            item.get("promotion_rate", 0) / 1000
                        ),  # 千分比→小数
                        commission_amount=price
                        * item.get("promotion_rate", 0)
                        / 1000,
                        shop_name=item.get("mall_name", ""),
                        category=item.get("category_name", ""),
                        image_url=item.get("goods_image_url", ""),
                        detail_url=item.get("goods_desc", ""),
                        coupon_amount=coupon,
                        coupon_price=max(price - coupon, 0),
                        extra={
                            "mall_id": item.get("mall_id", ""),
                            "has_coupon": item.get("has_coupon", False),
                            "sales_tip": item.get("sales_tip", ""),
                            "goods_sign": item.get("goods_sign", ""),
                            "brand_name": item.get("brand_name", ""),
                        },
                    )
                )

            return PlatformSearchResult(
                platform="pinduoduo",
                keyword=keyword,
                total_count=total,
                products=products,
                raw_response=data,
            )

        except Exception as e:
            return self._empty_result(keyword, f"多多进宝 API 请求失败: {e}")

    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        if not self.is_configured():
            return None

        params = {
            "type": "pdd.ddk.goods.detail",
            "client_id": PDD_CLIENT_ID,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "goods_id_list": f"[{product_id}]",
        }
        params["sign"] = self._sign(params)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(PDD_API_URL, json=params, timeout=15)
                data = resp.json()

            goods_list = (
                data.get("goods_detail_response", {}).get("goods_details", [])
            )
            if not goods_list:
                return None

            item = goods_list[0]
            price = item.get("min_group_price", 0) / 100
            return PlatformProduct(
                platform="pinduoduo",
                product_id=str(item.get("goods_id", "")),
                title=item.get("goods_name", ""),
                price=price,
                sales_volume=item.get("sold_quantity", None),
                image_url=item.get("goods_image_url", ""),
            )
        except Exception:
            return None

    @staticmethod
    def _parse_sales(item: dict) -> Optional[int]:
        """解析拼多多销量，优先 sold_quantity，其次 sales_tip。"""
        sold = item.get("sold_quantity")
        if sold is not None:
            return int(sold)
        tip = item.get("sales_tip", "")
        if not tip:
            return None
        tip = str(tip).replace(",", "").replace("+", "").strip()
        try:
            if "万" in tip:
                return int(float(tip.replace("万", "")) * 10000)
            return int(tip)
        except (ValueError, TypeError):
            return None

    def _sign(self, params: dict) -> str:
        """生成拼多多 API MD5 签名。"""
        sorted_params = sorted(params.items())
        sign_str = PDD_CLIENT_SECRET + "".join(
            f"{k}{v}" for k, v in sorted_params
        ) + PDD_CLIENT_SECRET
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()
