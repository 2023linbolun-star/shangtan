"""
Pipeline Engine — 串联各模块的自动化工作流引擎。

Pipeline 流程:
  Step 1: 市场分析 + 竞品分析
  Step 2: 选品决策 + 定价策略  [人工审批]
  Step 3: 内容生成 + Listing优化  [并行] [人工审批]
  Step 4: 发布排期建议
"""

import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Pipeline, PipelineStep, Product, GeneratedContent,
    PipelineStatus, StepStatus, StepType, ProductStatus, ContentStatus,
)
from app.services.event_bus import event_bus
from app.services.ai_engine import ai_analyze, ai_analyze_full

logger = logging.getLogger("shangtanai.pipeline")


class PipelineEngine:
    """Executes pipeline steps, passing output between steps."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, pipeline_id: str):
        """Run all pending steps until completion or an approval gate."""
        pipeline = await self._get_pipeline(pipeline_id)
        if not pipeline:
            logger.error(f"Pipeline {pipeline_id} not found")
            return

        pipeline.status = PipelineStatus.running
        await self.db.flush()

        steps = list(pipeline.steps)
        previous_output = {
            "keyword": pipeline.trigger_keyword,
            "platforms": pipeline.target_platforms,
            "config": pipeline.config,
        }

        for step in steps:
            # Skip already completed steps (for resume after approval)
            if step.status == StepStatus.completed:
                if step.output_data:
                    previous_output = {**previous_output, **step.output_data}
                continue

            # Skip already skipped steps
            if step.status == StepStatus.skipped:
                continue

            # Stop at steps awaiting approval
            if step.status == StepStatus.awaiting_approval:
                pipeline.status = PipelineStatus.paused
                await self.db.flush()
                await event_bus.emit("pipeline.paused", {"pipeline_id": pipeline_id, "step_id": step.id})
                return

            # Execute step
            step.status = StepStatus.running
            step.input_data = previous_output
            step.started_at = datetime.now(timezone.utc)
            await self.db.flush()

            await event_bus.emit("pipeline.step.started", {
                "pipeline_id": pipeline_id, "step_id": step.id, "step_type": step.step_type.value,
            })

            try:
                executor = STEP_EXECUTORS.get(step.step_type)
                if not executor:
                    raise ValueError(f"No executor for step type: {step.step_type}")

                result = await executor(self.db, pipeline, step, previous_output)
                step.output_data = result
                step.completed_at = datetime.now(timezone.utc)

                # Check if this step needs approval before continuing
                if step.step_type in APPROVAL_REQUIRED_STEPS:
                    step.status = StepStatus.awaiting_approval
                    pipeline.status = PipelineStatus.paused
                    await self.db.flush()
                    await event_bus.emit("pipeline.step.awaiting_approval", {
                        "pipeline_id": pipeline_id, "step_id": step.id,
                    })
                    return
                else:
                    step.status = StepStatus.completed
                    previous_output = {**previous_output, **result}

            except Exception as e:
                step.status = StepStatus.failed
                step.error_message = str(e)
                step.completed_at = datetime.now(timezone.utc)
                pipeline.status = PipelineStatus.failed
                await self.db.flush()
                logger.error(f"Step {step.step_type.value} failed: {e}")
                await event_bus.emit("pipeline.step.failed", {
                    "pipeline_id": pipeline_id, "step_id": step.id, "error": str(e),
                })
                return

            await self.db.flush()
            await event_bus.emit("pipeline.step.completed", {
                "pipeline_id": pipeline_id, "step_id": step.id,
            })

        # All steps done
        pipeline.status = PipelineStatus.completed
        await self.db.flush()
        await event_bus.emit("pipeline.completed", {"pipeline_id": pipeline_id})

    async def approve_step(self, pipeline_id: str, step_id: str, edits: dict | None = None):
        """Approve a step that's awaiting approval, then resume pipeline."""
        step = await self.db.get(PipelineStep, step_id)
        if not step or step.pipeline_id != pipeline_id:
            raise ValueError("Step not found")
        if step.status != StepStatus.awaiting_approval:
            raise ValueError(f"Step is not awaiting approval (status: {step.status})")

        # Apply edits if any
        if edits and step.output_data:
            step.output_data = {**step.output_data, **edits}

        step.status = StepStatus.completed
        await self.db.flush()

        # Resume pipeline execution from next step
        await self.run(pipeline_id)

    async def retry_step(self, pipeline_id: str, step_id: str):
        """Retry a failed step."""
        step = await self.db.get(PipelineStep, step_id)
        if not step or step.pipeline_id != pipeline_id:
            raise ValueError("Step not found")

        step.status = StepStatus.pending
        step.error_message = None
        step.output_data = None
        await self.db.flush()

        await self.run(pipeline_id)

    async def _get_pipeline(self, pipeline_id: str) -> Pipeline | None:
        result = await self.db.execute(
            select(Pipeline).where(Pipeline.id == pipeline_id)
        )
        return result.scalar_one_or_none()


