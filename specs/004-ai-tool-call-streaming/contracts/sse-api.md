# Contract: SSE Streaming API

**Endpoint**: `POST /api/classify/stream`

## Request

```http
POST /api/classify/stream
Content-Type: application/json

{
  "logs": ["log entry 1", "log entry 2", ...],
  "user_id": "optional_user_id"
}
```

## Response (SSE Stream)

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: progress
data: {"processed": 10, "total": 100, "percentage": 10}

event: result
data: {"index": 0, "category": "异常错误", "error_type": "NullPointerException", "normalized_message": "Null pointer at *", "extracted_params": {}}

event: error
data: {"code": "PARSE_ERROR", "message": "AI 响应格式错误", "index": 5}

event: done
data: {"total_processed": 100, "success_count": 95, "error_count": 5}
```

## Event Types

| Event | Description | Fields |
|-------|-------------|--------|
| progress | 处理进度 | processed, total, percentage |
| result | 单条结果 | index, category, error_type, normalized_message, extracted_params |
| error | 处理错误 | code, message, index (optional) |
| done | 完成 | total_processed, success_count, error_count |

## Error Codes

| Code | Description |
|------|-------------|
| PARSE_ERROR | AI 响应 JSON 解析失败 |
| TIMEOUT | 请求超时 |
| CANCELLED | 用户取消 |
| INTERNAL_ERROR | 内部错误 |

## Cancellation

客户端关闭 EventSource 连接即可取消:

```javascript
const es = new EventSource(...);
es.close(); // 发送取消信号到服务器
```
