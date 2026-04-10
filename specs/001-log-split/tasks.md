# Tasks: 日志文件切分

**Input**: Design documents from `/specs/001-log-split/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: 测试任务是必填项。必须先创建并执行失败测试，再开始实现，以满足 TDD 宪法要求。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (项目初始化)

**Purpose**: Project initialization and basic structure

- [x] T001 创建后端项目结构 `backend/src/`、`backend/tests/`、`backend/requirements.txt`
- [x] T002 创建前端项目结构 `frontend/src/`、`frontend/public/`、`frontend/package.json`、`frontend/vite.config.ts`
- [x] T003 [P] 配置后端 Python 虚拟环境并安装依赖：FastAPI、SQLAlchemy、psycopg2-binary、chardet、python-multipart、loguru、pytest
- [x] T004 [P] 配置前端依赖：React、Vite、TypeScript、axios
- [x] T005 创建 `/log` 目录并配置 loguru 日志框架（日志命名规范：`logfix-ai_{日期}.log`）
- [x] T006 创建 `specs/001-log-split/flow.md`，使用 Mermaid 编写中文流程图（包含数据流：文件上传→编码检测→切分处理→结果存储；控制流：前端组件状态转换、API请求响应链、用户交互事件）

---

## Phase 2: Foundational (核心基础设施)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 创建 PostgreSQL 数据库初始化脚本，创建 LogFile、SplitSession、SplitResult 表
- [x] T008 [P] 实现数据库会话管理 `backend/src/db/session.py`
- [x] T009 [P] 实现实体模型 `backend/src/models/entities.py`（LogFile、SplitSession、SplitResult）
- [x] T010 [P] 实现 API 路由基础结构 `backend/src/api/routes.py` 和 FastAPI 主入口 `backend/src/main.py`
- [x] T011 [P] 配置 CORS 中间件和错误处理基础设施
- [x] T012 创建 `.env` 环境配置模板（DATABASE_URL、LOG_DIR、LOG_LEVEL、MAX_FILE_SIZE）
- [x] T013 配置 Windows 兼容的文件路径处理（路径分隔符、正斜杠/反斜杠）
- [x] T013b [P] 创建 `backend/src/services/log_service.py`（loguru 结构化日志配置、日志文件输出到 /log 目录、命名规范 `logfix-ai_{日期}.log`）
- [x] T013c [P] 创建 `backend/src/services/file_handler.py`（文件上传与编码检测基础框架）

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 日志文件上传与预览 (Priority: P1) 🎯 MVP

**Goal**: 用户可以上传日志文件并在界面上预览内容

**Independent Test**: 上传已知内容的文件，验证返回的文件预览行数、内容与原文件一致

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T014 [P] [US1] Contract test: POST /api/upload 成功上传文本文件 in `backend/tests/contract/test_upload.py`
- [x] T015 [P] [US1] Contract test: POST /api/upload 拒绝非文本文件 in `backend/tests/contract/test_upload.py`
- [x] T016 [P] [US1] Contract test: GET /api/files/{file_id} 返回预览内容 in `backend/tests/contract/test_files.py`
- [x] T017 [P] [US1] Integration test: 完整文件上传预览流程 in `backend/tests/integration/test_upload_preview.py`

### Implementation for User Story 1

- [x] T018 [P] [US1] 实现 LogFile 模型的文件上传方法 in `backend/src/models/entities.py`
- [x] T019 [US1] 实现文件编码检测服务 `backend/src/services/file_handler.py`（使用 chardet/charset-normalizer）
- [x] T020 [US1] 实现 POST /api/upload 端点，支持分片上传 in `backend/src/api/routes.py`
- [x] T021 [US1] 实现 GET /api/files/{file_id} 端点，支持预览行数参数 in `backend/src/api/routes.py`
- [x] T022 [US1] 实现前端文件上传组件 `frontend/src/components/FileUpload.tsx`
- [x] T023 [US1] 实现前端文件预览组件 `frontend/src/components/LogPreview.tsx`
- [x] T024 [US1] 前端集成：App.tsx 挂载 FileUpload 和 LogPreview 组件
- [x] T025 [US1] 添加结构化日志：文件上传事件（文件名、文件大小、编码、创建时间）in `backend/src/services/log_service.py`
- [x] T025b [US1] 添加结构化日志：错误事件记录（无效文件类型、编码检测失败、上传中断）in `backend/src/services/log_service.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 正则表达式切分规则 (Priority: P1) 🎯 MVP

**Goal**: 用户可以使用正则表达式作为切分规则，将日志按匹配模式切分

**Independent Test**: 上传已知日志文件，应用正则规则 `^\d{4}-\d{2}-\d{2}`，验证切分结果包含所有匹配的日志条目

### Tests for User Story 2 ⚠️

- [x] T026 [P] [US2] Contract test: POST /api/validate/regex 验证有效正则 in `backend/tests/contract/test_validate.py`
- [x] T027 [P] [US2] Contract test: POST /api/validate/regex 拒绝无效正则 in `backend/tests/contract/test_validate.py`
- [x] T028 [P] [US2] Contract test: POST /api/split 执行正则切分 in `backend/tests/contract/test_split.py`
- [x] T029 [P] [US2] Integration test: 完整正则切分流程 in `backend/tests/integration/test_regex_split.py`

### Implementation for User Story 2

