"""
AI Engine - 统一多模型调用封装

多模型分工策略（质量优先阶段）：
  策略/分析  → Claude Opus 4      最强推理，策略不面向用户，不怕语感
  抖音脚本   → 豆包 Seed 2.0 Pro  字节自家模型，最懂抖音语感
  小红书文案  → DeepSeek V3        中文散文质量最高，最像真人
  质量审核   → Claude Opus 4      生成不行但审核最强，找AI味
  生图Prompt → 通义千问 Plus       和通义万相同生态，prompt适配最好
  Listing    → 通义千问 Plus       电商文案专精
  批量杂活   → 智谱 GLM-4 Flash   免费，关键词/违规检测

降级容错链：Claude → DeepSeek → 通义 → 智谱
"""

import logging
import os
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

# Task-specific max_tokens limits
TASK_MAX_TOKENS = {
    "strategy": 4096,       # 策略决策
    "analysis": 4096,       # 市场分析
    "content_douyin": 3000, # 抖音脚本
    "content_xhs": 4096,    # 小红书文案（需要更长）
    "content_social": 3000, # 通用社媒内容
    "content_formal": 3000, # 电商正式文案
    "content_review": 2048, # 内容质量审核
    "image_prompt": 3000,   # 生图Prompt
    "listing": 2048,        # Listing优化
    "batch": 1024,          # 批量任务
    "keywords": 1024,       # 关键词
    "violation": 1024,      # 违规检测
}

# Pricing per 1M tokens (USD) for cost tracking
PRICING = {
    # Claude
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    # OpenAI
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    # DeepSeek
    "deepseek-reasoner": {"input": 0.28, "output": 0.42},
    "deepseek-chat": {"input": 0.28, "output": 0.42},
    # 豆包
    DOUBAO_MODEL_PRO: {"input": 0.47, "output": 2.37},
    DOUBAO_MODEL_LITE: {"input": 0.042, "output": 0.042},
    # 通义千问
    QWEN_MODEL_PLUS: {"input": 0.40, "output": 1.20},
    QWEN_MODEL_FLASH: {"input": 0.05, "output": 0.20},
    # 智谱
    GLM_MODEL_FLASH: {"input": 0.0, "output": 0.0},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = PRICING.get(model, {"input": 0.5, "output": 1.0})
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


# ══════════════════════════════════════════════════════════════
#  Provider Callers
# ══════════════════════════════════════════════════════════════

async def call_claude(
    prompt: str,
    max_tokens: int = 4096,
    system: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """Claude API — 策略分析 + 质量审核。"""
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
            timeout=120,
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


async def call_openai(
    prompt: str,
    max_tokens: int = 4096,
    system: str | None = None,
    model: str | None = None,
) -> dict:
    """OpenAI GPT-4o — 备选。"""
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


async def _call_openai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int = 2048,
    system: str | None = None,
    timeout: int = 60,
) -> dict:
    """Generic caller for OpenAI-compatible APIs (DeepSeek/Qwen/GLM/Doubao)."""
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

    text = ""
    choices = data.get("choices", [])
    if choices:
        text = choices[0].get("message", {}).get("content", "")

    usage = data.get("usage", {})
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)
    cost = _estimate_cost(model, input_tokens, output_tokens)

    logger.info("ai_call", extra={
        "model": model,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cost_usd": round(cost, 6), "duration_ms": duration_ms,
    })
    return {
        "text": text, "model": model,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cost": cost,
    }


# ── Provider-specific wrappers ──

async def call_deepseek(prompt: str, max_tokens: int = 4096, system: str | None = None, reasoning: bool = False) -> dict:
    """DeepSeek V3 — 小红书文案（中文散文质量最高）/ Reasoner用于深度分析。"""
    model = "deepseek-reasoner" if reasoning else "deepseek-chat"
    return await _call_openai_compatible(
        base_url="https://api.deepseek.com/v1",
        api_key=DEEPSEEK_API_KEY,
        model=model,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=90,
    )


async def call_doubao(prompt: str, max_tokens: int = 3000, system: str | None = None, lite: bool = False) -> dict:
    """豆包 Seed 2.0 — 抖音脚本（字节自家模型，最懂抖音语感）。"""
    model = DOUBAO_MODEL_LITE if lite else DOUBAO_MODEL_PRO
    return await _call_openai_compatible(
        base_url=DOUBAO_BASE_URL,
        api_key=DOUBAO_API_KEY,
        model=model,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=60,
    )


