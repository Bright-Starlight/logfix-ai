# Research: 错误日志修复计划状态

**Branch**: `007-error-log-analysis-status` | **Date**: 2026-04-14

## 1. AI Agent 修复计划生成扩展

### 现有系统分析

现有 `ai_analyzer.py` 使用 MiniMax-M2.7 模型，Tool Call 模式：
- 工具名：`classify_log`
- 返回：category, error_type, normalized_message, extracted_params

### 修复计划生成方案

**扩展方案**：新增 `generate_fix_plan` 工具

```json
{
  "type": "function",
  "function": {
    "name": "generate_fix_plan",
    "description": "基于错误日志和代码仓库分析，生成修复计划",
    "parameters": {
      "type": "object",
      "properties": {
        "root_cause": {
          "type": "string",
          "description": "问题根因分析"
        },
        "fix_steps": {
          "type": "array",
          "items": {"type": "string"},
          "description": "修复步骤建议列表"
        },
        "code_locations": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "file_path": {"type": "string"},
              "line_range": {"type": "string"},
              "description": {"type": "string"}
            }
          },
          "description": "相关代码位置列表"
        },
        "confidence": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "description": "置信度 0-1"
        },
        "impact_assessment": {
          "type": "string",
          "description": "影响范围评估"
        }
      },
      "required": ["root_cause", "fix_steps", "code_locations", "confidence", "impact_assessment"]
    }
  }
}
```

### AI上下文获取

AI需要读取代码仓库内容进行上下文分析：
1. 从错误日志提取关键信息（error_type, stack_trace）
2. 根据error_type或关键词搜索相关代码文件
3. 将相关代码片段作为上下文提供给AI分析

**实现方式**：
- 使用 Python 的 `glob` 和文件读取获取仓库代码
- 限制搜索范围（只读相关文件，避免token溢出）
- 代码片段截断保留关键部分

## 2. 任务队列实现方案

### 方案选择

**推荐方案**：asyncio.Queue + 数据库持久化

原因：
- 现有项目已使用 asyncio，无需引入外部依赖（Celery等）
- 队列状态持久化到数据库，支持页面刷新后恢复
- 实现简单，适合单用户场景

### 队列设计

```python
class AnalysisQueue:
    """分析任务队列（内存+数据库双写）"""

    def __init__(self, max_size=5):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._max_size = max_size

    async def enqueue(self, log_entry_id: int) -> bool:
        """入队，返回是否成功"""
        if self._queue.full():
            return False  # 队列满，拒绝

        # 持久化到数据库
        session = AnalysisSession(
            log_entry_id=log_entry_id,
            status="queued"
        )
        await db.add(session)
        await self._queue.put(session.id)
        return True

    async def dequeue(self) -> Optional[int]:
        """出队，返回log_entry_id"""
        session_id = await self._queue.get()
        # 更新数据库状态为processing
        session = await db.get(AnalysisSession, session_id)
        session.status = "processing"
        return session.log_entry_id

    async def cancel(self, log_entry_id: int) -> bool:
        """取消任务"""
        session = await db.query(
            AnalysisSession,
            log_entry_id=log_entry_id,
            status="queued"
        )
        if session:
            session.status = "cancelled"
            return True
        return False
```

### 状态持久化策略

```sql
-- 分析会话表
CREATE TABLE analysis_sessions (
    id BIGINT PRIMARY KEY,
    log_entry_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,  -- queued/processing/completed/failed/cancelled
    queue_position INT,
    created_at DATETIME,
    started_at DATETIME,
    completed_at DATETIME
);
```

### 与现有ClassificationSession的关系

现有 `ClassificationSession` 用于日志分类进度跟踪。
新的 `AnalysisSession` 用于修复计划分析任务跟踪。
两者独立，分别服务于不同功能。

## 3. 决策总结

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 修复计划生成 | 扩展Tool Call，新增`generate_fix_plan` | 保持现有架构一致 |
| AI上下文获取 | 代码仓库文件搜索+片段提取 | 无需额外API |
| 任务队列 | asyncio.Queue + 数据库持久化 | 轻量级，适合现有架构 |
| 队列满处理 | 拒绝入队，提示用户 | FR-011明确要求 |
| 任务取消 | 仅支持排队中任务取消 | 已在规格明确 |

## 4. 替代方案考虑

### 替代方案A：独立队列服务（Celery）
- 优点：支持分布式、持久化、监控
- 缺点：引入额外依赖，增加部署复杂度
- 结论：不采用，项目规模不需要

### 替代方案B：数据库队列表
- 优点：完全持久化，无内存丢失风险
- 缺点：轮询效率低，不支持实时通知
- 结论：asyncio.Queue+数据库双写更平衡
