# 商探AI (ShangTan AI) — 产品手册 v1.0

## AI 赋能电商全链路运营

> **产品名称：** 商探AI (ShangTan AI)
> **Slogan：** AI 洞察商机，全链路掌控
> **版本：** v1.0
> **创建日期：** 2026-03-17
> **文档性质：** 产品规格书 + 技术架构文档 + Claude Code 项目知识库
> **适用环境：** 国内电商（淘宝/天猫、拼多多、抖音电商、京东、小红书、快手）

---

# ═══════════════════════════════════════════
# 第一部分：产品定义
# ═══════════════════════════════════════════

## 1.1 产品定位

商探AI 是面向国内电商卖家的 **AI 全链路运营一体化工具**。以选品分析为核心，覆盖从市场调研到售后客服的完整经营闭环，通过 AI 自动化替代传统电商团队中选品部、设计部、运营部、客服部的重复性工作。

**核心理念：** 一个人 + 商探AI = 一个电商运营团队

**一句话描述：** 给国内电商卖家用的 AI 全能运营工具，从选品到客服一站式搞定。

## 1.2 目标用户

| 用户类型 | 特征 | 核心需求 |
|---------|------|---------|
| 个人卖家/新手 | 刚入行，1人运营，预算有限 | 选品指导、内容生成、降低入行门槛 |
| 中小卖家 | 1-5人团队，已有一定销量 | 提升效率、降低人力成本、多平台管理 |
| 电商团队 | 5-20人，多店铺多平台运营 | 团队协作、数据驱动决策、规模化运营 |
| 工厂转电商 | 有供应链，不懂线上运营 | 从零到一的电商运营全套能力 |
| 代运营公司 | 管理多个品牌/店铺 | 批量操作、标准化流程、客户管理 |

## 1.3 支持平台

| 平台 | 优先级 | v1.0 支持方式 | 后续对接 |
|------|--------|-------------|---------|
| 抖音电商 | P0 | 手动输入 + AI 分析 | 抖店开放平台 API |
| 淘宝/天猫 | P0 | 手动输入 + AI 分析 | 淘宝开放平台 API（需 ISV） |
| 拼多多 | P1 | 手动输入 + AI 分析 | 拼多多开放平台 API |
| 小红书 | P1 | 手动输入 + AI 分析 | 聚光 API（广告侧） |
| 京东 | P2 | 手动输入 + AI 分析 | 京麦 API |
| 快手 | P2 | 手动输入 + AI 分析 | 磁力引擎 API |

## 1.4 功能模块总览

系统包含 **7 大功能模块 + 1 个基础平台**，按优先级排序：

| 优先级 | 模块编号 | 模块名称 | 标识符 | 核心职能 |
|--------|---------|---------|--------|---------|
| ★★★★★ | M1 | 选品雷达 | product_scout | 市场洞察、爆款追踪、竞品分析、选品推荐、利润测算 |
| ★★★★☆ | M2 | 内容工厂 | content_factory | 短视频脚本、种草笔记、商品图片、直播话术、广告素材 |
| ★★★☆☆ | M3 | 上架中心 | listing_hub | 标题优化、详情页、关键词、多平台格式导出 |
| ★★★☆☆ | M4 | 广告助手 | ad_assistant | 投放方案、素材优化、预算建议、ROI 追踪 |
| ★★☆☆☆ | M5 | 运营管家 | ops_manager | 定价策略、库存预警、促销策划、评论管理 |
| ★★☆☆☆ | M6 | 客服大脑 | cs_brain | AI 自动回复、多平台消息、工单系统、知识库 |
| ★★☆☆☆ | M7 | 数据驾驶舱 | data_cockpit | 经营看板、AI 日报、归因分析、趋势预测 |
| 基础 | P0 | 基础平台 | platform | 用户系统、店铺管理、积分计费、团队协作 |

## 1.5 产品设计原则

借鉴 MediaMatrix 的成功设计，商探AI 遵循以下原则：

1. **选品为根** — 选品是电商经营的第一步，也是最关键的一步，所有模块围绕"选对品、卖好货"展开
2. **用户做选择题** — 系统通过店铺定位 + AI 分析自动推导参数，用户只在关键节点做审核决策
3. **平台无关架构** — 核心 AI 能力不依赖任何平台 API，确保全平台通用；平台特定功能通过适配层扩展
4. **AI 越用越准** — 系统学习用户的选品偏好、经营风格、决策模式，持续优化推荐准确度
5. **模块独立、数据贯通** — 每个模块可独立使用，共享统一数据层；选品数据可直接流转到内容制作和上架
6. **降级容错** — 任何外部 API 失败都有备选方案，永不阻塞用户流程

---

# ═══════════════════════════════════════════
# 第二部分：功能详细规格
# ═══════════════════════════════════════════

## M1 — 选品雷达（Product Scout）★★★★★

> **模块定位：** 整个产品的核心和第一入口。帮助卖家从海量商品中发现高利润、低竞争的商机。

### 2.1.1 子功能清单

#### F1.1 市场洞察

**功能描述：** 输入关键词/品类/商品链接，AI 自动分析市场容量、竞争格局、价格带、趋势方向。

**输入方式（v1.0）：**
- 关键词搜索：输入"瑜伽裤"、"无线耳机"等
- 商品链接：粘贴淘宝/抖音/拼多多等平台商品链接
- 品类浏览：从品类树中选择
- 图片搜索（v1.1）：上传商品图片，AI 识别品类

**AI 分析输出：**
- 市场规模评估（大盘/增长率/天花板）
- 竞争格局分析（头部品牌占比/中小卖家机会/价格带分布）
- 进入难度评分（0-100分）
- 季节性分析（淡旺季周期/大促节点影响）
- 细分机会推荐（蓝海细分品类/差异化方向）

**AI 模型分配：**
- 深度市场分析报告：Claude Sonnet（质量优先）
- 批量关键词初筛：DeepSeek（成本优先）

#### F1.2 爆款追踪

**功能描述：** 追踪各平台热销商品和新晋爆款，发现跟款机会。

**追踪维度：**
- 抖音爆款：直播间热销、短视频带货爆品、商品榜单
- 淘宝爆款：热搜词飙升、行业热销榜、新品飙升榜
- 拼多多爆款：拼单热门、百亿补贴热销
- 小红书爆款：种草笔记高互动商品、热门话题关联商品
- 快手/京东同理

**数据来源策略（渐进式）：**
- v1.0：用户手动粘贴商品链接 + AI 分析商品信息
- v1.1：对接第三方数据服务（蝉妈妈/飞瓜/千瓜等 API，或使用开源采集工具）
- v2.0：自建数据采集系统

**输出内容：**
- 爆款商品卡片（标题/价格/销量/评分/趋势曲线）
- 爆款原因分析（AI 归因：价格优势/内容引爆/季节性/大促带动）
- 跟款可行性评估（供应链难度/差异化空间/利润预估）
- 跟款建议（建议跟/谨慎跟/不建议跟 + 理由）

#### F1.3 竞品监控

**功能描述：** 持续追踪竞争对手的店铺和商品动态。

**监控对象：**
- 竞品店铺：添加竞对店铺链接，监控其上新、价格调整、活动参与
- 竞品商品：添加竞品商品链接，监控价格/销量/评价/排名变化
- 关键词排名：追踪核心关键词下竞品的排名变化

**监控频率：**
- v1.0：用户手动刷新（点击"更新数据"按钮）
- v1.1：Celery Beat 自动定时采集（每 6 小时 / 每日 / 自定义）

**变化告警：**
- 竞品降价 > 10% → 告警
- 竞品上新 → 通知
- 竞品销量异常飙升 → 分析原因
- 竞品评分骤降 → 机会提醒
- 推送渠道：站内通知 + Telegram + 钉钉

#### F1.4 选品推荐引擎

**功能描述：** 基于用户设定的经营条件，AI 综合评分推荐值得做的商品。

**用户设定条件：**
- 目标平台（淘宝/抖音/拼多多等，可多选）
- 品类偏好（服饰/3C/家居/美妆/食品等）
- 预算范围（客单价区间、备货资金）
- 利润率要求（毛利率 > X%）
- 经营模式（自有供应链/1688拿货/代发/品牌代理）
- 风险偏好（保守/稳健/激进）

**AI 评分维度：**
```
综合得分 = 需求热度 × 0.25 + 利润空间 × 0.25 + 竞争可行性 × 0.20 + 趋势潜力 × 0.15 + 供应链匹配度 × 0.15
```

每个维度 0-100 分，综合得分 > 70 为推荐，50-70 为可考虑，< 50 为不推荐。

**输出：选品报告**
- 推荐商品列表（按综合得分排序）
- 每个商品的详细分析（五维雷达图 + 文字分析）
- 对标竞品（找到 3-5 个做得好的竞品作为参考）
- 差异化建议（AI 给出如何做出差异化的具体方向）
- 1688 货源建议（推荐搜索关键词和筛选条件）
- 风险提示（侵权风险/季节性风险/政策风险等）

#### F1.5 利润计算器

**功能描述：** 精确计算各平台的商品利润。

**输入项：**
- 采购成本（单件）
- 物流/快递费用（按重量/首重续重计算）
- 包装成本
- 目标售价（或让 AI 建议）
- 平台佣金比例（系统内置各平台各品类佣金表）
- 广告费占比（可调，默认 15-25%）
- 退货率（可调，系统按品类给默认值）
- 其他费用（仓储/人工等）

**输出项：**
- 毛利 / 毛利率
- 净利 / 净利率（扣除广告、退货、平台佣金后）
- 盈亏平衡点（每天需要卖多少单才不亏）
- 不同售价下的利润对比表
- ROI 预估（投入产出比）

**平台佣金内置表（预填，可用户自定义）：**

| 平台 | 基础佣金 | 技术服务费 | 其他 |
|------|---------|----------|------|
| 淘宝 | 0.6%-5% | — | 保证金 |
| 天猫 | 2%-5% | 3%-5% | 保证金 |
| 抖音电商 | 1%-5% | — | 保证金 |
| 拼多多 | 0.6%-3% | — | 保证金 |
| 京东 | 2%-8% | — | 保证金 |
| 小红书 | 3%-5% | — | — |
| 快手 | 1%-5% | — | — |

#### F1.6 趋势雷达

**功能描述：** 监测市场趋势和热点，提前发现商机。

**数据来源：**
- 百度指数 / 微信指数 / 抖音搜索趋势
- 社交媒体热点（微博热搜/抖音热门话题/小红书热门标签）
- 电商平台搜索词趋势
- 季节性日历（春节/618/双11/圣诞/情人节等节点）

