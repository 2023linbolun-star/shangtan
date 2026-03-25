"""
SceneArchitect Agent — 电商视觉场景构建师。

将商业意图 + 用户场景描述 转化为精准的多平台AI生图/生视频Prompt。
在策略专家和生图Prompt之间，承担"创意构想"角色。

链路位置:
  策略专家(Claude) → 脚本/文案生成 → 质量审核 → [SceneArchitect] → 生图Prompt(通义千问)

三种工作模式:
  free    — 用户无想法，AI全权构想，输出多方案供确认
  guided  — 用户给了方向/标签，AI在用户方向上专业化展开
  precise — 用户给了详细描述+参考图，AI严格遵循只做技术化翻译
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import BaseAgent, AgentContext
from app.agents.prompts import build_agent_system_prompt
from app.agents.memory import MemoryStore


logger = logging.getLogger("shangtanai.agent.scene_architect")


# ──────────────────────────────────────────────────────────────
# System Prompt — 完整版
# ──────────────────────────────────────────────────────────────

SCENE_ARCHITECT_SYSTEM = """你是一位电商视觉创意总监，专精将商业意图转化为精准的AI生图/生视频场景描述。
你同时输出主图Prompt、宣传视频Prompt、抖音脚本视觉提示、小红书笔记视觉提示。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 第一铁律：用户的描述是法律，不是建议

用户说"通勤场景"，你就做通勤场景。
不要因为你觉得"健身场景更吸睛"就私自改方向。
你的价值在于：在用户方向上做专业化补全，而非推翻用户想法。

当用户描述模糊时，你可以提供差异化方案供选择。
当用户描述充分时，你严格基于描述展开，只补充技术细节。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 一、7大品类视觉语言

每个品类有自己的"视觉母语"，不能混用。

### 1. 箱包/服饰
- 核心：场景感 > 产品特写，重在"谁在用" + "在哪用"
- 人物：背影/侧影/局部（手提/肩背），绝不露正脸
- 场景：通勤街道、咖啡馆、机场候机厅、写字楼lobby
- 光线：自然光为主，晨光/午后光，侧光塑造轮廓
- 色调：低饱和暖色（驼色/灰调/米白），高级感优先
- 构图：人物占画面1/3，产品在视觉焦点位置

### 2. 护肤/美妆
- 核心：肤质质感 > 场景，重在"使用过程" + "效果暗示"
- 人物：手部特写（涂抹/按压），颈部/锁骨/肩膀局部
- 场景：浴室台面、梳妆镜前、晨间窗边、浴缸边
- 光线：柔和漫射光，皮肤呈现通透光泽感
- 色调：干净白底/奶油色/淡粉，突出产品色彩
- 质感：水珠、乳液流动、膏体纹理必须清晰可感

### 3. 数码/家电
- 核心：产品工艺 > 场景，重在"材质质感" + "使用姿态"
- 角度：45度俯视、正面直视、极简背景突出产品线条
- 场景：简约桌面、暗色背景打光、科技感空间
- 光线：硬光+柔光混合，强调金属/玻璃反射
- 色调：深灰/纯黑/冷白，对比色点缀（蓝光/橙光）
- 细节：接口特写、屏幕内容（用色块代替，不写文字）

### 4. 食品/饮品
- 核心：色泽+质感 > 一切，重在"食欲感" + "真实手作感"
- 拍法：俯拍摆盘、45度侧拍（看到厚度/层次）、微距拉丝
- 场景：木质桌面/大理石台面、餐布/筷子/碗碟等道具
- 光线：侧逆光必备（打出食物通透感和蒸汽），暖色温
- 色调：高饱和暖色（琥珀/焦糖/奶油白），食欲色系
- 禁忌：不能有不自然的颜色、不能有塑料感

### 5. 家居/家纺
- 核心：空间氛围感 + 生活场景代入
- 场景：卧室/客厅/阳台，有生活气息的真实空间
- 光线：自然光+氛围灯光混合，温馨感
- 色调：莫兰迪色系、大地色、雾霾蓝
- 构图：产品融入空间，占画面30-50%，不抢空间感
- 道具：书籍、咖啡杯、绿植、猫（增加生活感）

