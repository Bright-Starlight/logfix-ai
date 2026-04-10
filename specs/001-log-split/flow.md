# 代码执行流程图：日志文件切分

**Feature**: `001-log-split`
**Date**: 2026-04-10

> 根据宪法 VII. 代码执行流程图 要求，必须使用 Mermaid 语法绘制流程图，所有文字内容必须使用中文。

## 1. 用户交互流程

```mermaid
flowchart TD
    A[用户打开应用] --> B[上传日志文件]
    B --> C{文件上传成功?}
    C -->|是| D[显示文件预览]
    C -->|否| E[显示错误提示]
    E --> B
    D --> F[配置切分规则]
    F --> G{规则类型}
    G -->|正则表达式| H[输入正则表达式]
    G -->|固定分隔符| I[输入分隔符]
    H --> J{正则校验}
    I --> J
    J -->|通过| K[执行切分]
    J -->|失败| L[显示错误提示]
    L --> F
    K --> M[轮询切分状态]
    M --> N{切分完成?}
    N -->|否| M
    N -->|是| O[显示切分结果]
    O --> P[查看片段详情]
    P --> Q[复制片段内容]
    Q --> R[显示已复制提示]
    R --> P
```

## 2. 前端组件状态转换

```mermaid
stateDiagram-v2
    [*] --> FileUpload: 用户打开应用

    FileUpload --> LogPreview: 文件上传成功
    LogPreview --> SplitConfig: 用户配置规则
    SplitConfig --> SplitConfig: 校验失败
    SplitConfig --> ResultList: 切分完成
    ResultList --> FileUpload: 上传新文件

    FileUpload --> [*]: 用户关闭应用
    ResultList --> [*]: 用户关闭应用
```

## 3. API 请求响应链

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端组件
    participant A as FastAPI后端
    participant D as PostgreSQL

    U->>F: 选择文件
    F->>A: POST /api/upload
    A->>D: 保存文件元数据
    D-->>A: 返回file_id
    A-->>F: 返回上传结果
    F-->>U: 显示预览

    U->>F: 输入正则表达式
    F->>A: POST /api/validate/regex
    A-->>F: 返回校验结果

    U->>F: 点击开始切分
    F->>A: POST /api/split
    A->>D: 创建切分会话
    D-->>A: 返回session_id
    A-->>F: 返回session_id

    loop 每2秒轮询
        F->>A: GET /api/sessions/{session_id}
        A-->>F: 返回状态
    end

    A->>D: 执行切分
    D-->>A: 保存结果
    A-->>F: 状态变为completed

    U->>F: 查看结果
    F->>A: GET /api/results/{session_id}
    A-->>F: 返回分页结果

    U->>F: 点击片段
    F->>A: GET /api/results/{session_id}/chunks/{index}
    A-->>F: 返回片段详情
```

## 4. 数据流

```mermaid
flowchart LR
    subgraph 前端
        A[FileUpload] --> B[LogPreview]
        B --> C[SplitConfig]
        C --> D[ResultList]
    end

    subgraph 后端服务
        E[文件上传服务] --> F[编码检测服务]
        F --> G[切分服务]
        G --> H[结果存储服务]
    end

    subgraph 数据库
        I[(LogFile表)]
        J[(SplitSession表)]
        K[(SplitResult表)]
    end

    A -->|multipart/form-data| E
    E -->|file_id| I
    I -->|文件路径| F
    F -->|编码| I
    G -->|session_id| J
    J -->|chunk数据| K
    C -->|API调用| G
    D -->|API调用| G
```

## 5. 核心模块依赖关系

```mermaid
flowchart TB
    subgraph 入口层
        A[backend/src/main.py]
    end

    subgraph API层
        B[backend/src/api/routes.py]
    end

    subgraph 服务层
        C[backend/src/services/file_handler.py]
        D[backend/src/services/splitter.py]
        E[backend/src/services/log_service.py]
    end

    subgraph 数据层
        F[backend/src/db/session.py]
        G[backend/src/models/entities.py]
    end

    A --> B
    B --> C
    B --> D
    B --> E
    C --> F
    C --> G
    D --> F
    D --> G
    E --> F
```

## 6. 用户完整操作时序

```mermaid
sequenceDiagram
    participant U as 用户
    participant FE as 前端
    participant BE as 后端
    participant DB as 数据库
    participant FS as 文件系统

    U->>FE: 打开应用
    FE-->>U: 显示上传界面

    U->>FE: 选择.log文件
    FE->>FE: 本地文件验证
    FE->>BE: POST /api/upload
    BE->>FS: 保存文件到storage_path
    BE->>DB: 插入LogFile记录
    DB-->>BE: file_id
    BE-->>FE: {file_id, preview_lines}
    FE->>BE: GET /api/files/{file_id}
    BE->>FS: 读取文件前100行
    BE-->>FE: 文件预览内容
    FE-->>U: 显示文件预览

    U->>FE: 输入正则表达式
    FE->>BE: POST /api/validate/regex
    BE->>BE: 正则语法校验
    BE-->>FE: {valid: true, sample_matches: 5}

    U->>FE: 点击开始切分
    FE->>BE: POST /api/split
    BE->>DB: 创建SplitSession记录
    DB-->>BE: session_id
    BE-->>FE: {session_id, status: processing}
    FE-->>U: 显示进度条

    loop 每2秒
        FE->>BE: GET /api/sessions/{session_id}
        BE-->>FE: {progress_percent: 50}
    end

    BE->>FS: 读取完整文件
    BE->>BE: 按规则切分
    BE->>DB: 批量插入SplitResult
    BE->>DB: 更新Session状态为completed
    BE-->>FE: status: completed

    FE->>BE: GET /api/results/{session_id}
    BE-->>FE: {results: [...], total_pages: 2}
    FE-->>U: 显示结果列表

    U->>FE: 点击片段#1
    FE->>BE: GET /api/results/{session_id}/chunks/1
    BE-->>FE: {content: "...", line_count: 50}
    FE-->>U: 显示片段详情

    U->>FE: 点击复制按钮
    FE->>FE: navigator.clipboard.writeText
    FE-->>U: 显示已复制提示
```