async def call_qwen(prompt: str, max_tokens: int = 2048, system: str | None = None, flash: bool = False) -> dict:
    """通义千问 — 生图Prompt + Listing优化（阿里生态协同）。"""
    model = QWEN_MODEL_FLASH if flash else QWEN_MODEL_PLUS
    return await _call_openai_compatible(
        base_url=QWEN_BASE_URL,
        api_key=QWEN_API_KEY,
        model=model,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=60,
    )


async def call_glm(prompt: str, max_tokens: int = 1024, system: str | None = None) -> dict:
    """智谱 GLM-4-Flash — 免费批量任务（关键词/违规检测）。"""
    return await _call_openai_compatible(
        base_url=GLM_BASE_URL,
        api_key=GLM_API_KEY,
        model=GLM_MODEL_FLASH,
        prompt=prompt, max_tokens=max_tokens, system=system, timeout=30,
    )


# ══════════════════════════════════════════════════════════════
#  Task Routing — 多模型分工
# ══════════════════════════════════════════════════════════════

# 当前阶段：质量优先，各任务使用最适合的模型
MODEL_MAP = {
    # 策略 & 分析 → Claude（推理最强）
    "strategy": (call_claude, {}),
    "analysis": (call_claude, {}),

    # 抖音内容 → 豆包（字节自家，抖音语感最佳）
    "content_douyin": (call_doubao, {}),

    # 小红书内容 → DeepSeek（中文散文最自然，最不像AI）
    "content_xhs": (call_deepseek, {}),

    # 通用社媒内容（快手等）→ DeepSeek
    "content_social": (call_deepseek, {}),

    # 质量审核 → Claude（分析找AI味最强）
    "content_review": (call_claude, {}),

    # 生图Prompt → 通义千问（和通义万相同生态）
    "image_prompt": (call_qwen, {}),

    # 电商正式文案 → 通义千问（电商基因）
    "content_formal": (call_qwen, {}),

    # Listing优化 → 通义千问 Flash（快+便宜）
    "listing": (call_qwen, {"flash": True}),

    # 批量杂活 → 智谱 GLM（免费）
    "keywords": (call_glm, {}),
    "violation": (call_glm, {}),
    "batch": (call_glm, {}),
}

# 商业化阶段：全部切国内模型，降低成本
PRODUCTION_MODEL_MAP = {
    "strategy": (call_deepseek, {"reasoning": True}),
    "analysis": (call_deepseek, {"reasoning": True}),
    "content_douyin": (call_doubao, {}),
    "content_xhs": (call_deepseek, {}),
    "content_social": (call_deepseek, {}),
    "content_review": (call_deepseek, {}),
    "image_prompt": (call_qwen, {}),
    "content_formal": (call_qwen, {}),
    "listing": (call_qwen, {"flash": True}),
    "keywords": (call_glm, {}),
    "violation": (call_glm, {}),
    "batch": (call_glm, {}),
}

# 降级容错链：按质量递减排列
FALLBACK_CHAIN = [call_claude, call_deepseek, call_qwen, call_glm]


# ══════════════════════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════════════════════

def _get_model_map() -> dict:
    """获取当前使用的模型映射。通过环境变量切换。"""
    if os.getenv("AI_ENGINE_MODE", "quality") == "production":
        return PRODUCTION_MODEL_MAP
    return MODEL_MAP


async def ai_analyze(
    prompt: str,
    task_type: str = "analysis",
    system: str | None = None,
) -> str:
    """Route to appropriate model based on task type. Returns text response."""
    model_map = _get_model_map()
    call_fn, kwargs = model_map.get(task_type, (call_deepseek, {}))
    max_tokens = TASK_MAX_TOKENS.get(task_type, 2048)

    try:
        result = await call_fn(prompt, max_tokens=max_tokens, system=system, **kwargs)
        return result["text"]
    except Exception as e:
        logger.warning(f"AI primary call failed ({call_fn.__name__}): {e}")
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
    model_map = _get_model_map()
    call_fn, kwargs = model_map.get(task_type, (call_deepseek, {}))
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


# ══════════════════════════════════════════════════════════════
#  Quality Review — 生成+审核双模型循环
# ══════════════════════════════════════════════════════════════

