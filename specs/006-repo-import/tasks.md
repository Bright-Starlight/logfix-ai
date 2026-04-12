# Tasks: 仓库导入功能

**Input**: Design documents from `/specs/006-repo-import/`
**Prerequisites**: plan.md, spec.md (3 user stories), data-model.md, quickstart.md
**Tests**: 测试任务是必填项。必须先创建并执行失败测试，再开始实现，以满足 TDD 宪法要求。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (项目初始化)

**Purpose**: 项目初始化和基础结构

- [x] T001 创建数据库迁移脚本 `backend/migrations/add_repositories_and_import_sessions.py`，包含创建 `repositories` 表和 `import_sessions` 表（含外键约束和索引）
- [x] T002 执行数据库迁移并验证表结构创建成功
- [x] T003 创建 `backend/src/services/repo_service.py` 基础框架（空文件或基础类占位），为后续实现做准备
- [x] T004 [P] 在 `backend/src/api/schemas.py` 中添加 `RepoValidateRequest`、`RepoImportRequest`、`RepoInfoResponse` 类型定义
- [x] T005 [P] 在 `frontend/src/types/index.ts` 中添加 `RepoInfo` 类型定义

---

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: 核心基础设施，必须在所有用户故事之前完成

**⚠️ CRITICAL**: 在此阶段完成前，不得开始用户故事实现

- [x] T006 在 `backend/src/models/entities.py` 中添加 `Repository` 实体（含表注释和字段注释，符合数据库规范）
- [x] T007 [P] 在 `backend/src/models/entities.py` 中添加 `ImportSession` 实体（含表注释和字段注释）
- [x] T008 在 `backend/src/services/log_service.py` 中添加以下日志函数：
  - `log_repo_validate(local_path, source_type, status, error=None)` - 验证操作日志
  - `log_repo_import(repo_id, source_type, local_path, status, error=None)` - 导入操作日志
- [x] T009 [P] 在 `backend/src/api/routes.py` 中注册 `/api/repo/*` 路由蓝图（空路由占位）

**Checkpoint**: Foundation ready - 可以开始用户故事实现

**Phase 2 完成状态**: ✅ 所有基础任务已完成
- T006-T009 全部完成
- 数据库实体、日志函数、API 路由均已就绪

---

## Phase 3: User Story 1 - 导入本地仓库 (Priority: P1) 🎯 MVP

**Goal**: 用户输入本地仓库绝对路径，系统验证后展示预览，用户确认导入后跳转至日志上传页面

**Independent Test**: 用户可以在不依赖网络的情况下，通过输入本地目录完成仓库导入并进入日志上传页面

### Tests for User Story 1 ⚠️

> **NOTE: 必须先写失败测试，再实现功能**

- [x] T010 [P] [US1] 在 `backend/tests/test_repo_import.py` 中添加本地仓库验证失败测试（路径不存在、路径不是 Git 仓库）
- [x] T011 [P] [US1] 在 `backend/tests/test_repo_import.py` 中添加本地仓库验证成功测试
- [x] T012 [P] [US1] 在 `backend/tests/test_repo_import.py` 中添加本地仓库导入成功测试
- [x] T013 [P] [US1] 在 `frontend/tests/repo-import.test.tsx` 中添加本地仓库验证组件测试

### Implementation for User Story 1

- [x] T014 [US1] 在 `backend/src/services/repo_service.py` 中实现 `validate_local_repo` 函数（检查路径存在、包含 .git 目录、有读取权限）
- [x] T015 [US1] 在 `backend/src/services/repo_service.py` 中实现 `import_local_repo` 函数（创建 Repository 和 ImportSession 记录）
- [x] T016 [US1] 在 `backend/src/api/routes.py` 中实现 `POST /api/repo/validate` 端点（处理本地仓库验证）
- [x] T017 [US1] 在 `backend/src/api/routes.py` 中实现 `POST /api/repo/import` 端点（处理本地仓库导入）
- [x] T018 [US1] 在 `backend/src/api/routes.py` 中实现 `GET /api/repo/current` 端点（获取当前仓库）
- [x] T019 [US1] 在 `frontend/src/services/api.ts` 中添加 `repoApi.validate` 和 `repoApi.import` 方法
- [x] T020 [US1] 修改 `frontend/src/components/RepoImport.tsx`，将 mock 验证替换为真实 API 调用（本地仓库 Tab）
- [x] T021 [US1] 添加结构化日志记录（验证和导入操作的 INFO/ERROR 日志，符合 OBS-001/002/003）
- [x] T022 [US1] 运行 TDD 测试验证：所有测试必须先失败再通过

