# Tasks: AI 结构化工具调用与流式输出优化

**Input**: Design documents from `/specs/004-ai-tool-call-streaming/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 测试任务是必填项。必须先创建并执行失败测试，再开始实现，以满足 TDD 宪法要求。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 安装依赖和基础结构

- [x] T001 安装 OpenAI SDK 和 SSE 依赖: `pip install openai sse-starlette`
- [x] T002 [P] 创建 `specs/004-ai-tool-call-streaming/flow.md`，使用 Mermaid 编写中文流程图

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 核心基础设施，所有用户故事实现前必须完成

**⚠️ CRITICAL**: 在此阶段完成前，不得开始任何用户故事实现

- [x] T003 [P] 重构 `backend/src/services/ai_analyzer.py`，从 Anthropic SDK 切换到 OpenAI SDK
- [x] T004 [P] 在 `backend/src/main.py` 实现 FastAPI lifespan 事件，OpenAI 客户端初始化（模型预加载在 US3）
- [x] T005 实现 `asyncio.Semaphore` 并发控制，默认 5 并发
- [x] T006 配置日志框架: `logfix-ai_YYYYMMDD.log` 输出到 `/log` 目录

**Checkpoint**: 基础就绪 - 用户故事实现可以开始

---

## Phase 3: User Story 1 - 使用工具调用进行 AI 结构化 (Priority: P1) 🎯 MVP

**Goal**: 通过 Tool Call 方式调用 MiniMax-M2.7 进行日志结构化

**Independent Test**: 上传标准日志文件，触发 AI 结构化，验证返回的 JSON 结构是否符合预期格式

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] 单元测试: Tool Call 解析逻辑 in `backend/tests/unit/test_ai_analyzer.py`
- [x] T008 [P] [US1] 集成测试: 工具调用完整流程 in `backend/tests/integration/test_classification_pipeline.py`

### Implementation for User Story 1

- [x] T009 [P] [US1] 定义 `classify_log` Tool Schema in `backend/src/services/ai_analyzer.py`
- [x] T010 [P] [US1] 实现 `analyze_logs_ai` 函数支持 tool call 模式
- [x] T011 [US1] 实现 tool call 流式输出解析，处理 SSE 事件并提取结构化结果 (depends on T009, T010)
- [x] T012 [US1] 添加结构化日志: 模型调用、token 消耗、结果解析

**Checkpoint**: User Story 1 应完全可用并可独立测试

---

## Phase 4: User Story 2 - 流式输出展示结构化进度 (Priority: P1)

**Goal**: 通过 SSE 实时推送处理进度和结构化结果

**Independent Test**: 触发结构化操作，观察前端是否实时更新处理进度并逐步收到结构化结果

### Tests for User Story 2 ⚠️

- [x] T013 [P] [US2] 单元测试: SSE 事件生成 in `backend/tests/unit/test_streaming.py`
- [x] T014 [P] [US2] 集成测试: SSE 端点完整流程 in `backend/tests/integration/test_streaming.py`

### Implementation for User Story 2

- [x] T015 [P] [US2] 新增 `POST /api/classify/stream` SSE 端点 in `backend/src/api/routes.py`
- [x] T016 [P] [US2] 实现 `StreamingResponse` 返回 SSE 事件 (progress/result/error/done)
- [x] T017 [US2] 实现取消操作支持: 客户端断开时立即中断请求 (depends on T015, T016)
- [ ] T017.5 [US2] 实现后台处理: 用户关闭页面时后台继续完成，结果存入数据库
- [x] T018 [US2] 添加 SSE 推送日志: 进度更新、结果发送、错误事件

**Checkpoint**: User Story 2 应完全可用并可独立测试

---

## Phase 5: User Story 3 - 模型预加载与复用 (Priority: P2)

**Goal**: 系统启动时预加载模型，实例全局复用

**Independent Test**: 查看系统日志确认模型在启动时被加载，多次调用验证模型实例被复用

### Tests for User Story 3 ⚠️

- [x] T019 [P] [US3] 单元测试: 模型预加载逻辑 in `backend/tests/unit/test_model_preload.py`
- [x] T020 [P] [US3] 集成测试: 预加载后请求响应时间 in `backend/tests/integration/test_model_preload.py`
- [ ] T020.5 [US3] 性能测试: 验证预加载后首次响应比无预加载快 80% (对比测试)

- [x] T021 [P] [US3] 实现全局单例 OpenAI 客户端 in `backend/src/services/ai_analyzer.py`
- [x] T022 [US3] lifespan 事件中调用预加载，记录启动日志 `"模型预加载完成, model=MiniMax-M2.7"` (depends on T004)
- [x] T023 [US3] 添加预加载日志: 开始/成功/失败，包含 duration_ms

**Checkpoint**: User Story 3 应完全可用并可独立测试

---

## Phase 6: User Story 4 - Token 消耗调研与优化 (Priority: P3)

**Goal**: 记录并对比工具调用 vs 提示词工程的 token 消耗

**Independent Test**: 对比相同日志数据两种方式的 token 消耗，计算成本差异

### Tests for User Story 4 ⚠️

- [x] T024 [P] [US4] 单元测试: Token 统计逻辑 in `backend/tests/unit/test_token_tracking.py`

### Implementation for User Story 4

- [x] T025 [P] [US4] 新增 `TokenUsage` 模型 in `backend/src/models/entities.py`
- [x] T026 [US4] 实现 token 消耗记录: input_tokens, output_tokens, method, user_id
- [x] T027 [US4] 添加 token 对比统计接口: tool_call vs prompt_engineering

**Checkpoint**: User Story 4 应完全可用并可独立测试

---

## Phase 7: Frontend Integration (Cross-Cutting)

**Purpose**: 前端 SSE 集成

- [x] T028 [P] 创建 `frontend/src/hooks/useClassificationProgress.ts`，使用 EventSource 接收 SSE
- [ ] T029 [P] 实现进度条实时更新 in `frontend/src/components/FileUpload.tsx`
- [x] T030 [P] 实现取消操作: `EventSource.close()` in `frontend/src/hooks/useClassificationProgress.ts`
- [ ] T031 在 `frontend/src/components/FileUpload.tsx` 中实现结果实时展示，逐步显示结构化结果

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 改进和收尾

- [x] T032 [P] 集成验证: 确认功能已导入主应用，组件正确渲染
- [x] T033 [P] 运行后端测试: `pytest tests/unit/ tests/integration/ -v`
- [x] T034 [P] 运行前端测试: `vitest run` (无测试文件，TypeScript 编译通过)
- [x] T035 验证日志输出: `/log/logfix-ai_YYYYMMDD.log` 包含所有埋点
- [x] T036 验证 quickstart.md 流程可执行

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | 依赖 | 说明 |
|-------|------|------|
| Phase 1: Setup | 无 | 可立即开始 |
| Phase 2: Foundational | Phase 1 | 阻塞所有用户故事 |
| Phase 3-6: User Stories | Phase 2 | 可并行进行 |
| Phase 7: Frontend | Phase 2 | 可并行于用户故事 |
| Phase 8: Polish | Phase 3-7 | 所有实现完成后 |

### User Story Dependencies

- **US1 (P1)**: Phase 2 完成后可开始 - 无需其他故事依赖
- **US2 (P1)**: Phase 2 完成后可开始 - 无需其他故事依赖
- **US3 (P2)**: Phase 2 完成后可开始 - 可与 US1/US2 并行
- **US4 (P3)**: Phase 2 完成后可开始 - 可与 US1/US2/US3 并行

### Within Each User Story

1. Tests MUST be written and FAIL before implementation
2. Models before services
3. Services before endpoints
4. Core implementation before integration
5. Story complete before moving to next priority

### Parallel Opportunities

| 任务组合 | 可并行原因 |
|----------|-----------|
| T001 + T002 | 不同文件 |
| T003 + T004 | 不同文件 |
| T007 + T008 | 不同测试文件 |
| T009 + T010 | 不同函数 |
| T015 + T016 | 不同实现部分 |
| T021 + T022 | 不同文件和逻辑 |

---

## MVP Scope

**建议 MVP**: Phase 1 + Phase 2 + Phase 3 (US1)

MVP 交付物:
- OpenAI SDK 切换完成
- 模型预加载完成
- Tool Call 结构化功能可用
- 基本 SSE 流式输出

---

## Independent Test Criteria

| User Story | 独立测试条件 |
|------------|-------------|
| US1 | 上传日志文件 → 点击结构化 → 验证 JSON 结构正确 |
| US2 | 触发结构化 → 观察进度条实时更新 → 逐步收到结果 |
| US3 | 查看启动日志 → 确认预加载完成 → 多次调用验证复用 |
| US4 | 对比两种方式 → 验证 token 记录准确 → 生成对比报告 |

---

## Total Task Count

| Phase | 任务数 |
|-------|--------|
| Phase 1: Setup | 2 |
| Phase 2: Foundational | 4 |
| Phase 3: US1 | 6 |
| Phase 4: US2 | 7 (含 T017.5 后台处理) |
| Phase 5: US3 | 6 (含 T020.5 性能测试) |
| Phase 6: US4 | 4 |
| Phase 7: Frontend | 4 |
| Phase 8: Polish | 5 |
| **Total** | **38** |