**输出：**
- 趋势上升品类/关键词排行
- 即将到来的热点预警（节日/事件/季节）
- AI 趋势周报：每周自动生成，推送到 Telegram/钉钉

### 2.1.2 选品雷达数据模型

```sql
-- 市场扫描记录
CREATE TABLE market_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    scan_type VARCHAR(20) NOT NULL, -- 'keyword','url','category','image'
    input_value TEXT NOT NULL, -- 关键词/链接/品类ID
    platform VARCHAR(20), -- 'taobao','douyin','pinduoduo','jd','xiaohongshu','kuaishou','all'
    market_size_score INTEGER CHECK (market_size_score BETWEEN 0 AND 100),
    competition_score INTEGER CHECK (competition_score BETWEEN 0 AND 100),
    entry_difficulty INTEGER CHECK (entry_difficulty BETWEEN 0 AND 100),
    trend_score INTEGER CHECK (trend_score BETWEEN 0 AND 100),
    avg_price_min DECIMAL(10,2),
    avg_price_max DECIMAL(10,2),
    analysis_summary TEXT, -- AI 生成的摘要
    analysis_full JSONB, -- 完整 AI 分析结果 JSON
    credits_consumed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 竞品追踪
CREATE TABLE competitor_tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    track_type VARCHAR(20) NOT NULL, -- 'product','shop','keyword'
    platform VARCHAR(20) NOT NULL,
    external_url TEXT, -- 原始链接
    external_id VARCHAR(255), -- 商品ID/店铺ID
    title VARCHAR(500),
    current_price DECIMAL(10,2),
    current_sales INTEGER, -- 月销量
    current_rating DECIMAL(3,2),
    current_reviews INTEGER,
    thumbnail_url VARCHAR(1024),
    alert_rules JSONB, -- 告警规则配置
    is_active BOOLEAN DEFAULT true,
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_competitor_tracks_user ON competitor_tracks(user_id, is_active);

-- 竞品快照（历史数据点）
CREATE TABLE competitor_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES competitor_tracks(id) ON DELETE CASCADE,
    price DECIMAL(10,2),
    sales INTEGER,
    rating DECIMAL(3,2),
    reviews INTEGER,
    rank_position INTEGER, -- 排名
    extra_data JSONB, -- 其他采集到的数据
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_snapshots_track_time ON competitor_snapshots(track_id, snapshot_at DESC);

-- 选品推荐
CREATE TABLE product_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    scan_id UUID REFERENCES market_scans(id),
    product_title VARCHAR(500),
    category VARCHAR(255),
    platform VARCHAR(20),
    overall_score INTEGER CHECK (overall_score BETWEEN 0 AND 100),
    demand_score INTEGER,
    profit_score INTEGER,
    competition_score INTEGER,
    trend_score INTEGER,
    supply_chain_score INTEGER,
    estimated_monthly_sales INTEGER,
    estimated_profit_margin DECIMAL(5,2),
    competitor_asins TEXT[], -- 对标竞品
    differentiation_suggestions TEXT, -- AI差异化建议
    risk_warnings TEXT, -- 风险提示
    report_json JSONB, -- 完整报告
    status VARCHAR(20) DEFAULT 'new', -- 'new','reviewed','accepted','rejected','testing'
    user_notes TEXT, -- 用户备注
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 利润计算记录
CREATE TABLE profit_calculations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    product_name VARCHAR(255),
    platform VARCHAR(20),
    cost_price DECIMAL(10,2), -- 采购成本
    shipping_cost DECIMAL(10,2), -- 物流费用
    packaging_cost DECIMAL(10,2), -- 包装成本
    selling_price DECIMAL(10,2), -- 售价
    commission_rate DECIMAL(5,4), -- 平台佣金率
    ad_spend_rate DECIMAL(5,4), -- 广告费占比
    return_rate DECIMAL(5,4), -- 退货率
    other_costs DECIMAL(10,2), -- 其他费用
    gross_profit DECIMAL(10,2), -- 毛利
    gross_margin DECIMAL(5,4), -- 毛利率
    net_profit DECIMAL(10,2), -- 净利
    net_margin DECIMAL(5,4), -- 净利率
    break_even_units INTEGER, -- 盈亏平衡单量/天
    calculation_json JSONB, -- 完整计算明细
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 趋势数据
CREATE TABLE trend_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keyword VARCHAR(255) NOT NULL,
    platform VARCHAR(20), -- 数据来源平台
    signal_type VARCHAR(30), -- 'rising','hot','seasonal','event'
    heat_score INTEGER, -- 热度分 0-100
    growth_rate DECIMAL(8,2), -- 增长率%
    related_categories VARCHAR(255)[], -- 关联品类
    description TEXT, -- AI 描述
    detected_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_trends_time ON trend_signals(detected_at DESC);
```

---

## M2 — 内容工厂（Content Factory）★★★★☆

> **模块定位：** AI 自动生成电商所需的全部内容素材。国内电商的核心战场是"内容种草+短视频+直播"，内容工厂围绕这三大场景设计。

### 2.2.1 子功能清单

#### F2.1 短视频脚本生成

**适用场景：** 抖音/快手/小红书视频号的带货短视频

**输入方式：**
- 选择商品（从商品库选或手动输入商品信息）
- 选择视频类型：
  - 商品展示（纯展示产品外观和功能）
  - 开箱种草（拆包 + 初体验 + 推荐）
  - 使用教程（功能演示 + 操作步骤）
  - 对比评测（与竞品对比突出优势）
  - 故事剧情（场景化种草，有剧情带入）
  - 口播带货（真人出镜讲解推荐）
- 选择目标平台（影响视频时长和风格）
- 选择风格调性（专业/轻松/搞笑/高级感/性价比）

**AI 生成 Pipeline（参考 MediaMatrix 6 步流水线）：**
1. **脚本生成** → AI 根据商品卖点 + 视频类型 + 平台特性生成分镜脚本
2. **画面描述** → 每个镜头的画面描述、运镜指导
3. **文案/旁白** → 配合画面的口播文案或字幕文案
4. **BGM 建议** → 根据内容调性推荐音乐风格
5. **封面标题** → 生成吸引点击的封面文案和配图建议
6. **发布建议** → 最佳发布时间、标签、话题推荐

**AI 模型：** Claude Sonnet（脚本质量是核心）

#### F2.2 种草笔记生成

**适用场景：** 小红书笔记、抖音图文、微博种草

**支持类型：**
- 好物分享笔记（"我入手了XX，真的绝了"）
- 合集推荐笔记（"X 个好用到哭的XX推荐"）
- 测评对比笔记（"XX vs XX 到底哪个值得买"）
- 教程攻略笔记（"手把手教你XX"）
- 场景种草笔记（"租房改造必备好物"）

**AI 生成内容：**
- 笔记标题（多个版本供选择，含 emoji 和热搜关键词）
- 正文内容（符合小红书/抖音的写作风格，自然不硬广）
- 配图建议（需要拍哪些角度的图、配图文案）
- 标签推荐（热门标签 + 精准标签）
- SEO 关键词植入

**AI 模型：** Claude Sonnet

#### F2.3 商品图片生成

**适用场景：** 主图、详情页图片、SKU 图、广告素材图

**支持类型：**
- 白底主图（符合各平台主图规范）
- 场景图（商品在使用场景中的展示）
- 卖点图（突出核心卖点的图文结合图）
- 对比图（使用前后对比、竞品对比）
- 尺寸图（商品尺寸标注图）

**工作流程：**
1. 用户上传商品原图（实拍图/供应商图）
2. 选择图片类型和目标平台
3. AI 自动处理：抠图 + 换背景 + 添加文案 + 排版
4. 生成多个版本供选择
5. 支持在线编辑微调

**AI 模型：** 可灵 AI kling-image-o1（图片生成/编辑）
**降级方案：** DALL-E 3 / Stable Diffusion API

#### F2.4 直播话术生成

**适用场景：** 直播间的完整话术脚本

**生成内容：**
- 开场话术（聚人气、留人）
- 商品讲解话术（卖点提炼、痛点刺激、场景带入）
- 逼单话术（限时限量、价格锚定、从众心理）
- 互动话术（引导评论/关注/转发）
- 过渡话术（商品之间的自然过渡）
- 下播话术（预告下次直播、引导关注）

**输入：** 商品信息 + 直播时长 + 商品数量 + 主播风格（激情型/专业型/亲和型）
**输出：** 完整直播脚本（带时间轴标注）

**AI 模型：** Claude Sonnet

#### F2.5 广告素材生成

**适用场景：** 千川素材、直通车创意、信息流广告

**支持平台和规格：**
- 巨量千川：竖版视频 9:16 / 横版 16:9 / 方形 1:1
- 直通车/万相台：主图创意 800×800
- 小红书聚光：图文笔记格式 / 视频格式
- 快手磁力引擎：竖版视频

**生成内容：**
- 广告文案（标题 + 描述，多组 A/B 变体）
- 广告配图（基于商品图 AI 生成多版本）
- 视频脚本（15秒/30秒/60秒短视频广告脚本）

**AI 模型：** Claude Sonnet（文案）+ 可灵 AI（图片/视频）

#### F2.6 素材库

**功能描述：** 所有生成的素材统一管理

**功能：**
- 自动按商品/平台/类型/日期归档
- 收藏、标签、搜索
- 素材效果追踪（关联到使用了该素材的商品/广告，追踪 CTR 等）
- 批量导出
- 存储：阿里云 OSS

### 2.2.2 内容工厂数据模型

