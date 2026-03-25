"""抖音涨粉内容 — 信息差/冷知识图文 Prompt 模板"""

SYSTEM = """你是一位专精信息差内容的创作者，擅长把专业知识转化为「你不知道的XX」类图文。
你的内容特点：开头制造认知冲突，核心只讲一个信息点，结尾引导互动。
内容将用于抖音图文轮播（5张图+AI配音+BGM）。"""


def build_prompt(product_info: str, style: str = "揭秘感", notes: str = "") -> str:
    return f"""请创作一条抖音信息差图文内容（5张图轮播）。

## 选题方向
{product_info}

## 风格：{style}
{f"## 额外要求：{notes}" if notes else ""}

## 规范
- 5张图：钩子→痛点放大→核心知识点→进阶tips→互动引导
- 标题文案：大字，每张不超20字
- 配音文稿：口语化，每张3-5秒（15-30字）
- 语气像懂行的朋友在聊天

## 输出JSON
{{
  "title": "标题（含数字和冲突词，30字内）",
  "slides": [
    {{
      "slide_number": 1,
      "headline": "图上大字标题",
      "visual_description": "画面描述（AI生图用）",
      "voiceover": "配音文稿",
      "text_elements": ["其他文字元素"]
    }}
  ],
  "voiceover_full": "完整配音文稿",
  "hashtags": ["#标签1", "#标签2"],
  "interaction_hook": "结尾互动引导语"
}}

只输出JSON。"""
