"""
AI Engine - 统一 AI 调用封装
支持 Claude (Sonnet/Haiku) 和 DeepSeek，自动模型路由和降级容错。
"""

import os
import httpx
from app.core.config import CLAUDE_API_KEY, DEEPSEEK_API_KEY

CLAUDE_BASE_URL = "https://api.anthropic.com/v1/messages"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"


async def call_claude(prompt: str, model: str = "claude-sonnet-4-20250514", max_tokens: int = 4096) -> str:
    """Call Claude API (Sonnet for analysis/generation, Haiku for quick replies)."""
    if not CLAUDE_API_KEY:
        return f"[Mock AI Response] 针对「{prompt[:50]}」的分析结果..."

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            CLAUDE_BASE_URL,
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        data = resp.json()
        return data.get("content", [{}])[0].get("text", "")


async def call_deepseek(prompt: str, max_tokens: int = 2048) -> str:
    """Call DeepSeek API for batch/lightweight tasks."""
    if not DEEPSEEK_API_KEY:
        return f"[Mock DeepSeek Response] {prompt[:50]}..."

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            DEEPSEEK_BASE_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


async def ai_analyze(prompt: str, task_type: str = "analysis") -> str:
    """Route to appropriate model based on task type."""
    model_map = {
        "analysis": ("claude", "claude-sonnet-4-20250514"),
        "generation": ("claude", "claude-sonnet-4-20250514"),
        "quick_reply": ("claude", "claude-haiku-4-5-20251001"),
        "batch": ("deepseek", None),
        "keywords": ("deepseek", None),
    }

    provider, model = model_map.get(task_type, ("claude", "claude-sonnet-4-20250514"))

    try:
        if provider == "claude":
            return await call_claude(prompt, model=model)
        else:
            return await call_deepseek(prompt)
    except Exception:
        # Fallback: try the other provider
        try:
            if provider == "claude":
                return await call_deepseek(prompt)
            else:
                return await call_claude(prompt)
        except Exception:
            return f"[AI 服务暂时不可用] 请稍后重试"
