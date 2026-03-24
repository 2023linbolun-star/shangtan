"""
AI Engine - 统一多模型调用封装
支持 Claude（测试阶段）+ 国内模型（DeepSeek/豆包/通义千问/智谱GLM）
自动路由、降级容错、成本追踪。
"""

import logging
import time
import httpx
from app.core.config import (
    CLAUDE_API_KEY,
    OPENAI_API_KEY, OPENAI_MODEL,
    DEEPSEEK_API_KEY,
    DOUBAO_API_KEY, DOUBAO_BASE_URL, DOUBAO_MODEL_PRO, DOUBAO_MODEL_LITE,
    QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL_PLUS, QWEN_MODEL_FLASH,
    GLM_API_KEY, GLM_BASE_URL, GLM_MODEL_FLASH,
)

logger = logging.getLogger("shangtanai.ai")

CLAUDE_BASE_URL = "https://api.anthropic.com/v1/messages"
OPENAI_BASE_URL = "https://api.openai.com/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

# Task-specific max_tokens limits
TASK_MAX_TOKENS = {
    "analysis": 4096,
    "content_social": 3000,
    "content_formal": 3000,
    "listing": 2048,
    "batch": 1024,
    "keywords": 1024,
    "violation": 1024,
}

# Pricing per 1M tokens (USD) for cost tracking
PRICING = {
    "deepseek-reasoner": {"input": 0.28, "output": 0.42},
    "deepseek-chat": {"input": 0.28, "output": 0.42},
    DOUBAO_MODEL_PRO: {"input": 0.47, "output": 2.37},
    DOUBAO_MODEL_LITE: {"input": 0.042, "output": 0.042},
    QWEN_MODEL_PLUS: {"input": 0.40, "output": 1.20},
    QWEN_MODEL_FLASH: {"input": 0.05, "output": 0.20},
    GLM_MODEL_FLASH: {"input": 0.0, "output": 0.0},  # 免费
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model, {"input": 0.5, "output": 1.0})
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


async def call_openai(
    prompt: str,
    max_tokens: int = 4096,
    system: str | None = None,
    model: str | None = None,
) -> dict:
    """OpenAI GPT-4o — 测试阶段使用。"""
    model = model or OPENAI_MODEL or "gpt-4o"
    if not OPENAI_API_KEY:
        return {
            "text": f"[Mock OpenAI] {prompt[:50]}...",
            "model": model, "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
        }

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"model": model, "messages": messages, "max_tokens": max_tokens},
            timeout=90,
        )
        data = resp.json()

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cost = _estimate_cost(model, input_tokens, output_tokens)

    logger.info("ai_call", extra={
        "provider": "openai", "model": model,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cost_usd": round(cost, 6), "duration_ms": duration_ms,
    })
    return {"text": text, "model": model, "input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost}


async def call_claude(
    prompt: str,
    max_tokens: int = 4096,
    system: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """Claude API — 测试阶段使用。"""
    if not CLAUDE_API_KEY:
        return {
            "text": f"[Mock Claude] {prompt[:50]}...",
            "model": model, "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
        }

    messages = [{"role": "user", "content": prompt}]
    body = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        body["system"] = system

    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            CLAUDE_BASE_URL,
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=body,
            timeout=90,
        )
        data = resp.json()

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    text = data.get("content", [{}])[0].get("text", "")
    usage = data.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost = _estimate_cost(model, input_tokens, output_tokens)

    logger.info("ai_call", extra={
        "provider": "claude", "model": model,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cost_usd": round(cost, 6), "duration_ms": duration_ms,
    })
    return {"text": text, "model": model, "input_tokens": input_tokens, "output_tokens": output_tokens, "cost": cost}


async def _call_openai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int = 2048,
    system: str | None = None,
    timeout: int = 60,
) -> dict:
    """Generic caller for OpenAI-compatible APIs (DeepSeek/Qwen/GLM/Doubao all support this)."""
    if not api_key:
        return {
            "text": f"[Mock {model}] {prompt[:50]}...",
            "model": model, "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
        }

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    url = f"{base_url}/chat/completions"

    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        data = resp.json()

    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    # Parse response (OpenAI format)
    text = ""
    choices = data.get("choices", [])
    if choices:
        text = choices[0].get("message", {}).get("content", "")

    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cost = _estimate_cost(model, input_tokens, output_tokens)

    logger.info(
        "ai_call",
        extra={
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "duration_ms": duration_ms,
        },
    )
    return {
        "text": text,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }


# ── Provider-specific wrappers ──

