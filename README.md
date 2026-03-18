# 商探AI (ShangTan AI)

> AI 洞察商机，全链路掌控

国内电商 AI 全链路运营工具，覆盖选品、内容、上架、广告、运营、客服、数据七大模块。

## 技术栈
- 前端：Next.js 14 + TypeScript + Tailwind CSS + Shadcn UI
- 后端：FastAPI + Python 3.11 + SQLAlchemy
- AI：Claude API + DeepSeek
- 数据库：PostgreSQL 16 + Redis 7

## 版本记录

### 当前开发中
- [refactor] 选品模块数据来源从「AI 编造」改为「联盟 API 真实数据 + AI 分析」
- [feat] 新增平台适配层：淘宝联盟 / 多多进宝 / 抖音精选联盟（聚推客）/ 小红书开放平台
- [feat] 新增多平台数据聚合服务（并发搜索 + 统一格式 + 统计分析）
- [feat] 重写 market-insight API：真实数据聚合 → AI 分析，不再让 AI 编造数据
- [feat] 新增 /platforms/status 接口，查询各平台 API 配置状态
- [feat] 增强利润计算器：支持物流/包装/广告费/退货率/盈亏平衡/多售价对比
- [feat] 前端市场洞察页面展示多平台真实数据（数据源状态、Top 10 商品、小红书种草热度）
- [fix] 选品推荐页下拉框全部改为中文标签，补充京东/快手/3C数码/服饰选项

### v0.2.0（2026-03-18）— 前端框架完成
- 完成全部 7 大模块 + 基础平台的前端页面（18个页面）
- 后端骨架：FastAPI + AI Engine（Claude/DeepSeek 双引擎 + 自动降级）
- 已知问题：选品推荐下拉框显示英文、全部数据为 Mock

### v0.1.0（2026-03-17）— 项目初始化
- 生成 Product-Spec.md、UI-Prompts.md
- 部署废才技能包
