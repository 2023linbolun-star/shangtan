"""
风格注册表 — 管理所有可用的内容风格。

所有风格在模块加载时自动注册，Agent 通过 style_id 查找。
新增风格只需：1.写prompt模板 2.调register_style注册，不改任何现有代码。
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StyleConfig:
    """一个内容风格的完整配置。"""
    id: str                                 # "douyin_3act_drama"
    name: str                               # "3幕场景剧"
    platform: str                           # "douyin" | "xiaohongshu" | "both"
    category: str                           # "growth" | "selling" | "both"
    description: str                        # 用户看到的一句话描述
    prompt_module: str                      # prompt模板模块路径，如 "app.services.prompts.content_douyin"
    agent_class: str | None = None          # Agent类路径（可选，无则用通用Agent）
    expert_modules: list[str] = field(default_factory=list)  # 需要的专家模块
    default_params: dict[str, Any] = field(default_factory=dict)  # 默认参数
    customizable_fields: list[dict] = field(default_factory=list)  # 用户可调字段
    task_type: str = "content_social"       # AI Engine 路由的 task_type
    thumbnail: str = ""                     # 风格预览缩略图URL（前端展示用）
    tags: list[str] = field(default_factory=list)  # 标签，如 ["热门", "新"]


# ── 注册表 ──

STYLE_REGISTRY: dict[str, StyleConfig] = {}


def register_style(config: StyleConfig):
    """注册一个风格到全局注册表。"""
    STYLE_REGISTRY[config.id] = config


def get_style(style_id: str) -> StyleConfig | None:
    """根据 style_id 获取风格配置。"""
    return STYLE_REGISTRY.get(style_id)


def list_styles(
    platform: str | None = None,
    category: str | None = None,
) -> list[StyleConfig]:
    """列出所有可用风格，支持按平台和类别过滤。"""
    results = []
    for style in STYLE_REGISTRY.values():
        if platform and style.platform not in (platform, "both"):
            continue
        if category and style.category not in (category, "both"):
            continue
        results.append(style)
    return results


def get_default_style(platform: str, category: str = "selling") -> StyleConfig | None:
    """获取某平台某类别的默认风格（第一个注册的）。"""
    styles = list_styles(platform=platform, category=category)
    return styles[0] if styles else None


# ══════════════════════════════════════════════════════════════
#  内置风格注册（模块加载时自动执行）
# ══════════════════════════════════════════════════════════════

# ── 抖音带货 ──

register_style(StyleConfig(
    id="douyin_3act_drama",
    name="3幕场景剧",
    platform="douyin",
    category="selling",
    description="痛点冲击→转折发现→卖点连击→真香结局→互动钩子，20秒高完播率视频",
    prompt_module="app.services.prompts.content_douyin",
    agent_class="app.agents.content_agent.DouyinContentAgent",
    expert_modules=["douyin_strategy", "image_prompt"],
    task_type="content_douyin",
    default_params={"duration": 20, "scenes": 5, "format": "video"},
    tags=["推荐", "带货"],
    customizable_fields=[
        {"key": "voice_style", "label": "配音语气", "type": "select",
         "options": ["活力女声", "温柔女声", "醇厚男声", "专业解说"], "default": "活力女声"},
        {"key": "hook_preference", "label": "开头风格", "type": "select",
         "options": ["冲突反差", "提问悬念", "数据冲击", "共鸣代入"], "default": "冲突反差"},
        {"key": "selling_intensity", "label": "推销强度", "type": "select",
         "options": ["软种草", "中等推荐", "强力带货"], "default": "中等推荐"},
        {"key": "content_length", "label": "视频时长", "type": "select",
         "options": ["15秒", "20秒", "30秒", "45秒", "60秒"], "default": "20秒"},
    ],
))

register_style(StyleConfig(
    id="douyin_seeding",
    name="种草推荐",
    platform="douyin",
    category="selling",
    description="经典种草视频，产品展示+卖点讲解+使用场景，适合日用消费品",
    prompt_module="app.services.prompts.content_douyin",
    agent_class="app.agents.content_agent.DouyinContentAgent",
    expert_modules=["douyin_strategy"],
    task_type="content_douyin",
    default_params={"duration": 30, "scenes": 5, "format": "video"},
    tags=["经典"],
))

# ── 抖音涨粉 ──

register_style(StyleConfig(
    id="douyin_info_gap",
    name="信息差/冷知识",
    platform="douyin",
    category="growth",
    description="「90%的人不知道」类图文轮播，涨粉效率最高，收藏率是视频的2-3倍",
    prompt_module="app.services.prompts.growth_info_gap",
    task_type="content_xhs",  # → DeepSeek，中文最自然
    default_params={"slides": 5, "format": "carousel"},
    tags=["涨粉", "推荐"],
    customizable_fields=[
        {"key": "voice_style", "label": "语气", "type": "select",
         "options": ["揭秘感", "朋友聊天", "专业科普", "吐槽风"], "default": "揭秘感"},
        {"key": "hook_preference", "label": "钩子类型", "type": "select",
         "options": ["认知冲突", "数据反差", "提问式", "反常识"], "default": "认知冲突"},
    ],
))

register_style(StyleConfig(
    id="douyin_ranking",
    name="清单盘点/排行榜",
    platform="douyin",
    category="both",
    description="「最值得买的5款XX」排行榜，涨粉和带货双栖，搜索流量大",
    prompt_module="app.services.prompts.growth_ranking",
    task_type="content_xhs",
    default_params={"items": 5, "format": "video"},
    tags=["涨粉", "带货"],
))

register_style(StyleConfig(
    id="douyin_life_hack",
    name="生活妙招图解",
    platform="douyin",
    category="growth",
    description="「用这招一擦就干净」类妙招图文，收藏率极高，自然过渡到好物推荐",
    prompt_module="app.services.prompts.growth_life_hack",
    task_type="content_xhs",
    default_params={"slides": 5, "format": "carousel"},
    tags=["涨粉"],
))

# ── 小红书 ──

register_style(StyleConfig(
    id="xhs_review",
    name="真人测评",
    platform="xiaohongshu",
    category="selling",
    description="模拟真人不露脸测评，公正客观有缺点，完全去AI味，最像真人写的笔记",
    prompt_module="app.services.prompts.xhs_review",
    agent_class="app.agents.content_agent.XHSContentAgent",
    expert_modules=["xhs_strategy", "image_prompt"],
    task_type="content_xhs",
    default_params={"images": 6, "format": "note", "image_style": "review"},
    tags=["推荐", "去AI味"],
    customizable_fields=[
        {"key": "voice_style", "label": "写作风格", "type": "select",
         "options": ["理性测评", "闺蜜分享", "专业分析", "学生党视角"], "default": "理性测评"},
        {"key": "visual_preference", "label": "图片风格", "type": "select",
         "options": ["真人手机拍", "日系清透", "极简白底", "生活感"], "default": "真人手机拍"},
        {"key": "selling_intensity", "label": "种草强度", "type": "select",
         "options": ["纯测评不推荐", "轻度种草", "明确推荐"], "default": "轻度种草"},
    ],
))

register_style(StyleConfig(
    id="xhs_seeding",
    name="闺蜜种草",
    platform="xiaohongshu",
    category="selling",
    description="经典种草笔记，闺蜜分享语气，适合美妆/穿搭/生活好物",
    prompt_module="app.services.prompts.content_xiaohongshu",
    agent_class="app.agents.content_agent.XHSContentAgent",
    expert_modules=["xhs_strategy", "image_prompt"],
    task_type="content_xhs",
    default_params={"images": 6, "format": "note", "image_style": "lifestyle"},
    tags=["经典"],
))

# ── 电商Listing ──

register_style(StyleConfig(
    id="listing_taobao",
    name="淘宝商品文案",
    platform="both",
    category="selling",
    description="淘宝/天猫商品详情页文案，5张主图描述+卖点提炼+详情页结构",
    prompt_module="app.services.prompts.content_taobao",
    task_type="content_formal",
    default_params={"format": "listing"},
    tags=["电商"],
))

register_style(StyleConfig(
    id="listing_pdd",
    name="拼多多商品文案",
    platform="both",
    category="selling",
    description="拼多多商品文案，价格敏感用户导向，短详情+强性价比话术",
    prompt_module="app.services.prompts.content_pdd",
    task_type="content_formal",
    default_params={"format": "listing"},
    tags=["电商"],
))
