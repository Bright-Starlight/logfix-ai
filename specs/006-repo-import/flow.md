# Flow: 仓库导入功能

**Branch**: `006-repo-import` | **Date**: 2026-04-12

## 用户流程

```mermaid
flowchart TD
    START([用户打开应用]) --> HOME{首页显示<br/>仓库导入页面}

    %% 本地仓库导入流程
    HOME --> LOCAL_SELECT[用户选择<br/>本地仓库 Tab]
    LOCAL_SELECT --> LOCAL_PATH[用户点击选择按钮<br/>弹出资源管理器<br/>选择本地文件夹]
    LOCAL_PATH --> LOCAL_VALIDATE[系统自动验证<br/>目录有效性]
    LOCAL_VALIDATE --> LOCAL_CHECK{目录存在且<br/>包含 .git 目录?}

    LOCAL_CHECK -->|否| LOCAL_ERROR[显示错误提示<br/>路径无效]
    LOCAL_ERROR --> LOCAL_SELECT

    LOCAL_CHECK -->|是| LOCAL_PREVIEW[展示仓库预览卡片<br/>仓库名称 + 路径]
    LOCAL_PREVIEW --> LOCAL_IMPORT_BTN{用户点击<br/>确认导入}

    LOCAL_IMPORT_BTN -->|取消| LOCAL_SELECT
    LOCAL_IMPORT_BTN -->|确认| LOCAL_DB_LOCAL[创建 Repository 记录<br/>创建 ImportSession 记录]
    LOCAL_DB_LOCAL --> LOCAL_LOG[记录导入日志<br/>INFO: 成功]
    LOCAL_LOG --> LOCAL_SUCCESS[自动跳转至<br/>日志上传页面]

    %% GitHub 仓库导入流程
    HOME --> GITHUB_SELECT[用户选择<br/>GitHub 仓库 Tab]
    GITHUB_SELECT --> GITHUB_URL[用户输入<br/>GitHub 仓库地址]
    GITHUB_URL --> GITHUB_PARSE[系统解析 URL<br/>支持 owner/repo<br/>和完整 HTTPS 格式]
    GITHUB_PARSE --> GITHUB_VALIDATE[系统调用<br/>GitHub API 验证仓库]
    GITHUB_VALIDATE --> GITHUB_CHECK{仓库存在?}

    GITHUB_CHECK -->|否| GITHUB_NOT_FOUND[显示错误<br/>仓库不存在]
    GITHUB_NOT_FOUND --> GITHUB_SELECT

    GITHUB_CHECK -->|是| GITHUB_PRIVATE{仓库是否为<br/>私有仓库?}

    GITHUB_PRIVATE -->|是| GITHUB_TOKEN_CHECK{用户是否已<br/>配置 GitHub Token?}

    GITHUB_TOKEN_CHECK -->|否| GITHUB_TOKEN_GUIDE[提示配置<br/>GitHub Token]
    GITHUB_TOKEN_GUIDE --> GITHUB_SELECT

    GITHUB_TOKEN_CHECK -->|是| GITHUB_CLONE_PATH
    GITHUB_PRIVATE -->|否| GITHUB_CLONE_PATH

    GITHUB_CLONE_PATH[用户点击选择目标文件夹<br/>弹出资源管理器<br/>选择克隆目标目录]
    GITHUB_CLONE_PATH --> GITHUB_PREVIEW[展示仓库预览卡片<br/>仓库名称 + 描述]
    GITHUB_PREVIEW --> GITHUB_IMPORT_BTN{用户点击<br/>确认导入}

    GITHUB_IMPORT_BTN -->|取消| GITHUB_SELECT
    GITHUB_IMPORT_BTN -->|确认| GITHUB_CLONE[执行 git clone<br/>克隆到目标目录]
    GITHUB_CLONE --> GITHUB_CLONE_CHECK{克隆成功?}

    GITHUB_CLONE_CHECK -->|否| GITHUB_CLONE_ERROR[显示克隆失败错误<br/>记录 ERROR 日志]
    GITHUB_CLONE_ERROR --> GITHUB_SELECT

    GITHUB_CLONE_CHECK -->|是| GITHUB_DB[创建 Repository 记录<br/>创建 ImportSession 记录]
    GITHUB_DB --> GITHUB_LOG[记录导入日志<br/>INFO: 成功]
    GITHUB_LOG --> GITHUB_SUCCESS[自动跳转至<br/>日志上传页面]

    %% 日志处理页面守卫
    LOCAL_SUCCESS --> LOG_PAGE[日志上传页面]
    GITHUB_SUCCESS --> LOG_PAGE

    LOG_PAGE --> GUARD_CHECK{用户是否已完成<br/>仓库导入?}

    GUARD_CHECK -->|否| REDIRECT[重定向至<br/>仓库导入页面<br/>提示请先导入仓库]
    REDIRECT --> HOME

    GUARD_CHECK -->|是| LOG_UPLOAD[用户上传日志文件<br/>进入日志处理流程]
    LOG_UPLOAD --> SWITCH_REPO[用户点击<br/>切换仓库]
    SWITCH_REPO --> HOME
```