- [x] T030 [P] [US2] 实现 SplitSession 模型的状态管理方法 in `backend/src/models/entities.py`
- [x] T031 [P] [US2] 实现 SplitResult 模型的片段存储方法 in `backend/src/models/entities.py`
- [x] T032 [US2] 实现日志切分核心服务 `backend/src/services/splitter.py`（正则匹配、流式处理）
- [x] T033 [US2] 实现 POST /api/validate/regex 端点（正则校验<200ms）in `backend/src/api/routes.py`
- [x] T034 [US2] 实现 POST /api/split 端点（执行切分）in `backend/src/api/routes.py`
- [x] T035 [US2] 实现 GET /api/sessions/{session_id} 端点（状态追踪）in `backend/src/api/routes.py`
- [x] T036 [US2] 实现 GET /api/results/{session_id} 端点（分页获取结果，每页最多1000条）in `backend/src/api/routes.py`
- [x] T037 [US2] 前端实现切分配置组件 `frontend/src/components/SplitConfig.tsx`（正则输入、实时校验）
- [x] T038 [US2] 前端集成：FileUpload → SplitConfig → 切分执行流程
- [x] T039 [US2] 添加结构化日志：切分规则应用事件（规则类型、内容、匹配数量）in `backend/src/services/log_service.py`
- [x] T039b [US2] 添加结构化日志：切分错误事件（无效正则、匹配超时、数据库错误）in `backend/src/services/log_service.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 固定分隔符切分规则 (Priority: P2)

**Goal**: 用户可以使用固定字符串（空行、自定义分隔符）作为切分规则

**Independent Test**: 上传已知日志，设置空行分隔，验证按空行切分的片段数量正确

### Tests for User Story 3 ⚠️

- [x] T040 [P] [US3] Contract test: POST /api/split 支持 fixed_string 类型 in `backend/tests/contract/test_split.py`
- [x] T041 [P] [US3] Integration test: 完整固定分隔符切分流程 in `backend/tests/integration/test_fixed_split.py`

### Implementation for User Story 3

- [x] T042 [US3] 扩展 splitter.py 支持固定分隔符类型（空行、自定义字符串）in `backend/src/services/splitter.py`
- [x] T043 [US3] 前端扩展 SplitConfig.tsx 支持"空行分隔"和"自定义分隔符"选项
- [x] T044 [US3] 前端集成：SplitConfig 支持两种切分类型切换

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - 切分结果查看与复制 (Priority: P1) 🎯 MVP

**Goal**: 用户可以查看切分后的结果，并复制片段内容到剪贴板

**Independent Test**: 执行切分后，验证结果列表展示、片段点击高亮、复制功能正常工作

### Tests for User Story 4 ⚠️

- [x] T045 [P] [US4] Contract test: GET /api/results/{session_id}/chunks/{chunk_index} 返回完整片段 in `backend/tests/contract/test_results.py`
- [x] T046 [P] [US4] Integration test: 完整结果查看和复制流程 in `backend/tests/integration/test_result_view.py`

### Implementation for User Story 4

- [x] T047 [P] [US4] 前端实现结果列表组件 `frontend/src/components/ResultList.tsx`（分页、展开统计）
- [x] T048 [US4] 前端实现片段点击高亮和完整内容展示
- [x] T049 [US4] 前端实现剪贴板复制功能和"已复制"提示
- [x] T050 [US4] 前端集成：SplitConfig → ResultList → 片段详情展示
- [x] T051 [US4] 添加结构化日志：错误事件记录（错误类型、错误消息、操作上下文）in `backend/src/services/log_service.py`

**Checkpoint**: At this point, all user stories should be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T052 [P] 断点续查功能：刷新页面后恢复切分状态 in `backend/src/api/routes.py`
- [x] T053 [P] 超大文件分片上传：前端 File.slice() 分片 + 后端流式合并
- [x] T054a [P] 后端进度 API：切分过程中实时更新 processed_chunks，支持轮询获取 in `backend/src/api/routes.py`
- [x] T054b [P] 前端传输进度条：FileUpload 组件显示分片上传进度（已上传/总大小）
- [x] T054c [P] 前端切分进度条：SplitConfig 组件显示切分进度（processed_chunks/total_chunks）
- [x] T055 前端响应式适配：支持 320px - 1920px 屏幕宽度
- [x] T056 性能验证：正则校验<200ms、10000行切分<5秒
- [x] T057 [P] 添加后端单元测试 in `backend/tests/unit/`（splitter、file_handler 服务）
- [x] T058 前端 E2E 测试：Playwright 覆盖关键用户流程
- [x] T059 运行 quickstart.md 验证：后端健康检查、前端连接测试
- [x] T060 验证功能已集成到主应用（导入、渲染、状态连接、用户入口、实际数据使用）
- [x] T061 [P] 验证 flow.md 中的日志命名规范（`logfix-ai_{日期}.log`）已正确实现

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P2 → P1)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories (Phase 3-6) can start in parallel
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: T026 "Contract test: POST /api/validate/regex 验证有效正则"
Task: T027 "Contract test: POST /api/validate/regex 拒绝无效正则"
Task: T028 "Contract test: POST /api/split 执行正则切分"
Task: T029 "Integration test: 完整正则切分流程"

# Launch all models for User Story 2 together:
Task: T030 "实现 SplitSession 模型的状态管理方法"
Task: T031 "实现 SplitResult 模型的片段存储方法"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 + 4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (文件上传预览)
4. Complete Phase 4: User Story 2 (正则切分)
5. Complete Phase 6: User Story 4 (结果查看复制)
6. **STOP and VALIDATE**: Test MVP independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (上传预览)
   - Developer B: User Story 2 (正则切分)
   - Developer C: User Story 3 (固定分隔符)
   - Developer D: User Story 4 (结果查看复制)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- 确保关键实现任务包含结构化日志任务和主应用集成验证任务
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
