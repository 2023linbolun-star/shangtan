"""
TrendScanAgent — 趋势扫描专家。
自动扫描全网趋势热搜，发现商品机会。
"""
from app.agents.base import BaseAgent, AgentContext
import httpx
import logging

logger = logging.getLogger("shangtanai.agent.trend_scan")

ROLE = """你是商探AI的趋势猎手——专门从全网热搜和趋势数据中发现电商商品机会。

你的工作不是分析单个商品，而是扫描全网热点，找出可能成为爆品的关键词和品类方向。

【数据来源】
- 抖音热搜/热销榜
- 百度指数上升关键词
- 微信指数突增词
- 淘宝搜索上升词
- 季节性商品日历

【评估标准】
- 搜索量上升速度（velocity）：越快越好
- 绝对搜索量（volume）：太低的不值得做
- 电商相关性：纯新闻热点不算，必须是能卖东西的
- 时效性：已经火了很久的不算趋势"""


class TrendScanAgent(BaseAgent):
    agent_type = "trend_scan"

    async def observe(self, ctx: AgentContext) -> dict:
        """Scan multiple trend sources."""
        trends = []
        errors = {}

        # Source 1: HotList API (free, covers douyin/weibo/bilibili)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                for platform in ["douyin", "weibo", "bilibili"]:
                    try:
                        resp = await client.get(f"https://api.vvhan.com/api/hotlist/{platform}")
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get("success"):
                                for item in (data.get("data", []) or [])[:20]:
                                    trends.append({
                                        "keyword": item.get("title", ""),
                                        "source": f"hotlist_{platform}",
                                        "hot_value": item.get("hot", 0),
                                        "url": item.get("url", ""),
                                    })
                    except Exception as e:
                        errors[f"hotlist_{platform}"] = str(e)
        except Exception as e:
            errors["hotlist"] = str(e)

        # Source 2: Seasonal calendar (hardcoded upcoming opportunities)
        import datetime
        now = datetime.datetime.now()
        month = now.month
        seasonal = self._get_seasonal_keywords(month)
        for kw in seasonal:
            trends.append({
                "keyword": kw,
                "source": "seasonal_calendar",
                "hot_value": 50,
                "url": "",
            })

        return {
            "raw_trends": trends,
            "errors": errors,
            "source_count": len(set(t["source"] for t in trends)),
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        trends = observation["raw_trends"]
        return {
            "reasoning": f"收集到 {len(trends)} 条趋势信号，来自 {observation['source_count']} 个数据源",
            "strategy": "filter_and_score",
        }

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        raw_trends = observation["raw_trends"]

        if not raw_trends:
            return {
                "trends": [],
                "errors": observation.get("errors", {}),
                "message": "未发现趋势信号",
            }

        # Filter: only keep commerce-relevant trends
        # Use AI to filter and score
        trend_text = "\n".join(
            f"- {t['keyword']} (来源: {t['source']}, 热度: {t['hot_value']})"
            for t in raw_trends[:50]
        )

        prompt = f"""从以下热搜/趋势列表中，筛选出有电商潜力的关键词。

## 趋势列表
{trend_text}

请输出JSON格式，包含：
{{
  "trends": [
    {{
      "keyword": "关键词",
      "ecommerce_relevance": 0.0-1.0,
      "category": "品类分类",
      "reasoning": "为什么这个有电商潜力",
      "urgency": "high/medium/low",
      "suggested_search_keyword": "在电商平台搜索的建议关键词"
    }}
  ]
}}

只保留 ecommerce_relevance >= 0.5 的。纯新闻/娱乐/政治热点排除。"""

        result = await self._ai_call(prompt, task_type="analysis")

        return {
            "ai_analysis": result["text"],
            "ai_cost": result.get("cost", 0),
            "raw_trend_count": len(raw_trends),
            "errors": observation.get("errors", {}),
        }

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        analysis = output.get("ai_analysis", "")
        has_trends = "keyword" in analysis
        return {
            "confidence": 0.7 if has_trends else 0.3,
            "issues": [] if has_trends else ["未识别到有电商潜力的趋势"],
        }

    def _get_seasonal_keywords(self, month: int) -> list[str]:
        """Seasonal commerce opportunities by month."""
        calendar = {
            1: ["年货礼盒", "暖手宝", "冬季保暖"],
            2: ["情人节礼物", "开学文具", "春季新款"],
            3: ["春装", "防过敏", "踏青户外"],
            4: ["防晒", "清明祭祀", "春季运动"],
            5: ["防晒衣", "夏装", "母亲节礼物", "618预热"],
            6: ["618大促", "夏季清凉", "防蚊", "便携风扇"],
            7: ["泳衣", "防晒霜", "冰丝", "暑假用品"],
            8: ["开学季", "秋装预售", "中秋月饼"],
            9: ["秋装", "中秋礼盒", "国庆出行"],
            10: ["国庆", "秋冬换季", "双11预热"],
            11: ["双11", "冬装", "暖宝宝", "加绒"],
            12: ["双12", "圣诞", "年终清仓", "新年装饰"],
        }
        return calendar.get(month, [])
