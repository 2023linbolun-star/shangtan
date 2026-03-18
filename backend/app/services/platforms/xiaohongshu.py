"""
小红书开放平台 API 适配器

获取小红书笔记搜索量和互动数据（点赞、收藏、评论），用于评估种草热度。

API 文档：https://open.xiaohongshu.com/
核心接口：笔记搜索

需要：App ID + App Secret（在小红书开放平台申请）

注意：小红书开放平台主要提供笔记/内容数据，不直接提供商品销量数据。
用于补充种草热度维度，而非替代电商平台的销量数据。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.core.config import XHS_APP_ID, XHS_APP_SECRET
from app.services.platforms.base import PlatformAdapter, PlatformSearchResult

XHS_API_URL = "https://ark.xiaohongshu.com/ark/open_api/v3"


@dataclass
class XhsNoteData:
    """小红书笔记数据。"""

    keyword: str
    note_count: int  # 相关笔记总数
    avg_likes: float  # 平均点赞数
    avg_collects: float  # 平均收藏数
    avg_comments: float  # 平均评论数
    hot_notes: list[dict] = field(default_factory=list)  # 热门笔记
    buzz_score: float = 0.0  # 种草热度评分 0-100


class XiaohongshuAdapter(PlatformAdapter):
    """小红书开放平台适配器。"""

    platform_name = "xiaohongshu"

    def is_configured(self) -> bool:
        return bool(XHS_APP_ID and XHS_APP_SECRET)

    async def search_products(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        sort: str = "default",
    ) -> PlatformSearchResult:
        """小红书不提供商品搜索，返回空结果。使用 search_notes 获取笔记数据。"""
        return self._empty_result(keyword, "小红书不提供商品搜索接口，请使用 search_notes")

    async def get_product_detail(self, product_id: str) -> None:
        return None

    async def search_notes(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Optional[XhsNoteData]:
        """搜索小红书笔记，返回种草热度数据。"""
        if not self.is_configured():
            return None

        try:
            token = await self._get_access_token()
            if not token:
                return None

            params = {
                "keyword": keyword,
                "page": page,
                "page_size": min(page_size, 20),
                "sort": "general",  # 综合排序
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{XHS_API_URL}/note/search",
                    params=params,
                    headers=headers,
                    timeout=15,
                )
                data = resp.json()

            if data.get("code") != 0:
                return None

            notes = data.get("data", {}).get("notes", [])
            total = data.get("data", {}).get("total", 0)

            if not notes:
                return XhsNoteData(keyword=keyword, note_count=0, avg_likes=0, avg_collects=0, avg_comments=0)

            total_likes = sum(n.get("likes", 0) for n in notes)
            total_collects = sum(n.get("collects", 0) for n in notes)
            total_comments = sum(n.get("comments", 0) for n in notes)
            count = len(notes)

            avg_likes = total_likes / count
            avg_collects = total_collects / count
            avg_comments = total_comments / count

            # 种草热度评分：基于笔记量、互动数据综合计算
            buzz_score = min(100, (
                min(total, 10000) / 10000 * 30  # 笔记量占 30 分
                + min(avg_likes, 1000) / 1000 * 30  # 平均点赞占 30 分
                + min(avg_collects, 500) / 500 * 25  # 平均收藏占 25 分
                + min(avg_comments, 200) / 200 * 15  # 平均评论占 15 分
            ))

            hot_notes = [
                {
                    "title": n.get("title", ""),
                    "likes": n.get("likes", 0),
                    "collects": n.get("collects", 0),
                    "note_id": n.get("note_id", ""),
                }
                for n in sorted(notes, key=lambda x: x.get("likes", 0), reverse=True)[:5]
            ]

            return XhsNoteData(
                keyword=keyword,
                note_count=total,
                avg_likes=round(avg_likes, 1),
                avg_collects=round(avg_collects, 1),
                avg_comments=round(avg_comments, 1),
                hot_notes=hot_notes,
                buzz_score=round(buzz_score, 1),
            )

        except Exception:
            return None

    async def _get_access_token(self) -> Optional[str]:
        """获取小红书 API Access Token。"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{XHS_API_URL}/token",
                    json={
                        "app_id": XHS_APP_ID,
                        "app_secret": XHS_APP_SECRET,
                        "grant_type": "client_credentials",
                    },
                    timeout=10,
                )
                data = resp.json()
            return data.get("data", {}).get("access_token")
        except Exception:
            return None
