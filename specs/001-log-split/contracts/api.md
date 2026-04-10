# API Contracts: 日志文件切分

**Branch**: `001-log-split`
**Date**: 2026-04-10

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

### 1. 上传文件

**POST** `/api/upload`

**描述**: 上传日志文件，支持分片上传

**请求**:
- Content-Type: `multipart/form-data`
- Body:
  - `file`: 文件（二进制）
  - `chunk_index` (可选): 分片序号（从0开始）
  - `total_chunks` (可选): 总分片数
  - `upload_id` (可选): 上传ID（用于分片续传）

**响应** (200):
```json
{
  "success": true,
  "data": {
    "file_id": "uuid",
    "filename": "app.log",
    "file_size": 1048576,
    "encoding": "utf-8",
    "preview_lines": 100,
    "upload_id": "uuid"
  }
}
```

**错误码**:
- `INVALID_FILE_TYPE`: 非文本文件
- `FILE_TOO_LARGE`: 文件超过限制
- `ENCODING_DETECTION_FAILED`: 编码检测失败

---

### 2. 获取文件预览

**GET** `/api/files/{file_id}`

**描述**: 获取文件内容预览

**路径参数**:
- `file_id`: 文件UUID

**查询参数**:
- `lines` (可选): 预览行数，默认100

**响应** (200):
```json
{
  "success": true,
  "data": {
    "file_id": "uuid",
    "filename": "app.log",
    "total_lines": 5000,
    "preview": ["第1行内容", "第2行内容", "..."],
    "encoding": "utf-8"
  }
}
```

---

### 3. 执行切分

**POST** `/api/split`

**描述**: 对已上传的文件执行切分

**请求**:
```json
{
  "file_id": "uuid",
  "rule_type": "regex",
  "rule_content": "^\\d{4}-\\d{2}-\\d{2}"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_id | UUID | 是 | 文件ID |
| rule_type | string | 是 | 规则类型: `regex` 或 `fixed_string` |
| rule_content | string | 是 | 规则内容 |

**响应** (200):
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "status": "processing",
    "estimated_chunks": 150
  }
}
```

---

### 4. 获取切分状态

**GET** `/api/sessions/{session_id}`

**描述**: 查询切分任务状态

**路径参数**:
- `session_id`: 会话UUID

**响应** (200):
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "file_id": "uuid",
    "status": "processing",
    "total_chunks": 150,
    "processed_chunks": 75,
    "progress_percent": 50,
    "created_at": "2026-04-10T10:00:00Z",
    "updated_at": "2026-04-10T10:01:00Z"
  }
}
```

**状态值**:
- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

---

### 5. 获取切分结果

**GET** `/api/results/{session_id}`

**描述**: 获取切分结果（分页）

**路径参数**:
- `session_id`: 会话UUID

**查询参数**:
- `page` (可选): 页码，默认1
- `page_size` (可选): 每页数量，默认100，最大1000

**响应** (200):
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "status": "completed",
    "total_chunks": 150,
    "page": 1,
    "page_size": 100,
    "total_pages": 2,
    "results": [
      {
        "chunk_index": 1,
        "start_line": 1,
        "end_line": 50,
        "content": "片段内容..."
      }
    ]
  }
}
```

---

### 6. 获取单个结果详情

**GET** `/api/results/{session_id}/chunks/{chunk_index}`

**描述**: 获取单个切分片段的完整内容

**路径参数**:
- `session_id`: 会话UUID
- `chunk_index`: 片段序号

**响应** (200):
```json
{
  "success": true,
  "data": {
    "chunk_index": 1,
    "start_line": 1,
    "end_line": 50,
    "content": "完整的片段内容...",
    "line_count": 50
  }
}
```

---

### 7. 校验正则表达式

**POST** `/api/validate/regex`

**描述**: 校验正则表达式语法是否正确

**请求**:
```json
{
  "pattern": "^\\d{4}-\\d{2}-\\d{2}"
}
```

**响应** (200):
```json
{
  "success": true,
  "data": {
    "valid": true,
    "sample_matches": 5
  }
}
```

**错误响应** (400):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REGEX",
    "message": "正则表达式语法错误"
  }
}
```

---

## 错误码汇总

| 错误码 | HTTP状态码 | 说明 |
|--------|------------|------|
| INVALID_FILE_TYPE | 400 | 非文本文件 |
| FILE_TOO_LARGE | 400 | 文件超过100MB |
| ENCODING_DETECTION_FAILED | 400 | 编码检测失败 |
| INVALID_REGEX | 400 | 正则表达式语法错误 |
| FILE_NOT_FOUND | 404 | 文件不存在 |
| SESSION_NOT_FOUND | 404 | 会话不存在 |
| CHUNK_NOT_FOUND | 404 | 片段不存在 |
| SPLIT_IN_PROGRESS | 409 | 切分任务进行中 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