```sql
-- 内容项目
CREATE TABLE content_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    store_id UUID REFERENCES stores(id),
    product_id UUID REFERENCES products(id),
    project_type VARCHAR(30) NOT NULL, -- 'short_video','xiaohongshu_note','product_image','live_script','ad_creative'
    title VARCHAR(255),
    platform VARCHAR(20), -- 目标平台
    style_preset VARCHAR(50), -- 风格预设
    status VARCHAR(20) DEFAULT 'draft', -- 'draft','generating','review','completed','failed'
    pipeline_step INTEGER DEFAULT 0, -- 当前步骤
    auto_mode BOOLEAN DEFAULT false,
    input_config JSONB, -- 用户输入的配置
    output_result JSONB, -- AI 生成的结果
    credits_consumed INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 内容素材
CREATE TABLE content_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES content_projects(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id),
    asset_type VARCHAR(20) NOT NULL, -- 'image','video','text','audio'
    file_url VARCHAR(1024),
    file_size INTEGER, -- bytes
    dimensions VARCHAR(20), -- '1080x1920'
    duration_seconds INTEGER, -- 视频/音频
    thumbnail_url VARCHAR(1024),
    content_text TEXT, -- 文案类内容直接存文本
    platform VARCHAR(20), -- 适用平台
    tags VARCHAR(100)[],
    is_favorite BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0, -- 被使用次数
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_assets_user_type ON content_assets(user_id, asset_type);
CREATE INDEX idx_assets_tags ON content_assets USING GIN(tags);

-- 文案输出（多语言/多版本）
CREATE TABLE copywriting_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES content_projects(id) ON DELETE CASCADE,
    content_type VARCHAR(30) NOT NULL, -- 'video_script','note_title','note_body','live_script','ad_copy','product_title','bullet_points','description'
    content_text TEXT NOT NULL,
    platform VARCHAR(20),
    seo_keywords VARCHAR(255)[],
    version INTEGER DEFAULT 1,
    is_selected BOOLEAN DEFAULT false, -- 用户选中的版本
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## M3 — 上架中心（Listing Hub）★★★☆☆

> **模块定位：** AI 优化商品信息，一键导出多平台上架所需的全部内容。

### 2.3.1 子功能清单

#### F3.1 商品信息管理

**功能描述：** 统一管理所有商品的基础信息，作为其他模块的数据源头。

**商品信息：**
- 基础信息：SKU、标题、品牌、品类、规格参数
- 成本信息：采购价、物流成本、包装成本
- 图片素材：主图、详情图（关联素材库）
- 卖点提炼：核心卖点、差异化优势、适用人群
- 供应商信息：1688 链接、供应商联系方式

#### F3.2 Listing 优化器

**功能描述：** AI 优化商品标题、详情、关键词，提升搜索排名和转化率。

**优化内容：**
- **标题优化：** 根据目标平台规则，智能嵌入高搜索量关键词，控制字符数
  - 淘宝标题：60 字符上限，核心词+属性词+长尾词
  - 抖音标题：30 字符，简洁有力+痛点关键词
  - 拼多多标题：60 字符，强调性价比关键词
- **卖点描述：** 五点式卖点（类似亚马逊 Bullet Points），突出差异化
- **详情页文案：** 痛点引入→解决方案→产品优势→使用场景→规格参数→FAQ
- **搜索关键词：** 挖掘高搜索量低竞争关键词，最大化覆盖

**优化评分：** AI 对优化前后的 Listing 给出评分（0-100），展示优化前后对比

**AI 模型：** Claude Sonnet

#### F3.3 多平台格式导出

**功能描述：** 一份商品信息，自动适配多平台格式差异，导出为各平台要求的文件格式。

**v1.0 支持：**
- 淘宝/天猫：数据包 CSV（淘宝助理格式）
- 拼多多：商品 Excel 模板
- 抖音电商：抖店商品 Excel 模板
- 京东：京东商品 Excel 模板
- 通用格式：JSON / CSV

**自动适配：**
- 标题长度裁剪（按各平台限制）
- 品类映射（统一品类 → 各平台品类 ID）
- 图片尺寸适配
- 必填字段检查

#### F3.4 关键词工具

**功能描述：** 关键词挖掘、分析、管理。

**子功能：**
- **关键词挖掘：** 输入核心词，AI 拓展长尾词、相关词、下拉词、热搜词
- **竞品关键词分析：** 分析竞品标题/详情中使用的关键词（v1.0 基于文本分析，v2.0 对接平台数据）
- **关键词分组：** AI 自动将关键词按搜索意图分组（品牌词/品类词/属性词/场景词/长尾词）
- **关键词库：** 保存和管理常用关键词，关联到商品

**AI 模型：** DeepSeek（批量处理成本低）+ Claude Haiku（智能分组）

#### F3.5 违规检测

**功能描述：** 上架前扫描内容，检测违规风险。

**检测项：**
- 广告法违禁词（"最好"/"第一"/"国家级"等绝对化用语）
- 平台禁用词（各平台特有的禁止关键词）
- 虚假宣传风险（夸大功效/虚假承诺）
- 侵权风险（品牌名/专利/外观设计相似度）
- 资质要求提醒（食品/化妆品/电子产品等需要的资质）

**技术实现：** 规则引擎（正则匹配禁词库）+ Claude Haiku（语义级别判断）
**输出：** 风险等级（绿色通过/黄色警告/红色阻断）+ 具体问题定位 + 修改建议

### 2.3.2 上架中心数据模型

```sql
-- 商品（核心实体，被所有模块引用）
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    store_id UUID REFERENCES stores(id),
    sku VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    category VARCHAR(255),
    brand VARCHAR(255),
    cost_price DECIMAL(10,2), -- 采购成本
    shipping_cost DECIMAL(10,2),
    packaging_cost DECIMAL(10,2),
    weight_g INTEGER, -- 重量(克)
    dimensions VARCHAR(50), -- 尺寸 LxWxH cm
    selling_points TEXT[], -- 核心卖点数组
    target_audience VARCHAR(255), -- 目标人群
    supplier_url VARCHAR(1024), -- 1688 供应商链接
    supplier_contact VARCHAR(255),
    images VARCHAR(1024)[], -- 主图URL数组
    status VARCHAR(20) DEFAULT 'draft', -- 'draft','active','paused','archived'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_products_user ON products(user_id, status);

-- Listing（每个商品在每个平台一条记录）
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    title VARCHAR(500), -- 优化后的平台标题
    bullet_points TEXT[], -- 卖点描述
    description TEXT, -- 详情描述
    search_keywords VARCHAR(500)[], -- 搜索关键词
    price DECIMAL(10,2),
    category_id VARCHAR(100), -- 平台品类ID
    optimization_score INTEGER, -- AI优化评分 0-100
    compliance_status VARCHAR(10) DEFAULT 'unchecked', -- 'unchecked','pass','warning','fail'
    compliance_details JSONB,
    export_format VARCHAR(20), -- 'csv','excel','json'
    exported_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'draft', -- 'draft','optimized','exported','published'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(product_id, platform)
);

