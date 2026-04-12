# Implementation Plan: 仓库导入功能

**Branch**: `006-repo-import` | **Date**: 2026-04-12 | **Spec**: [spec.md](./spec.md)

> 所有正文内容必须使用中文编写；如与宪法冲突，以 `.specify/memory/constitution.md` 为准。

## Summary

实现仓库导入功能，支持本地仓库和 GitHub 仓库两种导入方式。前端 RepoImport.tsx 组件 UI 已完成，采用两步验证流程（验证→确认导入）。GitHub 仓库导入时会执行 `git clone` 将仓库克隆到本地存储目录；私有仓库需要配置 GitHub Token。后端需要新增 Repository/ImportSession 实体、三个 API 端点、以及配套的日志函数。

## Technical Context

**Language/Version**: Python 3.11 (FastAPI backend), TypeScript/React 18 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy, React, Vite, SSE (for streaming), loguru, git (系统命令)
**Storage**: PostgreSQL (entities), local filesystem (repos in `user_data_dir/repos/`, logs in `/log`)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Windows/Linux 本地桌面应用
**Project Type**: Web 全栈应用（FastAPI + React）
**Performance Goals**:
- SC-001: 本地仓库导入 30 秒内完成
- SC-002: GitHub 公开仓库导入 60 秒内完成（含克隆时间）
**Constraints**: 本地仓库必须包含 `.git` 目录；GitHub 私有仓库必须配置 `GITHUB_TOKEN`
**Scale/Scope**: 单用户桌面应用，10-50 个仓库/天

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] 规格已获批准，且用户故事具备独立测试条件。spec.md 已完成并包含 3 个用户故事（P1/P2/P3）
- [x] 已明确采用 TDD，并列出先写失败测试的策略。后端测试先行：pytest 测试 validate/import 接口
- [x] 交付切片按 MVP 优先排序，可独立部署或演示。P1 本地导入 → P2 GitHub 导入 → P3 导航守卫
- [x] 已识别日志方案：日志框架（loguru）、`/log` 目录（logfix-ai_{date}.log）、关键埋点（OBS-001/002/003）
- [x] 已定义性能目标与验证方式。SC-001 30s 本地导入、SC-002 60s GitHub 导入
- [x] 已确认实现和脚本兼容 Windows。路径处理使用 pathlib.Path，PowerShell 7 兼容
- [x] 已规划 `/speckit.tasks` 阶段输出 `specs/006-repo-import/flow.md`（Mermaid，中文）
- [x] 已规划 `/speckit.implement` 完成后的主应用集成验证步骤（代码阅读确认 + vitest + /webapp-testing）

## Project Structure

### Documentation (this feature)

```text
specs/006-repo-import/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (N/A - 本特性为现有架构扩展，无需研究)
├── data-model.md        # Phase 1 output (Repository/ImportSession 实体定义)
├── quickstart.md        # Phase 1 output (API 快速调用示例)
├── flow.md              # Phase 2 output (/speckit.tasks command, Mermaid 中文流程图)
├── contracts/           # Phase 1 output (N/A - 内部 API 无需契约文档)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── entities.py          # [修改] 新增 Repository, ImportSession 实体
│   ├── services/
│   │   ├── log_service.py       # [修改] 新增 log_repo_import_* 日志函数
│   │   └── repo_service.py     # [新增] 仓库导入业务逻辑（本地 Git 检测、GitHub API、git clone）
│   └── api/
│       ├── routes.py           # [修改] 新增 /api/repo/* 端点
│       └── schemas.py          # [修改] 新增 RepoValidateRequest, RepoImportRequest, RepoInfoResponse
└── tests/
    └── test_repo_import.py     # [新增] 仓库导入 API 测试

frontend/
├── src/
│   ├── components/
│   │   └── RepoImport.tsx      # [修改] 将 mock 验证替换为真实 API 调用；支持 GitHub Token 输入
│   ├── services/
│   │   └── api.ts              # [修改] 新增 repoApi 对象（validate/import/current）
│   └── types/
│       └── index.ts            # [修改] 新增 RepoInfo 类型（local_path, remote_url）
└── tests/
    └── repo-import.test.tsx    # [新增] 仓库导入组件测试
```

**Structure Decision**: 基于现有 web application 结构（Option 2），复用 backend/frontend 目录
布局。RepoImport.tsx 已存在，仅需修改 API 集成；新增 repo_service.py 处理仓库验证核心逻辑。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