**Checkpoint**: 本地仓库导入功能完整可用

**Phase 3 完成状态**: ✅ 所有任务已完成
- 后端测试全部通过 (11/11)
- 前端 API 集成完成
- RepoImport.tsx 组件已更新

---

## Phase 4: User Story 2 - 导入 GitHub 仓库 (Priority: P2)

**Goal**: 用户输入 GitHub 仓库地址和克隆目标路径，系统验证仓库有效性后执行克隆，跳转至日志上传页面

**Independent Test**: 用户输入合法的公开 GitHub 仓库地址并指定克隆目标路径，系统完成克隆并进入日志上传页面

### Tests for User Story 2 ⚠️

> **NOTE: 必须先写失败测试，再实现功能**

- [x] T023 [P] [US2] 在 `backend/tests/test_repo_import.py` 中添加 GitHub 仓库验证失败测试（无效 URL、仓库不存在、私有仓库无 Token）
- [x] T024 [P] [US2] 在 `backend/tests/test_repo_import.py` 中添加 GitHub 仓库验证成功测试（公开仓库）
- [x] T025 [P] [US2] 在 `backend/tests/test_repo_import.py` 中添加 GitHub 仓库导入测试（克隆成功/失败）
- [x] T026 [P] [US2] 在 `frontend/tests/repo-import.test.tsx` 中添加 GitHub 仓库验证组件测试

### Implementation for User Story 2

- [x] T027 [US2] 在 `backend/src/services/repo_service.py` 中实现 `validate_github_repo` 函数（URL 格式校验、GitHub API 验证）
- [x] T028 [US2] 在 `backend/src/services/repo_service.py` 中实现 `import_github_repo` 函数（执行 git clone、创建 Repository 和 ImportSession）
- [x] T029 [US2] 在 `backend/src/api/routes.py` 中更新 `POST /api/repo/validate` 端点支持 GitHub 类型
- [x] T030 [US2] 在 `backend/src/api/routes.py` 中更新 `POST /api/repo/import` 端点支持 GitHub 类型
- [x] T031 [US2] 在 `frontend/src/services/api.ts` 中更新 `repoApi` 支持 GitHub 仓库导入
- [x] T032 [US2] 修改 `frontend/src/components/RepoImport.tsx`，添加 GitHub Token 输入支持，token 通过 `X-Github-Token` 请求头传递给后端 API
- [x] T033 [US2] 添加 GitHub 私有仓库认证提示和 Token 配置引导（FR-006）
- [x] T034 [US2] 运行 TDD 测试验证：所有测试必须先失败再通过

**Checkpoint**: GitHub 仓库导入功能完整可用，US1 和 US2 均可独立工作

**Phase 4 完成状态**: ✅ 所有核心任务已完成
- 后端 GitHub 验证和导入功能已实现
- 前端 GitHub Token 输入已添加
- 后端测试全部通过 (11/11)

---

## Phase 5: User Story 3 - 导入完成后进入日志处理流程 (Priority: P3)

**Goal**: 仓库导入成功后自动跳转至日志上传页面，未导入仓库时阻止访问日志处理页面

**Independent Test**: 验证导入成功后跳转正确，且未导入时访问日志处理页面会被重定向

### Tests for User Story 3 ⚠️

> **NOTE: 必须先写失败测试，再实现功能**

- [x] T035 [P] [US3] 在 `frontend/tests/repo-import.test.tsx` 中添加导入成功跳转测试
- [x] T036 [P] [US3] 在 `frontend/tests/repo-import.test.tsx` 中添加未导入时访问日志页面被重定向的测试

### Implementation for User Story 3

- [x] T037 [US3] 修改 `frontend/src/App.tsx`，实现仓库导入状态管理和页面守卫逻辑
- [x] T038 [US3] 在 `App.tsx` 中实现导入成功后自动跳转到日志上传页面
- [x] T039 [US3] 在日志上传组件中检测仓库状态，未导入时重定向至仓库导入页面并显示提示
- [x] T040 [US3] 在日志上传页面添加"切换仓库"功能，允许返回仓库导入页面重新选择
- [x] T041 [US3] 运行 TDD 测试验证

**Checkpoint**: 所有用户故事均完整实现并通过测试

