# 数据模型: 仓库导入功能

**Branch**: `006-repo-import` | **Date**: 2026-04-12

## 概述

本特性新增 `Repository` 和 `ImportSession` 两个实体，用于记录用户导入的仓库信息及每次导入操作的上下文。

## 新增实体

### Repository（仓库）

表示用户导入的代码仓库，是整个分析流水线的入口数据。

```python
class Repository(Base):
    """仓库实体"""

    __tablename__ = "repositories"
    __table_args__ = {"comment": "仓库表，记录用户导入的代码仓库信息"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(16), nullable=False, comment="来源类型：local/github")
    name = Column(String(255), nullable=False, comment="仓库名称")
    description = Column(Text, nullable=True, comment="仓库描述（GitHub 仓库时填充）")
    # 本地仓库：存储用户输入的绝对路径
    # GitHub 仓库：存储用户指定的克隆目标路径
    local_path = Column(String(1024), nullable=False, comment="本地绝对路径（本地仓库为原始路径，GitHub 仓库为克隆目标路径）")
    # 仅 GitHub 仓库使用，存储原始远程地址
    remote_url = Column(String(1024), nullable=True, comment="远程地址（GitHub 仓库的原始 URL）")
    is_valid = Column(Boolean, default=True, comment="仓库是否有效")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
```

**字段说明**:
- `source_type`: 区分本地仓库（local）和 GitHub 仓库（github）
- `local_path`: 统一存储本地绝对路径
  - 本地仓库：用户输入的原始路径
  - GitHub 仓库：用户指定的克隆目标路径（而非自动生成的路径）
- `remote_url`: 仅 GitHub 仓库填充，存储 `https://github.com/owner/repo` 格式的原始地址
- `is_valid`: 标记仓库是否仍然有效（克隆目录可能被删除或移动）

### ImportSession（导入会话）

表示一次导入操作的上下文，用于 OBS-001/002 要求的操作审计。

```python
class ImportSession(Base):
    """导入会话实体"""

    __tablename__ = "import_sessions"
    __table_args__ = (
        Index("ix_import_sessions_repo_id", "repo_id"),
        Index("ix_import_sessions_status", "status"),
        {"comment": "导入会话表，记录每次仓库导入操作的上下文和结果"}
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    repo_id = Column(BigInteger, ForeignKey("repositories.id"), nullable=False, comment="关联的仓库ID")
    source_type = Column(String(16), nullable=False, comment="导入来源类型：local/github")
    status = Column(String(16), nullable=False, default="pending", comment="状态：pending/success/failed")
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
```

**字段说明**:
- `status`: pending（导入中）、success（成功）、failed（失败）
- `error_message`: 失败时记录具体错误原因，用于日志和用户提示

## 关系

```
Repository (1) ─── (N) ImportSession
```

一个仓库可以被多次导入（重复导入时创建新的 ImportSession）。

## 验证规则

### 本地仓库验证

1. 路径必须为绝对路径（非相对路径）
2. 路径对应的目录必须存在
3. 目录必须包含 `.git` 子目录（有效的 Git 仓库）
4. 应用进程必须对目录有读取权限

### GitHub 仓库验证

**验证阶段**:
1. URL 格式必须符合 `owner/repo` 或 `https://github.com/owner/repo` 格式
2. 使用 GitHub API (`GET /repos/{owner}/{repo}`) 验证仓库存在性
3. 检查仓库是否为私有（私有仓库需要 Token）
4. 网络超时时间: 10 秒

**导入阶段（克隆）**:
1. 用户通过文件夹选择对话框指定 `local_clone_path`（克隆目标目录）
2. 验证目标目录的父目录是否存在
3. 使用 `git clone` 命令克隆仓库到目标路径
4. 克隆完成后验证本地目录包含 `.git`
5. 私有仓库使用 `GITHUB_TOKEN` 环境变量进行认证
6. 克隆超时时间: 5 分钟

### GitHub 认证配置

| 场景 | 配置方式 |
|------|----------|
| 公开仓库 | 无需配置 |
| 私有仓库 | 必须配置 `GITHUB_TOKEN` 环境变量或通过 UI 输入 |
| 企业 GitHub | 使用 `GITHUB_API_URL` 环境变量指定 API 端点 |

**Token 权限要求**:
- `repo` (完整控制权限) 或
- `repo:public` (仅公开仓库读取)

## 状态转换

### Repository 状态

```
(None) ──创建──> is_valid=True
                      │
                      └──── 仓库失效 ──> is_valid=False
```

### ImportSession 状态

```
pending ──成功──> success
    │
    └──失败──> failed
```

## 现有实体影响

本特性**不修改**现有实体，但影响以下现有流程：

1. **App.tsx**: `currentStep` 初始值从 `'upload'` 改为 `'repo'`（已完成）
2. **FileUpload**: 无需修改，但会依赖 `repo` 状态进行页面守卫

## 数据库迁移

需要创建迁移脚本 `add_repositories_and_import_sessions.py`，包含：

1. 创建 `repositories` 表
2. 创建 `import_sessions` 表
3. 添加外键约束
