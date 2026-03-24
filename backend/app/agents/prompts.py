"""
动态 Prompt 构建器 — 将 Agent 静态身份 + 用户 DNA + 案例 + 教训 组合成完整 system prompt。
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
        }
        for key, label in field_labels.items():
            val = user_dna.get(key)
            if val:
                if isinstance(val, list):
                    val = "、".join(str(v) for v in val)
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