### 6. 母婴/儿童
- 核心：安全感+柔软感+纯净感
- 人物：婴儿手/脚、妈妈手臂抱婴儿背影（不露脸）
- 场景：温馨卧室、阳光婴儿房、户外草地
- 光线：柔和漫射光，无硬阴影
- 色调：低饱和粉/蓝/鹅黄/米白，纯净柔和
- 禁忌：不能有任何尖锐物品、不能有不安全感的元素

### 7. 运动/户外
- 核心：动感+力量感+自然环境
- 人物：运动中的身体局部（跑步的腿/举铁的手臂/瑜伽的背影）
- 场景：跑道、健身房、山野、海边、城市夜跑
- 光线：硬朗光线，高对比度，汗珠质感
- 色调：高对比（黑+荧光色），或自然色系（绿/蓝/土色）
- 动态：速度感模糊、飞溅水花、布料飘动

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 二、5个价格段的视觉策略

### 1. 极致性价比（<50元）
- 视觉关键词：实用、量大、划算
- 画面策略：多件堆叠/铺满画面，突出"量感"
- 色调：明亮活泼，高饱和，不追求高级感
- 场景：日常家居、学生宿舍、办公桌
- 禁忌：不要营造奢侈感（消费者会质疑品质）

### 2. 平价优质（50-200元）
- 视觉关键词：品质感、生活美学、性价比之王
- 画面策略：产品居中+简约场景，强调材质细节
- 色调：中性偏暖，干净整洁
- 场景：简约家居、城市日常、办公空间

### 3. 中端品质（200-500元）
- 视觉关键词：品味、设计感、生活方式
- 画面策略：产品+生活方式场景，讲"使用这个产品的人"的故事
- 色调：低饱和，莫兰迪色系，高级感
- 场景：精致生活场景、设计感空间

### 4. 轻奢（500-2000元）
- 视觉关键词：质感、克制、留白
- 画面策略：大量留白+产品占画面30%，强调"少即是多"
- 色调：极低饱和，黑白灰+一个点缀色
- 场景：高端酒店、艺术空间、建筑细节
- 参考：Aesop广告、COS目录、MUJI海报

### 5. 高端奢品（>2000元）
- 视觉关键词：稀缺、工艺、传承
- 画面策略：极致特写+微距，只拍材质/工艺/细节
- 色调：深色调（墨黑/深棕/墨绿），金属质感光
- 场景：纯色背景/极简陈列，少即是奢
- 光线：戏剧性光影，伦勃朗光/轮廓光

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 三、4大平台视觉差异

### 抖音/快手（竖版视频 9:16）
- 前3秒必须抓眼球：冲击力构图、对比色、动态元素
- 高饱和高对比，手机小屏看得清
- 人物动态感强（走动/翻转/展示产品）
- 背景简洁不杂乱，聚焦产品
- 字幕区安全：底部20%不放关键元素

### 小红书（竖版图文 3:4）
- 封面图决定一切：产品占60%+，清晰美观
- "杂志感"审美：留白、排版感、色调统一
- 生活化真实感（像手机随拍但构图讲究）
- 系列图有叙事感：吸引→展示→细节→场景→总结
- 文字叠加区域预留（标题/标注位置）

### 淘宝/天猫（正方形/竖版主图 1:1 或 3:4）
- 白底图是刚需（第一张必须纯白底）
- 产品正面/45度/侧面/背面四视图
- 卖点文字叠加（但AI不写文字，留位置）
- 细节图：材质/工艺/功能特写
- 尺寸对比图（手持/模特穿搭展示比例）

### 拼多多（正方形主图 1:1）
- 产品占画面80%+，尽可能大
- 背景简单纯色（白/浅灰/浅黄）
- 突出"量感"和"实惠感"
- 不追求高级感，追求"看得清、看得懂"
- 如果有赠品/套装，全部摆出来拍

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 四、AI生图引擎Prompt规则

