# Flow: 错误日志修复计划状态

**Branch**: `007-error-log-analysis-status` | **Date**: 2026-04-14

## 代码执行流程图

### 用户点击"生成修复计划"按钮

```mermaid
sequenceDiagram
    participant 用户
    participant 前端 as LogList组件
    participant API as /api/analysis/start
    participant 队列 as AnalysisQueue
    participant 服务 as FixPlanService
    participant AI as AI Agent

    用户->>前端: 点击"生成修复计划"按钮
    前端->>API: POST /api/analysis/start {log_entry_id}

    alt 检查仓库是否存在
        API->>API: 查询Repository表
        alt 无有效仓库
            API-->>前端: 400 NO_REPOSITORY
            前端-->>用户: 提示"请先导入代码仓库"
        else 有有效仓库
            API->>队列: 检查队列是否已满
            alt 队列已满（≥5个任务）
                API-->>前端: 409 QUEUE_FULL
                前端-->>用户: 提示"队列已满，请稍后重试"
            else 队列未满
                API->>队列: enqueue(log_entry_id)
                队列->>数据库: 创建AnalysisSession(queued)
                API-->>前端: 200 {session_id, status: queued}
                前端-->>用户: 显示"排队中"状态

                Note over 队列: 后台：队列处理器

                alt 队列首个任务
                    队列->>服务: dequeue() -> log_entry_id
                    服务->>服务: 更新状态为processing
                    服务->>AI: 调用generate_fix_plan工具
                    AI-->>服务: 返回修复计划结果

                    alt 分析成功
                        服务->>数据库: 创建FixPlan记录
                        服务->>服务: 更新log_entry.analysis_status=completed
                        服务->>队列: 取出下一任务继续处理
                    else 分析失败
                        服务->>服务: 更新log_entry.analysis_status=failed
                        服务->>队列: 取出下一任务继续处理
                    end
                end
            end
        end
    end
```

### SSE进度监听流程

```mermaid
sequenceDiagram
    participant 前端 as useAnalysisProgress
    participant SSE as /api/analysis/stream/{session_id}
    participant 后端 as AI分析服务

    前端->>SSE: GET /api/analysis/stream/{session_id}

    loop 分析进行中
        后端-->>前端: event: progress<br/>{processed, total, percentage, current_phase}
        前端->>前端: 更新进度状态
        前端->>前端: 刷新UI显示
    end

    alt 分析完成
        后端-->>前端: event: result<br/>{root_cause, fix_steps, ...}
        后端-->>前端: event: done<br/>{status: completed}
        前端->>前端: 更新状态为completed
    else 分析失败
        后端-->>前端: event: error<br/>{code, message}
        前端->>前端: 更新状态为failed
    end
```

### 分析状态转换

```mermaid
stateDiagram-v2
    [*] --> un_analyzed: 日志创建
    un_analyzed --> analyzing: 点击"生成修复计划"
    analyzing --> queued: 加入队列（队列非空）
    queued --> processing: 队列轮到执行
    analyzing --> completed: 分析完成
    queued --> completed: 分析完成
    processing --> completed: 分析完成
    analyzing --> failed: 分析失败
    queued --> failed: 分析失败
    processing --> failed: 分析失败
    queued --> cancelled: 用户取消
    completed --> un_analyzed: 重新分析
    failed --> un_analyzed: 重新分析
    cancelled --> un_analyzed: 重新分析
```

### 队列状态管理

```mermaid
flowchart TD
    A[用户点击生成修复计划] --> B{队列是否已满?}
    B -->|是| C[返回QUEUE_FULL错误]
    B -->|否| D[创建AnalysisSession]
    D --> E[状态设为queued]
    E --> F[加入队列]

    subgraph 队列处理
        F --> G{队列是否为空?}
        G -->|否| H[等待执行]
        G -->|是| I[取出任务]
        I --> J[状态设为processing]
        J --> K[调用AI分析]
        K --> L{分析是否成功?}
        L -->|是| M[创建FixPlan]
        L -->|否| N[标记failed]
        M --> O[更新log_entry状态]
        N --> O
        O --> P[取出下一任务]
        P --> G
    end

    C --> Q[提示用户稍后重试]
```

## 关键函数调用链

### 后端

```
POST /api/analysis/start
  └─> check_repository()
  └─> analysis_queue.enqueue()
        └─> db.create(AnalysisSession)
  └─> return {session_id, status, queue_position}

GET /api/analysis/status/{log_entry_id}
  └─> db.query(LogEntry, analysis_status)
  └─> db.query(AnalysisSession, status, queue_position)
  └─> return {analysis_status, session_id, queue_position, progress_percent}

GET /api/analysis/fix-plan/{log_entry_id}
  └─> db.query(FixPlan, log_entry_id)
  └─> return FixPlan or 404

POST /api/analysis/cancel/{log_entry_id}
  └─> db.query(AnalysisSession, queued, log_entry_id)
  └─> update status=cancelled
  └─> return {cancelled}

GET /api/analysis/stream/{session_id}
  └─> SSE stream
        ├─> progress: 定期推送进度
        ├─> result: 修复计划结果
        ├─> error: 错误信息
        └─> done: 完成状态
```

### 前端

```
useAnalysisProgress
  ├─> startAnalysis(log_entry_id): 调用start API
  ├─> getStatus(log_entry_id): 轮询状态
  └─> subscribeStream(session_id): SSE订阅

useAnalysisQueue
  ├─> enqueue(log_entry_id): 添加到队列状态
  ├─> dequeue(): 从队列移除
  └─> getQueuePosition(): 获取位置

LogList
  ├─> 显示analysis_status标签
  ├─> 根据状态显示不同按钮
  └─> 点击按钮调用对应action
```
