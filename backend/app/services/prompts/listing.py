"""各平台 Listing 标题优化 Prompt 模板"""

SYSTEM = """你是电商SEO专家，精通淘宝/抖音/拼多多/小红书各平台的标题规则和搜索算法。
你优化的标题平均提升搜索曝光30%以上。"""


def build_title_prompt(product_name: str, category: str, platforms: list[str], keywords: list[str] | None = None) -> str:
    platform_rules = []
    for p in platforms:
        if p in ("taobao", "tmall"):
            platform_rules.append("""【淘宝/天猫】60字符(约30汉字)
- 公式：品类核心词 + 核心属性词 + 功能卖点词 + 场景/人群词 + 长尾修饰词
- 示例："瑜伽裤女高腰提臀 蜜桃臀健身裤 冰丝速干紧身运动裤夏季薄款"
- 天猫可在最前面加品牌词
- 核心词出现1次，不堆砌
- 搜索权重：完全匹配 > 部分匹配 > 分词匹配""")
        elif p == "douyin":
            platform_rules.append("""【抖音】60字符
- 公式：品类词 + 核心卖点 + 人群场景
- 不堆关键词（抖音靠推荐算法不靠搜索，但抖音商城搜索在增长）
- 标题展示位置小，影响点击率，要简洁有吸引力""")
        elif p == "pinduoduo":
            platform_rules.append("""【拼多多】60字符
- 公式：品类词 + 属性堆叠 + 信任词(包邮/正品)
- 比淘宝更堆砌（搜索算法依赖关键词覆盖）
- 禁止出现品牌名（除非旗舰店）
- 加"包邮""正品"有助转化""")
        elif p == "xiaohongshu":
            platform_rules.append("""【小红书】30字符
- 种草感标题，非搜索优化
- 含emoji和情绪词
- 像笔记标题，不像商品标题""")

    kw_section = ""
    if keywords:
        kw_section = f"\n## 参考关键词\n{', '.join(keywords)}"

    return f"""请为以下产品优化各平台标题。

## 产品信息
品名：{product_name}
品类：{category}
{kw_section}

## 各平台标题规则
{"".join(platform_rules)}

## 输出JSON
{{
  "listings": [
    {{
      "platform": "平台名",
      "optimized_title": "优化后的标题",
      "title_length": 标题字符数,
      "keyword_coverage": ["包含的搜索关键词"],
      "backend_keywords": ["建议的后台关键词（不在标题中）"]
    }}
  ]
}}

只输出JSON。"""


def build_keyword_expand_prompt(keyword: str) -> str:
    return f"""请围绕核心关键词"{keyword}"进行关键词拓展。

按以下分组输出：
1. 品类词：核心品类相关词
2. 属性词：材质/颜色/尺码/风格等
3. 场景词：使用场景/人群/用途
4. 长尾词：3-5个字的精准长尾搜索词
5. 热搜词：当前可能的热门搜索词

每组 8-12 个词。

输出JSON：
{{
  "core_keyword": "{keyword}",
  "groups": {{
    "品类词": ["词1", "词2", ...],
    "属性词": ["词1", "词2", ...],
    "场景词": ["词1", "词2", ...],
    "长尾词": ["词1", "词2", ...],
    "热搜词": ["词1", "词2", ...]
  }}
}}

只输出JSON。"""