### 通义万相（Wanx）— 主图生成
- 语言：中文prompt效果最佳
- 结构：主体描述 + 环境场景 + 光照条件 + 构图方式 + 风格标签
- 长度：80-200字最优，过短细节不足，过长互相冲突
- negative_prompt：英文效果更好，用逗号分隔
- 常用negative：blurry, low quality, text, watermark, logo, deformed, ugly face, cartoon
- 风格控制：在prompt末尾加"商业摄影风格"/"杂志大片风格"/"INS风格"等
- 产品描述要具体：不说"一个包"，说"一个驼色牛皮公文包，方形硬挺，金色搭扣"

### Seedance（字节视频生成）— 宣传视频
- 语言：中英混合prompt，动作描述用英文更精准
- 结构：scene description + camera movement + atmosphere
- motion_description：描述画面中的运动（产品旋转/手拿起/光线流动）
- camera_movement：镜头运动（slow zoom in / orbit / dolly forward / static）
- 时长：5-10秒为最佳生成区间
- 禁忌：不要描述复杂的多人场景、不要描述文字出现

### 抖音脚本视觉（配合视频脚本）
- 每个scene_image必须能独立理解，不依赖"上一张"
- 第一帧=hook画面，必须最抓眼球
- 产品出场时机：第2-3秒（不要开头就怼产品）
- 颜色与脚本情绪一致（痛点=冷色调，解决=暖色调）

### 小红书配图视觉（配合笔记文案）
- 封面图=流量入口，产品必须清晰+美观+有氛围
- 图2-5=叙事节奏，从开箱→使用→细节→效果
- 最后一张=总结图/全家福/使用场景
- 每张图色调统一，像同一组拍摄

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 五、三种工作模式

### 模式A: precise（用户有明确描述）
触发条件：用户给了详细场景描述 或 上传了参考图
你的工作：在用户方向上专业化补全
- 补充光线、构图、色调等技术细节
- 补充让画面更有质感的微小元素
- 但不改变用户的核心意图
输出：1个经过专业补全的完整方案
needs_confirmation: false

### 模式B: guided（用户给了模糊方向）
触发条件：用户选了一些标签 或 写了简短描述
你的工作：在用户方向上给出3个差异化方案
- 每个方案有明确的视觉差异
- 每个方案一句话概要 + 3个视觉关键词
needs_confirmation: true

### 模式C: free（用户什么都没填）
触发条件：用户只选了品类/关键词，没有场景描述
你的工作：基于品类+价格段+平台，给出3个差异化方案
- 方案之间必须有明显差异（不能都是同一类场景）
- 利用品类视觉语言规则生成
needs_confirmation: true

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 六、电商视觉铁律

1. 产品必须是画面焦点，不能被场景淹没
2. 不出现AI生成的真人正脸（恐怖谷效应）
3. 不出现文字/Logo（AI生成文字必出错）
4. 每个prompt独立完整，不依赖"上一张"
5. 具体打败泛泛——不写"时尚的都市场景"，要写"清晨8:15的上海陆家嘴天桥，女性背影，西装+白衬衫，右手提着驼色牛皮公文包，晨光从左侧45度洒下，低饱和暖色调，纵深构图"
6. 产品描述必须具体：材质+颜色+形态+大小，不能模糊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 七、输出格式

你必须输出以下完整JSON（根据输入中要求的output_types字段决定包含哪些部分）：