# ── Steps that require human approval before continuing ──
APPROVAL_REQUIRED_STEPS = {
    StepType.product_selection,  # 选品后必须人工确认
    StepType.content,            # 内容生成后必须人工审核
}


# ── Step Executors ──

async def _execute_scout(db: AsyncSession, pipeline: Pipeline, step: PipelineStep, ctx: dict) -> dict:
    """Step 1: 市场分析 + 竞品分析"""
    keyword = ctx["keyword"]
    platforms = ctx.get("platforms", ["taobao", "pinduoduo", "douyin"])

    # Reuse existing ScoutAggregator
    from app.services.scout_aggregator import ScoutAggregator
    aggregator = ScoutAggregator()
    agg_data = await aggregator.search(keyword=keyword, platforms=platforms)

    # Build AI analysis context
    ai_context = agg_data.to_ai_context()

    # AI market analysis (DeepSeek Reasoner)
    analysis_prompt = f"""你是一位资深电商市场分析师。请基于以下真实数据分析市场机会。

## 搜索关键词：{keyword}

## 多平台数据
{ai_context}

请输出JSON格式的分析报告，包含：
1. market_overview: 市场规模估算、竞争密度(低/中/高/极高)
2. price_opportunity: 黄金价格带（需求密集+竞争较低的区间）
3. platform_ratings: 各平台独立评级和适合的卖家类型
   - 淘宝：搜索竞争度评分
   - 抖音：内容机会度评分（适合视觉冲击力强的产品）
   - 拼多多：价格竞争度评分（极致性价比才能做）
4. risk_factors: 风险标签列表（退货率预估、季节性、资质要求）
5. entry_strategy: 建议的差异化进入方向（2-3个具体建议）
6. top_products: 推荐的5个选品方向，每个含名称、建议售价区间、预估毛利率、适合平台

只输出JSON，不要其他文字。"""

    ai_result = await ai_analyze_full(analysis_prompt, task_type="analysis")

    return {
        "scout_raw": {
            "price_summary": agg_data.price_summary(),
            "sales_summary": agg_data.sales_summary(),
            "commission_summary": agg_data.commission_summary(),
            "price_bands": agg_data.price_bands(),
            "platform_breakdown": agg_data.platform_breakdown(),
            "top_products": agg_data.top_products(limit=10),
        },
        "ai_analysis": ai_result["text"],
        "ai_cost": ai_result["cost"],
        "keyword": keyword,
    }


async def _execute_product_selection(db: AsyncSession, pipeline: Pipeline, step: PipelineStep, ctx: dict) -> dict:
    """Step 2: 选品决策 + 定价策略"""
    keyword = ctx.get("keyword", "")
    scout_raw = ctx.get("scout_raw", {})
    ai_analysis = ctx.get("ai_analysis", "")
    platforms = ctx.get("platforms", [])

    selection_prompt = f"""你是一位资深电商选品专家。基于以下市场分析结果，给出具体的选品决策。

## 关键词：{keyword}
## 目标平台：{', '.join(platforms)}

## 市场分析结果
{ai_analysis}

## 价格数据
{scout_raw.get('price_summary', {})}

请输出JSON格式，包含：
1. recommended_products: 推荐3-5个具体选品，每个包含：
   - name: 具体品名（如"高腰提臀蜜桃臀瑜伽裤"）
   - suggested_price_min/max: 建议售价区间
   - estimated_cost: 预估采购成本（1688参考）
   - gross_margin: 预估毛利率
   - return_rate: 预估退货率
   - net_margin_after_returns: 扣除退货后净利率
   - platform_fit: 各平台适合度评分(1-5星)
   - risk_tags: 风险标签列表
   - differentiation: 差异化方向建议
   - reason: 推荐理由（1-2句话）

2. pricing_strategy: 各平台定价策略建议
   - 淘宝：设较高原价+优惠券拉低实付价
   - 抖音：设锚定原价+有冲击力的直播间价
   - 拼多多：必须接近全网最低

3. hard_filters: 硬性过滤提醒（资质要求、侵权风险等）

只输出JSON。"""

    ai_result = await ai_analyze_full(selection_prompt, task_type="analysis")

    # Create Product records for each recommendation
    # (will be finalized after user approval)

    return {
        "product_selection": ai_result["text"],
        "ai_cost": ctx.get("ai_cost", 0) + ai_result["cost"],
    }


