# API Contracts: 错误日志修复计划状态

**Branch**: `007-error-log-analysis-status` | **Date**: 2026-04-14

## 1. 概述

本文档定义修复计划功能的API契约。前后端通过REST API + SSE进行通信。

**基础路径**: `/api`

## 2. REST API

### 2.1 启动分析任务

```
POST /api/analysis/start
```

**请求体**:
```json
{
  "log_entry_id": 12345
}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "session_id": "abc123",
    "status": "queued",
    "queue_position": 1
  },
  "error": null
}
```

**队列满响应** (409):
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "QUEUE_FULL",
    "message": "分析队列已满，请稍后重试"
  }
}
```

**无仓库响应** (400):
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NO_REPOSITORY",
    "message": "请先导入代码仓库"
  }
}
```

### 2.2 获取分析状态

```
GET /api/analysis/status/{log_entry_id}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "log_entry_id": 12345,
    "analysis_status": "analyzing",
    "session_id": "abc123",
    "queue_position": null,
    "progress_percent": 45,
    "current_phase": "搜索相关代码"
  },
  "error": null
}
```

### 2.3 获取修复计划

```
GET /api/analysis/fix-plan/{log_entry_id}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "log_entry_id": 12345,
    "root_cause": "空指针异常发生在 UserService.java:45",
    "fix_steps": [
      "在第43行添加空值检查",
      "在第45行使用 Optional.ofNullable() 包装"
    ],
    "code_locations": [
      {
        "file_path": "src/main/java/com/example/UserService.java",
        "line_range": "40-50",
        "description": "问题代码位置"
      }
    ],
    "confidence": 0.85,
    "impact_assessment": "影响用户登录功能",
    "created_at": "2026-04-14T10:30:00Z"
  },
  "error": null
}
```

**未完成响应** (404):
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "FIX_PLAN_NOT_READY",
    "message": "修复计划尚未生成"
  }
}
```

### 2.4 取消分析任务

```
POST /api/analysis/cancel/{log_entry_id}
```

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "cancelled": true
  },
  "error": null
}
```

**无法取消响应** (400):
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "CANNOT_CANCEL",
    "message": "任务已在执行中，无法取消"
  }
}
```

### 2.5 SSE：分析进度流

```
GET /api/analysis/stream/{session_id}
```

**SSE事件类型**:

1. **progress**:
```
event: progress
data: {"processed": 5, "total": 10, "percentage": 50, "current_phase": "分析代码上下文"}
```

2. **result**:
```
event: result
data: {"root_cause": "...", "fix_steps": [...], "code_locations": [...], "confidence": 0.85, "impact_assessment": "..."}
```

3. **error**:
```
event: error
data: {"code": "AI_ERROR", "message": "AI分析失败"}
```

4. **done**:
```
event: done
data: {"status": "completed", "total_time_ms": 15000}
```

## 3. 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| QUEUE_FULL | 409 | 队列已满 |
| NO_REPOSITORY | 400 | 未导入仓库 |
| LOG_ENTRY_NOT_FOUND | 404 | 日志条目不存在 |
| FIX_PLAN_NOT_READY | 404 | 修复计划未生成 |
| CANNOT_CANCEL | 400 | 无法取消（已在执行） |
| AI_ERROR | 500 | AI分析错误 |
| INTERNAL_ERROR | 500 | 内部错误 |

## 4. 前端类型定义

```typescript
type AnalysisStatus = 'un_analyzed' | 'analyzing' | 'completed' | 'failed'

interface FixPlan {
  log_entry_id: string
  root_cause: string
  fix_steps: string[]
  code_locations: Array<{
    file_path: string
    line_range: string
    description: string
  }>
  confidence: number
  impact_assessment: string
  created_at: string
}

interface AnalysisProgress {
  log_entry_id: string
  analysis_status: AnalysisStatus
  session_id: string | null
  queue_position: number | null
  progress_percent: number
  current_phase: string
}
```