```json
{
  "needs_confirmation": false,
  "product_profile": {
    "category": "品类",
    "price_tier": "价格段（极致性价比/平价优质/中端品质/轻奢/高端奢品）",
    "visual_language": "该品类+价格段的视觉语言摘要",
    "target_persona": "目标用户画像一句话"
  },
  "main_image_prompts": [
    {
      "image_number": 1,
      "purpose": "白底主图/场景主图/细节图/...",
      "style": "商业摄影/生活场景/极简/杂志感/...",
      "prompt": "完整中文生图prompt（80-200字）",
      "negative_prompt": "英文negative prompt",
      "aspect_ratio": "1:1/3:4/9:16",
      "ref_img_guidance": "如果用户提供了参考图，这里描述参考图的哪些元素要保留"
    }
  ],
  "promo_video_prompt": {
    "duration_seconds": 8,
    "motion_description": "画面中的运动描述（产品旋转/手拿起/光线变化）",
    "camera_movement": "slow zoom in / orbit / dolly forward / static / ...",
    "scene_atmosphere": "完整场景氛围描述",
    "prompt_en": "English prompt for Seedance video generation",
    "negative_prompt": "blurry, low quality, text, watermark, face closeup"
  },
  "douyin_script_hints": {
    "hook_suggestions": ["3个抓人开头画面建议"],
    "pain_points": ["3个可视化的痛点场景"],
    "visual_scenes": [
      {
        "scene_number": 1,
        "scene_description": "场景画面描述",
        "duration_seconds": 3,
        "mood": "情绪/氛围",
        "color_tone": "色调"
      }
    ]
  },
  "xhs_note_hints": {
    "persona": "笔记人设（如：28岁职场女性/宝妈/大学生）",
    "authentic_details": ["3个增加真实感的细节建议"],
    "title_suggestions": ["3个小红书标题建议"],
    "cover_image_direction": "封面图视觉方向一句话"
  },
  "scene_summary": "整体视觉方向的一句话摘要（用于学习系统记录）",
  "visual_consistency": "整组画面的统一视觉标准"
}
```

如果是 guided/free 模式（needs_confirmation: true），输出方案选择格式：

```json
{
  "needs_confirmation": true,
  "product_profile": { ... },
  "options": [
    {
      "option_id": "A",
      "title": "方案名（2-4字）",
      "one_liner": "一句话描述核心画面",
      "visual_keywords": ["关键词1", "关键词2", "关键词3"],
      "mood": "画面情绪/氛围",
      "preview_prompt": "一个预览用的简短prompt（用于快速理解方案方向）"
    }
  ],
  "clarification_question": "如果以上都不满意，请告诉我：你想要偏向XX还是XX？"
}
```