async def _execute_content(db: AsyncSession, pipeline: Pipeline, step: PipelineStep, ctx: dict) -> dict:
    """Step 3: 内容生成 + Listing优化（并行执行）"""
    keyword = ctx.get("keyword", "")
    product_selection = ctx.get("product_selection", "")
    platforms = ctx.get("platforms", [])
    total_cost = ctx.get("ai_cost", 0)

    # Run content generation and listing optimization in parallel
    tasks = []

    # Content generation per platform (Doubao for social, Qwen for formal)
    for platform in platforms:
        if platform in ("douyin", "xiaohongshu", "kuaishou"):
            tasks.append(_generate_social_content(keyword, product_selection, platform))
        elif platform in ("taobao", "tmall"):
            tasks.append(_generate_formal_content(keyword, product_selection, platform))
        elif platform == "pinduoduo":
            tasks.append(_generate_formal_content(keyword, product_selection, platform))

    # Listing optimization for all platforms (Qwen Flash)
    tasks.append(_optimize_listings(keyword, product_selection, platforms))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect outputs
    generated_contents = []
    listing_results = {}
    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Content/Listing task failed: {r}")
            continue
        if r.get("type") == "content":
            generated_contents.append(r)
            total_cost += r.get("cost", 0)
        elif r.get("type") == "listing":
            listing_results = r
            total_cost += r.get("cost", 0)

    return {
        "generated_contents": generated_contents,
        "listing_results": listing_results,
        "ai_cost": total_cost,
    }


async def _generate_social_content(keyword: str, product_selection: str, platform: str) -> dict:
    """Generate social media content using Doubao (best for Douyin/XHS voice)."""
    platform_instructions = {
        "douyin": """生成抖音短视频脚本。要求：
- 0-3秒必须有强Hook（制造冲突/悬念/共鸣，如"穿了3年瑜伽裤，终于找到一条不尴尬的！"）
- 3-10秒放大痛点
- 10-25秒产品展示（必须有before/after对比）
- 25-40秒信任背书（工厂直发/退货包运费）
- 40-60秒行动号召（限时价格）
- 总时长15-60秒，9:16竖屏
- 违禁词：不能说"最好/第一/绝对/100%"
- 输出格式：分镜脚本（场景序号+时长+画面描述+口播文案+BGM建议）""",

        "xiaohongshu": """生成小红书种草笔记。要求：
- 标题含emoji+数字+场景（如"3条瑜伽裤实测！这条真的绝了"）
- 正文800-1500字：人设开场→痛点共鸣→自然引入产品→具体使用体验（感官描述）→对比→总结
- 标签策略：3-5个热门大标签 + 5-8个精准中标签 + 5-7个长尾小标签
- 严禁出现"买/下单/链接在"等导购词
- 严禁提及其他平台名称
- 语气要真实有人感，不能像说明书""",

        "kuaishou": """生成快手短视频脚本。要求：
- 风格真实接地气，"家人们"比"姐妹们"更合适
- 偏好工厂实拍/源头直播风格，精致感反而扣分
- 强调信任关系和性价比
- 价格对比话术更有效""",
    }

    prompt = f"""你是{platform}平台的顶级内容创作者。

## 产品信息
关键词：{keyword}
选品方案：
{product_selection}

## 平台要求
{platform_instructions.get(platform, "")}

请为排名最高的推荐产品生成一篇完整的{platform}内容。输出JSON格式：
{{
  "platform": "{platform}",
  "title": "内容标题",
  "content": "完整内容正文/脚本",
  "tags": ["标签1", "标签2"],
  "publishing_tips": "发布建议（最佳时间/注意事项）"
}}"""

    result = await ai_analyze_full(prompt, task_type="content_social")
    return {"type": "content", "platform": platform, "data": result["text"], "cost": result["cost"]}