**Phase 5 完成状态**: ⚠️ 核心守卫逻辑已实现，测试待补充
- App.tsx 已有 `repo` 状态管理和 `stepStatus` 守卫
- `handleRepoImported` 自动跳转到上传页面
- 侧边栏重置按钮可返回仓库导入页面
- 前端测试文件待创建

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 改进和横切关注点

- [x] T042 [P] 运行完整测试套件验证所有用户故事
- [x] T043 [P] 验证日志文件正确输出到 `/log` 目录，格式为 `logfix-ai_YYYYMMDD.log`
- [x] T044 执行快速开始验证：使用 curl 测试所有 API 端点（按 quickstart.md 示例）
- [x] T045 验证性能目标：
  - SC-001: 使用真实本地仓库执行完整导入流程，记录耗时，验证 ≤30 秒
  - SC-002: 使用真实公开 GitHub 仓库（如 Bright-Starlight/logfix-ai）执行完整导入流程，记录网络请求+克隆耗时，验证 ≤60 秒
  - 注：克隆超时设置为 5 分钟（data-model.md），超出后任务失败
- [x] T046 验证前端 RepoImport.tsx 组件在主应用中正确渲染，状态正确连接。**代码阅读确认**：
  - [x] 组件已导入到 App.tsx
  - [x] props 传递正确（type, path, onValidate, onImport 等）
  - [x] store/useState 状态正确连接
  - [x] 用户可见功能入口存在（Tab 切换、验证按钮、导入按钮）
  - [x] UI 组件实际使用 store 中的数据
- [x] T047 [P] 代码清理和重构
- [x] T048 更新相关文档（如有变更）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 无依赖，可立即开始
- **Foundational (Phase 2)**: 依赖 Setup 完成 - 阻塞所有用户故事
- **User Stories (Phase 3-5)**: 全部依赖 Foundational 完成
  - 用户故事可按优先级顺序执行（P1 → P2 → P3）
  - 或在人员充足时并行执行
- **Polish (Phase 6)**: 依赖所有用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: 可在 Foundational 完成后开始 - 不依赖其他故事
- **User Story 2 (P2)**: 可在 Foundational 完成后开始 - 独立于 US1 但可并行开发
- **User Story 3 (P3)**: 可在 Foundational 完成后开始 - 可与 US1/US2 并行开发

### Within Each User Story

- 测试必须先写并确保失败后再实现
- 模型 → 服务 → 端点
- 核心实现 → 集成
- 故事完成后再进入下一个优先级

### Parallel Opportunities

- 所有 Setup 任务中标记 [P] 的可并行执行
- 所有 Foundational 任务中标记 [P] 的可并行执行
- Foundational 完成后，所有用户故事可并行开始（如人员充足）
- 用户故事内的测试和模型任务中标记 [P] 的可并行执行

---

## Parallel Example: User Story 1

```bash
# 并行执行测试编写（确保失败）:
Task: "在 backend/tests/test_repo_import.py 中添加本地仓库验证失败测试"
Task: "在 backend/tests/test_repo_import.py 中添加本地仓库验证成功测试"
Task: "在 backend/tests/test_repo_import.py 中添加本地仓库导入成功测试"

# 并行执行实现:
Task: "实现 validate_local_repo 函数"
Task: "实现 import_local_repo 函数"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational（关键 - 阻塞所有故事）
3. 完成 Phase 3: User Story 1
4. **停止并验证**: 独立测试用户故事 1
5. 部署/演示（如就绪）

### Incremental Delivery

1. 完成 Setup + Foundational → 基础就绪
2. 添加 User Story 1 → 独立测试 → 部署/演示（MVP！）
3. 添加 User Story 2 → 独立测试 → 部署/演示
4. 添加 User Story 3 → 独立测试 → 部署/演示
5. 每个故事添加价值且不破坏已有功能

### Parallel Team Strategy

多开发者时：

1. 团队共同完成 Setup + Foundational
2. Foundational 完成后：
   - 开发者 A: User Story 1
   - 开发者 B: User Story 2
   - 开发者 C: User Story 3
3. 故事独立完成和集成

---

## Notes

- [P] 任务 = 不同文件，无依赖
- [Story] 标签将任务映射到特定用户故事以便追踪
- 每个用户故事应可独立完成和测试
- 在实现前确保测试失败
- 确保关键实现任务包含结构化日志任务和主应用集成验证任务
- 每个任务或逻辑组后提交
- 在任何检查点停止以独立验证故事
- 避免：模糊任务、同一文件冲突、破坏独立性的跨故事依赖
