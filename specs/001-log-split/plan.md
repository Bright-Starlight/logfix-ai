# Implementation Plan: 日志文件切分

**Branch**: `001-log-split` | **Date**: 2026-04-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-log-split/spec.md`

> 所有正文内容必须使用中文编写；如与宪法冲突，以 `.specify/memory/constitution.md` 为准。

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

构建一个生产日志分析系统的Web应用，第一版核心功能是：用户上传日志文件后，按照正则表达式或固定分隔符规则对日志进行切分，并支持查看和复制切分结果。

**技术方案**：
- 前端：React + 分片上传
- 后端：Python（FastAPI）
- 数据库：PostgreSQL
- 特性：支持100MB以上大文件流式处理、切分状态追踪、断点续查

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, React, psycopg2-binary, chardet, python-multipart
**Storage**: PostgreSQL（本地单用户）
**Testing**: pytest（后端）, Vitest（前端）
**Target Platform**: Windows 环境
**Project Type**: Web 应用（前后端分离）
**Performance Goals**: 正则校验<200ms, 10000行切分<5秒, 支持100MB文件
**Constraints**: 单个片段<1MB, 分页每页最多1000个片段
**Scale/Scope**: 单用户本地使用

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] 规格已获批准，且用户故事具备独立测试条件。
- [x] 已明确采用 TDD，并列出先写失败测试的策略。
- [x] 交付切片按 MVP 优先排序，可独立部署或演示。
- [x] 已识别日志方案：Python logging框架、`/log` 目录、`logfix-ai_{日期}.log` 命名规范。
- [x] 已定义性能目标与验证方式。
- [x] 已确认实现和脚本兼容 Windows。
- [x] 已规划 `/speckit.tasks` 阶段输出 `specs/001-log-split/flow.md`（Mermaid，中文）。
- [x] 已规划 `/speckit.implement` 完成后的主应用集成验证步骤。

## Project Structure

### Documentation (this feature)

```text
specs/001-log-split/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── flow.md              # Phase 2 output (Mermaid 中文流程图)
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── models/
│   │   ├── __init__.py
│   │   └── entities.py      # SQLAlchemy 模型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_handler.py   # 文件上传与编码检测
│   │   ├── splitter.py       # 日志切分核心逻辑
│   │   └── log_service.py    # 结构化日志服务
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py         # API 路由
│   └── db/
│       ├── __init__.py
│       └── session.py        # 数据库会话
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt

frontend/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── FileUpload.tsx
│   │   ├── LogPreview.tsx
│   │   ├── SplitConfig.tsx
│   │   └── ResultList.tsx
│   ├── services/
│   │   └── api.ts
│   └── types/
│       └── index.ts
├── public/
├── package.json
└── vite.config.ts

/log/                         # 日志输出目录
└── logfix-ai_{date}.log
```

**Structure Decision**: Web应用采用前后端分离结构
- `backend/`: Python FastAPI 实现
- `frontend/`: React + Vite 实现
- `/log/`: Python结构化日志输出目录

## Phase 0: Research

### Research Tasks

| 任务 | 技术选择 | 研究目标 |
|------|----------|----------|
| 1 | Python FastAPI | Web框架最佳实践 |
| 2 | React + Vite | 前端项目结构 |
| 3 | PostgreSQL + SQLAlchemy | 数据库设计模式 |
| 4 | 分片上传 + 流式处理 | 大文件处理方案 |
| 5 | chardet / charset-normalizer | 文件编码检测 |

### 技术选型依据

**后端框架**：FastAPI
- 异步支持优秀，适合I/O密集型任务
- 自动OpenAPI文档
- 类型提示完整

**前端框架**：React + Vite
- 组件化开发
- 快速热更新
- 生态丰富

**数据库**：PostgreSQL + SQLAlchemy
- 支持JSON类型存储切分结果
- 成熟稳定

### 架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 大文件分片 | 前端分片 + 后端流式处理 | 避免内存溢出，支持100MB+ |
| 编码检测 | chardet / charset-normalizer | Python生态成熟方案 |
| 状态追踪 | PostgreSQL存储 | 支持刷新后断点续查 |
| 日志框架 | Python logging | 宪法要求使用logging模块 |

## Phase 1: Design & Contracts

（详见下方 data-model.md 和 contracts/ 目录）

## Complexity Tracking

> 本项目无宪法冲突，所有约束均已满足

| 项目 | 说明 |
|------|------|
| 无 | - |
