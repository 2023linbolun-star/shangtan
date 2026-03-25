"""抖音涨粉内容 — 生活妙招图解 Prompt 模板"""

SYSTEM = """你是一位生活达人，擅长把复杂的生活问题变成简单的图解教程。
你的内容特点：痛点精准、方法具体可操作、效果对比强烈。
内容将用于抖音图文轮播（5张图+AI配音+BGM），收藏率极高。"""


def build_prompt(product_info: str, style: str = "实用派", notes: str = "") -> str:
    return f"""请创作一条抖音生活妙招图文内容（5张图轮播）。

## 痛点/场景
{product_info}

## 风格：{style}
{f"## 额外要求：{notes}" if notes else ""}

## 规范
- 5张图：痛点场景→原理解释→方法步骤→效果对比→额外tips+互动
- 方法必须具体可操作（用什么+怎么用+多久见效）
- 标题文案：大字，每张不超20字
- 配音文稿：口语化，每张3-5秒
- 如果有相关产品可以推荐，在第5张图自然带出（但不强推）

## 输出JSON
{{
  "title": "标题（含问题和解决方案暗示，30字内）",
  "slides": [
    {{
      "slide_number": 1,
      "headline": "图上大字标题",
      "visual_description": "画面描述（AI生图用）",
      "voiceover": "配音文稿",
      "text_elements": ["其他文字元素"],
      "type": "pain_point | explanation | steps | result | tips"
    }}
  ],
  "voiceover_full": "完整配音文稿",
  "related_product": "可以自然关联的产品（如有）",
  "hashtags": ["#标签1", "#标签2"],
  "interaction_hook": "结尾互动引导语"
}}

只输出JSON。"""
