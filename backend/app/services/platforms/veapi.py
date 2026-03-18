"""
维易 API (veapi.cn) 平台适配器

聚合中间层，通过一个 vekey 调用淘宝联盟、多多进宝、京东联盟、抖音抖客的商品搜索接口。
暂时替代各平台官方 API，后续逐步切换到官方直连。

文档：https://www.veapi.cn/apidoc/wendangzhinan
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import VEAPI_KEY, VEAPI_TB_PID, VEAPI_PDD_PID, VEAPI_PDD_CUSTOM
from app.services.platforms.base import (
    PlatformAdapter,
    PlatformProduct,
    PlatformSearchResult,
)

logger = logging.getLogger(__name__)

VEAPI_BASE = "http://api.veapi.cn"
VEAPI_TIMEOUT = 15


class _VeapiClient:
    """veapi HTTP 请求封装。"""

    @staticmethod
    async def get(path: str, params: dict) -> dict:
        params["vekey"] = VEAPI_KEY
        url = f"{VEAPI_BASE}{path}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=VEAPI_TIMEOUT)
            resp.raise_for_status()
            return resp.json()


# ---------------------------------------------------------------------------
# 淘宝 — /tbk/tb_search_update
# ---------------------------------------------------------------------------

class VeapiTaobaoAdapter(PlatformAdapter):
    """通过维易 API 搜索淘宝联盟商品。"""

    platform_name = "taobao"

    SORT_MAP = {
        "default": "tk_rate_des",
        "sales": "total_sales_des",
        "price_asc": "price_asc",
        "price_desc": "price_des",
        "commission": "tk_rate_des",
    }

    def is_configured(self) -> bool:
        return bool(VEAPI_KEY)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        if not self.is_configured():
            return self._empty_result(keyword, "维易 API 未配置 (VEAPI_KEY)")

        params = {
            "para": keyword,
            "page": page,
            "pagesize": min(page_size, 100),
            "sort": self.SORT_MAP.get(sort, "tk_rate_des"),
        }
        if VEAPI_TB_PID:
            params["pid"] = VEAPI_TB_PID
        # 不传 pid 时依赖维易后台设置的默认 PID

        try:
            data = await _VeapiClient.get("/tbk/tb_search_update", params)

            if str(data.get("error", "")) != "0":
                return self._empty_result(keyword, data.get("msg", "淘宝搜索失败"))

            items = data.get("result_list", data.get("data", []))
            if isinstance(items, dict):
                items = items.get("result_list", [])
            total = int(data.get("total_results", len(items)))

            products = []
            for item in items:
                basic = item.get("item_basic_info", item)
                price_info = item.get("price_promotion_info", item)
                publish = item.get("publish_info", item)

                price = _float(price_info.get("zk_final_price",
                               basic.get("zk_final_price", 0)))
                coupon_price = _float(price_info.get("final_promotion_price",
                                     basic.get("final_promotion_price", 0)))
                commission_rate_pct = _float(publish.get("income_rate",
                                            item.get("commission_rate", 0)))
                coupon_amount = max(price - coupon_price, 0) if coupon_price and price else 0

                # 销量：优先 volume，其次 tk_total_sales
                volume = _int(basic.get("volume"))
                if not volume:
                    volume = _parse_sales_tip(basic.get("tk_total_sales", ""))

                products.append(PlatformProduct(
                    platform="taobao",
                    product_id=str(item.get("item_id", basic.get("item_id", ""))),
                    title=basic.get("title", ""),
                    price=price,
                    sales_volume=volume,
                    commission_rate=commission_rate_pct / 100 if commission_rate_pct else None,
                    shop_name=basic.get("shop_title", ""),
                    category=basic.get("category_name", ""),
                    image_url=basic.get("pict_url", ""),
                    detail_url=publish.get("click_url", ""),
                    coupon_amount=coupon_amount if coupon_amount > 0 else None,
                    coupon_price=coupon_price if coupon_price > 0 else None,
                    extra={
                        "user_type": basic.get("user_type", 0),
                        "brand_name": basic.get("brand_name", ""),
                    },
                ))

            return PlatformSearchResult(
                platform="taobao",
                keyword=keyword,
                total_count=total,
                products=products,
                raw_response=data,
            )
        except Exception as e:
            logger.exception("veapi taobao search error")
            return self._empty_result(keyword, f"淘宝搜索请求失败: {e}")

    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        if not self.is_configured():
            return None
        try:
            data = await _VeapiClient.get("/tbk/generalconvert", {"para": product_id, "detail": 2})
            if str(data.get("error", "")) != "0":
                return None
            d = data.get("data", {})
            price = _float(d.get("zk_final_price", 0))
            return PlatformProduct(
                platform="taobao",
                product_id=str(d.get("item_id", product_id)),
                title=d.get("title", ""),
                price=price,
                commission_rate=_float(d.get("commission_rate", 0)) / 100,
                image_url=d.get("pict_url", ""),
                detail_url=d.get("coupon_short_url", d.get("cps_short_url", "")),
                coupon_amount=_float(d.get("coupon_amount")),
                coupon_price=_float(d.get("promotion_price", 0)) / 100 if d.get("promotion_price") else None,
            )
        except Exception:
            logger.exception("veapi taobao detail error")
            return None


# ---------------------------------------------------------------------------
# 拼多多 — /pdd/pdd_goodssearch
# ---------------------------------------------------------------------------

class VeapiPinduoduoAdapter(PlatformAdapter):
    """通过维易 API 搜索拼多多商品。"""

    platform_name = "pinduoduo"

    SORT_MAP = {
        "default": 0,
        "sales": 6,
        "price_asc": 3,
        "price_desc": 4,
        "commission": 1,
    }

    def is_configured(self) -> bool:
        return bool(VEAPI_KEY and VEAPI_PDD_PID)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        if not self.is_configured():
            return self._empty_result(keyword, "维易拼多多 API 未配置 (VEAPI_KEY + VEAPI_PDD_PID)")

        params = {
            "keyword": keyword,
            "pid": VEAPI_PDD_PID,
            "custom_parameters": VEAPI_PDD_CUSTOM or "0",
            "page": page,
            "page_size": min(page_size, 100),
            "sort_type": self.SORT_MAP.get(sort, 0),
        }

        try:
            data = await _VeapiClient.get("/pdd/pdd_goodssearch", params)

            if str(data.get("error", "")) != "0":
                return self._empty_result(keyword, data.get("msg", "拼多多搜索失败"))

            items = data.get("data", [])
            if isinstance(items, dict):
                items = items.get("goods_search_response", {}).get("goods_list", items.get("goods_list", []))
            total = int(data.get("total_count", len(items)))

            products = []
            for item in items:
                # 拼多多价格单位是分，佣金率是千分比
                price_fen = _int(item.get("min_group_price", item.get("min_normal_price", 0)))
                price = price_fen / 100 if price_fen else 0
                coupon_discount_fen = _int(item.get("coupon_discount", 0))
                coupon_price = (price_fen - coupon_discount_fen) / 100 if coupon_discount_fen else None
                promotion_rate = _int(item.get("promotion_rate", 0))  # 千分比

                sales_tip = item.get("sales_tip", "")
                sales_volume = _parse_sales_tip(sales_tip)

                products.append(PlatformProduct(
                    platform="pinduoduo",
                    product_id=str(item.get("goods_sign", item.get("goods_id", ""))),
                    title=item.get("goods_name", ""),
                    price=round(price, 2),
                    sales_volume=sales_volume,
                    commission_rate=promotion_rate / 1000 if promotion_rate else None,
                    shop_name=item.get("mall_name", ""),
                    image_url=item.get("goods_image_url", ""),
                    detail_url=item.get("goods_desc", ""),
                    coupon_amount=round(coupon_discount_fen / 100, 2) if coupon_discount_fen else None,
                    coupon_price=round(coupon_price, 2) if coupon_price else None,
                    extra={
                        "merchant_type": item.get("merchant_type"),
                        "has_coupon": item.get("has_coupon"),
                    },
                ))

            return PlatformSearchResult(
                platform="pinduoduo",
                keyword=keyword,
                total_count=total,
                products=products,
                raw_response=data,
            )
        except Exception as e:
            logger.exception("veapi pinduoduo search error")
            return self._empty_result(keyword, f"拼多多搜索请求失败: {e}")

    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        # 通过搜索接口查指定商品
        if not self.is_configured():
            return None
        try:
            params = {
                "keyword": product_id,
                "pid": VEAPI_PDD_PID,
                "custom_parameters": VEAPI_PDD_CUSTOM or "0",
            }
            data = await _VeapiClient.get("/pdd/pdd_goodssearch", params)
            items = data.get("data", [])
            if isinstance(items, dict):
                items = items.get("goods_list", [])
            if not items:
                return None
            item = items[0]
            price_fen = _int(item.get("min_group_price", 0))
            return PlatformProduct(
                platform="pinduoduo",
                product_id=str(item.get("goods_sign", "")),
                title=item.get("goods_name", ""),
                price=round(price_fen / 100, 2) if price_fen else 0,
                shop_name=item.get("mall_name", ""),
                image_url=item.get("goods_image_url", ""),
            )
        except Exception:
            logger.exception("veapi pinduoduo detail error")
            return None


# ---------------------------------------------------------------------------
# 京东 — /jd/jd_search
# ---------------------------------------------------------------------------

class VeapiJingdongAdapter(PlatformAdapter):
    """通过维易 API 搜索京东联盟商品。"""

    platform_name = "jingdong"

    SORT_MAP = {
        "default": ("inOrderCount30Days", "desc"),
        "sales": ("inOrderCount30Days", "desc"),
        "price_asc": ("price", "asc"),
        "price_desc": ("price", "desc"),
        "commission": ("commissionShare", "desc"),
    }

    def is_configured(self) -> bool:
        return bool(VEAPI_KEY)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        if not self.is_configured():
            return self._empty_result(keyword, "维易 API 未配置 (VEAPI_KEY)")

        sort_name, sort_dir = self.SORT_MAP.get(sort, ("inOrderCount30Days", "desc"))
        params = {
            "keyword": keyword,
            "pageIndex": page,
            "pageSize": min(page_size, 30),
            "sortName": sort_name,
            "sort": sort_dir,
        }

        try:
            data = await _VeapiClient.get("/jd/jd_search", params)

            if str(data.get("error", "")) != "0":
                return self._empty_result(keyword, data.get("msg", "京东搜索失败"))

            items = data.get("data", [])
            if isinstance(items, dict):
                items = items.get("goods_list", items.get("data", []))
            total = int(data.get("totalCount", len(items)))

            products = []
            for item in items:
                price_info = item.get("priceInfo", {})
                commission_info = item.get("commissionInfo", {})
                shop_info = item.get("shopInfo", {})
                coupon_list = item.get("couponInfo", {}).get("couponList", []) if isinstance(item.get("couponInfo"), dict) else []

                price = _float(price_info.get("lowestCouponPrice",
                               price_info.get("lowestPrice",
                               price_info.get("price", 0))))
                commission_share = _float(commission_info.get("commissionShare", 0))
                commission_amount = _float(commission_info.get("commission", 0))

                best_coupon = None
                for c in coupon_list:
                    if c.get("isBest") == 1:
                        best_coupon = c
                        break
                if not best_coupon and coupon_list:
                    best_coupon = coupon_list[0]

                image_list = item.get("imageInfo", {}).get("imageList", [])
                image_url = image_list[0].get("url", "") if image_list else ""

                products.append(PlatformProduct(
                    platform="jingdong",
                    product_id=str(item.get("itemId", item.get("skuId", ""))),
                    title=item.get("skuName", ""),
                    price=price,
                    sales_volume=_int(item.get("inOrderCount30Days")),
                    commission_rate=commission_share / 100 if commission_share else None,
                    commission_amount=commission_amount if commission_amount else None,
                    shop_name=shop_info.get("shopName", ""),
                    image_url=image_url,
                    detail_url=item.get("materialUrl", ""),
                    coupon_amount=_float(best_coupon.get("discount")) if best_coupon else None,
                    coupon_price=_float(price_info.get("lowestCouponPrice")) if price_info.get("lowestCouponPrice") else None,
                    extra={
                        "sku_id": item.get("skuId"),
                        "good_comments_share": item.get("goodCommentsShare"),
                        "owner": item.get("owner", ""),
                    },
                ))

            return PlatformSearchResult(
                platform="jingdong",
                keyword=keyword,
                total_count=total,
                products=products,
                raw_response=data,
            )
        except Exception as e:
            logger.exception("veapi jingdong search error")
            return self._empty_result(keyword, f"京东搜索请求失败: {e}")

    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        if not self.is_configured():
            return None
        try:
            data = await _VeapiClient.get("/jd/jd_search", {"skuIds": product_id})
            items = data.get("data", [])
            if not items:
                return None
            item = items[0]
            price_info = item.get("priceInfo", {})
            return PlatformProduct(
                platform="jingdong",
                product_id=str(item.get("skuId", product_id)),
                title=item.get("skuName", ""),
                price=_float(price_info.get("price", 0)),
                sales_volume=_int(item.get("inOrderCount30Days")),
                shop_name=item.get("shopInfo", {}).get("shopName", ""),
                detail_url=item.get("materialUrl", ""),
            )
        except Exception:
            logger.exception("veapi jingdong detail error")
            return None


# ---------------------------------------------------------------------------
# 抖音 — /douke/csj_search (穿山甲，免授权)
# ---------------------------------------------------------------------------

class VeapiDouyinAdapter(PlatformAdapter):
    """通过维易 API 搜索抖音抖客商品（达人搜索接口）。"""

    platform_name = "douyin"

    SORT_MAP = {
        "default": 0,
        "sales": 1,
        "price_asc": 2,
        "price_desc": 2,
        "commission": 3,
    }

    def is_configured(self) -> bool:
        return bool(VEAPI_KEY)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        if not self.is_configured():
            return self._empty_result(keyword, "维易 API 未配置 (VEAPI_KEY)")

        search_type = self.SORT_MAP.get(sort, 0)
        sort_type = 1 if sort in ("price_desc", "sales", "commission") else 0

        params = {
            "title": keyword,
            "page": page,
            "page_size": min(page_size, 20),
            "search_type": search_type,
            "sort_type": sort_type,
        }

        try:
            data = await _VeapiClient.get("/douke/kol_MaterialsProductsSearch", params)

            if str(data.get("error", "")) != "0":
                return self._empty_result(keyword, data.get("msg", "抖音搜索失败"))

            raw_data = data.get("data", data)
            items = []
            if isinstance(raw_data, dict):
                items = raw_data.get("products", raw_data.get("data", []))
            elif isinstance(raw_data, list):
                items = raw_data
            total = int(raw_data.get("total", len(items)) if isinstance(raw_data, dict) else data.get("total", len(items)))

            products = []
            for item in items:
                # 价格单位是分，cos_ratio 是百分比（如 10 = 10%）
                price_fen = _int(item.get("price", 0))
                price = price_fen / 100 if price_fen else 0
                cos_ratio = _float(item.get("cos_ratio", 0))  # 百分比
                cos_fee_fen = _int(item.get("cos_fee", item.get("kol_cos_fee", 0)))

                products.append(PlatformProduct(
                    platform="douyin",
                    product_id=str(item.get("product_id", "")),
                    title=item.get("title", ""),
                    price=round(price, 2),
                    sales_volume=_int(item.get("sales")),
                    commission_rate=cos_ratio / 100 if cos_ratio else None,  # 转为 0-1
                    commission_amount=round(cos_fee_fen / 100, 2) if cos_fee_fen else None,
                    shop_name=item.get("shop_name", ""),
                    image_url=item.get("cover", ""),
                    detail_url=item.get("detail_url", ""),
                    extra={
                        "sharable": item.get("sharable"),
                        "kol_cos_ratio": item.get("kol_cos_ratio"),
                    },
                ))

            return PlatformSearchResult(
                platform="douyin",
                keyword=keyword,
                total_count=total,
                products=products,
                raw_response=data,
            )
        except Exception as e:
            logger.exception("veapi douyin search error")
            return self._empty_result(keyword, f"抖音搜索请求失败: {e}")

    async def get_product_detail(self, product_id: str) -> Optional[PlatformProduct]:
        return None


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _float(v) -> float:
    try:
        return float(v) if v is not None else 0
    except (ValueError, TypeError):
        return 0


def _int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _parse_sales_tip(tip: str) -> Optional[int]:
    """解析拼多多的 sales_tip 字段，如 '10万+' -> 100000。"""
    if not tip:
        return None
    tip = tip.replace(",", "").replace("+", "").strip()
    try:
        if "万" in tip:
            return int(float(tip.replace("万", "")) * 10000)
        return int(tip)
    except (ValueError, TypeError):
        return None
