"""
违规词检测服务
广告法违禁词 + 各平台特定规则 + 功效宣称限制
"""

import re

# ── 广告法违禁词（核心集）──
AD_LAW_FORBIDDEN = [
    "最", "第一", "唯一", "首个", "首选", "顶级", "极品", "国家级", "世界级",
    "全网最低", "史上最", "万能", "绝对", "100%", "永久", "无敌", "极致",
    "秒杀一切", "独一无二", "绝无仅有", "前无古人", "无与伦比",
    "驰名商标", "国家免检", "老字号",
]

# ── 平台特定禁词 ──
PLATFORM_FORBIDDEN: dict[str, list[str]] = {
    "taobao": ["天猫同款", "淘宝爆款", "微信", "wx", "抖音同款"],
    "douyin": ["淘宝", "天猫", "拼多多", "微信号", "抖音同款"],
    "pinduoduo": ["天猫同款", "淘宝爆款", "正品保障", "微信"],
    "xiaohongshu": ["买", "下单", "链接在", "去购买", "淘宝", "天猫", "拼多多", "微信号"],
}

# ── 功效宣称限制（品类→禁止用语）──
EFFICACY_FORBIDDEN: dict[str, list[str]] = {
    "化妆品": ["治疗", "去除", "根治", "药用", "医疗级"],
    "食品": ["疗效", "治愈", "预防疾病", "替代药物", "保健功能"],
    "服饰": ["防辐射", "抗菌99%", "医用级"],
    "保健品": ["治愈", "根治", "替代药物"],
}


def check_violations(
    text: str,
    platform: str = "",
    category: str = "",
) -> dict:
    """
    检测文本中的违规内容。

    Returns:
        {
            "has_violation": bool,
            "risk_level": "green" | "yellow" | "red",
            "issues": [{"type": str, "keyword": str, "detail": str, "suggestion": str}]
        }
    """
    issues = []
    text_lower = text.lower()

    # 1. 广告法违禁词
    for word in AD_LAW_FORBIDDEN:
        if word in text:
            issues.append({
                "type": "广告法",
                "keyword": word,
                "detail": f"包含广告法违禁词「{word}」",
                "suggestion": f"删除或替换「{word}」",
            })

    # 2. 平台特定禁词
    platform_words = PLATFORM_FORBIDDEN.get(platform, [])
    for word in platform_words:
        if word.lower() in text_lower:
            issues.append({
                "type": "平台规则",
                "keyword": word,
                "detail": f"{platform}平台禁止出现「{word}」",
                "suggestion": f"删除「{word}」",
            })

    # 3. 功效宣称
    for cat, words in EFFICACY_FORBIDDEN.items():
        if cat in category or not category:
            for word in words:
                if word in text:
                    issues.append({
                        "type": "功效宣称",
                        "keyword": word,
                        "detail": f"该品类禁止使用「{word}」等功效宣称",
                        "suggestion": f"改用合规表述替代「{word}」",
                    })

    # 4. 联系方式检测
    phone_pattern = re.compile(r"1[3-9]\d{9}")
    wechat_pattern = re.compile(r"(微信|wx|v信|薇信)[\s:：]?\s*\w+", re.IGNORECASE)
    if phone_pattern.search(text):
        issues.append({
            "type": "站外引流",
            "keyword": "手机号",
            "detail": "内容中包含手机号码",
            "suggestion": "删除手机号",
        })
    if wechat_pattern.search(text):
        issues.append({
            "type": "站外引流",
            "keyword": "微信号",
            "detail": "内容中包含微信联系方式",
            "suggestion": "删除微信相关信息",
        })

    # Risk level
    if not issues:
        risk_level = "green"
    elif any(i["type"] == "广告法" for i in issues):
        risk_level = "red"
    else:
        risk_level = "yellow"

    return {
        "has_violation": len(issues) > 0,
        "risk_level": risk_level,
        "issues": issues,
    }
