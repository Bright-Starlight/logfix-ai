# Data Model: AI 结构化工具调用与流式输出优化

**Branch**: `004-ai-tool-call-streaming`
**Date**: 2026-04-11

## Entities

### LogEntry (现有)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | 主键 |
| original_message | String | 原始日志消息 |
| normalized_message | String | 归一化消息 |
| stack_trace | Text | 堆栈跟踪 |
| category_id | FK | 关联分类 |
| error_type | String | 错误类型 |
| extracted_params | JSON | 提取的参数 |
| log_level | String | 日志级别 |
| occurrence_count | Integer | 出现次数 |
| first_seen_at | DateTime | 首次出现时间 |
| last_seen_at | DateTime | 最后出现时间 |

### StructuredResult (新增)

| Field | Type | Description |
|-------|------|-------------|
| index | Integer | 日志索引 |
| category | String | 分类名称 |
| error_type | String | 错误类型 |
| normalized_message | String | 归一化消息 |
| extracted_params | JSON | 提取的参数 |

### ClassificationSession (新增)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | 主键 |
| user_id | String | 用户标识 |
| status | Enum | pending/processing/completed/cancelled/failed |
| total_count | Integer | 总条数 |
| processed_count | Integer | 已处理条数 |
| success_count | Integer | 成功条数 |
| error_count | Integer | 错误条数 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| completed_at | DateTime | 完成时间 |

### TokenUsage (新增)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | 主键 |
| user_id | String | 用户标识 |
| session_id | UUID | 关联会话 |
| method | Enum | tool_call / prompt_engineering |
| input_tokens | Integer | 输入 token 数 |
| output_tokens | Integer | 输出 token 数 |
| model | String | 模型名称 |
| created_at | DateTime | 创建时间 |

## SSE Event Schema

### Progress Event

```json
{
  "event": "progress",
  "data": {
    "processed": 10,
    "total": 100,
    "percentage": 10
  }
}
```

### Result Event

```json
{
  "event": "result",
  "data": {
    "index": 0,
    "category": "异常错误",
    "error_type": "NullPointerException",
    "normalized_message": "Null pointer at *",
    "extracted_params": {"line": "10"}
  }
}
```

### Error Event

```json
{
  "event": "error",
  "data": {
    "code": "PARSE_ERROR",
    "message": "AI 响应格式错误"
  }
}
```

### Done Event

```json
{
  "event": "done",
  "data": {
    "total_processed": 100,
    "success_count": 95,
    "error_count": 5
  }
}
```

## Tool Call Schema

### classify_log Tool

```json
{
  "name": "classify_log",
  "description": "对单条日志进行结构化分类，返回分类结果",
  "parameters": {
    "type": "object",
    "properties": {
      "log_entry": {
        "type": "string",
        "description": "原始日志条目"
      },
      "index": {
        "type": "integer",
        "description": "日志在列表中的索引"
      }
    },
    "required": ["log_entry", "index"]
  }
}
```

### Tool Call Response

```json
{
  "index": 0,
  "category": "异常错误",
  "error_type": "NullPointerException",
  "normalized_message": "Null pointer at line *",
  "extracted_params": {"line": "10"}
}
```

### Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| max_concurrent | int | 5 | 最大并发数（付费用户留 30% 余量） |
| batch_size | int | 100 | 每批处理的日志条数 |