async def call_deepseek(prompt: str, max_tokens: int = 4096, system: str | None = None, reasoning: bool = False) -> dict:
    """DeepSeek V3.2 — 市场分析/推理/降级备选"""
    model = "deepseek-reasoner" if reasoning else "deepseek-chat"
    return await _call_openai_compatible(
        base_url="https://api.deepseek.com/v1",
        api_key=DEEPSEEK_API_KEY,
        model=model,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=90,
    )


async def call_doubao(prompt: str, max_tokens: int = 3000, system: str | None = None, lite: bool = False) -> dict:
    """豆包 Seed 2.0 — 社媒内容生成（抖音/小红书）"""
    model = DOUBAO_MODEL_LITE if lite else DOUBAO_MODEL_PRO
    return await _call_openai_compatible(
        base_url=DOUBAO_BASE_URL,
        api_key=DOUBAO_API_KEY,
        model=model,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=60,
    )


async def call_qwen(prompt: str, max_tokens: int = 2048, system: str | None = None, flash: bool = False) -> dict:
    """通义千问 — 正式文案/Listing优化"""
    model = QWEN_MODEL_FLASH if flash else QWEN_MODEL_PLUS
    return await _call_openai_compatible(
        base_url=QWEN_BASE_URL,
        api_key=QWEN_API_KEY,
        model=model,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=60,
    )


async def call_glm(prompt: str, max_tokens: int = 1024, system: str | None = None) -> dict:
    """智谱 GLM-4-Flash — 免费快速任务"""
    return await _call_openai_compatible(
        base_url=GLM_BASE_URL,
        api_key=GLM_API_KEY,
        model=GLM_MODEL_FLASH,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=30,
    )


# ── Task routing ──

# 测试阶段：全部走 OpenAI GPT-4o
MODEL_MAP = {
    "analysis": (call_openai, {}),
    "content_social": (call_openai, {}),
    "content_formal": (call_openai, {}),
    "listing": (call_openai, {}),
    "keywords": (call_openai, {}),
    "violation": (call_openai, {}),
    "batch": (call_openai, {}),
}

# 正式上线时切换到这个（国内模型分工）：
# PRODUCTION_MODEL_MAP = {
#     "analysis": (call_deepseek, {"reasoning": True}),
#     "content_social": (call_doubao, {}),
#     "content_formal": (call_qwen, {}),
#     "listing": (call_qwen, {"flash": True}),
#     "keywords": (call_glm, {}),
#     "violation": (call_glm, {}),
#     "batch": (call_deepseek, {}),
# }

# Fallback chain
FALLBACK_CHAIN = [call_openai, call_deepseek, call_qwen]


async def ai_analyze(
    prompt: str,
    task_type: str = "analysis",
    system: str | None = None,
) -> str:
    """Route to appropriate model based on task type. Returns text response."""
    call_fn, kwargs = MODEL_MAP.get(task_type, (call_deepseek, {}))
    max_tokens = TASK_MAX_TOKENS.get(task_type, 2048)

    try:
        result = await call_fn(prompt, max_tokens=max_tokens, system=system, **kwargs)
        return result["text"]
    except Exception as e:
        logger.warning(f"AI primary call failed ({call_fn.__name__}): {e}")
        # Try fallback chain
        for fallback_fn in FALLBACK_CHAIN:
            if fallback_fn == call_fn:
                continue
            try:
                result = await fallback_fn(prompt, max_tokens=max_tokens, system=system)
                return result["text"]
            except Exception:
                continue
        logger.error("All AI providers failed")
        return "[AI 服务暂时不可用] 请稍后重试"


async def ai_analyze_full(
    prompt: str,
    task_type: str = "analysis",
    system: str | None = None,
) -> dict:
    """Same as ai_analyze but returns full metadata dict (text, model, tokens, cost)."""
    call_fn, kwargs = MODEL_MAP.get(task_type, (call_deepseek, {}))
    max_tokens = TASK_MAX_TOKENS.get(task_type, 2048)

    try:
        return await call_fn(prompt, max_tokens=max_tokens, system=system, **kwargs)
    except Exception as e:
        logger.warning(f"AI primary call failed ({call_fn.__name__}): {e}")
        for fallback_fn in FALLBACK_CHAIN:
            if fallback_fn == call_fn:
                continue
            try:
                return await fallback_fn(prompt, max_tokens=max_tokens, system=system)
            except Exception:
                continue
        logger.error("All AI providers failed")
        return {
            "text": "[AI 服务暂时不可用] 请稍后重试",
            "model": "none", "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
        }
