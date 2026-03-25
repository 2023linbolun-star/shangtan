"""
专家知识模块 — 方案C（混合架构）

动态专家（每次生成时做AI调用，根据具体产品动态决策）：
  - douyin_strategy   抖音内容策略专家
  - xhs_strategy      小红书内容策略专家
  - image_prompt      AI生图Prompt工程专家

静态规则（固定参数，直接注入，不浪费AI调用）：
  - video_specs       视频合成技术参数
  - platform_rules    平台合规与发布规则
"""