async def _generate_formal_content(keyword: str, product_selection: str, platform: str) -> dict:
    """Generate formal product content using Qwen (best for Taobao/PDD listings)."""
    platform_instructions = {
        "taobao": """生成淘宝商品文案。包含：
- 5张主图描述（第1张白底搜索主图、第2张核心卖点、第3张使用场景、第4张面料细节、第5张尺码表）
- 详情页结构：模特上身效果→核心卖点提炼(不超过5个)→面料工艺细节→尺码表→售后承诺
- 5个核心卖点用"痛点→方案"结构""",

        "pinduoduo": """生成拼多多商品文案。要求：
- 强调价格感：券后价、拼团价突出
- 详情页更短更直接（用户决策快）
- 严禁出现"天猫同款"、"淘宝爆款"等引流词""",

        "tmall": """生成天猫商品文案。同淘宝但更注重品牌调性。""",
    }

    prompt = f"""你是资深电商文案专家。

## 产品信息
关键词：{keyword}
选品方案：
{product_selection}

## 平台要求
{platform_instructions.get(platform, "")}

请为排名最高的推荐产品生成完整的{platform}商品文案。输出JSON格式：
{{
  "platform": "{platform}",
  "main_images_description": ["图1描述", "图2描述", ...],
  "selling_points": ["卖点1", "卖点2", ...],
  "detail_page_sections": [{{"title": "段落标题", "content": "内容"}}],
  "seo_keywords": ["关键词1", "关键词2"]
}}"""

    result = await ai_analyze_full(prompt, task_type="content_formal")
    return {"type": "content", "platform": platform, "data": result["text"], "cost": result["cost"]}


async def _optimize_listings(keyword: str, product_selection: str, platforms: list) -> dict:
    """Optimize listing titles and keywords per platform using Qwen Flash."""
    prompt = f"""你是电商Listing优化专家。

## 产品信息
关键词：{keyword}
选品方案：
{product_selection}

## 各平台标题规则
- 淘宝（60字符/30汉字）：品类核心词+属性+功能+场景+长尾，关键词密度适中
- 抖音（60字符）：品类词+核心卖点+人群场景，不堆关键词
- 拼多多（60字符）：品类词+属性堆叠+信任词(包邮/正品)，不加品牌名（除非旗舰店）
- 小红书（30字符）：种草感标题，非搜索优化

请为排名最高的推荐产品生成各平台优化标题。输出JSON：
{{
  "listings": [
    {{
      "platform": "平台名",
      "optimized_title": "优化后的标题",
      "backend_keywords": ["后台关键词1", "关键词2"],
      "violation_check": {{"has_violation": false, "details": []}}
    }}
  ]
}}

目标平台：{', '.join(platforms)}"""

    result = await ai_analyze_full(prompt, task_type="listing")
    return {"type": "listing", "data": result["text"], "cost": result["cost"]}


async def _execute_media_production(db: AsyncSession, pipeline: Pipeline, step: PipelineStep, ctx: dict) -> dict:
    """Step 3.5: 素材生产 — 将AI内容转化为可发布的视频/图文。"""
    from app.services.media.producer import produce_all

    generated_contents = ctx.get("generated_contents", [])
    category = ctx.get("config", {}).get("category", "default")

    if not generated_contents:
        logger.warning("No generated contents for media production")
        return {"media_assets": [], "ai_cost": ctx.get("ai_cost", 0)}

    logger.info(f"Starting media production for {len(generated_contents)} contents")

    media_results = await produce_all(
        content_outputs=generated_contents,
        category=category,
    )

    # 汇总成本
    media_cost = sum(
        r.get("cost_breakdown", {}).get("total", 0)
        for r in media_results
    )

    return {
        "media_assets": media_results,
        "ai_cost": ctx.get("ai_cost", 0) + media_cost,
    }


async def _execute_publish_schedule(db: AsyncSession, pipeline: Pipeline, step: PipelineStep, ctx: dict) -> dict:
    """Step 4: 发布排期建议"""
    keyword = ctx.get("keyword", "")
    platforms = ctx.get("platforms", [])

    prompt = f"""你是电商运营排期专家。

## 产品关键词：{keyword}
## 目标平台：{', '.join(platforms)}

请给出发布排期建议，输出JSON：
{{
  "recommended_order": ["先发哪个平台", "再发哪个"],
  "platform_schedule": [
    {{
      "platform": "平台名",
      "best_publish_time": "最佳发布时间段",
      "reason": "原因",
      "preparation_checklist": ["准备事项1", "准备事项2"]
    }}
  ],
  "calendar_alerts": ["近期大促提醒（如618/双11/年货节）"],
  "tips": "整体建议（1-2句话）"
}}"""

    result = await ai_analyze_full(prompt, task_type="batch")
    return {
        "publish_schedule": result["text"],
        "ai_cost": ctx.get("ai_cost", 0) + result["cost"],
    }


# ── Step executor registry ──
STEP_EXECUTORS = {
    StepType.scout: _execute_scout,
    StepType.product_selection: _execute_product_selection,
    StepType.content: _execute_content,
    StepType.media_production: _execute_media_production,
    StepType.publish_schedule: _execute_publish_schedule,
}