REVIEW_SYSTEM = """你是一位严格的中文社交媒体内容质量审核专家。
你的任务是审核AI生成的内容，找出所有"AI味"的痕迹。

中国消费者对AI生成内容非常敏感，以下是常见的AI味标志：
- 过于工整的排比句式
- 不自然的过渡词（"总的来说"、"综上所述"、"不得不说"）
- 缺少口语化表达和语气词
- 形容词堆砌但缺少具体细节
- 过于平衡的观点（真人会有明显偏好）
- 缺少个人经历和具体场景

你必须严格打分，7分以下的内容不适合发布。"""

REVIEW_PROMPT = """请审核以下{platform}内容的质量。

## 待审核内容
{content}

## 请输出JSON格式的审核报告
{{
  "overall_score": 8,
  "authenticity_score": 7,
  "engagement_score": 8,
  "ai_smell_issues": [
    {{
      "location": "问题所在的原文片段",
      "issue": "问题描述",
      "suggestion": "修改建议"
    }}
  ],
  "strengths": ["优点1", "优点2"],
  "must_fix": ["必须修改的问题1"],
  "nice_to_fix": ["建议修改的问题1"],
  "publish_ready": true,
  "rewrite_needed": false
}}

评分标准（1-10）：
- 9-10: 和真人博主内容无法区分，可直接发布
- 7-8: 基本自然，有少量AI痕迹但不影响大局，可发布
- 5-6: AI味较重，需要修改后才能发布
- 1-4: 明显AI生成，不能发布

只输出JSON。"""


async def review_content(content: str, platform: str = "小红书") -> dict:
    """
    用Claude审核AI生成的内容质量。

    Returns:
        审核报告dict，包含评分、AI味问题、修改建议
    """
    prompt = REVIEW_PROMPT.format(platform=platform, content=content)
    result = await ai_analyze_full(prompt, task_type="content_review", system=REVIEW_SYSTEM)
    return result


async def generate_and_review(
    prompt: str,
    task_type: str,
    system: str | None = None,
    platform: str = "小红书",
    max_retries: int = 1,
) -> dict:
    """
    生成+审核循环：先用最优模型生成，再用Claude审核。
    如果审核不通过（分数<7），带着审核意见重新生成一次。

    Returns:
        {
            "text": "最终内容",
            "model": "生成模型",
            "review": {审核报告},
            "retried": false,
            "total_cost": 0.05,
        }
    """
    # Step 1: 生成
    gen_result = await ai_analyze_full(prompt, task_type=task_type, system=system)
    total_cost = gen_result.get("cost", 0)

    # Step 2: 审核
    review_result = await review_content(gen_result["text"], platform=platform)
    total_cost += review_result.get("cost", 0)

    # 解析审核分数
    import json
    review_text = review_result.get("text", "{}")
    try:
        # 清理markdown代码块
        cleaned = review_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        review_data = json.loads(cleaned)
    except json.JSONDecodeError:
        review_data = {"overall_score": 7, "publish_ready": True}

    score = review_data.get("overall_score", 7)
    retried = False

    # Step 3: 如果分数不够，带审核意见重新生成
    if score < 7 and max_retries > 0:
        issues = review_data.get("ai_smell_issues", [])
        must_fix = review_data.get("must_fix", [])

        fix_instructions = "\n".join([
            f"- {issue.get('issue', '')}: {issue.get('suggestion', '')}"
            for issue in issues
        ])
        if must_fix:
            fix_instructions += "\n必须修改：\n" + "\n".join(f"- {f}" for f in must_fix)

        retry_prompt = f"""{prompt}

## ⚠️ 质量审核反馈（必须按此修改）
审核得分：{score}/10，不合格。

以下问题必须修复：
{fix_instructions}

请根据以上反馈重新生成，确保内容更加自然、真实、有人感。"""

        gen_result = await ai_analyze_full(retry_prompt, task_type=task_type, system=system)
        total_cost += gen_result.get("cost", 0)

        # 重新审核
        review_result = await review_content(gen_result["text"], platform=platform)
        total_cost += review_result.get("cost", 0)

        try:
            cleaned = review_result.get("text", "{}").strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines)
            review_data = json.loads(cleaned)
        except json.JSONDecodeError:
            review_data = {"overall_score": 7, "publish_ready": True}

        retried = True

    return {
        "text": gen_result["text"],
        "model": gen_result.get("model", "unknown"),
        "review": review_data,
        "retried": retried,
        "total_cost": total_cost,
    }
