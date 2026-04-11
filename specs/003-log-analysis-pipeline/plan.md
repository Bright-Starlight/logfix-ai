# Implementation Plan: 日志分析完整流程集成

**Branch**: `003-log-analysis-pipeline` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)

> 所有正文内容必须使用中文编写；如与宪法冲突，以 `.specify/memory/constitution.md` 为准。

## Summary

将001（日志文件切分）与002（日志分类与结构化存储）集成为完整日志分析流水线。用户在切分完成后选择分类模式（规则引擎/AI），系统后台执行分类、去重、忽略过滤，并将结果存储到数据库，同时前端实时显示处理进度。

## Technical Context

**Language/Version**: Python 3.11（后端）, TypeScript/React 18（前端）
**Primary Dependencies**: FastAPI（后端）, Pydantic（数据验证）, SQLAlchemy（ORM）, React 18 + Vite（前端）
**Storage**: PostgreSQL + SQLite（开发）, 文件系统（上传文件）
**Testing**: pytest（后端）, Vitest（前端）
**Target Platform**: Windows/Linux Web 应用
**Project Type**: 全栈 Web 应用（日志分析工具）
**Performance Goals**:
- 切分10000行日志 < 5秒
- 规则引擎分类1000条日志 < 10秒
- AI模式分类每条日志平均 < 5秒（含AI调用延迟）
- 进度更新延迟 < 2秒
**Constraints**:
- 单文件大小限制100MB
- 单次分类任务超时300秒
- 进度轮询间隔2秒
**Scale/Scope**:
- 单用户本地使用
- 日志量预估每天不超过10万条
- 忽略规则数量预估100条以内

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] 规格已获批准，且用户故事具备独立测试条件。 —— 003 spec 已完成clarify
- [x] 已明确采用 TDD，并列出先写失败测试的策略。 —— 先写测试：先是单元测试覆盖分类逻辑和进度跟踪，再做集成测试
- [x] 交付切片按 MVP 优先排序，可独立部署或演示。 —— MVP优先：1)进度API 2)切分->分类串联 3)前端进度条
- [x] 已识别日志方案：日志框架、`/log` 目录、日志文件命名、关键埋点位置。 —— 使用log_service框架，日志输出到/log/logfix-ai_{日期}.log
- [x] 已定义性能目标与验证方式。 —— 成功标准SC-006/007/010已定义性能指标
- [x] 已确认实现和脚本兼容 Windows。 —— 后端Python+FastAPI跨平台，前端React跨平台
- [x] 已规划 `/speckit.tasks` 阶段输出 `specs/003-log-analysis-pipeline/flow.md`（Mermaid，中文）。
- [x] 已规划 `/speckit.implement` 完成后的主应用集成验证步骤。 —— 代码层面验证组件导入和渲染

## Project Structure

### Documentation (this feature)

```text
specs/003-log-analysis-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output (not needed - 001/002 research reusable)
├── data-model.md        # Phase 1 output (entity definitions for new progress tracking)
├── quickstart.md        # Phase 1 output (integration testing guide)
├── flow.md              # Phase 2 output (Mermaid 中文流程图, /speckit.tasks)
├── contracts/           # Phase 1 output
│   └── classification-progress.yaml  # Progress tracking API contract
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── routes.py          # [修改] 新增 classification progress 端点
│   │   └── schemas.py         # [修改] 新增 ClassificationProgressSchema
│   ├── services/
│   │   ├── classification_service.py  # [修改] 改为异步+进度上报
│   │   └── log_service.py      # [已存在] 日志框架
│   └── models/
│       ├── entities.py         # [修改] 新增 ClassificationSession entity
│       └── __init__.py
└── tests/
    ├── unit/
    │   └── test_classification_progress.py  # [新增] 进度跟踪单元测试
    └── integration/
        └── test_classification_pipeline.py   # [新增] 集成测试

frontend/
├── src/
│   ├── components/
│   │   ├── ClassificationModeSelect.tsx  # [新增] 分类模式选择组件
│   │   └── ProgressBar.tsx                # [新增] 分类进度条组件
│   ├── pages/
│   │   └── AnalysisPipeline.tsx           # [新增] 完整分析流水线页面
│   ├── hooks/
│   │   └── useClassificationProgress.ts   # [新增] 进度轮询 hook
│   ├── services/
│   │   └── api.ts              # [修改] 新增 classification progress API
│   └── App.tsx                 # [修改] 集成新页面和路由
└── tests/
    └── unit/
        └── test_classification_progress.ts  # [新增] 进度 hook 单元测试
```

