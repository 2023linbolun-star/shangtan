"""抖音涨粉/带货内容 — 清单盘点/排行榜 Prompt 模板"""

SYSTEM = """你是一位消费品测评专家，擅长用排行榜和清单盘点的形式帮用户做消费决策。
你的内容特点：信息密度高，每款产品一句话核心卖点，排名递进制造期待感。
内容将用于抖音视频（产品轮播+AI配音+字幕+BGM）。"""


def build_prompt(product_info: str, style: str = "专业测评", notes: str = "") -> str:
    return f"""请创作一条抖音清单盘点视频内容（TOP 5排行榜）。

## 品类/产品信息
{product_info}

## 风格：{style}
{f"## 额外要求：{notes}" if notes else ""}

## 规范
- TOP 5 排行，从第5名到第1名（递进制造期待感）
- 每款产品：品名+一句话核心卖点+价格区间+适合人群
- 开头3秒：强钩子（"花3000块测了20款，就这5款值得买"）
- 结尾：总结+互动引导
- 总时长25-35秒

## 输出JSON
{{
  "title": "视频标题（30字内）",
  "hook": "开头3秒钩子文案",
  "items": [
    {{
      "rank": 5,
      "name": "产品名称",
      "one_liner": "一句话核心卖点",
      "price_range": "价格区间",
      "target_audience": "适合人群",
      "visual_description": "展示画面描述（AI生图用）",
      "voiceover": "这款的配音文案"
    }}
  ],
  "summary_voiceover": "结尾总结配音",
  "interaction_hook": "互动引导语",
  "hashtags": ["#标签1", "#标签2"]
}}

只输出JSON。"""
