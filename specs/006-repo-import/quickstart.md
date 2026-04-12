# 快速开始: 仓库导入功能

**Branch**: `006-repo-import` | **Date**: 2026-04-12

## API 端点概览

| 方法 | 路径 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/repo/validate` | 验证仓库有效性 | `RepoValidateRequest` | `RepoInfoResponse` |
| POST | `/api/repo/import` | 确认导入仓库 | `RepoImportRequest` | `RepoInfoResponse` |
| GET | `/api/repo/current` | 获取当前仓库 | - | `RepoInfoResponse` |

## 请求/响应类型

### RepoValidateRequest

```typescript
interface RepoValidateRequest {
  type: 'local' | 'github'      // 仓库来源类型
  path: string                    // 本地绝对路径 或 GitHub URL (owner/repo)
}
```

### RepoImportRequest

```typescript
interface RepoImportRequest {
  type: 'local' | 'github'      // 仓库来源类型
  path: string                    // 本地绝对路径（本地仓库）或 GitHub URL（GitHub 仓库）
  name: string                    // 仓库名称
  // GitHub 仓库专用字段
  local_clone_path?: string       // GitHub 仓库克隆到的本地目录（由用户配置）
}
```

### RepoInfoResponse

```typescript
interface RepoInfoResponse {
  success: boolean
  data?: {
    id: string                    // 仓库 ID
    type: 'local' | 'github'     // 来源类型
    local_path: string           // 本地绝对路径
    remote_url?: string          // 原始远程地址（仅 GitHub）
    name: string                 // 仓库名称
    description?: string         // GitHub 仓库描述
    imported_at: string          // ISO 8601 时间戳
  }
  error?: {
    code: string                 // 错误码
    message: string              // 错误消息
  }
}
```

## 错误码

| 错误码 | 说明 | 适用场景 |
|--------|------|----------|
| `INVALID_PATH` | 无效路径 | 本地路径为空、格式错误 |
| `NOT_A_GIT_REPO` | 不是 Git 仓库 | 目录缺少 `.git` |
| `PATH_NOT_ACCESSIBLE` | 路径不可访问 | 无读取权限或目录不存在 |
| `INVALID_GITHUB_URL` | 无效 GitHub URL | 格式不符合要求 |
| `GITHUB_REPO_NOT_FOUND` | 仓库不存在 | GitHub API 返回 404 |
| `GITHUB_REPO_PRIVATE` | 私有仓库需认证 | 无 Token 访问私有仓库 |
| `GITHUB_TOKEN_MISSING` | Token 未配置 | 用户未配置 GitHub Token |
| `GITHUB_TOKEN_INVALID` | Token 无效 | Token 过期或权限不足 |
| `GITHUB_CLONE_FAILED` | 克隆失败 | git clone 执行失败 |
| `NETWORK_ERROR` | 网络错误 | GitHub API 请求失败 |
| `INTERNAL_ERROR` | 服务器内部错误 | 数据库或文件系统错误 |

## 环境变量配置

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `GITHUB_TOKEN` | 仅私有仓库 | GitHub Personal Access Token |
| `GITHUB_API_URL` | 可选 | GitHub Enterprise API URL，默认 `https://api.github.com` |

### GitHub Token 认证方式

私有仓库导入时，Token 支持两种传递方式：

**方式一：通过请求头传递（优先推荐）**

```bash
curl -X POST http://localhost:8000/api/repo/validate \
  -H "Content-Type: application/json" \
  -H "X-Github-Token: ghp_xxxx" \
  -d '{"type": "github", "path": "owner/private-repo"}'
```

**方式二：通过环境变量**

设置 `GITHUB_TOKEN` 环境变量后，后端自动使用。

## 调用示例

### 验证本地仓库

```bash
curl -X POST http://localhost:8000/api/repo/validate \
  -H "Content-Type: application/json" \
  -d '{"type": "local", "path": "D:\\projects\\my-repo"}'
```

**成功响应**:
```json
{
  "success": true,
  "data": {
    "type": "local",
    "local_path": "D:\\projects\\my-repo",
    "name": "my-repo",
    "is_valid": true
  }
}
```

**失败响应** (不是 Git 仓库):
```json
{
  "success": false,
  "error": {
    "code": "NOT_A_GIT_REPO",
    "message": "所选目录不是有效的 Git 仓库"
  }
}
```

### 验证 GitHub 仓库

验证阶段仅检查 GitHub API，不执行克隆。

