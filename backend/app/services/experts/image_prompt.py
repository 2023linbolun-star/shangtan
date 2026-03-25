"""
AI生图Prompt工程专家 — 动态AI Agent
根据内容策略和场景描述，生成高质量的AI生图prompt。

知识来源：图片Prompt工程专家 + 视觉叙事专家

支持平台：通义万相（中文prompt友好）
"""

SYSTEM = """你是一位专业的AI生图Prompt工程师，专精电商产品场景图和社交媒体配图。

你的核心能力：
- 5层Prompt结构：主体→环境→光照→技术参数→风格美学
- 电商产品摄影专精：白底图、场景图、细节图、对比图、氛围图
- 平台风格适配：抖音偏冲击力/高饱和，小红书偏清新/高级感/生活化
- 使用通义万相API，prompt用中文效果更好

你的输出必须遵守：
- 每个prompt都是独立完整的，不依赖其他图片
- 产品描述要具体（材质、颜色、形态），不能模糊
- 明确指定画面风格、光线、构图
- 不能出现真人面部（AI生人脸容易恐怖谷）
- 可以出现人体局部（手、身体轮廓、背影）
"""

# ── 抖音视频场景图Prompt ──

DOUYIN_IMAGE_PROMPT = """请为以下抖音视频的每个场景生成AI生图prompt。

## 产品信息
{product_info}

## 视频策略
{strategy_json}

## 视频脚本场景
{scenes_json}

## 要求
- 为每个场景生成1个生图prompt
- 画面比例9:16竖屏（1080x1920）
- 风格统一，视觉连贯
- 产品必须是画面主角
- 不出现真人正脸，可以出现手/身体局部/背影
- prompt用中文，适配通义万相

## 输出JSON格式
{{
  "scene_images": [
    {{
      "scene_number": 1,
      "prompt": "完整的中文生图prompt，包含：主体描述+环境+光照+风格",
      "negative_prompt": "不要出现的元素",
      "style_tag": "风格标签（如：商业摄影/生活场景/极简/赛博朋克）"
    }}
  ],
  "cover_image": {{
    "prompt": "封面图的生图prompt（最吸引眼球的一张）",
    "negative_prompt": "不要出现的元素"
  }},
  "visual_consistency": "整组图的统一视觉风格描述"
}}

只输出JSON。"""

# ── 小红书图文配图Prompt ──

XHS_IMAGE_PROMPT = """请为以下小红书笔记生成全套配图的AI生图prompt。

## 产品信息
{product_info}

## 内容策略
{strategy_json}

## 图片规划
{image_plan_json}

## 要求
- 共生成6张图的prompt（1封面+5内容图）
- 画面比例3:4竖版（1080x1440）
- 小红书审美：清新、高级感、生活化、有质感
- 封面图必须抓眼球，产品占画面60%以上
- 不出现真人正脸，可以出现手/身体局部/背影
- 配图要有叙事感：从吸引→展示→细节→场景→总结
- prompt用中文，适配通义万相

## 输出JSON格式
{{
  "images": [
    {{
      "position": "封面图",
      "prompt": "完整的中文生图prompt",
      "negative_prompt": "不要出现的元素",
      "text_overlay": "需要用Pillow叠加的文字（留空则不叠加）",
      "text_position": "文字位置（top/center/bottom）",
      "style_tag": "风格标签"
    }},
    {{
      "position": "图2",
      "prompt": "...",
      "negative_prompt": "...",
      "text_overlay": "...",
      "text_position": "...",
      "style_tag": "..."
    }}
  ],
  "color_palette": "整组图的主色调描述",
  "visual_consistency": "统一视觉风格描述"
}}

只输出JSON。"""


def build_douyin_image_prompt(
    product_info: str,
    strategy_json: str,
    scenes_json: str,
) -> str:
    """构建抖音视频场景图的生图prompt。"""
    return DOUYIN_IMAGE_PROMPT.format(
        product_info=product_info,
        strategy_json=strategy_json,
        scenes_json=scenes_json,
    )


def build_xhs_image_prompt(
    product_info: str,
    strategy_json: str,
    image_plan_json: str,
) -> str:
    """构建小红书图文配图的生图prompt。"""
    return XHS_IMAGE_PROMPT.format(
        product_info=product_info,
        strategy_json=strategy_json,
        image_plan_json=image_plan_json,
    )
