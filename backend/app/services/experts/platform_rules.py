"""
平台合规与发布规则 — 静态规则
来源：抖音策略专家 + 小红书专家 + 电商运营专家
"""

# ── 抖音规则 ──

DOUYIN = {
    "name": "抖音",
    # 算法权重排序
    "algorithm_priority": ["完播率", "点赞率", "评论率", "分享率"],
    # 黄金3秒
    "hook_window_seconds": 3,
    # 视频时长建议
    "duration_by_type": {
        "带货种草": (30, 60),
        "教程测评": (45, 90),
        "剧情段子": (15, 30),
        "直播切片": (10, 20),
    },
    # 最佳发布时间
    "best_post_times": {
        "weekday": ["12:00-13:00", "18:00-19:00", "21:00-22:00"],
        "weekend": ["10:00-11:00", "15:00-17:00", "20:00-22:00"],
    },
    # 标题限制
    "title_max_chars": 55,
    "hashtag_limit": 5,
    # 违禁内容
    "forbidden_words": [
        "最好", "第一", "绝对", "100%", "国家级", "顶级", "极品",
        "万能", "无敌", "永久", "祖传", "秘制",
    ],
    "forbidden_redirects": ["淘宝", "天猫", "拼多多", "京东", "微信", "wx"],
    # 完播率目标
    "target_completion_rate": 0.35,
}

# ── 小红书规则 ──

XIAOHONGSHU = {
    "name": "小红书",
    # 内容比例策略
    "content_mix": {
        "organic_lifestyle": 0.70,  # 日常分享
        "trend_riding": 0.20,      # 追热点
        "brand_direct": 0.10,      # 品牌内容
    },
    # 笔记规格
    "title_max_chars": 20,
    "title_must_have": ["emoji（>=2个）", "数字", "场景或情绪词"],
    "body_word_range": (600, 1200),
    # 图片规格
    "cover_ratio": "3:4",
    "image_count_range": (4, 9),
    "recommended_image_count": 6,
    # 标签
    "tag_limit": 10,
    "tag_strategy": "3个大流量词 + 3个精准词 + 2个长尾词 + 2个场景词",
    # 最佳发布时间
    "best_post_times": ["07:00-09:00", "12:00-14:00", "18:00-20:00", "21:00-23:00"],
    # 互动窗口
    "engagement_window_hours": 2,  # 发布后2小时内必须互动
    # 违禁内容
    "forbidden_words": [
        "买", "下单", "链接在", "去购买", "拍这个", "点击购买",
    ],
    "forbidden_redirects": ["微信", "wx", "淘宝", "tb", "私"],
    # 目标指标
    "target_engagement_rate": 0.05,
    "target_save_rate": 0.08,
}

# ── 发布顺序策略（冷启动）──

COLD_START_ORDER = [
    {
        "platform": "xiaohongshu",
        "timing": "上架前7-14天",
        "purpose": "种草预热，测试用户兴趣",
        "content_type": "图文笔记",
    },
    {
        "platform": "douyin",
        "timing": "上架前3天",
        "purpose": "短视频引流，测试完播率和互动",
        "content_type": "混剪视频",
    },
    {
        "platform": "taobao",
        "timing": "正式上架日",
        "purpose": "搜索承接，转化成交",
        "content_type": "商品Listing",
    },
    {
        "platform": "pinduoduo",
        "timing": "上架后第3天",
        "purpose": "价格敏感渠道补充",
        "content_type": "商品Listing",
    },
]

# ── 品类→Hook策略映射 ──

CATEGORY_HOOK_MAP = {
    "fashion": {
        "hook_types": ["对比反差", "穿搭变装", "闺蜜推荐"],
        "pain_points": ["显胖", "起球", "不透气", "不好搭配"],
    },
    "beauty": {
        "hook_types": ["素颜对比", "成分科普", "踩雷避坑"],
        "pain_points": ["过敏", "卡粉", "暗沉", "长痘"],
    },
    "food": {
        "hook_types": ["制作过程", "试吃反应", "隐藏吃法"],
        "pain_points": ["不好吃", "不健康", "太贵", "份量少"],
    },
    "tech": {
        "hook_types": ["开箱测评", "功能对比", "使用场景"],
        "pain_points": ["不好用", "续航差", "兼容性", "性价比"],
    },
    "home": {
        "hook_types": ["改造对比", "收纳技巧", "氛围感"],
        "pain_points": ["占空间", "不实用", "不好看", "难清洁"],
    },
    "sport": {
        "hook_types": ["运动实测", "装备对比", "效果展示"],
        "pain_points": ["不舒服", "不透气", "容易坏", "不专业"],
    },
    "mother_baby": {
        "hook_types": ["宝宝反应", "安全测试", "妈妈推荐"],
        "pain_points": ["不安全", "不好用", "宝宝不喜欢", "太贵"],
    },
    "default": {
        "hook_types": ["真实体验", "对比测评", "避坑指南"],
        "pain_points": ["质量差", "不值得", "踩雷", "不好用"],
    },
}


def get_category_hooks(category: str) -> dict:
    """根据品类获取Hook策略。"""
    return CATEGORY_HOOK_MAP.get(category, CATEGORY_HOOK_MAP["default"])