-- 关键词库
CREATE TABLE keywords (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    keyword VARCHAR(255) NOT NULL,
    platform VARCHAR(20),
    keyword_type VARCHAR(20), -- 'brand','category','attribute','scene','longtail'
    search_volume_estimate INTEGER, -- 预估搜索量
    competition_level VARCHAR(10), -- 'low','medium','high'
    relevance_score INTEGER, -- 相关度 0-100
    source VARCHAR(20), -- 'ai_mined','competitor','manual','trend'
    linked_product_id UUID REFERENCES products(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_keywords_user ON keywords(user_id);

-- 违禁词库（系统级）
CREATE TABLE forbidden_words (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- 'absolute','medical','false_claim','brand'
    platform VARCHAR(20), -- null = 全平台通用
    severity VARCHAR(10), -- 'block','warn'
    replacement_suggestion VARCHAR(255),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## M4 — 广告助手（Ad Assistant）★★★☆☆

> **模块定位：** AI 生成投放方案和广告素材，追踪 ROI，给出优化建议。v1.0 以方案生成和数据手动录入分析为主，v2.0 对接广告平台 API。

### 2.4.1 子功能清单

#### F4.1 投放方案生成

**功能描述：** 根据商品信息和预算，AI 生成完整的广告投放方案。

**支持平台：**
- 巨量千川（抖音电商）
- 直通车 / 万相台 / 引力魔方（淘系）
- 多多搜索 / 多多场景（拼多多）
- 小红书聚光
- 磁力金牛（快手）

**AI 生成内容：**
- 投放策略选择（搜索推广/信息流/直播间引流）
- 关键词/人群定向建议
- 出价区间建议
- 日预算分配方案
- 投放时段建议
- 素材搭配建议（关联内容工厂 M2 生成的素材）
- 预期效果估算（曝光/点击/转化/ROAS 预估）

**AI 模型：** Claude Sonnet

#### F4.2 广告数据录入与分析

**v1.0 数据来源：** 用户手动上传各平台的广告报表（CSV/Excel）
**v2.0 数据来源：** 对接广告平台 API 自动同步

**分析维度：**
- 按计划/单元/关键词/素材维度分析效果
- 核心指标：花费、曝光、点击、CTR、转化、ROI/ROAS、CPC、CPA
- 趋势图表：日/周/月趋势
- 异常检测：花费异常飙升、ROI 骤降等自动告警

#### F4.3 AI 优化建议

**功能描述：** 基于广告数据，AI 给出具体的优化建议。

**建议类型：**
- 关键词优化：暂停高花费低转化词、加价高转化低花费词、添加否定词
- 出价调整：根据时段/竞争情况建议调价
- 预算分配：将预算从低效计划转移到高效计划
- 素材迭代：识别疲劳素材，建议更换
- 人群优化：收窄或扩大人群定向

**AI 模型：** Claude Haiku（实时分析，快速响应）

#### F4.4 A/B 测试管理

- 创建素材/文案/出价的 A/B 测试计划
- 追踪各版本的效果数据
- 自动计算统计显著性，推荐赢家

### 2.4.2 广告助手数据模型

```sql
-- 广告计划
CREATE TABLE ad_campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    store_id UUID REFERENCES stores(id),
    product_id UUID REFERENCES products(id),
    platform VARCHAR(20) NOT NULL, -- 'qianchuan','zhitongche','duoduo_search','juhguang','cili'
    campaign_name VARCHAR(255),
    campaign_type VARCHAR(30), -- 'search','feed','live_stream','brand'
    daily_budget DECIMAL(10,2),
    target_roas DECIMAL(5,2),
    ai_plan JSONB, -- AI 生成的投放方案
    status VARCHAR(20) DEFAULT 'draft', -- 'draft','active','paused','ended'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 广告效果数据（手动上传或API同步）
CREATE TABLE ad_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES ad_campaigns(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10,2) DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    revenue DECIMAL(10,2) DEFAULT 0,
    ctr DECIMAL(8,6),
    cvr DECIMAL(8,6),
    cpc DECIMAL(10,4),
    cpa DECIMAL(10,2),
    roas DECIMAL(8,2),
    data_source VARCHAR(20) DEFAULT 'manual', -- 'manual','api'
    raw_data JSONB, -- 原始上传数据
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, date)
);

-- AI 优化建议
CREATE TABLE ad_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES ad_campaigns(id) ON DELETE CASCADE,
    suggestion_type VARCHAR(30), -- 'pause_keyword','increase_bid','decrease_bid','add_negative','change_creative','adjust_budget'
    target_entity VARCHAR(255), -- 具体关键词/素材/人群
    current_value VARCHAR(100), -- 当前值
    suggested_value VARCHAR(100), -- 建议值
    reason TEXT, -- AI 给出的原因
    expected_impact TEXT, -- 预期效果
    confidence DECIMAL(3,2), -- 置信度 0-1
    status VARCHAR(20) DEFAULT 'pending', -- 'pending','accepted','rejected','applied'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- A/B 测试
CREATE TABLE ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    campaign_id UUID REFERENCES ad_campaigns(id),
    test_name VARCHAR(255),
    test_type VARCHAR(20), -- 'creative','copy','bid','audience'
    variant_a JSONB,
    variant_b JSONB,
    metric VARCHAR(30), -- 'ctr','cvr','roas'
    status VARCHAR(20) DEFAULT 'running', -- 'running','concluded','cancelled'
    winner VARCHAR(1), -- 'a','b' or null
    significance DECIMAL(5,4), -- 统计显著性
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);
```

---

## M5 — 运营管家（Operations Manager）★★☆☆☆

> **模块定位：** 日常运营辅助。智能定价、库存管理、促销策划、评论管理。

### 2.5.1 子功能清单

#### F5.1 智能定价
- 基于竞品价格 + 成本 + 目标利润率，AI 推荐最优定价
- 动态定价规则：跟随竞品 / 固定利润率 / 大促价 / 日常价
- 多平台差异化定价建议（同一商品在淘宝和拼多多的定价策略不同）

#### F5.2 库存预警
- 手动录入库存数量（v1.0）/ 对接 ERP（v2.0）
- 基于日均销量计算可售天数
- 安全库存提醒、补货建议
- 大促前备货计算器

#### F5.3 促销策划
- 基于电商日历（618/双11/年货节/38女王节等）自动生成促销方案
- AI 生成：折扣力度、优惠券策略、满减方案、赠品搭配
- 促销效果预估
- 活动报名提醒（平台活动报名截止日期）

#### F5.4 评论管理
- 手动录入/粘贴评论（v1.0）/ API 自动采集（v2.0）
- AI 情感分析：正面/中性/负面
- 差评归因分类（质量/物流/色差/尺码/气味/描述不符等）
- AI 生成回复模板
- 差评预警（1星/2星评论立即通知）
- 好评分析：提炼用户最认可的卖点，反馈到内容制作

### 2.5.2 运营管家数据模型

```sql
-- 定价规则
CREATE TABLE pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    platform VARCHAR(20),
    rule_type VARCHAR(20), -- 'fixed_margin','follow_competitor','promo','manual'
    target_margin DECIMAL(5,4),
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    competitor_track_id UUID REFERENCES competitor_tracks(id),
    price_offset DECIMAL(10,2), -- 比竞品高/低多少
    promo_price DECIMAL(10,2), -- 大促价
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 库存记录
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse VARCHAR(100) DEFAULT 'default', -- 仓库
    current_stock INTEGER NOT NULL DEFAULT 0,
    safety_stock INTEGER DEFAULT 50, -- 安全库存
    daily_avg_sales DECIMAL(8,2), -- 日均销量
    days_of_stock INTEGER, -- 可售天数（计算字段）
    reorder_point INTEGER, -- 补货点
    suggested_reorder_qty INTEGER,
    last_restocked_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 促销活动
CREATE TABLE promotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    store_id UUID REFERENCES stores(id),
    promo_name VARCHAR(255),
    platform VARCHAR(20),
    promo_type VARCHAR(30), -- 'coupon','discount','full_reduction','gift','flash_sale','bundle'
    discount_detail JSONB, -- 折扣详情
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    target_products UUID[], -- 参与商品
    ai_plan JSONB, -- AI 生成的方案
    estimated_sales_lift DECIMAL(5,2),
    actual_sales_lift DECIMAL(5,2),
    status VARCHAR(20) DEFAULT 'draft', -- 'draft','scheduled','active','ended'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 评论
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id),
    platform VARCHAR(20),
    reviewer_name VARCHAR(255),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    content TEXT,
    images VARCHAR(1024)[],
    sentiment VARCHAR(10), -- 'positive','neutral','negative'
    issue_category VARCHAR(50), -- 'quality','shipping','size','color','smell','description'
    ai_reply TEXT, -- AI 生成的回复
    is_replied BOOLEAN DEFAULT false,
    review_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_reviews_product ON reviews(product_id, sentiment);
```

---

## M6 — 客服大脑（CS Brain）★★☆☆☆

> **模块定位：** 多平台 AI 智能客服系统。基于已有的小洛客服 AI 架构扩展。

### 2.6.1 子功能清单

#### F6.1 多平台消息接入
**v1.0 支持：**
- Email（SMTP/IMAP）— 最易对接
- Telegram Bot — 已有基础
- 网页在线客服（WebSocket）— 适用于独立站

**v2.0 扩展：**
- 淘宝千牛工作台
- 抖店飞鸽客服
- 拼多多商家客服
- 京东咚咚

**统一收件箱：** 所有渠道消息汇聚到一个界面，按店铺/平台/紧急程度分类

#### F6.2 AI 自动回复
- 基于商品知识库 + 订单信息 + 店铺政策自动生成回复
- 自动检测买家语言（方言/非标准表达也能理解）
- 回复策略：
  - 高置信度(>0.9)：自动发送
  - 中置信度(0.7-0.9)：推荐回复，人工确认后发送
  - 低置信度(<0.7)：转人工
- 常见场景：查物流/退换货/尺码咨询/优惠咨询/投诉处理
- **AI 模型：** Claude Haiku（速度快、成本低、适合高频客服场景）

#### F6.3 知识库
- 店铺级知识库（退换货政策、发货时效、常见问题）
- 商品级知识库（从 Listing 自动提取 + 手动补充）
- FAQ 管理：常见问题一问一答
- 向量化存储：pgvector 支持语义搜索

#### F6.4 工单系统
- AI 无法处理的问题自动创建工单
- 优先级：紧急（投诉/差评/退款纠纷）> 高 > 中 > 低
- 工单分配（按技能/平台/语言分配给团队成员）
- SLA 追踪
- 与运营管家 M5 的评论管理联动

### 2.6.2 客服大脑数据模型

```sql
-- 客服会话
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id), -- 店铺所有者
    store_id UUID REFERENCES stores(id),
    channel VARCHAR(20) NOT NULL, -- 'email','telegram','webchat','taobao','douyin','pinduoduo'
    customer_id VARCHAR(255), -- 客户标识
    customer_name VARCHAR(255),
    related_order_id VARCHAR(255),
    related_product_id UUID REFERENCES products(id),
    status VARCHAR(20) DEFAULT 'open', -- 'open','ai_handling','human_handling','resolved','closed'
    priority VARCHAR(10) DEFAULT 'medium', -- 'urgent','high','medium','low'
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    ai_handled BOOLEAN DEFAULT false,
    assigned_to UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- 消息
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL, -- 'customer','ai','human_agent'
    content TEXT NOT NULL,
    ai_confidence DECIMAL(3,2), -- AI回复的置信度
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- 知识库
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id),
    product_id UUID REFERENCES products(id), -- null=店铺级
    title VARCHAR(255),
    content TEXT NOT NULL,
    content_type VARCHAR(20), -- 'faq','policy','product_info','custom'
    embedding VECTOR(1536), -- pgvector 向量
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 工单
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255),
    description TEXT,
    priority VARCHAR(10) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open', -- 'open','in_progress','waiting','resolved','closed'
    assigned_to UUID REFERENCES users(id),
    sla_deadline TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## M7 — 数据驾驶舱（Data Cockpit）★★☆☆☆

> **模块定位：** 全局数据看板 + AI 智能洞察。汇聚所有模块数据，提供经营决策支持。

### 2.7.1 子功能清单

#### F7.1 经营看板
**核心指标卡片：**
- 总销售额 / 总利润 / 订单量 / 客单价
- 退货率 / 广告 ROI / 转化率
- 内容产出量（本周生成了多少素材/视频/笔记）
- 选品通过率（推荐的品有多少进入了测试/上架）

**维度切换：** 按店铺/平台/商品/时间

**时间范围：** 今日 / 7天 / 30天 / 自定义

#### F7.2 AI 经营日报/周报
**每日自动生成：**
- 昨日关键指标变化（同比/环比）
- 异常告警（销量骤降/差评激增/广告 ROI 异常/库存告急）
- AI 归因分析（"销量下降可能因为竞品降价 15%"）
- 今日行动建议（优先处理的 3 件事）

**每周自动生成：**
- 本周经营总结
- 各模块使用情况统计
- 市场趋势变化
- 下周重点事项

**推送渠道：** 站内通知 + Telegram + 钉钉 + Email（可配置）

**AI 模型：** Claude Sonnet（深度分析）

#### F7.3 归因分析
- 销量变化归因：价格变动/评分变化/广告投放/竞品动作/季节性/大促
- 各渠道贡献分析：自然流量 vs 付费流量 vs 内容引流
- AI 自动识别最可能的原因

#### F7.4 趋势预测
- 基于历史数据预测未来 7/30 天销量
- 考虑：季节性 + 促销日历 + 广告计划 + 库存水平
- 输出结果用于库存管理和预算规划

### 2.7.2 数据驾驶舱数据模型

```sql
-- 每日经营指标
CREATE TABLE daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    store_id UUID REFERENCES stores(id),
    product_id UUID REFERENCES products(id), -- null=店铺汇总
    platform VARCHAR(20),
    date DATE NOT NULL,
    revenue DECIMAL(12,2) DEFAULT 0,
    profit DECIMAL(12,2) DEFAULT 0,
    orders INTEGER DEFAULT 0,
    units_sold INTEGER DEFAULT 0,
    refunds INTEGER DEFAULT 0,
    refund_amount DECIMAL(12,2) DEFAULT 0,
    ad_spend DECIMAL(12,2) DEFAULT 0,
    ad_revenue DECIMAL(12,2) DEFAULT 0,
    organic_revenue DECIMAL(12,2) DEFAULT 0,
    page_views INTEGER DEFAULT 0,
    conversion_rate DECIMAL(8,6),
    avg_order_value DECIMAL(10,2),
    new_reviews INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2),
    data_source VARCHAR(20) DEFAULT 'manual', -- 'manual','api','calculated'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, product_id, platform, date)
);

