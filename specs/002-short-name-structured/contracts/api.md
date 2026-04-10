# API Contracts: 日志分类与结构化存储

**Branch**: `002-short-name-structured`
**Date**: 2026-04-11

## 概述

本项目为前后端分离架构，所有API均通过JSON进行数据交换。

**Base URL**: `/api`

**通用响应格式**:
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

**错误响应格式**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 接口列表

### 1. 分类日志

**POST** `/api/classify`

**描述**: 对日志数据进行分类和去重（支持规则引擎和AI模式）

**请求**:
```json
{
  "logs": [
    "2024-01-01 10:00:00 ERROR java.lang.NullPointerException: Cannot invoke method on null object at line 10",
    "2024-01-01 10:00:01 ERROR java.lang.NullPointerException: Cannot invoke method on null object at line 20"
  ],
  "mode": "rule_engine",
  "file_id": "uuid"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| logs | string[] | 是 | 日志条目列表 |
| mode | string | 是 | 处理模式: `rule_engine` 或 `ai` |
| file_id | UUID | 否 | 来源文件ID（用于关联） |

**响应** (200):
```json
{
  "success": true,
  "data": {
    "processed": 2,
    "new_entries": 1,
    "duplicates": 1,
    "entries": [
      {
        "id": "uuid",
        "original_message": "2024-01-01 10:00:00 ERROR java.lang.NullPointerException...",
        "normalized_message": "java.lang.NullPointerException: Cannot invoke method on null object at line *",
        "stack_trace": "at com.example.App.process(App.java:10)\nat com.example.Main.main(Main.java:20)",
        "category": "异常错误",
        "error_type": "NullPointerException",
        "occurrence_count": 2
      }
    ]
  }
}
```

**错误码**:
- `INVALID_MODE`: 无效的处理模式
- `AI_SERVICE_ERROR`: AI 服务调用失败
- `RULE_EXECUTION_ERROR`: 规则执行错误

---

### 2. 获取日志列表

**GET** `/api/logs`

**描述**: 获取已分类的日志列表（分页）

**查询参数**:
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页数量，默认50，最大200
- `category` (可选): 分类名称过滤
- `level` (可选): 日志级别过滤
- `keyword` (可选): 关键词搜索
- `start_date` (可选): 开始日期 (YYYY-MM-DD)
- `end_date` (可选): 结束日期 (YYYY-MM-DD)

**响应** (200):
```json
{
  "success": true,
  "data": {
    "total": 1000,
    "page": 1,
    "page_size": 50,
    "total_pages": 20,
    "entries": [
      {
        "id": "uuid",
        "normalized_message": "java.lang.NullPointerException: Cannot invoke method on null object at line *",
        "stack_trace": "at com.example.App.process(App.java:10)\nat com.example.Main.main(Main.java:20)",
        "category": "异常错误",
        "error_type": "NullPointerException",
        "log_level": "ERROR",
        "occurrence_count": 15,
        "first_seen_at": "2024-01-01T10:00:00Z",
        "last_seen_at": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

---

### 3. 获取日志详情

**GET** `/api/logs/{log_id}`

**描述**: 获取单条日志的完整详情

**路径参数**:
- `log_id`: 日志UUID

**响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "original_message": "2024-01-01 10:00:00 ERROR java.lang.NullPointerException: Cannot invoke method on null object at line 10",
    "normalized_message": "java.lang.NullPointerException: Cannot invoke method on null object at line *",
    "stack_trace": "at com.example.App.process(App.java:10)\nat com.example.Main.main(Main.java:20)",
    "category": "异常错误",
    "category_id": "uuid",
    "error_type": "NullPointerException",
    "extracted_params": {"line": "10"},
    "log_level": "ERROR",
    "occurrence_count": 15,
    "first_seen_at": "2024-01-01T10:00:00Z",
    "last_seen_at": "2024-01-01T12:00:00Z"
  }
}
```

---

### 4. 获取统计信息

**GET** `/api/stats`

**描述**: 获取日志统计信息

**查询参数**:
- `start_date` (可选): 开始日期
- `end_date` (可选): 结束日期

**响应** (200):
```json
{
  "success": true,
  "data": {
    "total_entries": 5000,
    "unique_errors": 120,
    "categories": [
      {
        "name": "异常错误",
        "count": 3000,
        "percentage": 60
      },
      {
        "name": "警告",
        "count": 1500,
        "percentage": 30
      }
    ],
    "daily_trend": [
      {
        "date": "2024-01-01",
        "count": 500
      }
    ]
  }
}
```

---

### 5. 规则管理 - 获取规则列表

**GET** `/api/rules`

**描述**: 获取解析规则列表

**响应** (200):
```json
{
  "success": true,
  "data": {
    "rules": [
      {
        "id": "uuid",
        "name": "Java异常提取",
        "rule_type": "regex",
        "pattern": "java\\.lang\\.(\\w+Exception): (.+)",
        "priority": 10,
        "enabled": true,
        "is_system": true
      }
    ]
  }
}
```

---

### 6. 规则管理 - 创建规则

**POST** `/api/rules`

**描述**: 创建新的解析规则

**请求**:
```json
{
  "name": "Python异常提取",
  "rule_type": "regex",
  "pattern": "(\\w+Error): (.+)",
  "priority": 5,
  "enabled": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 规则名称 |
| rule_type | string | 是 | 类型: `regex` 或 `code` |
| pattern | string | 否 | 正则表达式（regex类型必填） |
| code | string | 否 | Python代码片段（code类型必填） |
| priority | integer | 否 | 优先级，默认0 |
| enabled | boolean | 否 | 是否启用，默认true |

**响应** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Python异常提取",
    "rule_type": "regex",
    "pattern": "(\\w+Error): (.+)",
    "priority": 5,
    "enabled": true
  }
}
```

---

### 7. 规则管理 - 更新规则

**PUT** `/api/rules/{rule_id}`

**描述**: 更新解析规则

**请求**:
```json
{
  "name": "Python异常提取(更新)",
  "pattern": "(\\w+Exception): (.+)",
  "priority": 10,
  "enabled": true
}
```

---

### 8. 规则管理 - 删除规则

**DELETE** `/api/rules/{rule_id}`

**描述**: 删除解析规则（系统预置规则不可删除）

**响应** (200):
```json
{
  "success": true,
  "data": null
}
```

---

### 9. 忽略规则 - 获取列表

**GET** `/api/ignore-rules`

**描述**: 获取忽略规则列表

**响应** (200):
```json
{
  "success": true,
  "data": {
    "rules": [
      {
        "id": "uuid",
        "name": "忽略连接超时",
        "match_type": "contains",
        "pattern": "Connection timeout",
        "enabled": true
      }
    ]
  }
}
```

---

### 10. 忽略规则 - 创建

**POST** `/api/ignore-rules`

**描述**: 创建忽略规则

**请求**:
```json
{
  "name": "忽略连接超时",
  "match_type": "contains",
  "pattern": "Connection timeout",
  "enabled": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 规则名称 |
| match_type | string | 是 | 类型: `contains`, `regex`, `exact` |
| pattern | string | 是 | 匹配模式 |
| enabled | boolean | 否 | 是否启用，默认true |

---

### 11. 忽略规则 - 删除

**DELETE** `/api/ignore-rules/{rule_id}`

**描述**: 删除忽略规则

---

## 错误码汇总

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| INVALID_MODE | 400 | 无效的处理模式 |
| INVALID_RULE | 400 | 无效的规则定义 |
| RULE_EXECUTION_ERROR | 400 | 规则执行错误 |
| AI_SERVICE_ERROR | 502 | AI 服务调用失败 |
| LOG_NOT_FOUND | 404 | 日志条目不存在 |
| RULE_NOT_FOUND | 404 | 规则不存在 |
| SYSTEM_RULE_CANNOT_DELETE | 400 | 系统预置规则不可删除 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
