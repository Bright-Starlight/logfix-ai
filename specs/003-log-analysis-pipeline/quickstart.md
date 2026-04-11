# 003 日志分析流水线 - 集成测试指南

## 概述

本文档描述如何测试 003 功能集成（日志分析完整流程）。

## 前置条件

1. **后端服务运行中**（端口 8000）
   ```bash
   cd backend && uvicorn src.main:app --reload --port 8000
   ```

2. **前端开发服务器运行中**（端口 5173）
   ```bash
   cd frontend && npm run dev
   ```

3. **数据库已初始化**
   ```bash
   cd backend && python -m src.db.init_db
   ```

4. **准备测试日志文件**
   创建包含多种错误类型的测试日志文件，例如：
   ```
   2026-04-11 10:00:00 INFO Application started
   2026-04-11 10:00:01 ERROR Division by zero at line 10
   2026-04-11 10:00:02 ERROR Null pointer exception
   2026-04-11 10:00:03 WARNING Connection timeout
   2026-04-11 10:00:04 ERROR Division by zero at line 20
   2026-04-11 10:00:05 INFO Request processed
   ```

## 集成测试流程

### 步骤 1：上传日志文件

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.log"
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "file_id": "<uuid>",
    "filename": "test.log",
    "file_size": 256,
    "encoding": "utf-8",
    "preview_lines": 6,
    "upload_id": "<uuid>"
  }
}
```

记录返回的 `file_id`。

### 步骤 2：执行切分

```bash
curl -X POST http://localhost:8000/api/split \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "<file_id>",
    "rule_type": "regex",
    "rule_content": "^\\d{4}-\\d{2}-\\d{2}"
  }'
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "session_id": "<session_id>",
    "status": "completed",
    "estimated_chunks": 6
  }
}
```

记录返回的 `session_id`（这是 split_session_id）。

### 步骤 3：获取切分结果

```bash
curl "http://localhost:8000/api/sessions/<split_session_id>"
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "session_id": "<session_id>",
    "status": "completed",
    "total_chunks": 6,
    "processed_chunks": 6,
    "progress_percent": 100
  }
}
```

### 步骤 4：启动分类流程（规则引擎模式）

```bash
curl -X POST http://localhost:8000/api/classification/start \
  -H "Content-Type: application/json" \
  -d '{
    "split_session_id": "<split_session_id>",
    "mode": "rule_engine"
  }'
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "session_id": "<classification_session_id>",
    "status": "pending"
  }
}
```

记录返回的 `session_id`（这是 classification_session_id）。

### 步骤 5：轮询进度（关键测试点）

```bash
# 立即查询（应该是 pending 或刚开始 processing）
curl "http://localhost:8000/api/classification/<classification_session_id>/progress"

# 等待2秒后再查询
sleep 2
curl "http://localhost:8000/api/classification/<classification_session_id>/progress"

# 继续轮询直到完成
sleep 2
curl "http://localhost:8000/api/classification/<classification_session_id>/progress"
```

**预期进度响应**:
```json
{
  "success": true,
  "data": {
    "session_id": "<classification_session_id>",
    "status": "processing",
    "total_items": 6,
    "processed_items": 3,
    "current_phase": "去重检测中",
    "estimated_remaining_seconds": 2,
    "progress_percent": 50
  }
}
```

**验证点**:
- `progress_percent` 随时间增长
- `current_phase` 随处理阶段变化
- `processed_items` 逐渐接近 `total_items`

**完成响应**:
```json
{
  "success": true,
  "data": {
    "session_id": "<classification_session_id>",
    "status": "completed",
    "total_items": 6,
    "processed_items": 6,
    "current_phase": "完成",
    "estimated_remaining_seconds": 0,
    "progress_percent": 100
  }
}
```

### 步骤 6：查看分类结果

```bash
curl "http://localhost:8000/api/logs?page=1&page_size=50"
```

**预期响应**:
```json
{
  "success": true,
  "data": {
    "total": 4,
    "page": 1,
    "page_size": 50,
    "total_pages": 1,
    "entries": [
      {
        "id": "<entry_id>",
        "normalized_message": "Division by zero",
        "category": "异常错误",
        "error_type": "division_by_zero",
        "occurrence_count": 2,
        ...
      },
      ...
    ]
  }
}
```

**验证点**:
- `total` 应该小于等于切分片段数（因为去重）
- "Division by zero" 出现2次但只显示1条记录（去重生效）

### 步骤 7：测试 AI 模式

```bash
curl -X POST http://localhost:8000/api/classification/start \
  -H "Content-Type: application/json" \
  -d '{
    "split_session_id": "<split_session_id>",
    "mode": "ai"
  }'
```

**验证点**:
- AI 模式能正常启动
- 进度能正常更新（AI 模式可能更慢）

### 步骤 8：测试错误恢复

在分类过程中刷新页面，验证：
1. 进度条能恢复显示当前实际进度
2. 不从头开始重新处理

## 前端 UI 测试

### 访问流水线页面

1. 打开浏览器访问 `http://localhost:5173/pipeline`
2. 或访问首页 `http://localhost:5173` 导航到流水线页面

### 验证进度条

1. 上传文件 → 执行切分 → 选择分类模式
2. 观察进度条是否实时更新
3. 刷新页面，验证进度条恢复而非重置

## 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 进度一直显示 pending | 分类任务未启动 | 检查 `classification_service.py` 是否正确更新状态 |
| 进度为 0% | 数据库会话未提交 | 检查事务是否正确提交 |
| AI 模式超时 | API Key 配置错误 | 检查 `.env` 文件中的 `ANTHROPIC_API_KEY` |
| 分类结果为空 | 切分片段未传递给分类 | 检查 `split_session_id` 是否正确传递 |
