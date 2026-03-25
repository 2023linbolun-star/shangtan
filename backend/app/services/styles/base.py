"""
风格模板基类 — 所有内容风格的统一接口。

每个风格模板继承此基类，实现 build_system / build_prompt / get_customizable_fields。
Agent 通过 Style Registry 查找风格，调用模板生成 prompt。
"""

from abc import ABC, abstractmethod


class BaseStylePrompt(ABC):
    """所有风格模板的基类。"""

    style_id: str = ""

    @abstractmethod
    def build_system(self, user_dna: dict | None = None) -> str:
        """
        构建 system prompt，注入用户偏好。

        Args:
            user_dna: 用户画像数据（从 UserDNA 加载）

        Returns:
            完整的 system prompt 字符串
        """
        ...

    @abstractmethod
    def build_prompt(
        self,
        product_info: str,
        user_preferences: dict | None = None,
        **kwargs,
    ) -> str:
        """
        构建 user prompt，融合用户的细粒度偏好。

        Args:
            product_info: 产品信息
            user_preferences: 用户个性化偏好（voice_style, visual_preference 等）
            **kwargs: 风格特有的参数

        Returns:
            完整的 user prompt 字符串
        """
        ...

    def get_customizable_fields(self) -> list[dict]:
        """
        返回用户可调整的参数列表（供前端渲染偏好设置表单）。

        Returns:
            [
                {
                    "key": "voice_style",
                    "label": "语气风格",
                    "type": "select",  # select / text / slider / toggle
                    "options": ["闺蜜聊天", "专业测评", "轻幽默", "真诚推荐"],
                    "default": "真诚推荐",
                    "description": "生成内容时的说话语气",
                },
                ...
            ]
        """
        return []

    def inject_preferences(self, base_prompt: str, preferences: dict | None) -> str:
        """
        将用户偏好注入到 prompt 中。子类可覆盖。

        默认实现：将偏好作为一个独立的 section 追加到 prompt 末尾。
        """
        if not preferences:
            return base_prompt

        pref_lines = ["\n## 用户个人偏好（必须遵循）"]

        field_labels = {
            "voice_style": "语气风格",
            "visual_preference": "视觉风格",
            "hook_preference": "开头偏好",
            "content_length": "内容长度",
            "emoji_usage": "emoji使用",
            "humor_level": "幽默程度",
            "selling_intensity": "推销强度",
        }

        for key, label in field_labels.items():
            val = preferences.get(key)
            if val:
                pref_lines.append(f"- {label}: {val}")

        # 品类特殊偏好
        category = preferences.get("_current_category")
        overrides = preferences.get("category_overrides", {})
        if category and category in overrides:
            pref_lines.append(f"\n### {category}品类特殊要求")
            for k, v in overrides[category].items():
                pref_lines.append(f"- {k}: {v}")

        # 明确不喜欢的
        avoid = preferences.get("avoid_patterns", [])
        if avoid:
            pref_lines.append("\n### 明确避免")
            for a in avoid:
                pref_lines.append(f"- ⚠️ 不要: {a}")

        if len(pref_lines) > 1:
            return base_prompt + "\n" + "\n".join(pref_lines)
        return base_prompt
