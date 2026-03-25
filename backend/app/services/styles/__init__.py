"""
内容风格系统

风格注册表 + 统一模板接口，支持：
- 多种默认风格供用户选择
- 用户自定义偏好注入
- 新风格热插拔，不影响现有代码
"""
from app.services.styles.registry import (
    StyleConfig,
    register_style,
    get_style,
    list_styles,
    STYLE_REGISTRY,
)
from app.services.styles.base import BaseStylePrompt
