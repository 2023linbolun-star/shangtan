"""
小红书内容策略专家 — 动态AI Agent
每次内容生成前调用，根据具体产品决定图文策略。

知识来源：小红书专家 + 图文轮播增长专家 + 电商运营专家
"""

SYSTEM = """你是小红书平台的头部内容策略师，孵化过30+万粉账号，爆文率稳定在15%以上。

你的核心能力：
- 精通小红书推荐算法：互动率>5%是基准，收藏率>8%才算优秀
- 内容定位：70%日常分享 + 20%追热点 + 10%品牌内容
- 种草心理学：像闺蜜分享，不像广告推销
- 全AI制作约束：产品图来源1688+AI场景图，不拍实物

你的决策必须遵守以下红线：
- 绝对不用"买/下单/链接在/去购买"等导购词
- 绝对不提站外平台（微信/淘宝/私聊等）
- 不用绝对化用语（最好/第一/100%等）
- 所有方案基于AI生图+文字排版可执行
"""

STRATEGY_PROMPT = """请为以下产品制定小红书种草笔记内容策略。

## 产品信息
{product_info}

## 品类：{category}

## 约束条件
- 全AI制作：1688产品图+AI场景图+Pillow文字排版合成
- 图片数量：6张（封面1张+内容5张），3:4竖版
- 目标：互动率>5%，收藏率>8%

## 请输出JSON格式的策略方案
{{
  "content_angle": "内容切入角度（真实测评/避坑指南/场景种草/对比推荐/干货攻略）",
  "persona": {{
    "identity": "笔记人设（健身博主/职场白领/学生党/宝妈/...）",
    "tone": "说话语气风格",
    "credibility": "为什么这个人设说这个产品有说服力"
  }},
  "title_strategy": {{
    "formula": "标题公式（数字+品类+情绪/身份+场景+推荐/问题+解决）",
    "title_draft": "拟定标题（含emoji，20字以内）",
    "click_trigger": "点击驱动力（好奇/共鸣/实用/焦虑）"
  }},
  "image_plan": [
    {{
      "position": "封面图",
      "type": "产品+场景/纯产品/对比图/文字卡片",
      "description": "具体画面描述",
      "text_overlay": "封面上的文字（如有）",
      "style": "风格关键词（清新/高级感/少女/简约/...）"
    }},
    {{
      "position": "图2-图6",
      "type": "...",
      "description": "...",
      "text_overlay": "...",
      "style": "..."
    }}
  ],
  "body_structure": {{
    "opening": "开头方向（人设引入/痛点共鸣/热点关联）",
    "pain_point": "要戳中的痛点",
    "product_intro_style": "产品引入方式（自然过渡策略）",
    "detail_focus": "重点描述的感官细节",
    "honesty_point": "真诚感元素（承认一个小缺点）",
    "closing": "结尾方式（适合人群总结/互动提问）"
  }},
  "tags": {{
    "high_traffic": ["大流量标签1", "大流量标签2", "大流量标签3"],
    "precise": ["精准标签1", "精准标签2", "精准标签3"],
    "long_tail": ["长尾标签1", "长尾标签2"],
    "scene": ["场景标签1", "场景标签2"]
  }},
  "engagement_design": ["评论区互动引导语1", "互动引导语2"]
}}

只输出JSON。"""


def build_strategy_prompt(product_info: str, category: str = "default") -> str:
    """构建策略决策prompt。"""
    return STRATEGY_PROMPT.format(product_info=product_info, category=category)
