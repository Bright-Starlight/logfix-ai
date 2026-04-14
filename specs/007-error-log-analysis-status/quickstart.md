# Quickstart: 错误日志修复计划状态

**Branch**: `007-error-log-analysis-status` | **Date**: 2026-04-14

## 1. 功能概述

为错误日志添加AI修复计划分析功能：
- 状态UI：未分析 → 分析中 → 分析完成/分析失败
- 操作按钮：根据状态显示不同操作
- AI排队分析：最大5个任务排队

## 2. 快速开始

### 2.1 前置条件

1. 已导入代码仓库（Repository表有有效记录）
2. 日志已完成分类

### 2.2 用户流程

```
1. 用户在日志列表看到每条日志的状态标签
2. 未分析的日志显示"生成修复计划"按钮
3. 点击后状态变为"分析中"（如队列有任务则显示"排队中"）
4. AI分析完成后，状态变为"分析完成"
5. 用户点击"查看修复计划"查看结果
```

## 3. 数据库迁移

```sql
-- 1. 添加 analysis_status 字段到 log_entries
ALTER TABLE log_entries ADD COLUMN analysis_status VARCHAR(20) NOT NULL DEFAULT 'un_analyzed';

-- 2. 创建 analysis_sessions 表
CREATE TABLE analysis_sessions (
    id BIGSERIAL PRIMARY KEY,
    log_entry_id BIGINT NOT NULL REFERENCES log_entries(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    queue_position INT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_analysis_session_log_entry ON analysis_sessions(log_entry_id);
CREATE INDEX idx_analysis_session_status ON analysis_sessions(status);

-- 3. 创建 fix_plans 表
CREATE TABLE fix_plans (
    id BIGSERIAL PRIMARY KEY,
    log_entry_id BIGINT NOT NULL UNIQUE REFERENCES log_entries(id),
    session_id BIGINT REFERENCES analysis_sessions(id),
    root_cause TEXT NOT NULL,
    fix_steps JSONB NOT NULL,
    code_locations JSONB NOT NULL,
    confidence FLOAT NOT NULL,
    impact_assessment TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fix_plan_log_entry ON fix_plans(log_entry_id);
```

## 4. 核心文件变更

### 后端新增

| 文件 | 说明 |
|------|------|
| `backend/src/models/entities.py` | 新增 AnalysisSession, FixPlan 实体 |
| `backend/src/services/analysis_queue.py` | 分析任务队列管理 |
| `backend/src/services/fix_plan_service.py` | 修复计划生成服务 |
| `backend/src/api/routes.py` | 新增分析相关API端点 |

### 前端新增/修改

| 文件 | 说明 |
|------|------|
| `frontend/src/components/FixPlanViewer.tsx` | 修复计划查看组件 |
| `frontend/src/components/AnalysisProgress.tsx` | 分析进度组件 |
| `frontend/src/hooks/useAnalysisProgress.ts` | 分析进度监听hook |
| `frontend/src/hooks/useAnalysisQueue.ts` | 队列状态管理hook |
| `frontend/src/components/LogList.tsx` | 扩展：添加状态标签和按钮 |
| `frontend/src/types/index.ts` | 新增相关类型定义 |

## 5. API调用示例

### 启动分析

```bash
curl -X POST http://localhost:8000/api/analysis/start \
  -H "Content-Type: application/json" \
  -d '{"log_entry_id": 12345}'
```

### 获取修复计划

```bash
curl http://localhost:8000/api/analysis/fix-plan/12345
```

### SSE进度流

```bash
curl -N http://localhost:8000/api/analysis/stream/session123
```

## 6. 测试验证

```bash
# 后端测试
pytest backend/tests/unit/test_analysis_queue.py
pytest backend/tests/integration/test_analysis_api.py

# 前端测试
cd frontend && npm test -- --run
```

## 7. 配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| ANALYSIS_QUEUE_MAX_SIZE | 5 | 队列最大长度 |
| AI_BATCH_SIZE | 10 | AI分析批次大小 |
| ANALYSIS_TIMEOUT | 无限制 | 分析超时时间（毫秒） |
