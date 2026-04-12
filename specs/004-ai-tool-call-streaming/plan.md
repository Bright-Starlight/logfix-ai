# Implementation Plan: AI 结构化工具调用与流式输出优化

**Branch**: `004-ai-tool-call-streaming` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)

> 所有正文内容必须使用中文编写；如与宪法冲突，以 `.specify/memory/constitution.md` 为准。

## Summary

通过 Tool Call 方式调用 MiniMax-M2.7 模型进行日志结构化，统一使用 OpenAI SDK 与 MiniMax 交互，并使用 SSE 流式输出实时推送处理进度和结构化结果。模型在系统启动时预加载，采用 `asyncio.Semaphore` 控制并发（默认 5 并发，付费用户留 30% 余量），批次处理提高 TPM 利用率。

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, OpenAI SDK (MiniMax OpenAI 兼容接口), SSE (sse-starlette)
**Storage**: PostgreSQL (现有), 无新存储需求
**Testing**: pytest (后端), Vitest (前端)
**Target Platform**: Linux Server (后端), Web Browser (前端)
**Project Type**: Web Service + Frontend SPA
**Performance Goals**:
- 进度更新延迟 ≤ 500ms
- 模型预加载后首次响应快 80%
- 支持 10 万条日志分批处理
**Constraints**: <200ms p95 进度更新, 100 条/批
**Scale/Scope**: 单用户顺序处理，多用户通过队列隔离

## Constitution Check

- [x] 规格已获批准，且用户故事具备独立测试条件。
- [x] 已明确采用 TDD，并列出先写失败测试的策略。
- [x] 交付切片按 MVP 优先排序，可独立部署或演示。
- [x] 已识别日志方案：使用现有 `log_service` 框架，日志文件 `logfix-ai_YYYYMMDD.log` 输出到 `/log` 目录。
- [x] 已定义性能目标与验证方式。
- [x] 已确认实现和脚本兼容 Windows。
- [x] 已规划 `/speckit.tasks` 阶段输出 `flow.md`（Mermaid，中文）。
- [x] 已规划 `/speckit.implement` 完成后的主应用集成验证步骤。

## Project Structure

### Documentation (this feature)

```text
specs/004-ai-tool-call-streaming/
├── plan.md              # This file
├── research.md          # Phase 0 output (MiniMax API 调研)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── flow.md              # Phase 2 output (Mermaid 中文流程图)
├── contracts/           # Phase 1 output (SSE 事件格式)
└── tasks.md             # Phase 2 output
```

### Source Code

```text
backend/
├── src/
│   ├── services/
│   │   ├── ai_analyzer.py       # 重构：Tool Call + 流式输出
│   │   ├── classification_service.py  # SSE 进度推送集成
│   │   └── log_service.py       # 现有日志框架
│   ├── api/
│   │   └── routes.py            # 新增 SSE 流式端点
│   └── main.py                  # 模型预加载初始化
└── tests/
    ├── unit/
    │   └── test_ai_analyzer.py  # TDD 测试
    └── integration/
        └── test_streaming.py    # SSE 集成测试

frontend/
├── src/
│   ├── components/
│   │   └── FileUpload.tsx       # 集成 SSE 进度显示
│   ├── hooks/
│   │   └── useClassificationProgress.ts  # SSE EventSource
│   └── services/
│       └── api.ts               # SSE 流式调用
└── tests/
    └── unit/
        └── test_classification_progress.ts
```

## Complexity Tracking

> 无复杂度违规，无需追踪

## Phase 0: Research

### Research Topics

1. **MiniMax OpenAI SDK Tool Call 支持**
   - Decision: 使用 OpenAI SDK 的 `tools` 参数调用 MiniMax-M2.7
   - Rationale: MiniMax OpenAI 兼容接口原生支持 `tools` 参数和 `stream=True`
   - Alternatives considered: Anthropic SDK (不支持 MiniMax tool call), 手动解析 XML (复杂)

2. **MiniMax 流式输出支持**
   - Decision: 使用 `stream=True` + SSE 前端展示
   - Rationale: OpenAI SDK 流式响应 + FastAPI StreamingResponse 实现 SSE
   - Alternatives considered: WebSocket (需双向通信, 过度设计)

