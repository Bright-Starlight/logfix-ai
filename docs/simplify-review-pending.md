# Simplify Review - 待架构调整项

> 生成日期: 2026-04-14
> 来源: `/simplify` 代码审查

## 概述

以下问题在本次审查中被识别，但需要较大的架构调整才能修复。现记录于此，供后续迭代参考。

---

## 1. SSE 解析逻辑重复

### 问题描述

`useAnalysisProgress.ts` 和 `useClassificationProgress.ts` 两个 hooks 中包含几乎完全相同的 SSE 解析逻辑（约 40 行代码重复）。

### 代码位置

- `frontend/src/hooks/useAnalysisProgress.ts` (lines 96-138)
- `frontend/src/hooks/useClassificationProgress.ts` (lines 95-137)

### 重复代码

```typescript
while (true) {
  const { done, value } = await reader.read()
  if (done) break

  buffer += decoder.decode(value, { stream: true })

  // 按 SSE 格式解析（event: xxx\ndata: yyy\n\n）
  const eventMatch = buffer.match(/^event: (\w+)\n/m)
  if (eventMatch) {
    currentEvent = eventMatch[1]
  }

  const dataMatch = buffer.match(/^data: (.+?)\n\n/ms)
  if (dataMatch) {
    currentData = dataMatch[1]
    buffer = buffer.slice(dataMatch[0].length)

    try {
      const parsedData = JSON.parse(currentData)
      // event handling...
    } catch {
      // Ignore parse errors
    }

    currentEvent = ''
    currentData = ''
  }
}
```

### 建议方案

提取为共享工具函数：

```typescript
// frontend/src/utils/sseParser.ts
export interface SSEParserOptions<T> {
  onEvent: (event: string, data: T) => void
  onError?: (error: Error) => void
}

export async function parseSSEStream<T>(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  options: SSEParserOptions<T>
): Promise<void> {
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = ''
  let currentData = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    const eventMatch = buffer.match(/^event: (\w+)\n/m)
    if (eventMatch) {
      currentEvent = eventMatch[1]
    }

    const dataMatch = buffer.match(/^data: (.+?)\n\n/ms)
    if (dataMatch) {
      currentData = dataMatch[1]
      buffer = buffer.slice(dataMatch[0].length)

      try {
        const parsedData = JSON.parse(currentData)
        options.onEvent(currentEvent, parsedData)
      } catch (e) {
        options.onError?.(e as Error)
      }

      currentEvent = ''
      currentData = ''
    }
  }
}
```

### 优先级

- **优先级**: 中
- **工作量**: 中（需要重构两个 hooks）
- **收益**: 减少代码重复，便于统一修改 SSE 解析逻辑

---

## 2. Polling 无 Backoff 机制

### 问题描述

`analysis_stream` 端点中的轮询等待使用固定 1 秒间隔，且每次轮询都执行数据库查询。

### 代码位置

`backend/src/api/routes.py` (lines 1768-1783)

```python
while queue.get_queue_position(log_entry_id) is None or queue.get_queue_position(log_entry_id) > 1:
    await asyncio.sleep(1)
    with get_db_session() as db:
        session = db.query(AnalysisSession).filter(
            AnalysisSession.id == int(session_id)
        ).first()
        if session and session.status == "cancelled":
            yield {
                "event": "error",
                "data": json.dumps({
                    "code": "CANCELLED",
                    "message": "任务已被取消",
                }),
            }
            return
```

### 问题影响

1. 数据库每秒查询，无指数退避
2. 无事件驱动唤醒机制
3. 队列位置变化时无法及时响应

### 建议方案

**方案 A**: 实现指数退避 + 最大等待时间

```python
wait_time = 1
max_wait = 30
while True:
    position = queue.get_queue_position(log_entry_id)
    if position is None or position > 1:
        await asyncio.sleep(wait_time)
        wait_time = min(wait_time * 1.5, max_wait)
    else:
        break
```

**方案 B**: 事件驱动架构（推荐）

使用 Redis Pub/Sub 或 WebSocket 替代轮询，队列位置变化时主动推送通知。

### 优先级

- **优先级**: 低
- **工作量**: 高（需要重构 SSE 流机制）
- **收益**: 降低数据库负载，提高响应延迟

---

## 3. EventSource 无 Timeout

### 问题描述

前端 `createEventSource` 方法创建 SSE 连接后，无超时处理机制。如果服务器无响应（网络分区、服务器崩溃），连接会无限挂起。

### 代码位置

`frontend/src/services/api.ts` (lines 338-340)

```typescript
createEventSource: (sessionId: string): EventSource => {
  return new EventSource(`/api/analysis/stream/${sessionId}`)
},
```

### 问题影响

- 无网络超时检测
- 无重连机制
- 无优雅降级

### 建议方案

使用 `fetch` + `ReadableStream` 替代原生 `EventSource`，可实现细粒度超时控制：

```typescript
async function fetchWithTimeout(
  url: string,
  timeoutMs: number = 60000
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, { signal: controller.signal })
    clearTimeout(timeoutId)
    return response
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时')
    }
    throw error
  }
}
```

### 优先级

- **优先级**: 中
- **工作量**: 中（需重构 SSE 连接管理）
- **收益**: 提高网络异常时的用户体验

---

## 4. 字符串状态值（未使用枚举）

### 问题描述

多处使用字符串字面量表示状态值，未使用 TypeScript 枚举或 Python 枚举。

### 代码位置

**Python (routes.py)**
```python
AnalysisSession.status.in_(["pending", "queued", "processing"])
```

**TypeScript (types/index.ts)**
```typescript
export type AnalysisStatus = 'un_analyzed' | 'analyzing' | 'completed' | 'failed'
```

### 现状

- TypeScript 使用 string literal union type，功能等效于枚举
- Python 端使用字符串列表，虽提取为常量但仍为字符串

### 建议方案

如需更强类型约束，可引入枚举：

```typescript
// TypeScript
export enum AnalysisStatus {
  UN_ANALYZED = 'un_analyzed',
  ANALYZING = 'analyzing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}
```

```python
# Python
from enum import Enum

class AnalysisStatus(str, Enum):
    UN_ANALYZED = "un_analyzed"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
```

### 优先级

- **优先级**: 低
- **工作量**: 低
- **收益**: 轻微（当前实现功能正常，仅类型安全性略低）

---

## 总结

| 问题 | 优先级 | 工作量 | 收益 |
|------|--------|--------|------|
| SSE 解析逻辑重复 | 中 | 中 | 减少重复代码 |
| Polling 无 backoff | 低 | 高 | 降低 DB 负载 |
| EventSource 无 timeout | 中 | 中 | 提高容错性 |
| 字符串状态值 | 低 | 低 | 轻微类型安全提升 |

**建议**: 优先处理 SSE 解析逻辑重复问题，其他项可在后续迭代中根据业务需求酌情处理。
