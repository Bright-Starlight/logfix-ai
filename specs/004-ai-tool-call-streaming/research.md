# Research: AI 结构化工具调用与流式输出优化

**Branch**: `004-ai-tool-call-streaming`
**Date**: 2026-04-11

## Research 1: MiniMax API Tool Call 支持

### Decision

使用 OpenAI SDK 的 `tools` 参数调用 MiniMax-M2.7

### Rationale

- MiniMax OpenAI 兼容接口原生支持 `tools` 参数
- 旧版 `function_call` 参数已废弃
- OpenAI SDK 生态完善，支持 `stream=True`

### Evidence

1. MiniMax 文档: "旧版的 function_call 已废弃，请使用 tools 参数"
2. OpenAI SDK 流式响应示例在 MiniMax 文档中有官方示例
3. 当前代码使用 Anthropic SDK，但 Anthropic 不支持 MiniMax tool call

### Alternatives Considered

| 方案 | 缺点 |
|------|------|
| Anthropic SDK | 不支持 MiniMax tool call |
| 手动解析 XML | 需要解析 `<tool_calls>` 标签，复杂易错 |
| MiniMax 原生 API | 非标准，生态差 |

---

## Research 2: MiniMax 流式输出支持

### Decision

使用 `stream=True` + SSE 前端展示

### Rationale

- MiniMax OpenAI 兼容接口支持 `stream=True`
- SSE (Server-Sent Events) 轻量单向，实现简单
- 前端 `EventSource` API 支持良好

### Evidence

```python
# MiniMax 流式响应示例 (来自官方文档)
stream = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[...],
    stream=True
)
```

### Alternatives Considered

| 方案 | 缺点 |
|------|------|
| WebSocket | 需双向通信，过度设计 |
| 长轮询 | 延迟高，资源浪费 |
| 一次性返回 | 无法实时展示进度，违反需求 |

---

## Research 3: Python 模型预加载模式

### Decision

FastAPI lifespan events + 全局单例

### Rationale

- 与现有架构兼容
- 不增加额外依赖
- 生命周期清晰

### Evidence

```python
# main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 预加载模型
    logger.info("模型预加载开始...")
    await preload_model()
    logger.info("模型预加载完成")
    yield
    # 清理
```

### Alternatives Considered

| 方案 | 缺点 |
|------|------|
| 第三方 DI (punq) | 增加依赖 |
| 线程锁 | 不适合异步场景 |
| 每次新建 | 延迟高，资源浪费 |

---

## Research 4: 请求并发策略

### Decision

`asyncio.Semaphore` 控制并发数 + 智能批次大小

### Rationale

- MiniMax 官方支持并发请求，付费用户 500 RPM（约 8.3 QPS）
- 通过 Semaphore 限制并发数避免触发 RPM 限制
- 批次处理提高 TPM 利用率

### Evidence

MiniMax 速率限制（官方文档）：
- 免费用户：20 RPM, 1,000,000 TPM
- 付费用户：500 RPM, 20,000,000 TPM

```python
# 并发控制：使用 Semaphore 限制并发数
semaphore = asyncio.Semaphore(5)  # 留 3 QPS 余量

async def call_with_limit():
    async with semaphore:
        return await client.chat.completions.create(...)

# 批次处理：单请求多条日志，提高 TPM 利用率
# MiniMax 建议：集中处理请求，批量放入每个请求
```

### Concurrency Calculation

| 用户类型 | RPM | 安全并发 (留 30% 余量) | 批次大小 |
|----------|-----|------------------------|----------|
| 免费用户 | 20 | 2 | 10 条/请求 |
| 付费用户 | 500 | 5 | 100 条/请求 |

### Alternatives Considered

| 方案 | 缺点 |
|------|------|
| 纯串行 | 吞吐量低，无法充分利用 TPM |
| 无限制并发 | 可能触发 RPM 限制 |
| 外部队列 (Celery) | 过度重量 |

---

## Summary

所有关键技术问题已通过调研解决，可以进入 Phase 1 实现阶段。

### Key Takeaways

1. **统一 OpenAI SDK** — MiniMax OpenAI 兼容接口功能最完整
2. **SSE + stream=True** — 官方支持，实现简单
3. **Lifespan 预加载** — FastAPI 原生支持
4. **asyncio.Semaphore 并发控制** — MiniMax 支持 500 RPM，并发安全可控
   - 默认 5 并发（留 30% 余量）
   - 批次处理提高 TPM 利用率
