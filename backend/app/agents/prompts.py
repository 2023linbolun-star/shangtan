"""
动态 Prompt 构建器 — 将 Agent 静态身份 + 用户 DNA + 案例 + 教训 + 细粒度偏好 组合成完整 system prompt。
"""


def build_agent_system_prompt(
    role: str,
    user_dna: dict | None = None,
    few_shot_examples: list[dict] | None = None,
    failure_guardrails: list[str] | None = None,
) -> str:
    """构建完整的 Agent system prompt，注入进化数据。"""

    parts = [role]

    # 注入用户画像
    if user_dna:
        dna_lines = ["\n## 用户画像（根据历史交互学习）"]
        field_labels = {
            "store_style": "店铺风格",
            "brand_voice": "品牌调性",
            "target_audience": "目标客群",
            "price_positioning": "价格定位",
            "preferred_platforms": "常用平台",
            "content_preferences": "内容偏好",
            "preferred_tone": "偏好语气",
            "avoid_patterns": "明确不喜欢的",
            "risk_tolerance": "风险偏好",
            "min_margin": "最低利润率要求",
            "preferred_price_band": "偏好价格带",
            "categories": "常做品类",
            # 新增细粒度偏好
            "voice_style": "语气风格",
            "visual_preference": "视觉偏好",
            "hook_preference": "开头偏好",
            "content_length": "内容长度偏好",
            "emoji_usage": "emoji使用偏好",
            "humor_level": "幽默程度",
            "selling_intensity": "推销强度偏好",
        }
        for key, label in field_labels.items():
            val = user_dna.get(key)
            if val:
                if isinstance(val, list):
                    val = "、".join(str(v) for v in val)
                elif isinstance(val, dict):
                    continue  # 跳过复杂嵌套
                dna_lines.append(f"- {label}: {val}")

        if len(dna_lines) > 1:
            parts.append("\n".join(dna_lines))

    # 注入优秀案例
    if few_shot_examples:
        parts.append("\n## 历史优秀案例（用户认可的输出风格参考）")
        for i, ex in enumerate(few_shot_examples[:3], 1):
            keyword = ex.get("keyword", "")
            summary = ex.get("output_summary", "")[:300]
            parts.append(f"\n### 案例{i}: {keyword}\n{summary}")

    # 注入失败教训
    if failure_guardrails:
        parts.append("\n## 注意事项（从历史错误中学习，必须遵守）")
        for g in failure_guardrails[:5]:
            parts.append(f"- ⚠️ 避免: {g}")

    return "\n".join(parts)


def get_applied_preferences_list(user_dna: dict | None, few_shots: list | None, guardrails: list | None) -> list[str]:
    """
    生成归因流列表——记录这次生成实际引用了哪些用户数据。
    用于前端展示"AI正在参考你的XX偏好"。
    """
    applied = []

    if user_dna:
        pref_fields = {
            "voice_style": "语气风格",
            "visual_preference": "视觉偏好",
            "hook_preference": "开头偏好",
            "selling_intensity": "推销强度",
            "content_length": "内容长度",
        }
        for key, label in pref_fields.items():
            val = user_dna.get(key)
            if val:
                applied.append(f"已加载偏好「{label}: {val}」")

        avoid = user_dna.get("avoid_patterns", [])
        if avoid:
            applied.append(f"排除{len(avoid)}条回避模式")

        styles = user_dna.get("preferred_styles", {})
        if styles:
            applied.append(f"使用你选择的默认风格")

    if few_shots:
        applied.append(f"参考你认可的{len(few_shots)}个优秀案例")

    if guardrails:
        applied.append(f"遵守{len(guardrails)}条从错误中学到的教训")

    return applied