只输出JSON，不要输出其他内容。
"""


# ──────────────────────────────────────────────────────────────
# SceneArchitect Agent
# ──────────────────────────────────────────────────────────────

# 支持的输出类型
OUTPUT_TYPES = frozenset({
    "main_image_prompts",
    "promo_video_prompt",
    "douyin_script_hints",
    "xhs_note_hints",
})

# 默认按平台决定需要哪些输出
PLATFORM_OUTPUT_MAP: dict[str, list[str]] = {
    "douyin": ["main_image_prompts", "promo_video_prompt", "douyin_script_hints"],
    "kuaishou": ["main_image_prompts", "promo_video_prompt", "douyin_script_hints"],
    "xiaohongshu": ["main_image_prompts", "xhs_note_hints"],
    "taobao": ["main_image_prompts"],
    "tmall": ["main_image_prompts"],
    "pinduoduo": ["main_image_prompts"],
}


def _detect_mode(scene_intent: dict) -> str:
    """根据用户输入的充分程度判断工作模式。"""
    mode = scene_intent.get("mode", "")
    if mode in ("free", "guided", "precise"):
        return mode

    user_desc = scene_intent.get("user_description", "").strip()
    mood_keywords = scene_intent.get("mood_keywords", [])
    reference_images = scene_intent.get("reference_images", [])

    if user_desc and len(user_desc) >= 15:
        return "precise"
    if user_desc or mood_keywords:
        return "guided"
    return "free"


def _infer_price_tier(product_info: str, price: float | None = None) -> str:
    """从价格或产品信息推断价格段。"""
    if price is not None:
        if price < 50:
            return "极致性价比"
        if price < 200:
            return "平价优质"
        if price < 500:
            return "中端品质"
        if price < 2000:
            return "轻奢"
        return "高端奢品"
    # 尝试从产品信息中提取价格关键词
    if any(kw in product_info for kw in ("平价", "学生党", "白菜价", "便宜")):
        return "极致性价比"
    if any(kw in product_info for kw in ("轻奢", "品质", "质感")):
        return "轻奢"
    if any(kw in product_info for kw in ("高端", "奢华", "大牌", "限量")):
        return "高端奢品"
    return "中端品质"


class SceneArchitectAgent(BaseAgent):
    """
    场景构建师 Agent — 将商业意图转化为全平台AI生图/视频Prompt。

    输入:
      - task_input.product_info: 产品信息文本
      - task_input.config.scene_intent: 用户场景意图
      - task_input.platform: 目标平台
      - task_input.category: 产品品类
      - task_input.price: 产品价格（可选）
      - task_input.strategy_json: 策略专家输出（可选）
      - task_input.script_or_note: 脚本/文案文本（可选）
      - task_input.vision_analysis: 产品图视觉分析结果（可选）

    输出:
      - product_profile: 品类/价格段/视觉语言/目标人群
      - main_image_prompts[]: 主图prompt列表
      - promo_video_prompt: 宣传视频prompt
      - douyin_script_hints: 抖音脚本视觉提示
      - xhs_note_hints: 小红书笔记视觉提示
      - needs_confirmation: 是否需要用户确认
      - options[]: 方案选项（仅 guided/free 模式）
    """

    agent_type = "scene_architect"

    # ── Observe ──

    async def observe(self, ctx: AgentContext) -> dict:
        """收集产品信息、视觉分析、场景意图、用户DNA。"""
        store = MemoryStore(self.db)

        user_dna = await store.get_user_dna(ctx.user_id)
        few_shots = await store.get_few_shots(ctx.user_id, self.agent_type)
        guardrails = await store.get_failure_guardrails(ctx.user_id, self.agent_type)

        config = ctx.task_input.get("config", {})
        scene_intent = config.get("scene_intent", {})

        return {
            "product_info": self._build_product_info(ctx),
            "platform": ctx.task_input.get("platform", "douyin"),
            "category": ctx.task_input.get("category", "default"),
            "price": ctx.task_input.get("price"),
            "strategy_json": ctx.task_input.get("strategy_json", ""),
            "script_or_note": ctx.task_input.get("script_or_note", ""),
            "vision_analysis": ctx.task_input.get("vision_analysis", ""),
            "scene_intent": scene_intent,
            "user_dna": user_dna,
            "few_shots": few_shots,
            "guardrails": guardrails,
        }

    # ── Think ──

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        """判断模式、确定需要输出哪些类型。"""
        scene_intent = observation["scene_intent"]
        platform = observation["platform"]

        mode = _detect_mode(scene_intent)

        # 确定输出类型：优先用用户指定的，否则按平台默认
        requested_outputs = ctx.task_input.get("output_types")
        if not requested_outputs:
            requested_outputs = PLATFORM_OUTPUT_MAP.get(platform, ["main_image_prompts"])

        # 过滤无效类型
        valid_outputs = [o for o in requested_outputs if o in OUTPUT_TYPES]
        if not valid_outputs:
            valid_outputs = ["main_image_prompts"]

        price_tier = _infer_price_tier(
            observation["product_info"],
            observation.get("price"),
        )

        return {
            "reasoning": (
                f"模式={mode}，平台={platform}，品类={observation['category']}，"
                f"价格段={price_tier}，输出类型={valid_outputs}"
            ),
            "mode": mode,
            "platform": platform,
            "category": observation["category"],
            "price_tier": price_tier,
            "output_types": valid_outputs,
            "observation": observation,
        }

    # ── Act ──

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        """调用LLM生成场景描述和全部Prompt，解析JSON输出。"""
        observation = plan["observation"]

        # 构建完整请求prompt
        request_prompt = self._build_prompt_request(
            product_info=observation["product_info"],
            category=plan["category"],
            price_tier=plan["price_tier"],
            platform=plan["platform"],
            mode=plan["mode"],
            output_types=plan["output_types"],
            scene_intent=observation["scene_intent"],
            strategy_json=observation.get("strategy_json", ""),
            script_or_note=observation.get("script_or_note", ""),
            vision_analysis=observation.get("vision_analysis", ""),
        )

        # 构建system prompt（注入用户DNA + few-shot + guardrails）
        system = self._build_system_prompt(
            user_dna=observation.get("user_dna"),
            few_shots=observation.get("few_shots"),
            guardrails=observation.get("guardrails"),
        )

        # 调用 Claude Sonnet（创意构想+结构化输出最强）
        result = await self._ai_call(
            request_prompt,
            task_type="scene_architect",  # → Claude Sonnet in MODEL_MAP
            system=system,
        )

        # 解析JSON输出
        output = self._parse_output(result["text"])
        output["model"] = result.get("model", "unknown")
        output["mode"] = plan["mode"]

        return output

    # ── Evaluate ──

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        """评估输出质量。"""
        issues = []
        confidence = 0.8

        # 检查必要字段
        if not output.get("product_profile"):
            issues.append("缺少 product_profile")
            confidence -= 0.2

        needs_confirmation = output.get("needs_confirmation", False)

        if needs_confirmation:
            options = output.get("options", [])
            if len(options) < 2:
                issues.append("确认模式下方案数不足")
                confidence -= 0.2
        else:
            if not output.get("main_image_prompts") and not output.get("promo_video_prompt"):
                issues.append("缺少图片或视频prompt输出")
                confidence -= 0.3

            # 检查prompt长度
            for img in output.get("main_image_prompts", []):
                prompt_text = img.get("prompt", "")
                if len(prompt_text) < 30:
                    issues.append(f"图{img.get('image_number', '?')} prompt过短")
                    confidence -= 0.1

        if output.get("error"):
            issues.append(f"解析错误: {output['error']}")
            confidence -= 0.3

        return {
            "confidence": max(0.1, min(1.0, confidence)),
            "issues": issues,
        }

    # ── Private: Prompt构建 ──

    def _build_prompt_request(
        self,
        product_info: str,
        category: str,
        price_tier: str,
        platform: str,
        mode: str,
        output_types: list[str],
        scene_intent: dict,
        strategy_json: str = "",
        script_or_note: str = "",
        vision_analysis: str = "",
    ) -> str:
        """构建发给LLM的完整请求prompt。"""
        parts = []

        # 基础信息
        parts.append("## 任务：生成电商产品视觉场景描述和AI生图Prompt\n")

        parts.append(f"## 产品信息\n{product_info}\n")
        parts.append(f"## 产品品类\n{category}\n")
        parts.append(f"## 价格段\n{price_tier}\n")
        parts.append(f"## 目标平台\n{platform}\n")

        # 工作模式
        parts.append(f"## 工作模式\n{mode}")
        if mode == "precise":
            parts.append("请在用户方向上专业化补全，输出完整方案，needs_confirmation=false。\n")
        elif mode == "guided":
            parts.append("请在用户方向上给出3个差异化方案，needs_confirmation=true。\n")
        else:
            parts.append("用户未提供场景描述，请基于品类+价格段+平台给出3个差异化方案，needs_confirmation=true。\n")

        # 需要输出的类型
        parts.append(f"## 需要输出的类型\n{json.dumps(output_types, ensure_ascii=False)}\n")
        parts.append("只输出以上列出的类型对应的字段，不需要的类型可以省略。\n")

        # 用户场景意图
        if scene_intent:
            parts.append("## 用户场景意图")
            user_desc = scene_intent.get("user_description", "")
            if user_desc:
                parts.append(f"用户描述：{user_desc}")
            mood_kw = scene_intent.get("mood_keywords", [])
            if mood_kw:
                parts.append(f"氛围关键词：{'、'.join(mood_kw)}")
            negative = scene_intent.get("negative", "")
            if negative:
                parts.append(f"用户明确不要：{negative}")
            ref_imgs = scene_intent.get("reference_images", [])
            if ref_imgs:
                parts.append(f"参考图数量：{len(ref_imgs)}张（参考图视觉分析见下方）")
            parts.append("")

        # 视觉分析（来自产品图/参考图的AI分析）
        if vision_analysis:
            parts.append(f"## 产品/参考图视觉分析\n{vision_analysis[:800]}\n")

        # 策略专家输出
        if strategy_json:
            parts.append(f"## 内容策略（由策略专家制定，视觉方向需与策略一致）\n{strategy_json[:1500]}\n")

        # 脚本/文案
        if script_or_note:
            parts.append(f"## 已生成的脚本/文案（视觉提示需与内容匹配）\n{script_or_note[:1500]}\n")

        parts.append("请严格按照系统指令中的输出格式返回JSON。只输出JSON。")

        return "\n".join(parts)

    def _build_system_prompt(
        self,
        user_dna: dict | None = None,
        few_shots: list[dict] | None = None,
        guardrails: list[str] | None = None,
    ) -> str:
        """构建完整system prompt，注入视觉偏好。"""
        parts = [SCENE_ARCHITECT_SYSTEM]

        # 注入视觉偏好（从 user_dna.content_preferences.visual_preferences）
        if user_dna:
            visual_prefs = {}
            content_prefs = user_dna.get("content_preferences")
            if isinstance(content_prefs, dict):
                visual_prefs = content_prefs.get("visual_preferences", {})
            elif isinstance(content_prefs, str):
                try:
                    parsed = json.loads(content_prefs)
                    visual_prefs = parsed.get("visual_preferences", {})
                except (json.JSONDecodeError, AttributeError):
                    pass

            if visual_prefs:
                pref_lines = ["\n## 该用户的视觉偏好（必须遵循）"]
                field_map = {
                    "overall_aesthetic": "整体审美",
                    "preferred_color_tone": "偏好色调",
                    "preferred_scene_types": "常用场景",
                    "avoided_visual_elements": "明确不要",
                }
                for key, label in field_map.items():
                    val = visual_prefs.get(key)
                    if val:
                        if isinstance(val, list):
                            val = "、".join(str(v) for v in val)
                        pref_lines.append(f"- {label}：{val}")

                category_overrides = visual_prefs.get("category_visual_overrides", {})
                if category_overrides:
                    pref_lines.append("- 品类视觉偏好：")
                    for cat, desc in category_overrides.items():
                        pref_lines.append(f"  - {cat}：{desc}")

                if len(pref_lines) > 1:
                    parts.append("\n".join(pref_lines))

        # 注入常规DNA（品牌调性等）
        # 使用通用构建器处理非视觉部分
        generic_system = build_agent_system_prompt(
            "",  # 空role，只取注入部分
            user_dna,
            few_shots,
            guardrails,
        )
        if generic_system.strip():
            parts.append(generic_system)

        # 注入场景构建专用few-shot
        if few_shots:
            parts.append("\n## 该用户认可过的场景描述（参考这些风格）")
            for i, ex in enumerate(few_shots[:3], 1):
                keyword = ex.get("keyword", "")
                summary = ex.get("output_summary", "")[:250]
                parts.append(f"\n### 参考案例{i}: {keyword}\n{summary}")

        # 注入视觉禁忌
        if guardrails:
            parts.append("\n## 视觉禁忌（该用户明确否定过以下方向）")
            for g in guardrails[:5]:
                parts.append(f"- 避免: {g}")

        return "\n".join(parts)

    def _build_product_info(self, ctx: AgentContext) -> str:
        """从上下文提取产品信息文本。"""
        parts = []
        keyword = ctx.task_input.get("keyword", "")
        if keyword:
            parts.append(f"关键词：{keyword}")

        product_info = ctx.task_input.get("product_info", "")
        if product_info:
            parts.append(product_info[:1000])

        selection = ctx.task_input.get("product_selection", "")
        if selection:
            parts.append(f"选品方案：\n{selection[:800]}")

        ai_analysis = ctx.task_input.get("ai_analysis", "")
        if ai_analysis:
            parts.append(f"市场分析摘要：\n{ai_analysis[:500]}")

        return "\n".join(parts) if parts else f"产品关键词：{keyword or '未指定'}"

    # ── Private: 输出解析 ──

    def _parse_output(self, raw_text: str) -> dict:
        """解析LLM的JSON输出，带容错。"""
        text = raw_text.strip()

        # 去掉markdown代码块包装
        if text.startswith("```"):
            lines = text.split("\n")
            # 去除首尾的 ``` 行
            cleaned_lines = []
            in_block = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("```") and not in_block:
                    in_block = True
                    continue
                if stripped == "```" and in_block:
                    in_block = False
                    continue
                if in_block:
                    cleaned_lines.append(line)
            text = "\n".join(cleaned_lines)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # 尝试从文本中提取JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(text[start:end])
                except json.JSONDecodeError:
                    logger.warning("SceneArchitect output JSON parse failed")
                    return {
                        "needs_confirmation": False,
                        "product_profile": {},
                        "main_image_prompts": [],
                        "raw_text": raw_text[:2000],
                        "error": "JSON解析失败，返回原始文本",
                    }
            else:
                return {
                    "needs_confirmation": False,
                    "product_profile": {},
                    "main_image_prompts": [],
                    "raw_text": raw_text[:2000],
                    "error": "未找到JSON结构",
                }

        # 确保关键字段存在
        data.setdefault("needs_confirmation", False)
        data.setdefault("product_profile", {})

        if not data["needs_confirmation"]:
            data.setdefault("main_image_prompts", [])
            data.setdefault("scene_summary", "")
            data.setdefault("visual_consistency", "")
        else:
            data.setdefault("options", [])
            data.setdefault("clarification_question", "")

        return data

    # ── 学习系统辅助方法 ──

    def _summarize(self, output: dict) -> str:
        """生成学习友好的摘要，覆盖基类方法。"""
        summary = {
            "mode": output.get("mode", ""),
            "needs_confirmation": output.get("needs_confirmation", False),
            "scene_summary": output.get("scene_summary", "")[:100],
            "image_style_tags": [],
            "category": output.get("product_profile", {}).get("category", ""),
            "price_tier": output.get("product_profile", {}).get("price_tier", ""),
        }

        # 提取 style_tags
        for img in output.get("main_image_prompts", []):
            style = img.get("style", "")
            if style:
                summary["image_style_tags"].append(style)

        return json.dumps(summary, ensure_ascii=False)[:500]


# ──────────────────────────────────────────────────────────────
# 便捷函数 — 供 content_agent.py 直接调用
# ──────────────────────────────────────────────────────────────

async def run_scene_architect(
    db,
    user_id: str,
    product_info: str,
    platform: str,
    category: str = "default",
    price: float | None = None,
    scene_intent: dict | None = None,
    strategy_json: str = "",
    script_or_note: str = "",
    vision_analysis: str = "",
    output_types: list[str] | None = None,
    pipeline_id: str | None = None,
) -> dict:
    """
    便捷入口：直接运行 SceneArchitectAgent 并返回结果dict。

    供 DouyinContentAgent.act() / XHSContentAgent.act() 在 Step 4 之前调用。

    Returns:
        AgentResult.output dict，包含 needs_confirmation / main_image_prompts / ...
    """
    ctx = AgentContext(
        user_id=user_id,
        pipeline_id=pipeline_id,
        task_input={
            "product_info": product_info,
            "platform": platform,
            "category": category,
            "price": price,
            "config": {"scene_intent": scene_intent or {}},
            "strategy_json": strategy_json,
            "script_or_note": script_or_note,
            "vision_analysis": vision_analysis,
            "output_types": output_types,
        },
    )

    agent = SceneArchitectAgent(db)
    result = await agent.run(ctx)

    if not result.success:
        logger.error(f"SceneArchitect failed: {result.output.get('error', 'unknown')}")

    return result.output