**Structure Decision**:
- 这是一个集成功能，主要涉及现有组件的串联和新功能（进度跟踪）的添加
- 后端：在现有 classification_service.py 基础上改为异步+进度上报，新增 API 端点
- 前端：新增 ClassificationPipeline 页面整合切分和分类流程，新增进度条组件
- 进度跟踪通过轮询实现，前端每2秒请求一次进度 API

## Complexity Tracking

> 无复杂度违规。这是集成功能，主要是串联现有组件并添加进度跟踪新功能。

## Phase 0: Research

无需额外研究。001和002的技术方案已在各自的spec中明确，本功能复用：
- 后端：Python + FastAPI + SQLAlchemy（已有）
- 前端：React + Vite + TypeScript（已有）
- 数据库：PostgreSQL（已有）
- AI集成：LangChain + Anthropic SDK（002已有）
- 日志框架：log_service（已有）

**新增研究任务**:
- 进度跟踪方案：使用数据库存储进度 + 前端轮询

## Phase 1: Design & Contracts

### 1.1 新增数据模型 (data-model.md)

```markdown
# ClassificationSession 实体
- id: UUID（主键）
- split_session_id: UUID（外键，关联SplitSession）
- mode: str（"rule_engine" | "ai"）
- status: str（"pending" | "processing" | "completed" | "failed"）
- total_items: int（待处理日志总数）
- processed_items: int（已处理数量）
- current_phase: str（当前阶段名称）
- estimated_remaining_seconds: int（预估剩余秒数）
- error_message: str（失败时的错误信息，可选）
- created_at: datetime
- updated_at: datetime
- completed_at: datetime（可选）
```

### 1.2 新增 API 契约 (contracts/)

**GET /api/classification/{session_id}/progress**

响应：
```json
{
  "session_id": "uuid",
  "status": "processing",
  "total_items": 1000,
  "processed_items": 350,
  "current_phase": "去重检测中",
  "estimated_remaining_seconds": 45,
  "progress_percent": 35
}
```

状态枚举：
- `PENDING`（等待中）
- `PROCESSING`（处理中）
- `COMPLETED`（已完成）
- `FAILED`（失败）

**POST /api/classification/start**（新增端点）

请求：
```json
{
  "split_session_id": "uuid",
  "mode": "rule_engine"
}
```

响应：
```json
{
  "session_id": "uuid",
  "status": "pending"
}
```

### 1.3 快速入门 (quickstart.md)

```markdown
# 003 功能集成测试指南

## 测试前提
1. 后端服务运行中（端口8000）
2. 前端开发服务器运行中（端口5173）
3. 数据库已初始化

## 集成测试步骤

1. **上传日志文件**
   - POST /api/upload
   - 获取 file_id

2. **执行切分**
   - POST /api/split（file_id + 切分规则）
   - 获取 session_id

3. **获取切分结果**
   - GET /api/sessions/{session_id}
   - 等待 status=completed

4. **启动分类流程**
   - POST /api/classification/start
   - 获取 classification_session_id

5. **轮询进度**
   - GET /api/classification/{session_id}/progress
   - 观察进度更新

6. **查看分类结果**
   - GET /api/logs
   - 验证分类数据
```

## Phase 2: Task Breakdown

将在 `/speckit.tasks` 阶段输出完整的 tasks.md 和 flow.md。

### 关键实现任务

**后端**:
1. 修改 ClassificationSession entity（新增状态、进度字段）
2. 修改 classification_service.py（改为异步处理+进度上报）
3. 新增 GET /api/classification/{session_id}/progress 端点
4. 新增 POST /api/classification/start 端点
5. 编写单元测试和集成测试

**前端**:
1. 新增 ClassificationPipeline 页面（整合切分+分类流程）
2. 新增 ClassificationModeSelect 组件（模式选择）
3. 新增 ProgressBar 组件（显示处理进度）
4. 新增 useClassificationProgress hook（轮询进度）
5. 修改 App.tsx 添加路由
6. 编写单元测试

### 交付优先级

**MVP（必须）**:
1. 进度跟踪API（后端）
2. 切分->分类串联（前端）
3. 进度条UI

**扩展（可选）**:
4. 统计面板集成
5. 错误处理优化
