# Implementation Plan: 日志分类与结构化存储

**Branch**: `002-short-name-structured` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-short-name-structured/spec.md`

> 所有正文内容必须使用中文编写；如与宪法冲突，以 `.specify/memory/constitution.md` 为准。

## Summary

构建日志分类与结构化存储系统，核心功能：
1. 接收切分后的日志数据，进行分类并结构化存储到数据库
2. 支持规则引擎模式（用户可编辑规则）和 AI 模式（LangChain + MiniMax）两种去重方式
3. 支持忽略规则配置
4. 提供 Web 页面展示日志列表、搜索过滤和统计

**技术方案**：
- 后端：Python（FastAPI，复用 001-log-split 技术栈）
- 前端：React（复用 001-log-split 技术栈）
- 数据库：PostgreSQL（复用 001-log-split 技术栈）
- AI 集成：LangChain + Anthropic SDK → MiniMax-M2.7（`https://api.minimaxi.com/anthropic`）
- 日志框架：loguru

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy, psycopg2-binary, loguru, langchain, langchain-anthropic, python-dotenv
**Storage**: PostgreSQL（复用 001-log-split 数据库）
**Testing**: pytest（后端）, Vitest（前端）
**Target Platform**: Windows 环境
**Project Type**: Web 应用（前后端分离）
**Performance Goals**: 日志分类和存储<5秒, AI模式响应<10秒, 搜索过滤<2秒
**Constraints**: 规则引擎为默认模式, AI模式为可选补充, 日志量每天<10万条
**Scale/Scope**: 单用户本地使用

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] 规格已获批准，且用户故事具备独立测试条件。
- [x] 已明确采用 TDD，并列出先写失败测试的策略。
- [x] 交付切片按 MVP 优先排序，可独立部署或演示。
- [x] 已识别日志方案：loguru框架、`/log` 目录、`logfix-ai_{日期}.log` 命名规范。
- [x] 已定义性能目标与验证方式。
- [x] 已确认实现和脚本兼容 Windows。
- [x] 已规划 `/speckit.tasks` 阶段输出 `specs/002-short-name-structured/flow.md`（Mermaid，中文）。
- [x] 已规划 `/speckit.implement` 完成后的主应用集成验证步骤。

## Project Structure

### Documentation (this feature)

```text
specs/002-short-name-structured/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── flow.md              # Phase 2 output (Mermaid 中文流程图)
├── contracts/           # Phase 1 output
│   └── api.md
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
│   │   └── entities.py      # SQLAlchemy 模型（LogEntry, IgnoreRule, ParseRule, LogCategory）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── classifier.py     # 日志分类服务
│   │   ├── deduplicator.py  # 去重服务（规则引擎 + AI 模式）
│   │   ├── rule_engine.py   # 规则引擎（用户编辑的解析规则）
│   │   ├── ai_analyzer.py   # AI 分析服务（LangChain + MiniMax）
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
│   │   ├── LogList.tsx           # 日志列表展示
│   │   ├── LogDetail.tsx         # 日志详情
│   │   ├── RuleEditor.tsx        # 规则编辑器
│   │   ├── IgnoreRules.tsx       # 忽略规则配置
│   │   ├── StatsPanel.tsx       # 统计面板
│   │   └── SearchFilter.tsx      # 搜索过滤
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

**Structure Decision**: Web应用采用前后端分离结构，复用 001-log-split 的技术栈和项目结构

## Phase 0: Research

### Research Tasks

| 任务 | 技术选择 | 研究目标 |
|------|----------|----------|
| 1 | LangChain + Anthropic SDK | MiniMax Anthropic API 兼容接入方式 |
| 2 | 规则引擎设计 | 用户编辑规则的数据模型和执行机制 |
| 3 | AI Prompt 设计 | 日志分类和去重的 Prompt 模板 |
| 4 | 去重算法 | 规则引擎模式下的去重匹配算法 |

### 技术选型依据

**LangChain + Anthropic SDK**：
- MiniMax 提供 Anthropic API 兼容接口 (`https://api.minimaxi.com/anthropic`)
- 可直接使用 Anthropic SDK 调用 MiniMax-M2.7 模型
- LangChain 提供 Agent 和 Chain 抽象，便于构建复杂分析流程

**规则引擎**：
- 用户编写的规则存储为正则表达式或 Python 代码片段
- 使用 `re` 模块执行正则匹配
- 使用 `eval` 或 `exec` 执行代码片段（沙箱环境）

**AI 模式 Prompt 设计**：
- 输入：日志条目列表
- 输出：结构化 JSON（分类、去重分组、参数提取）

### 架构决策

| 决策 | 选择 | 理由 |
|------|------|------|
| AI 接入 | Anthropic SDK + MiniMax-M2.7 | Anthropic API 兼容，无需额外适配 |
| 规则存储 | PostgreSQL JSON字段 | 规则灵活扩展，复用现有数据库 |
| 规则执行 | re + eval 沙箱 | 简单直接，用户可编写正则或简单代码 |
| 模式切换 | 用户可配置，默认规则引擎 | 规则引擎快速，AI 模式智能 |

## Phase 1: Design & Contracts

（详见下方 data-model.md 和 contracts/ 目录）

## Complexity Tracking

> 本项目无宪法冲突，所有约束均已满足

| 项目 | 说明 |
|------|------|
| 无 | - |
