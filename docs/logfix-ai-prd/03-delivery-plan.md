# LogFix AI 交付计划与实现建议

## 1. 建议交付顺序

### Phase 1: 跑通最小链路

目标是尽快完成一次端到端流程：

`上传日志 -> 解析 -> 聚合 -> 展示异常 -> 生成 AI 报告 -> 导出修复 Task`

建议先实现：

1. [WP-01 基础骨架、上传与解析](D:\code\test\docs\logfix-ai-prd\requirements\WP-01-bootstrap-upload-parse.md)
2. [WP-02 异常聚合与基础界面](D:\code\test\docs\logfix-ai-prd\requirements\WP-02-grouping-and-ui.md)

### Phase 2: 补齐代码上下文

在排障界面可用后，再增强 AI 分析质量。

建议实现：

1. [WP-03 本地仓库接入与代码检索](D:\code\test\docs\logfix-ai-prd\requirements\WP-03-repo-and-search.md)

### Phase 3: 强化 AI 输出可执行性

建议实现：

1. [WP-04 AI 分析与修复任务生成](D:\code\test\docs\logfix-ai-prd\requirements\WP-04-analysis-and-fix-task.md)
2. [WP-05 可用性增强](D:\code\test\docs\logfix-ai-prd\requirements\WP-05-usability-enhancements.md)

## 2. 建议的技术实现路径

## 后端

- FastAPI 负责 API 与任务编排
- SQLite 保存结构化数据
- 本地文件系统保存原始日志、仓库与导出文档

## 前端

MVP 建议优先选 `FastAPI + Jinja2 + HTMX`，原因如下：

- 依赖更少
- 更接近常规 Web 应用结构
- 上传、列表、详情、Markdown 展示成本低
- 后续扩展 API 和页面不会受限

如果后续需要更重的前端交互，再考虑升级页面层方案。

## AI 分析

- 优先接入 AI API
- 首版 Prompt 明确限制模型必须引用证据
- 分析输出使用固定标题，降低结果飘逸性
- API Key 通过环境变量注入

## 3. 建议目录结构

```text
logfix-ai/
  app/
    api/
    services/
    models/
    repositories/
    prompts/
    workers/
  data/
    uploads/
    exports/
    repos/
    db/
  docs/
    prd/
  tests/
  README.md
```

## 4. 建议数据库最小实体

### `uploads`

- 记录一次上传任务

### `log_entries`

- 记录每条解析后的日志

### `error_groups`

- 记录聚合后的异常组

### `error_group_items`

- 记录异常组与日志的关联

### `repositories`

- 记录接入的本地代码仓库

### `code_chunks`

- 记录切分后的代码块元数据

### `analysis_reports`

- 记录 AI 分析结果

### `fix_tasks`

- 记录生成的修复任务

## 5. AI Agent 投喂建议

如果你后续要把文档发给 coding agent，推荐按以下顺序投喂：

1. `01-prd.md`
2. `02-mvp-breakdown.md`
3. 当前代码仓库结构
4. 指定本轮只做一个 P0 任务

推荐 prompt：

```md
请根据 docs/logfix-ai-prd/02-mvp-breakdown.md，只实现 P0-2 和 P0-3：

- 保持依赖轻量
- 后端使用 FastAPI
- 数据落 SQLite
- 输出可运行代码、数据库迁移和最小测试
- 完成后说明如何本地启动与验证
```

## 6. 风险控制建议

- 不要一开始就做复杂 AST 解析，先用文件级检索
- 不要一开始就做高级日志语义聚类，先用规则聚合
- 不要让模型自由发挥，必须要求输出证据链和引用来源
- 不要过早优化 UI，美观应让位于信息清晰和链路可用

## 7. 下一步建议

文档完成后，最合理的下一步是：

1. 先补一版数据库 schema 草稿
2. 再补一版 API 设计
3. 然后生成初始项目脚手架

这样可以直接从“文档”进入“实现”。