3. **Python 模型预加载模式**
   - Decision: FastAPI lifespan events + 全局单例
   - Rationale: 与现有架构兼容，简单可靠
   - Alternatives considered: 第三方 DI 框架 (增加依赖)

4. **请求并发策略**
   - Decision: `asyncio.Semaphore` 控制并发 + 智能批次大小
   - Rationale: MiniMax 付费用户支持 500 RPM，通过 Semaphore 限制并发数避免触发限制
   - 实现:
     - 默认并发数: 5（留 30% 余量）
     - 批次大小: 100 条/请求
     - 通过 `max_concurrent` 和 `batch_size` 配置控制

### Research Output

已生成 `research.md`（见下节总结）

## Phase 1: Design & Contracts

### Data Model

详见 `data-model.md`

### Interface Contracts

**SSE 流式端点**: `POST /api/classify/stream`

```json
// SSE 事件类型

// 1. 进度事件
event: progress
data: {"processed": 10, "total": 100, "percentage": 10}

// 2. 结果事件
event: result
data: {"index": 0, "category": "异常错误", "error_type": "NullPointerException", "normalized_message": "Null pointer at *", "extracted_params": {}}

// 3. 错误事件
event: error
data: {"code": "PARSE_ERROR", "message": "AI 响应格式错误"}

// 4. 完成事件
event: done
data: {"total_processed": 100, "success_count": 95, "error_count": 5}
```

### Quickstart

详见 `quickstart.md`

---

## Implementation Phases

### Phase 1: 基础设施 (MVP 优先)

1. **模型预加载机制**
   - 在 `main.py` 的 lifespan 事件中预加载 OpenAI 客户端
   - 实现单例模式，模型实例全局复用
   - 记录启动日志: `"模型预加载完成, model=MiniMax-M2.7"`

2. **SSE 端点基础**
   - 新增 `/api/classify/stream` 端点
   - 使用 `StreamingResponse` 返回 SSE
   - 实现请求队列 (`asyncio.Queue`)，支持动态并行/串行切换

3. **Tool Call 重构**
   - 定义 `classify_log` 工具 schema
   - 重构 `analyze_logs_ai` 支持 tool call
   - 实现流式响应处理

### Phase 2: 前端集成

1. **SSE 客户端**
   - 使用 `EventSource` 接收流式事件
   - 实现进度条实时更新
   - 支持取消操作 (`EventSource.close()`)

2. **结果实时展示**
   - 流式接收并逐步展示结构化结果
   - 错误状态展示

### Phase 3: 测试与优化

1. **TDD 测试编写**
   - 单元测试: Tool Call 解析、队列逻辑
   - 集成测试: SSE 端点完整流程

2. **Token 消耗统计**
   - 记录每次请求的 token 消耗
   - 支持两种方式对比

---

## TDD Strategy

### 先写失败测试

1. `test_ai_analyzer_tool_call` - 测试 tool call 解析 (应失败: 功能未实现)
2. `test_streaming_progress` - 测试 SSE 进度推送 (应失败: 端点不存在)
3. `test_model_preload` - 测试模型预加载 (应失败: 无预加载逻辑)

### Red-Green-Refactor 循环

1. RED: 运行测试，确认失败
2. GREEN: 实现最小代码使测试通过
3. REFACTOR: 优化代码结构

---

## 日志埋点设计

| 位置 | 事件 | 级别 | 上下文 |
|------|------|------|--------|
| 模型预加载 | 开始/成功/失败 | INFO/ERROR | model, duration_ms |
| 结构化请求 | 开始/结束 | INFO | batch_size, total |
| Token 消耗 | 记录 | DEBUG | input_tokens, output_tokens |
| SSE 推送 | 进度/结果/错误 | DEBUG | processed, total |
| 队列操作 | 入队/出队/满 | DEBUG | queue_size |
| 取消操作 | 用户取消 | INFO | processed_at_cancel |

---

## Performance Targets

| 指标 | 目标 | 验证方式 |
|------|------|----------|
| 进度更新延迟 | ≤ 500ms | 手动测试 + 日志时间戳 |
| 首次响应加速 | ≥ 80% | 预加载 vs 非预加载对比 |
| 结构化成功率 | ≥ 99% | 自动化测试 |
| Token 记录准确率 | 100% | 单元测试验证 |
