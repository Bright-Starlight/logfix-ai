# Implementation Plan: 错误日志修复计划状态

**Branch**: `007-error-log-analysis-status` | **Date**: 2026-04-14 | **Spec**: [spec.md](./spec.md)

> 所有正文内容必须使用中文编写；如与宪法冲突，以 `.specify/memory/constitution.md` 为准。

## Summary

为错误日志添加AI修复计划分析功能，包括状态UI（未分析/分析中/分析完成/分析失败）、生成修复计划按钮、AI Agent排队分析（最大5个任务）、修复计划查看与重新分析。

**技术方案**：基于现有的SSE流式处理和AI分析服务扩展，新增FixPlan实体存储分析结果，前端在LogList组件添加状态标签和操作按钮，后端实现分析任务队列管理。

## Technical Context

**Language/Version**: Python 3.11 (后端) / TypeScript + React (前端)
**Primary Dependencies**: FastAPI, SQLAlchemy, SSE (后端)；React, TypeScript (前端)
**Storage**: PostgreSQL (现有数据库，新增分析状态和修复计划表)
**Testing**: pytest (后端), vitest (前端)
**Target Platform**: Windows/Linux 服务器
**Project Type**: Web服务（前后端分离）
**Constraints**: 队列最大5个任务（1执行中+4排队中），无超时限制
**Scale/Scope**: 单用户场景，队列仅管理当前用户任务

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] 规格已获批准，且用户故事具备独立测试条件。
- [x] 已明确采用 TDD，并列出先写失败测试的策略。
- [x] 交付切片按 MVP 优先排序，可独立部署或演示。
- [x] 已识别日志方案：日志框架、`/log` 目录、日志文件命名（`logfix-ai_YYYYMMDD.log`）、关键埋点位置（分析开始/完成/失败）。
- [x] 已确认实现和脚本兼容 Windows。
- [x] 已规划 `/speckit.tasks` 阶段输出 `specs/007-error-log-analysis-status/flow.md`（Mermaid，中文）。
- [x] 已规划 `/speckit.implement` 完成后的主应用集成验证步骤（代码阅读确认+测试运行）。

## Project Structure

### Documentation (this feature)

```text
specs/007-error-log-analysis-status/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── flow.md              # Phase 2 output (Mermaid 中文流程图)
├── contracts/           # Phase 1 output (API contracts)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── entities.py          # 新增 FixPlan, AnalysisSession 实体
│   │   └── __init__.py
│   ├── services/
│   │   ├── fix_plan_service.py   # 新增：修复计划服务
│   │   ├── analysis_queue.py    # 新增：分析任务队列
│   │   └── ai_analyzer.py       # 扩展：支持修复计划生成
│   ├── api/
│   │   └── routes.py            # 扩展：新增分析相关API端点
│   └── __init__.py
└── tests/
    ├── unit/
    │   ├── test_fix_plan_service.py
    │   ├── test_analysis_queue.py
    │   └── test_ai_analyzer_extended.py
    └── integration/
        └── test_analysis_api.py

frontend/
├── src/
│   ├── components/
│   │   ├── LogList.tsx          # 扩展：添加状态标签和按钮
│   │   ├── FixPlanViewer.tsx    # 新增：修复计划查看组件
│   │   └── AnalysisProgress.tsx # 新增：分析进度组件
│   ├── hooks/
│   │   ├── useAnalysisProgress.ts # 新增：分析进度监听hook
│   │   └── useAnalysisQueue.ts   # 新增：队列状态管理hook
│   ├── services/
│   │   └── api.ts               # 扩展：新增分析相关API调用
│   ├── types/
│   │   └── index.ts             # 扩展：新增类型定义
│   └── pages/
│       └── AnalysisPipeline.tsx  # 扩展：集成修复计划功能
└── tests/
    ├── unit/
    │   ├── test_LogList.tsx
    │   └── test_FixPlanViewer.tsx
    └── integration/
        └── test_analysis_flow.ts
```

**Structure Decision**: Web应用（前后端分离），沿用现有项目结构，在backend/src/services新增fix_plan_service.py和analysis_queue.py，在frontend/src/components新增FixPlanViewer.tsx和AnalysisProgress.tsx。

## Complexity Tracking

> 无复杂度违规，无需追踪。

## Phase 0: Research

### 需要研究的未知项

1. **AI Agent修复计划生成**：现有`ai_analyzer.py`仅支持日志分类，需要扩展支持修复计划生成（基于错误日志和代码仓库分析根因、修复建议）
2. **分析任务队列实现**：需要研究Python中适合排队任务的模式（ asyncio.Queue vs 独立队列服务）

### 研究任务

- 研究现有AI分析服务扩展方式
- 研究任务队列实现模式

## Phase 1: Design & Contracts

### 已完成文档

- [x] `research.md` - AI Agent扩展方案 + 任务队列实现
- [x] `data-model.md` - AnalysisSession, FixPlan实体设计
- [x] `quickstart.md` - 快速开始指南
- [x] `contracts/api-contracts.md` - API契约

### Constitution Check (Post-Design)

- [x] 所有Phase 0研究已确认
- [x] 数据模型符合数据库规范（表注释、字段注释、Long主键）
- [x] API契约完整（启动/状态/修复计划/取消/SSE）
- [x] 队列设计符合规格（最大5个，无超时）

## Phase 2: Tasks

待 `/speckit.tasks` 阶段生成：
- `flow.md`（Mermaid中文流程图）
- `tasks.md`（任务清单）
