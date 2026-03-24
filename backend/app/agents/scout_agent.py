"""
Scout Agent — 选品分析专家。
基于真实多平台数据进行市场分析和选品推荐。
"""

from app.agents.base import BaseAgent, AgentContext
from app.agents.prompts import build_agent_system_prompt
from app.agents.memory import MemoryStore

ROLE = """你是商探AI的首席选品分析师——一位年薪80万的资深电商选品专家。

【身份背景】
你在电商行业深耕10年，曾任某TOP3 TP公司选品总监。你亲手选出过37个百万级爆款SKU。你最擅长的能力是：在1688上用30元采购成本找到的产品，在抖音上卖到129元还能爆单。

你不相信"感觉"，只相信数据。你的选品方法论是：需求验证 → 竞争评估 → 利润测算 → 差异化定位 → 风险排查。

【核心原则】
- 所有数字必须来源于API返回的真实数据，严禁编造
- 佣金率是成本（负向），高销量是竞争壁垒不是机会
- 毛利率>40%才建议做抖音（退货率高+投流成本），>30%可做淘宝，>25%可做拼多多
- 退货率预估：服饰30-50%、美妆10-15%、家居5-10%、食品2-5%、3C 3-8%
- 必须有筛选和淘汰——不能所有品类都给"建议做"

【各平台选品差异】
- 抖音：视觉冲击力强、客单价59-199元、3秒抓眼球的非标品
- 淘宝：搜索需求明确、复购率高、SKU丰富可做矩阵
- 拼多多：价格极致、日用消耗品、白牌替代品、客单价<50元
- 小红书：高颜值、女性向、生活方式类、客单价100-500元

【绝对禁止】
- 禁止编造任何销量、价格、搜索量数据
- 禁止推荐明显侵权的品类
- 禁止忽略退货率对利润的影响
- 禁止推荐需要特殊资质但未提示的品类"""


class ScoutAgent(BaseAgent):
    agent_type = "scout"

    async def observe(self, ctx: AgentContext) -> dict:
        store = MemoryStore(self.db)
        user_dna = await store.get_user_dna(ctx.user_id)
        few_shots = await store.get_few_shots(ctx.user_id, self.agent_type)
        guardrails = await store.get_failure_guardrails(ctx.user_id, self.agent_type)

        # 获取真实市场数据
        from app.services.scout_aggregator import ScoutAggregator
        keyword = ctx.task_input["keyword"]
        platforms = ctx.task_input.get("platforms", ["taobao", "pinduoduo", "douyin"])

        aggregator = ScoutAggregator()
        agg_data = await aggregator.search(keyword=keyword, platforms=platforms)

        return {
            "agg_data": agg_data,
            "ai_context": agg_data.to_ai_context(),
            "user_dna": user_dna,
            "few_shots": few_shots,
            "guardrails": guardrails,
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        agg_data = observation["agg_data"]
        total = getattr(agg_data, 'total_products', 0) if hasattr(agg_data, 'total_products') else len(getattr(agg_data, 'products', {}).get('all', []))

        return {
            "reasoning": f"收集到 {total} 条商品数据，{len(agg_data.configured_platforms)} 个平台可用",
            "strategy": "deep" if total > 20 else "standard",
        }

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)

        # ── 数据有效性检查：无数据时直接失败，不调用 AI ──
        agg_data = observation["agg_data"]
        if agg_data.total_products == 0:
            error_details = agg_data.errors or {"all": "所有平台返回 0 条商品"}
            raise RuntimeError(
                f"数据采集失败：所有平台均未返回有效商品数据。"
                f"错误详情：{error_details}。"
                f"已配置平台：{agg_data.configured_platforms}，"
                f"未配置平台：{agg_data.unconfigured_platforms}"
            )

        system = build_agent_system_prompt(
            ROLE,
            observation.get("user_dna"),
            observation.get("few_shots"),
            observation.get("guardrails"),
        )

        keyword = ctx.task_input["keyword"]
        platforms = ctx.task_input.get("platforms", [])

        prompt = f"""基于以下真实数据分析市场机会。

## 搜索关键词：{keyword}
## 目标平台：{', '.join(platforms)}

## 多平台数据
{observation['ai_context']}

请输出JSON格式的分析报告，包含：
1. market_overview: 市场规模估算、竞争密度(低/中/高/极高)、市场集中度
2. price_opportunity: 黄金价格带（需求密集+竞争较低的区间）
3. platform_ratings: 各平台独立评级，每个平台包含评分(1-5)和适合的卖家类型
   - 抖音评分依据：视觉冲击力、内容创作空间、客单价59-199匹配度
   - 淘宝评分依据：搜索量、SKU矩阵潜力、复购率
   - 拼多多评分依据：价格竞争力、日耗属性、能否做到全网最低
   - 小红书评分依据：颜值/出片感、女性向匹配度、种草空间
4. risk_factors: 风险标签列表（退货率预估、季节性、资质要求、侵权风险）
5. recommended_products: 推荐3-5个选品方向，每个含：
   - name: 具体品名（如"高腰提臀蜜桃臀瑜伽裤"）
   - suggested_price: 各平台建议售价（抖音/淘宝/拼多多/小红书可能不同）
   - estimated_cost: 预估1688采购成本
   - gross_margin: 预估毛利率
   - return_rate: 预估退货率（服饰30-50%、美妆10-15%、家居5-10%）
   - net_margin: 扣除退货后净利率
   - platform_fit: 各平台适合度(1-5星)及一句话理由
   - risk_tags: 风险标签
   - differentiation: 差异化方向
   - reason: 推荐理由
   - supplier_search_keyword: 在1688上搜索的建议关键词
6. cross_platform_strategy: 跨平台协同策略
   - primary_platform: 建议主攻平台及理由
   - seeding_platform: 种草平台（通常是小红书）
   - search_capture: 搜索承接平台（通常是淘宝）
   - not_recommended: 不建议的平台及原因
   - pricing_difference: 各平台定价差异建议
   - launch_sequence: 建议的上线顺序和时间间隔
7. supplier_suggestion: 供应商建议
   - sourcing_model: 建议采购模式（一件代发/小批量批发/工厂定制）
   - estimated_moq: 预估起订量
   - sample_cost: 样品测试预估成本
   - key_quality_checks: 验货关键检查项

只输出JSON，不要其他文字。"""

        result = await self._ai_call(prompt, task_type="analysis", system=system)

        agg_data = observation["agg_data"]
        return {
            "scout_raw": {
                "price_summary": agg_data.price_summary(),
                "sales_summary": agg_data.sales_summary(),
                "commission_summary": agg_data.commission_summary(),
                "price_bands": agg_data.price_bands(),
                "platform_breakdown": agg_data.platform_breakdown(),
                "top_products": agg_data.top_products(limit=10),
            },
            "ai_analysis": result["text"],
            "ai_cost": result["cost"],
            "keyword": keyword,
        }

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        # 基础检查：是否返回了有效的 JSON 分析
        analysis = output.get("ai_analysis", "")
        has_json = "{" in analysis and "}" in analysis
        has_data = bool(output.get("scout_raw", {}).get("price_summary"))

        confidence = 0.8 if (has_json and has_data) else 0.3
        issues = []
        if not has_json:
            issues.append("AI 分析未返回有效 JSON")
        if not has_data:
            issues.append("缺少平台数据")

        return {"confidence": confidence, "issues": issues}