-- AI 生成的报告
CREATE TABLE ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    report_type VARCHAR(20) NOT NULL, -- 'daily','weekly','monthly','alert','custom'
    title VARCHAR(255),
    content_markdown TEXT, -- 报告正文（Markdown格式）
    key_metrics JSONB, -- 关键指标数据
    anomalies JSONB, -- 异常项
    recommendations JSONB, -- 建议项
    period_start DATE,
    period_end DATE,
    push_channels VARCHAR(50)[], -- 已推送的渠道
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 预测数据
CREATE TABLE forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id),
    platform VARCHAR(20),
    forecast_date DATE,
    predicted_units INTEGER,
    predicted_revenue DECIMAL(12,2),
    confidence_lower INTEGER,
    confidence_upper INTEGER,
    factors JSONB, -- 影响因子
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## P0 — 基础平台（Platform）

### 2.8.1 用户系统

**注册方式：**
- 手机号 + 短信验证码（阿里云 SMS）
- 邮箱 + 密码
- 微信登录（v1.1）
- 邀请码制（内测阶段）

**用户角色：**
- `superadmin` — 平台超级管理员
- `owner` — 团队所有者（拥有全部权限）
- `admin` — 团队管理员（管理成员和设置）
- `editor` — 编辑（创建和编辑内容、操作日常功能）
- `viewer` — 只读成员（查看数据和报告）

### 2.8.2 店铺管理

每个用户可管理多个店铺，每个店铺关联一个平台和市场。

**店铺经营 DNA（类似 MediaMatrix 的风格基因）：**
- 经营风格：低价走量型 / 中端性价比 / 高端品牌溢价
- 选品偏好：趋势跟款 / 利基深耕 / 新奇特 / 刚需日用
- 广告策略：激进投放 / 稳健 ROI / 自然流量优先
- 内容风格：专业测评 / 轻松种草 / 性价比导向 / 品牌质感
- 客服风格：热情亲切 / 简洁高效 / 专业正式

系统根据经营 DNA 自动调整各模块的 AI 输出风格。

### 2.8.3 积分计费系统（运营力）

**概念：** "运营力"是平台的虚拟资源单位，每次 AI 操作消耗对应运营力。

**获取方式：**
- 注册赠送：3,000 运营力
- 每日签到：+100 运营力
- 种子期每日发放：2,000 运营力（限时）
- 购买充值：¥1 = 100 运营力（基础价）
- 邀请好友注册：双方各 +500

**消耗定价：**

| 操作 | 运营力 | 预估真实成本 | 加价倍率 |
|------|--------|------------|---------|
| **M1 选品雷达** | | | |
| 市场洞察分析 | 25 | ~¥0.20 | 12.5x |
| 竞品数据刷新（单个） | 5 | ~¥0.02 | 25x |
| 选品推荐报告 | 35 | ~¥0.30 | 12x |
| 利润计算 | 免费 | ¥0 | — |
| 趋势周报 | 15 | ~¥0.10 | 15x |
| **M2 内容工厂** | | | |
| 短视频脚本 | 30 | ~¥0.20 | 15x |
| 种草笔记 | 20 | ~¥0.12 | 17x |
| 商品主图（每张） | 30 | ~¥0.20 | 15x |
| 详情页（整套） | 80 | ~¥0.60 | 13x |
| 直播话术（完整版） | 40 | ~¥0.30 | 13x |
| 广告素材（每组） | 20 | ~¥0.12 | 17x |
| **M3 上架中心** | | | |
| Listing 优化 | 25 | ~¥0.15 | 17x |
| 关键词挖掘 | 15 | ~¥0.05 | 30x |
| 违规检测 | 10 | ~¥0.03 | 33x |
| 格式导出 | 免费 | ¥0 | — |
| **M4 广告助手** | | | |
| 投放方案生成 | 30 | ~¥0.20 | 15x |
| AI 优化建议 | 15 | ~¥0.08 | 19x |
| **M5 运营管家** | | | |
| 定价建议 | 10 | ~¥0.05 | 20x |
| 促销方案生成 | 25 | ~¥0.15 | 17x |
| 评论 AI 回复（每条） | 5 | ~¥0.02 | 25x |
| **M6 客服大脑** | | | |
| AI 自动回复（每条） | 2 | ~¥0.01 | 20x |
| **M7 数据驾驶舱** | | | |
| AI 日报 | 10 | ~¥0.10 | 10x |
| AI 周报 | 20 | ~¥0.20 | 10x |
| 归因分析 | 15 | ~¥0.10 | 15x |

**消耗优先级：** 奖励池(30天过期) → 月额度池(月末重置) → 购买池(2年有效)

**会员等级：**

| 等级 | 累计消费 | 折扣 | 额外权益 |
|------|---------|------|---------|
| 新手 | ¥0 | 无 | 基础功能 |
| 银牌 | ¥500 | 9折 | 竞品监控 10 个 |
| 金牌 | ¥2,000 | 8折 | 竞品监控 50 个 + 团队协作(5人) |
| 钻石 | ¥5,000 | 7折 | 无限竞品 + 团队(20人) + API + 优先支持 |

### 2.8.4 基础平台数据模型

```sql
-- 用户
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    display_name VARCHAR(100),
    avatar_url VARCHAR(1024),
    invite_code VARCHAR(20) UNIQUE, -- 我的邀请码
    invited_by UUID REFERENCES users(id), -- 谁邀请我的
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- 店铺
CREATE TABLE stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    store_name VARCHAR(255) NOT NULL,
    platform VARCHAR(20) NOT NULL, -- 'taobao','tmall','douyin','pinduoduo','jd','xiaohongshu','kuaishou'
    store_url VARCHAR(1024),
    store_id_external VARCHAR(255), -- 平台店铺ID
    business_type VARCHAR(30), -- 'self_supply','1688','dropship','brand_agent','factory'
    category_focus VARCHAR(255)[], -- 主营品类
    store_dna JSONB, -- 店铺经营DNA
    api_credentials JSONB, -- 平台API凭证（加密存储）
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 团队
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 团队成员
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    role VARCHAR(20) NOT NULL DEFAULT 'editor', -- 'owner','admin','editor','viewer'
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team_id, user_id)
);

-- 积分账户
CREATE TABLE credit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
    balance_total INTEGER DEFAULT 0,
    balance_bonus INTEGER DEFAULT 0, -- 奖励池（30天过期）
    balance_monthly INTEGER DEFAULT 0, -- 月额度池
    balance_purchased INTEGER DEFAULT 0, -- 购买池（2年有效）
    total_consumed INTEGER DEFAULT 0,
    total_purchased_amount DECIMAL(10,2) DEFAULT 0, -- 累计充值金额
    member_level VARCHAR(10) DEFAULT 'starter', -- 'starter','silver','gold','diamond'
    discount_rate DECIMAL(3,2) DEFAULT 1.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 积分交易记录
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(20) NOT NULL, -- 'bonus','monthly','purchase','consume','refund','signin','invite'
    amount INTEGER NOT NULL, -- 正=获得，负=消耗
    pool VARCHAR(20), -- 'bonus','monthly','purchased'
    operation VARCHAR(50), -- 'market_scan','image_gen','listing_optimize' etc.
    related_id UUID, -- 关联的项目/任务ID
    balance_after INTEGER,
    description VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_credits_user_time ON credit_transactions(user_id, created_at DESC);

-- 充值订单
CREATE TABLE payment_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    order_no VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    credits INTEGER NOT NULL,
    payment_method VARCHAR(20), -- 'wechat','alipay'
    payment_status VARCHAR(20) DEFAULT 'pending', -- 'pending','paid','refunded','failed'
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 通知
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(30) NOT NULL, -- 'alert','report','system','promo'
    title VARCHAR(255),
    content TEXT,
    source_module VARCHAR(20), -- 'M1','M2',...'P0'
    related_id UUID, -- 关联实体ID
    is_read BOOLEAN DEFAULT false,
    push_channels VARCHAR(50)[], -- 已推送渠道
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
```

---

# ═══════════════════════════════════════════
# 第三部分：技术架构
# ═══════════════════════════════════════════

## 3.1 系统架构总览

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Web SPA)                       │
│              Next.js 14 + React 18 + TypeScript           │
│              Tailwind CSS + Shadcn UI (暗色主题)            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS / WebSocket / SSE
┌────────────────────────▼────────────────────────────────┐
│                     API 网关层                             │
│                FastAPI (Python 3.11+)                     │
│          JWT 认证 / 速率限制 / 请求日志 / CORS              │
└──┬────────┬────────┬────────┬────────┬────────────────┘
   │        │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──────────────┐
│ M1  │ │ M2  │ │M3-M5│ │ M6  │ │ M7 + P0         │
│选品  │ │内容  │ │上架/ │ │客服  │ │数据/用户/计费     │
│雷达  │ │工厂  │ │广告/ │ │大脑  │ │                  │
│     │ │     │ │运营  │ │     │ │                  │
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──────────────┘
   │       │       │       │       │
