"""
选题批量生成器 — 为涨粉内容自动生成选题库。

支持：信息差选题、生活妙招选题、清单盘点选题。
选题来源：AI生成 + 品类痛点库交叉。
"""

import json
import logging
from app.services.ai_engine import ai_analyze_full

logger = logging.getLogger("shangtanai.topic_generator")


async def generate_info_gap_topics(category: str, count: int = 20) -> list[dict]:
    """
    批量生成信息差/冷知识选题。

    Returns:
        [{"title": "...", "hook": "...", "category": "...", "linkable_product": "..."}, ...]
    """
    prompt = f"""请生成{count}个适合抖音图文的信息差/冷知识选题。

## 品类领域：{category}

## 选题要求
- 每个选题必须有认知冲突（"大部分人都不知道/做错了"）
- 覆盖不同角度：使用误区、隐藏知识、省钱技巧、健康安全、效率提升
- 标注哪些选题可以自然衔接到产品推荐（linkable_product不为空）
- 选题不能太专业（普通人看不懂）也不能太常识（没有信息差）

## 输出JSON
{{
  "topics": [
    {{
      "title": "选题标题（含数字和冲突词）",
      "hook": "3秒钩子文案",
      "angle": "切入角度（误区/隐藏知识/省钱/安全/效率）",
      "category": "{category}",
      "linkable_product": "可关联的产品类型（如有，无则留空）",
      "difficulty": "制作难度（低/中/高）"
    }}
  ]
}}

只输出JSON。"""

    result = await ai_analyze_full(prompt, task_type="strategy")
    return _parse_topics(result["text"])


async def generate_life_hack_topics(category: str, count: int = 20) -> list[dict]:
    """批量生成生活妙招选题。"""
    prompt = f"""请生成{count}个适合抖音图文的生活妙招选题。

## 品类领域：{category}

## 选题要求
- 每个选题解决一个具体的生活痛点
- 方法必须简单可操作（材料易得、步骤不超3步）
- 效果要有对比性（before/after明显）
- 标注哪些选题可以引出产品推荐

## 输出JSON
{{
  "topics": [
    {{
      "title": "选题标题（含问题和暗示有解决方案）",
      "pain_point": "痛点描述",
      "solution_hint": "方法概要",
      "category": "{category}",
      "linkable_product": "可关联的产品（如有）",
      "difficulty": "制作难度"
    }}
  ]
}}

只输出JSON。"""

    result = await ai_analyze_full(prompt, task_type="strategy")
    return _parse_topics(result["text"])


async def generate_ranking_topics(
    category: str,
    products: list[dict] | None = None,
    count: int = 10,
) -> list[dict]:
    """基于品类（可选产品列表）生成清单盘点选题。"""
    product_context = ""
    if products:
        product_context = f"\n## 可用产品列表\n{json.dumps(products[:10], ensure_ascii=False)}"

    prompt = f"""请生成{count}个适合抖音的清单盘点/排行榜选题。

## 品类领域：{category}
{product_context}

## 选题要求
- 格式："最值得买的N款XX"、"XX品类红黑榜"、"N款XX横向对比"
- 覆盖不同价格段、不同人群、不同场景
- 标注是涨粉版（不挂车）还是带货版（可挂车）

## 输出JSON
{{
  "topics": [
    {{
      "title": "选题标题",
      "format": "TOP N / 红黑榜 / 横向对比",
      "item_count": 5,
      "price_range": "价格区间",
      "target_audience": "目标人群",
      "category": "{category}",
      "monetizable": true,
      "difficulty": "制作难度"
    }}
  ]
}}

只输出JSON。"""

    result = await ai_analyze_full(prompt, task_type="strategy")
    return _parse_topics(result["text"])


def _parse_topics(text: str) -> list[dict]:
    """安全解析选题JSON。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
        return data.get("topics", [])
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(cleaned[start:end + 1])
                return data.get("topics", [])
            except json.JSONDecodeError:
                pass
    logger.warning(f"Failed to parse topics: {cleaned[:100]}")
    return []