---

## 状态转换

### 仓库导入状态

```mermaid
stateDiagram-v2
    [*] --> 空闲状态: 应用启动
    空闲状态 --> 验证中: 用户输入路径并触发验证
    验证中 --> 验证成功: 路径有效
    验证中 --> 验证失败: 路径无效
    验证成功 --> 导入中: 用户点击确认导入
    验证失败 --> 空闲状态: 用户修改输入重新验证
    导入中 --> 导入成功: Repository 和 ImportSession 创建完成
    导入中 --> 导入失败: 克隆失败或数据库错误
    导入成功 --> [*]: 跳转至日志上传页面
    导入失败 --> 空闲状态: 显示错误，用户可重试
```

---

## API 调用流程

```mermaid
sequenceDiagram
    participant Frontend
    participant Backend
    participant Database
    participant GitHub
    participant FileSystem

    %% 本地仓库验证
    Frontend->>Backend: POST /api/repo/validate<br/>{type: "local", path: "D:/path"}
    Backend->>FileSystem: 检查路径是否存在
    Backend->>FileSystem: 检查 .git 目录存在
    Backend-->>Frontend: RepoInfoResponse

    %% 本地仓库导入
    Frontend->>Backend: POST /api/repo/import<br/>{type: "local", path, name}
    Backend->>Database: 创建 Repository 记录
    Backend->>Database: 创建 ImportSession 记录
    Backend->>Backend: log_repo_import_info()
    Backend-->>Frontend: RepoInfoResponse

    %% GitHub 仓库验证
    Frontend->>Backend: POST /api/repo/validate<br/>{type: "github", path: "owner/repo"}
    Backend->>GitHub: GET /repos/owner/repo
    alt 公开仓库
        GitHub-->>Backend: 200 OK
    else 私有仓库
        GitHub-->>Backend: 404 Not Found
    else Token 无效
        GitHub-->>Backend: 401 Unauthorized
    end
    Backend-->>Frontend: RepoInfoResponse

    %% GitHub 仓库导入
    Frontend->>Backend: POST /api/repo/import<br/>{type: "github", path, name, local_clone_path}
    Backend->>GitHub: GET /repos/owner/repo
    Backend->>FileSystem: 执行 git clone
    FileSystem-->>Backend: 克隆完成
    Backend->>Database: 创建 Repository 记录
    Backend->>Database: 创建 ImportSession 记录
    Backend->>Backend: log_repo_import_info()
    Backend-->>Frontend: RepoInfoResponse

    %% 获取当前仓库
    Frontend->>Backend: GET /api/repo/current
    Backend->>Database: 查询最新 Repository
    Backend-->>Frontend: RepoInfoResponse
```

---

## 错误处理流程

```mermaid
flowchart TD
    ERROR[发生错误] --> ERROR_TYPE{错误类型}

    ERROR_TYPE -->|本地路径错误| LOCAL_ERR_DISPLAY[显示错误提示<br/>行内红色边框<br/>文字说明]
    LOCAL_ERR_DISPLAY --> RETRY_LOCAL[用户修改路径<br/>重新验证]

    ERROR_TYPE -->|GitHub API 错误| GH_ERR_DISPLAY[根据错误码显示<br/>仓库不存在/需认证/网络错误]
    GH_ERR_DISPLAY --> RETRY_GH[用户检查配置<br/>重新验证]

    ERROR_TYPE -->|克隆失败| CLONE_ERR_DISPLAY[显示克隆失败提示<br/>记录 ERROR 日志]
    CLONE_ERR_DISPLAY --> RETRY_CLONE[用户检查目标目录<br/>重新导入]

    ERROR_TYPE -->|数据库错误| DB_ERR_LOG[记录 ERROR 日志<br/>包含错误详情]
    DB_ERR_LOG --> DB_ERR_DISPLAY[显示通用错误提示<br/>请联系支持]
```

---

## 关键日志埋点

| 操作 | 日志级别 | 埋点 | 内容 |
|------|----------|------|------|
| 本地仓库验证成功 | INFO | OBS-001 | source_type=local, local_path, status=success |
| 本地仓库验证失败 | ERROR | OBS-002 | source_type=local, local_path, error=具体错误 |
| GitHub 仓库验证成功 | INFO | OBS-001 | source_type=github, remote_url, status=success |
| GitHub 仓库验证失败 | ERROR | OBS-002 | source_type=github, remote_url, error=具体错误 |
| 仓库导入成功 | INFO | OBS-001 | repo_id, source_type, local_path, status=success |
| 仓库导入失败 | ERROR | OBS-002 | repo_id=null, source_type, remote_url, error=具体错误 |