┌──▼───────▼───────▼───────▼───────▼──────────────────┐
│                    数据层                               │
│   PostgreSQL 16 (主库) + pgvector (向量搜索)             │
│   Redis 7 (缓存 / 会话 / Celery Broker)                 │
│   阿里云 OSS (文件存储)                                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  异步任务层                              │
│             Celery Worker + Celery Beat                │
│   队列: default / fast / generation / heavy / scraper  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 外部服务层                               │
│                                                       │
│  ┌─AI文本──────┐ ┌─AI图片/视频──┐ ┌─AI语音────────┐   │
│  │Claude API   │ │可灵AI        │ │火山引擎TTS    │   │
│  │(Sonnet/Haiku│ │(kling-image  │ │火山引擎ASR    │   │
│  │DeepSeek API │ │ kling-v3)    │ │               │   │
│  └─────────────┘ └──────────────┘ └───────────────┘   │
│                                                       │
│  ┌─数据采集─────┐ ┌─通知─────────┐ ┌─支付──────────┐   │
│  │爬虫/API     │ │Telegram Bot  │ │微信支付       │   │
│  │(预留接口)   │ │钉钉 Webhook  │ │支付宝        │    │
│  │             │ │Email SMTP    │ │              │    │
│  └─────────────┘ └──────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 3.2 技术栈选型

| 层级 | 技术 | 选型原因 |
|------|------|---------|
| **前端框架** | Next.js 14 + React 18 + TypeScript | SSR/SSG + 路由 + 生态丰富 |
| **UI 组件** | Tailwind CSS + Shadcn UI | 快速开发，暗色主题一键切换，组件质量高 |
| **状态管理** | Zustand | 轻量、简单、TypeScript 友好 |
| **图表** | Recharts | React 原生图表库 |
| **后端框架** | FastAPI (Python 3.11) | 异步、高性能、自动 OpenAPI 文档、类型安全 |
| **ORM** | SQLAlchemy 2.0 + Alembic | 成熟稳定、异步支持、数据库迁移 |
| **数据库** | PostgreSQL 16 + pgvector | 关系数据 + 向量搜索（客服知识库） |
| **缓存/Broker** | Redis 7 | 会话管理、API 限流、Celery 消息队列 |
| **任务队列** | Celery 5 + Redis | 异步任务、定时任务（Beat） |
| **文件存储** | 阿里云 OSS | 图片/视频/文档/导出文件存储 |
| **AI 文本** | Claude API (Sonnet + Haiku) | 高质量文案/分析/推理 |
| **AI 文本(低成本)** | DeepSeek API | 批量关键词、简单分析等低成本任务 |
| **AI 图片** | 可灵 AI (kling-image-o1) | 电商图片生成 |
| **AI 视频** | 可灵 AI (kling-v3) | 短视频生成（v1.1） |
| **AI 语音** | 火山引擎 TTS | 视频配音（v1.1） |
| **通知** | Telegram Bot + 钉钉 Webhook + Email | 告警推送 |
| **部署** | 阿里云新加坡 ECS + systemd | 已有基础设施 |

## 3.3 Celery 队列设计

| 队列名 | 职责 | Worker 并发 | 任务超时 |
|--------|------|------------|---------|
| `default` | 定时任务、轻量操作（签到、通知） | 4 | 60s |
| `fast` | 快速 AI 调用（客服回复、违规检测、关键词分析） | 8 | 30s |
| `generation` | 图片/视频生成、长文案生成（IO 密集） | 4 | 600s |
| `heavy` | 大报告生成、FFmpeg 合成、批量导出（CPU 密集） | 2 | 1800s |
| `scraper` | 数据采集、竞品监控刷新（v1.1） | 6 | 120s |

## 3.4 API 路由设计

```
# ═══ 认证 ═══
POST   /api/auth/register              # 注册
POST   /api/auth/login                 # 登录
POST   /api/auth/refresh               # 刷新 token
GET    /api/auth/me                    # 当前用户信息
POST   /api/auth/send-code             # 发送验证码

# ═══ 店铺管理 ═══
GET    /api/stores                     # 店铺列表
POST   /api/stores                     # 创建店铺
GET    /api/stores/{id}                # 店铺详情
PUT    /api/stores/{id}                # 更新店铺
DELETE /api/stores/{id}                # 删除店铺

# ═══ M1 选品雷达 ═══
POST   /api/scout/scan                 # 发起市场洞察
GET    /api/scout/scans                # 扫描历史列表
GET    /api/scout/scans/{id}           # 扫描详情
POST   /api/scout/competitors          # 添加竞品追踪
GET    /api/scout/competitors          # 竞品列表
PUT    /api/scout/competitors/{id}     # 更新竞品追踪
DELETE /api/scout/competitors/{id}     # 删除竞品
POST   /api/scout/competitors/{id}/refresh  # 手动刷新竞品数据
GET    /api/scout/competitors/{id}/history  # 竞品历史数据
GET    /api/scout/recommendations      # 选品推荐列表
PUT    /api/scout/recommendations/{id} # 更新推荐状态（接受/拒绝）
POST   /api/scout/profit-calc          # 利润计算
GET    /api/scout/trends               # 趋势雷达

# ═══ M2 内容工厂 ═══
POST   /api/content/projects           # 创建内容项目
GET    /api/content/projects           # 项目列表
GET    /api/content/projects/{id}      # 项目详情
PUT    /api/content/projects/{id}      # 更新项目（审核/修改配置）
POST   /api/content/projects/{id}/generate  # 触发 AI 生成
GET    /api/content/assets             # 素材库列表
GET    /api/content/assets/{id}        # 素材详情
PUT    /api/content/assets/{id}        # 更新素材（标签/收藏）
DELETE /api/content/assets/{id}        # 删除素材
POST   /api/content/assets/upload      # 上传素材

# ═══ M3 上架中心 ═══
GET    /api/products                   # 商品列表
POST   /api/products                   # 创建商品
GET    /api/products/{id}              # 商品详情
PUT    /api/products/{id}              # 更新商品
DELETE /api/products/{id}              # 删除商品
POST   /api/listings/optimize          # AI 优化 Listing
GET    /api/listings                   # Listing 列表
GET    /api/listings/{id}              # Listing 详情
PUT    /api/listings/{id}              # 更新 Listing
POST   /api/listings/export            # 导出为平台格式
POST   /api/keywords/discover          # 关键词挖掘
POST   /api/keywords/analyze           # 竞品关键词分析
GET    /api/keywords                   # 关键词库
POST   /api/listings/compliance        # 违规检测

# ═══ M4 广告助手 ═══
POST   /api/ads/campaigns              # 创建广告计划
GET    /api/ads/campaigns              # 广告列表
GET    /api/ads/campaigns/{id}         # 广告详情
PUT    /api/ads/campaigns/{id}         # 更新广告
POST   /api/ads/campaigns/{id}/plan    # AI 生成投放方案
POST   /api/ads/performance/upload     # 上传广告数据
GET    /api/ads/performance            # 广告效果数据
GET    /api/ads/suggestions            # AI 优化建议
PUT    /api/ads/suggestions/{id}       # 接受/拒绝建议
POST   /api/ads/ab-tests               # 创建 A/B 测试
GET    /api/ads/ab-tests/{id}          # A/B 测试详情

# ═══ M5 运营管家 ═══
GET    /api/ops/pricing/{product_id}   # 定价建议
PUT    /api/ops/pricing/{product_id}   # 设置定价规则
GET    /api/ops/inventory              # 库存总览
PUT    /api/ops/inventory/{product_id} # 更新库存
POST   /api/ops/promotions             # 创建促销
GET    /api/ops/promotions             # 促销列表
GET    /api/ops/reviews                # 评论列表
POST   /api/ops/reviews/{id}/reply     # AI 生成回复
POST   /api/ops/reviews/import         # 导入评论

# ═══ M6 客服大脑 ═══
GET    /api/cs/conversations           # 会话列表
GET    /api/cs/conversations/{id}      # 会话详情（含消息）
POST   /api/cs/conversations/{id}/reply  # 发送回复
PUT    /api/cs/conversations/{id}/assign  # 分配会话
PUT    /api/cs/conversations/{id}/status  # 更新状态
GET    /api/cs/tickets                 # 工单列表
POST   /api/cs/tickets                 # 创建工单
PUT    /api/cs/tickets/{id}            # 更新工单
GET    /api/cs/knowledge               # 知识库列表
POST   /api/cs/knowledge               # 添加知识条目
PUT    /api/cs/knowledge/{id}          # 更新知识条目
DELETE /api/cs/knowledge/{id}          # 删除知识条目

# ═══ M7 数据驾驶舱 ═══
GET    /api/analytics/dashboard        # 总览看板数据
GET    /api/analytics/metrics          # 指标查询
POST   /api/analytics/metrics/import   # 导入经营数据
GET    /api/analytics/reports          # AI 报告列表
GET    /api/analytics/reports/{id}     # 报告详情
POST   /api/analytics/reports/generate # 手动触发报告生成
GET    /api/analytics/forecast/{product_id}  # 销量预测
POST   /api/analytics/export           # 导出报表

# ═══ 积分/计费 ═══
GET    /api/billing/balance            # 余额查询
GET    /api/billing/transactions       # 交易记录
POST   /api/billing/recharge           # 发起充值
GET    /api/billing/recharge/{order_no}/status  # 查询支付状态
POST   /api/billing/signin             # 每日签到

# ═══ 团队 ═══
GET    /api/teams                      # 我的团队
POST   /api/teams                      # 创建团队
POST   /api/teams/{id}/invite          # 生成邀请链接
POST   /api/teams/{id}/join            # 加入团队
PUT    /api/teams/{id}/members/{user_id}  # 修改成员角色
DELETE /api/teams/{id}/members/{user_id}  # 移除成员

# ═══ 通知 ═══
GET    /api/notifications              # 通知列表
PUT    /api/notifications/{id}/read    # 标记已读
PUT    /api/notifications/read-all     # 全部已读
GET    /api/notifications/settings     # 通知设置
PUT    /api/notifications/settings     # 更新通知设置

# ═══ 实时推送 (SSE) ═══
GET    /api/stream/tasks/{task_id}     # 任务进度推送
GET    /api/stream/notifications       # 实时通知推送
```

## 3.5 项目目录结构

```
shangtanai/
├── frontend/                          # Next.js 前端
│   ├── src/
│   │   ├── app/                       # App Router
│   │   │   ├── (auth)/                # 登录/注册/邀请
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── (dashboard)/           # 需要登录的页面
│   │   │   │   ├── layout.tsx         # 侧边栏+顶栏布局
│   │   │   │   ├── page.tsx           # 工作台首页
│   │   │   │   ├── scout/             # M1 选品雷达
│   │   │   │   │   ├── page.tsx       # 选品首页
│   │   │   │   │   ├── scan/page.tsx  # 市场洞察
│   │   │   │   │   ├── competitors/page.tsx  # 竞品监控
│   │   │   │   │   ├── recommend/page.tsx    # 选品推荐
│   │   │   │   │   ├── profit/page.tsx       # 利润计算器
│   │   │   │   │   └── trends/page.tsx       # 趋势雷达
│   │   │   │   ├── content/           # M2 内容工厂
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   ├── new/page.tsx   # 新建内容项目
│   │   │   │   │   ├── [id]/page.tsx  # 项目详情/编辑
│   │   │   │   │   └── assets/page.tsx # 素材库
│   │   │   │   ├── listings/          # M3 上架中心
│   │   │   │   │   ├── page.tsx       # 商品列表
│   │   │   │   │   ├── new/page.tsx   # 新建商品
│   │   │   │   │   ├── [id]/page.tsx  # 商品详情/Listing优化
│   │   │   │   │   ├── keywords/page.tsx  # 关键词工具
│   │   │   │   │   └── export/page.tsx    # 多平台导出
│   │   │   │   ├── ads/              # M4 广告助手
│   │   │   │   ├── ops/              # M5 运营管家
│   │   │   │   ├── cs/               # M6 客服大脑
│   │   │   │   ├── analytics/        # M7 数据驾驶舱
│   │   │   │   ├── billing/          # 积分/计费
│   │   │   │   ├── settings/         # 设置
│   │   │   │   └── guide/            # 使用说明
│   │   │   └── layout.tsx             # 根布局
│   │   ├── components/
│   │   │   ├── ui/                    # Shadcn UI 组件
│   │   │   ├── layout/                # Sidebar, Topbar, Breadcrumb
│   │   │   ├── charts/                # Recharts 图表组件
│   │   │   └── shared/                # 通用业务组件
│   │   ├── lib/
│   │   │   ├── api.ts                 # Axios API 客户端
│   │   │   ├── auth.ts                # 认证逻辑
│   │   │   └── utils.ts               # 工具函数
│   │   ├── stores/                    # Zustand 状态
│   │   │   ├── auth-store.ts
│   │   │   ├── store-store.ts         # 店铺状态
│   │   │   └── notification-store.ts
│   │   └── types/                     # TypeScript 类型定义
│   │       └── index.ts
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.js
│
├── backend/                           # FastAPI 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI 入口 + 中间件
│   │   ├── config.py                  # Settings (pydantic-settings)
│   │   ├── database.py                # async SQLAlchemy engine + session
│   │   ├── dependencies.py            # 依赖注入 (get_db, get_current_user, check_credits)
│   │   │
│   │   ├── models/                    # SQLAlchemy ORM
│   │   │   ├── __init__.py            # Base + 统一导入
│   │   │   ├── user.py                # User, Team, TeamMember
│   │   │   ├── store.py               # Store
│   │   │   ├── product.py             # Product, Listing, Keyword, ForbiddenWord
│   │   │   ├── research.py            # MarketScan, CompetitorTrack, CompetitorSnapshot, ProductRecommendation, ProfitCalculation, TrendSignal
│   │   │   ├── content.py             # ContentProject, ContentAsset, CopywritingOutput
│   │   │   ├── ad.py                  # AdCampaign, AdPerformance, AdSuggestion, ABTest
│   │   │   ├── operation.py           # PricingRule, Inventory, Promotion, Review
│   │   │   ├── cs.py                  # Conversation, Message, KnowledgeBase, Ticket
│   │   │   ├── analytics.py           # DailyMetrics, AIReport, Forecast
│   │   │   └── billing.py             # CreditAccount, CreditTransaction, PaymentOrder, Notification
│   │   │
│   │   ├── schemas/                   # Pydantic 请求/响应 schema
│   │   │   ├── auth.py
│   │   │   ├── store.py
│   │   │   ├── research.py
│   │   │   ├── content.py
│   │   │   ├── listing.py
│   │   │   ├── ad.py
│   │   │   ├── operation.py
│   │   │   ├── cs.py
│   │   │   ├── analytics.py
│   │   │   └── billing.py
│   │   │
│   │   ├── routers/                   # API 路由
│   │   │   ├── auth.py
│   │   │   ├── stores.py
│   │   │   ├── scout.py               # M1
│   │   │   ├── content.py             # M2
│   │   │   ├── listings.py            # M3
│   │   │   ├── ads.py                 # M4
│   │   │   ├── ops.py                 # M5
│   │   │   ├── cs.py                  # M6
│   │   │   ├── analytics.py           # M7
│   │   │   ├── billing.py
│   │   │   ├── teams.py
│   │   │   └── notifications.py
│   │   │
│   │   ├── services/                  # 业务逻辑
│   │   │   ├── ai_engine.py           # AI 调用统一封装（模型路由、降级、限流）
│   │   │   ├── scout_service.py       # M1 业务逻辑
│   │   │   ├── content_service.py     # M2 业务逻辑
│   │   │   ├── listing_service.py     # M3 业务逻辑
│   │   │   ├── ad_service.py          # M4 业务逻辑
│   │   │   ├── ops_service.py         # M5 业务逻辑
│   │   │   ├── cs_service.py          # M6 业务逻辑
│   │   │   ├── analytics_service.py   # M7 业务逻辑
│   │   │   ├── billing_service.py     # 积分扣费逻辑
│   │   │   └── notification_service.py # 通知推送
│   │   │
│   │   ├── tasks/                     # Celery 异步任务
│   │   │   ├── celery_app.py          # Celery 实例 + 队列配置
│   │   │   ├── scout_tasks.py         # M1 异步任务
│   │   │   ├── content_tasks.py       # M2 异步任务
│   │   │   ├── scraper_tasks.py       # 数据采集任务
│   │   │   ├── report_tasks.py        # 报告生成任务
│   │   │   └── scheduled.py           # Beat 定时任务（竞品刷新、日报生成等）
│   │   │
│   │   ├── ai/                        # AI Provider 封装
│   │   │   ├── __init__.py
│   │   │   ├── claude_client.py       # Claude API 封装
│   │   │   ├── deepseek_client.py     # DeepSeek API 封装
│   │   │   ├── kling_client.py        # 可灵 AI 封装
│   │   │   ├── volcano_tts.py         # 火山引擎 TTS 封装
│   │   │   └── prompts/               # Prompt 模板
│   │   │       ├── scout_prompts.py   # M1 选品分析 Prompt
│   │   │       ├── content_prompts.py # M2 内容生成 Prompt
│   │   │       ├── listing_prompts.py # M3 Listing优化 Prompt
│   │   │       ├── ad_prompts.py      # M4 广告 Prompt
│   │   │       ├── ops_prompts.py     # M5 运营 Prompt
│   │   │       └── cs_prompts.py      # M6 客服 Prompt
│   │   │
│   │   ├── scrapers/                  # 数据采集器（v1.1 启用）
│   │   │   ├── __init__.py
│   │   │   ├── base_scraper.py        # 采集器基类
│   │   │   ├── douyin_scraper.py      # 抖音数据采集
│   │   │   ├── taobao_scraper.py      # 淘宝数据采集
│   │   │   └── trend_scraper.py       # 趋势数据采集
│   │   │
│   │   ├── platform_adapters/         # 平台适配层（v2.0 启用）
│   │   │   ├── __init__.py
│   │   │   ├── base_adapter.py        # 适配器基类
│   │   │   ├── douyin_adapter.py
│   │   │   ├── taobao_adapter.py
│   │   │   ├── pinduoduo_adapter.py
│   │   │   └── jd_adapter.py
│   │   │
│   │   ├── utils/
│   │   │   ├── security.py            # JWT 编解码、密码哈希
│   │   │   ├── rate_limiter.py        # Redis 令牌桶限流
│   │   │   ├── validators.py          # 通用校验
│   │   │   └── export.py              # CSV/Excel 导出工具
│   │   │
│   │   └── migrations/                # Alembic 迁移
│   │       ├── env.py
│   │       └── versions/
│   │
│   ├── requirements.txt
│   ├── alembic.ini
│   └── pytest.ini
│
├── docs/
│   ├── PRODUCT_SPEC.md                # 本产品手册
│   ├── API_REFERENCE.md               # API 文档（FastAPI 自动生成）
│   └── CHANGELOG.md                   # 版本变更日志
│
├── scripts/
│   ├── deploy.sh                      # 部署脚本
│   ├── backup_db.sh                   # 数据库备份
│   ├── init_db.py                     # 初始化数据库（创建表、插入禁词库等）
│   └── seed_data.py                   # 测试数据填充
│
├── CLAUDE.md                          # Claude Code 项目指令文件
├── docker-compose.yml                 # 本地开发环境（PostgreSQL + Redis）
├── .env.example                       # 环境变量模板
└── README.md
```

## 3.6 环境变量清单

```bash
# ═══ 基础配置 ═══
APP_NAME=ShangTanAI
APP_ENV=development                    # development / staging / production
APP_SECRET_KEY=your-secret-key-here    # JWT 签名密钥
APP_BASE_URL=https://shangtanai.com    # 生产环境域名
FRONTEND_URL=http://localhost:3000     # 前端地址（CORS）

# ═══ 数据库 ═══
DATABASE_URL=postgresql+asyncpg://shangtanai:password@localhost:5432/shangtanai
REDIS_URL=redis://localhost:6379/0

# ═══ AI 服务 ═══
ANTHROPIC_API_KEY=sk-ant-xxx           # Claude API
DEEPSEEK_API_KEY=sk-xxx                # DeepSeek API
KLING_ACCESS_KEY=xxx                   # 可灵 AI Access Key
KLING_SECRET_KEY=xxx                   # 可灵 AI Secret Key

# ═══ 火山引擎（v1.1 视频/配音功能启用时配置） ═══
# VOLCANO_TTS_API_KEY=xxx
# VOLCANO_TTS_APP_ID=xxx
# VOLCANO_ASR_API_KEY=xxx

# ═══ 文件存储 ═══
OSS_ACCESS_KEY=xxx                     # 阿里云 OSS
OSS_SECRET_KEY=xxx
OSS_BUCKET=shangtanai
OSS_ENDPOINT=oss-ap-southeast-1.aliyuncs.com
OSS_CDN_DOMAIN=cdn.shangtanai.com      # CDN 加速域名（可选）

# ═══ 通知服务 ═══
TELEGRAM_BOT_TOKEN=xxx                 # Telegram 通知机器人
TELEGRAM_ADMIN_CHAT_ID=xxx             # 管理员通知群
DINGTALK_WEBHOOK_URL=xxx               # 钉钉 Webhook
SMTP_HOST=smtp.qq.com                  # 邮件服务
SMTP_PORT=465
SMTP_USER=xxx@qq.com
SMTP_PASSWORD=xxx

# ═══ 短信（注册验证码） ═══
ALIYUN_SMS_ACCESS_KEY=xxx
ALIYUN_SMS_SECRET_KEY=xxx
ALIYUN_SMS_SIGN_NAME=商探AI
ALIYUN_SMS_TEMPLATE_CODE=SMS_xxx

# ═══ 支付（v1.1） ═══
# WECHAT_PAY_APP_ID=xxx
# WECHAT_PAY_MCH_ID=xxx
# WECHAT_PAY_API_KEY=xxx
# ALIPAY_APP_ID=xxx
# ALIPAY_PRIVATE_KEY=xxx

# ═══ 数据采集（v1.1 预留） ═══
# TIKHUB_API_KEY=xxx
# CHANMAMA_API_KEY=xxx                 # 蝉妈妈 API

# ═══ 平台 API（v2.0 预留） ═══
# DOUYIN_APP_KEY=xxx
# DOUYIN_APP_SECRET=xxx
# TAOBAO_APP_KEY=xxx
# TAOBAO_APP_SECRET=xxx
# PDD_CLIENT_ID=xxx
# PDD_CLIENT_SECRET=xxx
```

---

# ═══════════════════════════════════════════
# 第四部分：CLAUDE.md — Claude Code 项目配置
# ═══════════════════════════════════════════

将以下内容保存为项目根目录的 `CLAUDE.md`：

```markdown
# 商探AI (ShangTan AI) — Claude Code 项目配置

## 项目概述
商探AI 是国内电商 AI 全链路运营工具。完整产品规格见 docs/PRODUCT_SPEC.md。

## 技术栈
- 前端: Next.js 14 + React 18 + TypeScript + Tailwind CSS + Shadcn UI
- 后端: FastAPI (Python 3.11) + SQLAlchemy 2.0 + Alembic
- 数据库: PostgreSQL 16 + pgvector + Redis 7
- 任务队列: Celery 5 + Redis
- AI: Claude API (Sonnet/Haiku) + DeepSeek + 可灵AI

## 核心架构原则
- 7 个业务模块(M1-M7) + 1 个基础平台(P0)，模块间通过数据库解耦
- 所有 AI 调用通过 ai_engine.py 统一封装，支持模型路由和降级
- 所有 AI 操作消耗"运营力"积分，通过 billing_service.py 统一扣费
- 平台特定逻辑通过 platform_adapters/ 适配层隔离，核心逻辑平台无关
- 耗时操作走 Celery 异步任务，SSE 推送进度

## 代码规范
- Python: type hints, PEP 8, async/await 优先, docstring 用中文
- TypeScript: strict mode, Zod 运行时校验
- API 响应统一格式: {"success": bool, "data": any, "message": str, "error": str|null}
- 数据库 ID: UUID
- 时间: UTC (TIMESTAMPTZ)
- 文件命名: snake_case (Python), kebab-case (前端文件)
- 组件命名: PascalCase (React 组件)

## 运行命令
- 后端: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
- 前端: cd frontend && npm run dev -- -p 3000
- Celery Worker: cd backend && celery -A app.tasks.celery_app worker -Q default,fast,generation,heavy,scraper -l info
- Celery Beat: cd backend && celery -A app.tasks.celery_app beat -l info
- 数据库迁移: cd backend && alembic upgrade head
- 创建迁移: cd backend && alembic revision --autogenerate -m "description"
- 初始化数据: cd backend && python scripts/init_db.py

## 部署
- 服务器: 阿里云新加坡 ECS（已有）
- 后端: systemd (shangtanai-api.service)
- Celery: systemd (shangtanai-worker.service, shangtanai-beat.service)
- 前端: PM2 或 nginx 静态部署
- 数据库备份: 每日 pg_dump → 阿里云 OSS

## 重要提醒
- 每次 AI 调用前必须检查用户运营力余额 (dependencies.py 的 check_credits)
- AI 调用失败时要退还已扣运营力
- 所有用户输入必须做 XSS/SQL 注入防护
- 平台 API 凭证必须加密存储（stores.api_credentials 字段）
- 文件上传限制: 图片 10MB, 视频 100MB
```

---

# ═══════════════════════════════════════════
# 第五部分：开发路线图
# ═══════════════════════════════════════════

## 一个月冲刺计划

### Week 1 (Day 1-7)：基础框架 + 用户系统 + 工作台

**后端：**
- [ ] 初始化 FastAPI 项目结构
- [ ] 配置 SQLAlchemy + Alembic + PostgreSQL
- [ ] 创建全部数据模型（30+ 张表）并执行迁移
- [ ] 实现用户注册/登录（手机号+邮箱，JWT）
- [ ] 实现店铺 CRUD
- [ ] 实现积分系统基础（CreditAccount, CreditTransaction, 扣费/充值/签到）
- [ ] 统一 API 响应格式 + 错误处理中间件
- [ ] Redis 连接 + 基本缓存
- [ ] AI Engine 统一封装（claude_client.py + deepseek_client.py）

**前端：**
- [ ] 初始化 Next.js + Tailwind + Shadcn UI
- [ ] 实现登录/注册页面
- [ ] 实现主布局（暗色侧边栏 + 顶栏 + 面包屑）
- [ ] 实现工作台首页（引导流程卡片 + 模块快捷入口）
- [ ] API 客户端封装（Axios + 拦截器 + Token 刷新）
- [ ] 路由守卫（未登录跳转登录页）

### Week 2 (Day 8-14)：M1 选品雷达（核心模块）

**后端：**
- [ ] 市场洞察接口（POST /api/scout/scan → Claude Sonnet 分析 → 存储结果）
- [ ] 竞品追踪 CRUD（添加/列表/删除/手动刷新）
- [ ] 竞品快照存储 + 历史查询接口
- [ ] 选品推荐引擎（AI 评分 + 五维雷达数据）
- [ ] 利润计算器接口（纯计算，不消耗积分）
- [ ] 趋势信号接口（初期：AI 基于用户输入分析；后期：自动采集）
- [ ] Celery 任务：AI 分析异步执行 + SSE 进度推送

**前端：**
- [ ] 选品雷达首页（模块导航）
- [ ] 市场洞察页面（搜索框 + AI 分析结果展示 + 雷达图）
- [ ] 竞品监控页面（竞品卡片列表 + 添加弹窗 + 历史趋势图）
- [ ] 选品推荐页面（推荐列表 + 详情弹窗 + 接受/拒绝操作）
- [ ] 利润计算器页面（表单输入 + 实时计算 + 结果表格）
- [ ] 趋势雷达页面（趋势列表 + 热度排行）

### Week 3 (Day 15-21)：M2 内容工厂 + M3 上架中心

**后端：**
- [ ] M2：内容项目 CRUD
- [ ] M2：AI 生成接口（短视频脚本 / 种草笔记 / 直播话术 / 广告文案）
- [ ] M2：素材库接口（上传到 OSS + 列表/搜索/标签）
- [ ] M3：商品 CRUD
- [ ] M3：Listing 优化接口（Claude Sonnet 优化标题/描述/关键词）
- [ ] M3：关键词挖掘接口
- [ ] M3：违规检测接口（禁词库 + AI 语义判断）
- [ ] M3：多平台格式导出（CSV/Excel 生成）
- [ ] 初始化禁词库数据（init_db.py 中插入常见广告法违禁词）

**前端：**
- [ ] M2：内容工厂首页（选择内容类型）
- [ ] M2：内容创建流程页面（填写商品信息 → 选择类型和风格 → AI 生成 → 预览编辑）
- [ ] M2：素材库页面（网格展示 + 筛选 + 搜索）
- [ ] M3：商品管理列表页
- [ ] M3：商品详情/编辑页（基础信息 + Listing 优化 + 导出按钮）
- [ ] M3：关键词工具页面
- [ ] M3：违规检测结果展示

### Week 4 (Day 22-30)：M4-M7 + 全局打磨

**后端：**
- [ ] M4：广告计划 CRUD + AI 生成投放方案
- [ ] M4：广告数据手动上传 + 解析
- [ ] M5：定价建议接口 + 评论导入/AI回复
- [ ] M6：客服基础（会话/消息/知识库 CRUD + AI 自动回复）
- [ ] M7：经营看板接口（手动录入数据 + 汇总统计）
- [ ] M7：AI 日报生成（Celery Beat 每日触发）
- [ ] 通知系统（站内 + Telegram + 钉钉推送）
- [ ] 使用说明文档内容

**前端：**
- [ ] M4：广告助手基础页面
- [ ] M5：运营管家基础页面（定价/评论）
- [ ] M6：客服界面（统一收件箱 + 对话窗口）
- [ ] M7：数据驾驶舱（看板卡片 + 趋势图表 + 报告列表）
- [ ] 积分/计费页面（余额 + 交易记录 + 充值 + 签到 + 会员等级）
- [ ] 使用说明页面（参考 MediaMatrix 的多 tab 文档页）
- [ ] 全局 UI 打磨 + 响应式适配
- [ ] 全流程自测

### Phase 2 (第二个月+)：
- [ ] 数据采集系统（爬虫 / 第三方 API 对接）
- [ ] 短视频生成 Pipeline（可灵 AI 视频 + 火山引擎 TTS + FFmpeg 合成）
- [ ] 商品图片 AI 生成/编辑
- [ ] 平台 API 对接（抖店 → 淘宝 → 拼多多）
- [ ] 广告平台 API 对接
- [ ] 微信/支付宝支付
- [ ] 微信登录
- [ ] "自我进化"机制（店铺经营 DNA 学习）
- [ ] 移动端适配 / 小程序

---

# 附录

## A. 外部服务申请清单

| 服务 | 地址 | 预估审批时间 | 优先级 | v1.0 是否必需 |
|------|------|------------|--------|-------------|
| Claude API | console.anthropic.com | 即时 | P0 | ✅ 必需 |
| DeepSeek API | platform.deepseek.com | 即时 | P0 | ✅ 必需 |
| 可灵 AI API | klingai.com | 1-3 天 | P1 | ❌ 图片功能时需要 |
| 阿里云 OSS | aliyun.com | 已有 | P0 | ✅ 必需 |
| 阿里云 SMS | aliyun.com | 已有 | P1 | ⚠️ 手机注册时需要 |
| 域名 | 域名注册商 | 即时 | P1 | ⚠️ 上线时需要 |

## B. 国内电商竞品工具对照

| 竞品 | 覆盖环节 | 商探AI 的差异化 |
|------|---------|---------------|
| 1688 遨虾 | 选品+找厂+上架 | 遨虾绑定1688生态，商探AI平台无关且覆盖全链路 |
| 卖家精灵 | 亚马逊选品+关键词 | 卖家精灵只做亚马逊，商探AI面向国内全平台 |
| 蝉妈妈/飞瓜 | 抖音数据分析 | 纯数据工具不做内容生成和运营，商探AI是AI驱动的一体化工具 |
| 店小秘/马帮 | 多平台ERP | 传统ERP没有AI能力，商探AI以AI为核心 |
| 千牛/抖店后台 | 单平台运营 | 平台自己的工具只管自己，商探AI跨平台统一管理 |
| MediaMatrix | 自媒体内容创作 | MediaMatrix做自媒体内容，商探AI做电商全链路 |

## C. 风险和挑战

| 风险 | 应对策略 |
|------|---------|
| 平台反爬/API 权限难获取 | v1.0 不依赖采集，用户手动输入；后续走正规 ISV/开发者申请 |
| AI 生成内容质量不稳定 | Prompt 工程持续优化 + 人工审核机制 + 用户反馈闭环 |
| 国内电商变化快 | 架构设计平台无关，新平台通过适配层快速接入 |
| 竞品跟进快 | 先发优势 + 全链路一体化壁垒 + 数据积累飞轮 |
| 合规风险 | 不存储用户平台密码，API 凭证加密，数据隐私合规 |

---

**文档结束**

*商探AI v1.0 产品手册 — 最后更新：2026-03-17*
*本文档同时作为 Claude Code 项目知识库使用*
