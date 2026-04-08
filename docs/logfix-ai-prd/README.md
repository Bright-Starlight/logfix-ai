# LogFix AI 文档目录

本目录用于沉淀 `LogFix AI` 的产品需求与开发拆解，面向个人开发者场景，强调本地运行、轻量部署和 AI 辅助排障闭环。
本目录用于沉淀 `LogFix AI` 的产品需求与开发拆解，当前方向强调轻量依赖、快速启动，以及优先接入 AI API 的分析链路。

## 文档清单

1. [01-prd.md](D:\code\test\docs\logfix-ai-prd\01-prd.md)
   - 产品需求文档正式稿
   - 包含目标、范围、功能、非功能、风险与依赖
2. [02-mvp-breakdown.md](D:\code\test\docs\logfix-ai-prd\02-mvp-breakdown.md)
   - 将 MVP 拆成可执行的小需求
   - 每项包含目标、输入输出、验收标准、优先级
3. [03-delivery-plan.md](D:\code\test\docs\logfix-ai-prd\03-delivery-plan.md)
   - 建议的迭代顺序、里程碑与实现建议
   - 便于直接转换为开发任务
4. [requirements/README.md](D:\code\test\docs\logfix-ai-prd\requirements\README.md)
   - 按“单次会话可完成的工作包”合并后的需求卡目录
   - 适合直接交给 AI coding agent 执行

## 推荐使用方式

- 如果你要继续细化产品，先看 `01-prd.md`
- 如果你要开始做开发排期，直接从 `02-mvp-breakdown.md` 开始
- 如果你要逐个派发需求，优先使用 `requirements/` 下的 `WP-*` 文件
- 如果你要让 AI coding agent 开工，优先投喂 `02-mvp-breakdown.md` 和 `03-delivery-plan.md`
