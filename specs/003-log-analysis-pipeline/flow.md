# 代码执行流程图: 日志分析完整流程集成

**Feature**: 003-log-analysis-pipeline
**Created**: 2026-04-11

## 整体流程概览

```mermaid
flowchart TD
    subgraph 前端["前端"]
        A1[上传文件] --> A2[选择切分规则]
        A2 --> A3[执行切分]
        A3 --> A4{切分状态}
        A4 -->|进行中| A5[显示切分进度]
        A4 -->|已完成| A6[显示分类模式选择]
        A6 --> A7[用户选择模式]
        A7 --> A8[启动分类]
        A8 --> A9[显示进度条]
        A9 --> A10{处理状态}
        A10 -->|进行中| A11[更新进度]
        A10 -->|完成| A12[显示结果摘要]
        A11 --> A9
    end

    subgraph 后端["后端 API"]
        B1[POST /api/upload] --> B2[文件存储]
        B2 --> B3[POST /api/split]
        B3 --> B4[切分处理]
        B4 --> B5[保存切分结果]
        B5 --> B6[POST /api/classification/start]
        B6 --> B7[创建分类会话]
        B7 --> B8[GET /api/classification/progress]
        B8 --> B9[分类处理循环]
        B9 --> B10[去重检测]
        B10 --> B11[忽略规则过滤]
        B11 --> B12[分类分析]
        B12 --> B13[结构化存储]
        B13 --> B14[更新进度]
        B14 --> B15{处理完成?}
        B15 -->|否| B9
        B15 -->|是| B16[GET /api/classification/result]
    end

    A3 -->|调用| B3
    A8 -->|调用| B6
    A9 -->|轮询2秒| B8
    A12 -->|查询| B16
```

## 用户故事 1: 完整日志分析流程

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as 后端
    participant DB as 数据库

    U->>F: 上传日志文件
    F->>B: POST /api/upload
    B->>DB: 保存文件记录
    DB-->>B: file_id
    B-->>F: 上传成功
    F-->>U: 显示文件预览

    U->>F: 选择切分规则
    U->>F: 点击切分
    F->>B: POST /api/split
    B->>B: 执行切分逻辑
    B->>DB: 保存切分结果
    DB-->>B: session_id
    B-->>F: 切分完成
    F-->>U: 显示切分结果

    U->>F: 选择分类模式
    U->>F: 点击开始分类
    F->>B: POST /api/classification/start
    B->>DB: 创建分类会话
    DB-->>B: classification_session_id
    B-->>F: 启动成功

    loop 每2秒轮询
        F->>B: GET /api/classification/progress
        B-->>F: 进度数据
        F-->>U: 更新进度条
    end

    B->>B: 分类处理循环
    B->>DB: 去重检测
    B->>DB: 忽略规则过滤
    B->>DB: 分类分析
    B->>DB: 存储结果

    B-->>F: 处理完成
    F-->>U: 显示结果摘要

    U->>F: 查看日志列表
    F->>B: GET /api/logs
    B-->>F: 日志列表
    F-->>U: 显示日志列表
```

## 用户故事 2.1: 后台处理进度显示

```mermaid
stateDiagram-v2
    [*] --> 等待中
    等待中 --> 处理中: 开始处理第一条日志
    处理中 --> 处理中: 处理中持续更新进度

    处理中 --> 去重检测: 进入去重阶段
    去重检测 --> 忽略规则过滤: 去重完成
    忽略规则过滤 --> 分类分析: 过滤完成
    分类分析 --> 存储: 分析完成
    存储 --> 处理中: 更新进度

    处理中 --> 已完成: 所有日志处理完毕
    处理中 --> 失败: 发生错误

    已完成 --> [*]
    失败 --> [*]
```

## 分类处理内部流程

```mermaid
flowchart LR
    subgraph 输入
        I1[切分结果片段]
    end

    subgraph 处理阶段
        P1[去重检测]
        P2[忽略规则过滤]
        P3[分类分析]
        P4[结构化存储]
    end

    subgraph 输出
        O1[新增日志条目]
        O2[更新重复计数]
        O3[被忽略日志]
    end

    I1 --> P1
    P1 -->|新增| O1
    P1 -->|重复| O2
    P1 --> P2
    P2 -->|不忽略| P3
    P2 -->|忽略| O3
    P3 --> P4
    P4 --> O1
```

## 进度跟踪流程

```mermaid
flowchart TD
    A[启动分类] --> B[初始化进度状态]
    B --> C[设置 total_items]
    C --> D[更新状态为 processing]
    D --> E{处理每个日志}

    E -->|处理中| F[更新 processed_items]
    F --> G[计算预估剩余时间]
    G --> H[更新 current_phase]

    H --> E
    E -->|所有日志处理完| I[更新状态为 completed]
    I --> J[记录 completed_at]

    E -->|发生错误| K[更新状态为 failed]
    K --> L[记录 error_message]

    J --> M[返回处理结果]
    L --> M
```

## 前端组件交互流程

```mermaid
flowchart TD
    P["AnalysisPipeline页面"]
    F1["FileUpload"]
    F2["SplitConfig"]
    F3["ResultList"]
    F4["ClassificationModeSelect"]
    F5["ProgressBar"]
    F6["LogList"]
    H1["useClassificationProgress"]
    A1["POST upload"]
    A2["POST split"]
    A3["POST classification/start"]
    A4["GET classification/progress"]
    A5["GET logs"]

    P --> F1
    P --> F2
    P --> F3
    P --> F4
    P --> F5
    P --> F6

    F1 --> A1
    F2 --> A2
    F3 --> A2
    F4 --> A3
    F5 --> H1
    H1 --> A4
    F6 --> A5
```

## 关键数据流

```mermaid
flowchart LR
    subgraph 文件上传
        L1[本地文件] --> L2[file_id]
    end

    subgraph 切分
        L2 --> S1[切分规则]
        S1 --> S2[切分结果]
        S2 --> S3[session_id]
    end

    subgraph 分类
        S3 --> C1[mode: rule_engine/ai]
        C1 --> C2[classification_session_id]
        C2 --> C3[progress 轮询]
        C3 --> C4[分类结果]
    end

    subgraph 展示
        C4 --> D1[LogList 组件]
        C4 --> D2[StatsPanel 组件]
    end
```

## 错误处理流程

```mermaid
flowchart TD
    A[分类处理] --> B{发生错误?}

    B -->|否| C[继续处理]
    B -->|是| D[记录错误信息]

    D --> E{错误类型}
    E -->|AI超时| F[降级到规则引擎]
    E -->|数据库错误| G[重试机制]
    E -->|其他| H[标记为失败]

    F --> C
    G --> C
    H --> I[更新状态为 failed]

    I --> J[前端显示错误]
    J --> K[用户可重新选择模式]
```

## 进度更新时序

```mermaid
sequenceDiagram
    participant F as 前端
    participant H as useClassificationProgress Hook
    participant B as 后端

    Note over H: 初始化状态: pending

    H->>B: GET /api/classification/progress
    B-->>H: status: "processing", progress: 0%
    H->>F: 更新状态
    Note over F: 显示进度条 0%

    loop 每2秒
        H->>B: GET /api/classification/progress
        B-->>H: status: "processing", progress: 35%, phase: "去重检测中"
        H->>F: 更新状态
        Note over F: 显示进度条 35%, 阶段: 去重检测中
    end

    H->>B: GET /api/classification/progress
    B-->>H: status: "completed", progress: 100%
    H->>F: 更新状态
    H->>F: 停止轮询
    Note over F: 显示完成状态
```