```bash
curl -X POST http://localhost:8000/api/repo/validate \
  -H "Content-Type: application/json" \
  -d '{"type": "github", "path": "owner/repo"}'
```

**成功响应**:
```json
{
  "success": true,
  "data": {
    "type": "github",
    "remote_url": "https://github.com/owner/repo",
    "name": "repo",
    "description": "This is a sample repository",
    "is_valid": true
  }
}
```

**私有仓库失败**:
```json
{
  "success": false,
  "error": {
    "code": "GITHUB_REPO_PRIVATE",
    "message": "该仓库为私有仓库，请配置 GitHub Token"
  }
}
```

### 确认导入

**本地仓库**: 直接验证路径有效性后记录
**GitHub 仓库**: 执行 `git clone` 将仓库克隆到用户指定的本地目录

```bash
curl -X POST http://localhost:8000/api/repo/import \
  -H "Content-Type: application/json" \
  -d '{"type": "github", "path": "owner/repo", "name": "repo", "local_clone_path": "D:\\my-repos\\owner\\repo"}'
```

**成功响应**:
```json
{
  "success": true,
  "data": {
    "id": "123",
    "type": "github",
    "local_path": "D:\\my-repos\\owner\\repo",
    "remote_url": "https://github.com/owner/repo",
    "name": "repo",
    "description": "This is a sample repository",
    "imported_at": "2026-04-12T10:30:00Z"
  }
}
```

**克隆失败响应**:
```json
{
  "success": false,
  "error": {
    "code": "GITHUB_CLONE_FAILED",
    "message": "克隆仓库失败，请检查目标目录是否存在"
  }
}
```

### 获取当前仓库

```bash
curl http://localhost:8000/api/repo/current
```

**有仓库时**:
```json
{
  "success": true,
  "data": {
    "id": "123",
    "type": "github",
    "local_path": "C:\\Users\\machi\\AppData\\Local\\logfix-ai\\repos\\owner\\repo",
    "remote_url": "https://github.com/owner/repo",
    "name": "repo",
    "imported_at": "2026-04-12T10:30:00Z"
  }
}
```

**无仓库时**:
```json
{
  "success": true,
  "data": null
}
```

## 前端集成

### API 服务接口

```typescript
// frontend/src/services/api.ts
const repoApi = {
  validate: (type: 'local' | 'github', path: string) =>
    api.post<RepoInfoResponse>('/api/repo/validate', { type, path }),

  import: (type: 'local' | 'github', path: string, name: string, localClonePath?: string) =>
    api.post<RepoInfoResponse>('/api/repo/import', { type, path, name, local_clone_path: localClonePath }),

  getCurrent: () =>
    api.get<RepoInfoResponse>('/api/repo/current'),
}
```

### RepoInfo 类型

```typescript
// frontend/src/types/index.ts
export interface RepoInfo {
  type: 'local' | 'github'
  local_path: string        // 本地绝对路径
  remote_url?: string       // 仅 GitHub 仓库有值
  name: string
  description?: string
  imported_at: string
}
```

### 路径选择 UI

统一使用 Windows 资源管理器选择路径，不使用文本输入：

```typescript
// 本地仓库：选择文件夹
const handleSelectLocalPath = async () => {
  const path = await window.electron.openDirectoryDialog() // 或使用 dialog 模块
  if (path) {
    setLocalPath(path)
    // 自动触发验证
    handleValidate(path)
  }
}

// GitHub 克隆路径：选择目标文件夹
const handleSelectClonePath = async () => {
  const path = await window.electron.openDirectoryDialog()
  if (path) {
    setLocalClonePath(path)
  }
}
```

> 注：前端使用 Electron 的 `dialog.showOpenDialog` 或类似 API 实现文件夹选择对话框。后端 `local_path` 统一使用绝对路径格式。

## 日志对应

每次导入操作对应两条日志（符合 OBS-001/002/003）：

1. **验证操作** (成功/失败):
   ```
   INFO | 仓库验证: source_type=local, local_path=D:\projects\my-repo, status=success
   INFO | 仓库验证: source_type=github, remote_url=https://github.com/owner/repo, status=failed, error=GITHUB_REPO_PRIVATE
   ```

2. **导入操作** (成功/失败):
   ```
   INFO | 仓库导入: repo_id=123, source_type=local, local_path=D:\projects\my-repo, status=success
   INFO | 仓库导入: repo_id=null, source_type=github, remote_url=https://github.com/owner/repo, status=failed, error=GITHUB_CLONE_FAILED
   ```

**日志级别**: 成功为 INFO，失败为 ERROR（OBS-002）
