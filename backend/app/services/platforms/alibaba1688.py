"""
1688 Open Platform adapter — 供应商搜索。
个人开发者可注册，实名认证+实名支付宝即可。
"""
import hashlib
import hmac
import logging
import time
from typing import Optional

import httpx

from app.core.config import ALIBABA_APP_KEY, ALIBABA_APP_SECRET

logger = logging.getLogger("shangtanai.platform.1688")


class Alibaba1688Adapter:
    """1688 Open Platform API adapter for supplier search."""

    BASE_URL = "https://gw.open.1688.com/openapi"

    def __init__(self):
        self.app_key = ALIBABA_APP_KEY
        self.app_secret = ALIBABA_APP_SECRET

    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict]:
        """Search products on 1688."""
        if not self.is_configured():
            logger.warning("1688 API not configured (missing APP_KEY/SECRET)")
            return []

        try:
            params = {
                "keywords": keyword,
                "beginPage": str(page),
                "pageSize": str(page_size),
            }
            # TODO: Implement actual 1688 API call with HMAC-SHA1 signature
            # The 1688 API requires:
            # 1. Sign all params with HMAC-SHA1 using app_secret
            # 2. Include timestamp, app_key in request
            # 3. OAuth token for user-specific operations
            #
            # For now, return empty list until API credentials are configured
            logger.info("1688 search for '%s' (page=%d, size=%d)", keyword, page, page_size)
            return []

        except Exception as e:
            logger.error("1688 API error: %s", e)
            return []

    async def get_product_detail(self, product_id: str) -> Optional[dict]:
        """Get detailed product info from 1688."""
        if not self.is_configured():
            return None

        try:
            # TODO: Implement actual API call
            logger.info("1688 product detail for %s", product_id)
            return None
        except Exception as e:
            logger.error("1688 product detail error: %s", e)
            return None

    async def search_dropship_suppliers(
        self,
        keyword: str,
        min_rating: float = 2.0,
        page_size: int = 20,
    ) -> list[dict]:
        """Search specifically for suppliers that support dropshipping (一件代发)."""
        products = await self.search_products(
            keyword=f"{keyword} 一件代发",
            page_size=page_size,
        )

        # Filter for dropship-capable suppliers
        dropship_suppliers = [
            p for p in products
            if p.get("supports_dropship", False)
            and p.get("supplier_rating", 0) >= min_rating
        ]

        return dropship_suppliers

    def _sign_request(self, api_path: str, params: dict) -> str:
        """Generate HMAC-SHA1 signature for 1688 API."""
        sorted_params = sorted(params.items())
        sign_str = api_path + "".join(f"{k}{v}" for k, v in sorted_params)
        signature = hmac.new(
            self.app_secret.encode("utf-8"),
            sign_str.encode("utf-8"),
            hashlib.sha1,
        ).hexdigest().upper()
        return signature
