# Tasks: 日志分类与结构化存储

**Input**: Design documents from `/specs/002-short-name-structured/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md
**Tests**: 测试任务是必填项。必须先创建并执行失败测试，再开始实现，以满足 TDD 宪法要求。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Initialize project structure and dependencies

- [ ] T001 Create backend project structure per plan.md in `backend/src/`
- [ ] T002 Create frontend project structure per plan.md in `frontend/src/`
- [ ] T003 [P] Initialize Python venv and install dependencies in `backend/requirements.txt`
- [ ] T004 [P] Configure loguru logging in `backend/src/` with `/log` directory and `logfix-ai_{date}.log` naming
- [ ] T005 [P] Create `specs/002-short-name-structured/flow.md` with Chinese Mermaid flowchart (CONSTITUTION §VII)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Setup PostgreSQL database schema with SQLAlchemy models in `backend/src/models/entities.py`
- [ ] T007 [P] Create LogCategory entity and seeder in `backend/src/models/entities.py`
- [ ] T008 [P] Create LogEntry entity in `backend/src/models/entities.py`
- [ ] T009 [P] Create ParseRule entity in `backend/src/models/entities.py`
- [ ] T010 [P] Create IgnoreRule entity in `backend/src/models/entities.py`
- [ ] T011 [P] Create LogStatistics entity in `backend/src/models/entities.py`
- [ ] T012 Configure database session management in `backend/src/db/session.py`
- [ ] T013 Setup FastAPI app entry point with CORS and middleware in `backend/src/main.py`
- [ ] T014 Configure environment variables management with python-dotenv in `backend/`
- [ ] T015 Implement API response format with extracted_params field in `backend/src/api/routes.py` (A3: data-model vs api consistency)

**Checkpoint**: Foundation ready - user story implementation can now begin

### Tests for Phase 2 Infrastructure (TDD Compliance)

> NOTE: Infrastructure tests validate database schema and API response format

- [ ] T015.1 [P] Unit test for database session management in `backend/tests/unit/test_db_session.py`
- [ ] T015.2 [P] Unit test for API response format envelope in `backend/tests/unit/test_api_response.py`

---

## Phase 3: User Story 1 - 日志自动分类与存储 (Priority: P1) MVP

**Goal**: 实现日志分类服务，自动将日志按错误类型分类并结构化存储到数据库

**Independent Test**: 向系统发送不同类型的日志数据，验证日志是否被正确分类并存储到数据库中

### Tests for User Story 1

> NOTE: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T016 [P] [US1] Contract test for POST /api/classify in `backend/tests/contract/test_classify.py`
- [ ] T017 [P] [US1] Unit test for classifier service in `backend/tests/unit/test_classifier.py`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Create LogService in `backend/src/services/log_service.py`
- [ ] T019 [P] [US1] Create ClassifierService in `backend/src/services/classifier.py`
- [ ] T020 [US1] Implement POST /api/classify endpoint in `backend/src/api/routes.py`
- [ ] T021 [US1] Add structured logging for classification operations (OBS-001)

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 - 报错信息去重存储 (Priority: P1)

**Goal**: 实现去重服务，相同错误消息只保留一条记录

**Independent Test**: 向系统发送多条错误消息相同但参数不同的日志，验证数据库中只存在一条该错误类型的记录

### Tests for User Story 2

> NOTE: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T022 [P] [US2] Integration test for deduplication in `backend/tests/integration/test_deduplication.py`
- [ ] T023 [P] [US2] Unit test for normalization in `backend/tests/unit/test_normalization.py`

### Implementation for User Story 2

- [ ] T024 [P] [US2] Create RuleEngine in `backend/src/services/rule_engine.py`
- [ ] T025 [P] [US2] Create DeduplicatorService in `backend/src/services/deduplicator.py`
- [ ] T026 [US2] Implement message normalization logic (去除参数、数字、路径)
- [ ] T027.5 [US2] Implement deduplication timeout mechanism (Spec Edge Case #4)
- [ ] T027 [US2] Integrate deduplication into POST /api/classify (OBS-002)
- [ ] T028 [US2] Add deduplication result logging (OBS-002)

**Checkpoint**: User Story 2 fully functional and testable independently

---

## Phase 5: User Story 3 - 配置忽略规则 (Priority: P2)

**Goal**: 允许管理员配置哪些错误消息不需要进行结构化存储

**Independent Test**: 配置忽略规则后发送符合规则的日志，验证这些日志不会被存储到数据库中

### Tests for User Story 3

> NOTE: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T029 [P] [US3] Contract tests for ignore-rules endpoints in `backend/tests/contract/test_ignore_rules.py`
- [ ] T030 [P] [US3] Unit test for ignore rule matching in `backend/tests/unit/test_ignore_rule_matching.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Create IgnoreRule CRUD in `backend/src/api/routes.py`
- [ ] T032 [P] [US3] Create IgnoreRuleService in `backend/src/services/ignore_rule_service.py`
- [ ] T033 [US3] Implement ignore rule matching (contains/regex/exact)
- [ ] T034 [US3] Integrate ignore rules into classification flow
- [ ] T035 [US3] Add ignore rule audit logging (OBS-003)

**Checkpoint**: User Story 3 fully functional and testable independently

---

## Phase 6: User Story 4 - 日志展示页面 (Priority: P2)

**Goal**: 提供Web页面展示已存储的日志列表，支持分页和基本导航

**Independent Test**: 浏览器访问日志展示页面，验证页面能够正常加载并显示日志列表

### Tests for User Story 4

> NOTE: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T036 [P] [US4] Contract tests for GET /api/logs in `backend/tests/contract/test_logs_list.py`
- [ ] T037 [P] [US4] Contract tests for GET /api/logs/{log_id} in `backend/tests/contract/test_log_detail.py`
- [ ] T038 [P] [US4] Frontend component tests for LogList in `frontend/tests/components/LogList.test.tsx`

### Implementation for User Story 4

Backend:
- [ ] T039 [P] [US4] Implement GET /api/logs endpoint with pagination in `backend/src/api/routes.py`
- [ ] T040 [P] [US4] Implement GET /api/logs/{log_id} endpoint in `backend/src/api/routes.py`

Frontend:
- [ ] T041 [P] [US4] Create LogList component in `frontend/src/components/LogList.tsx`
- [ ] T042 [P] [US4] Create LogDetail component in `frontend/src/components/LogDetail.tsx`
- [ ] T043 [US4] Create API service in `frontend/src/services/api.ts`
- [ ] T044 [US4] Add pagination UI with page navigation
- [ ] T045 [US4] Connect components to App.tsx routing

**Checkpoint**: User Story 4 fully functional and testable independently

---

## Phase 7: User Story 5 - 日志搜索与过滤 (Priority: P3)

**Goal**: 在日志展示页面通过关键词搜索和条件过滤快速找到日志记录

**Independent Test**: 在页面上输入搜索条件，验证返回的日志列表符合过滤条件

### Tests for User Story 5

> NOTE: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T046 [P] [US5] Contract tests for search/filter params in `backend/tests/contract/test_logs_search.py`
- [ ] T047 [P] [US5] Integration test for search functionality in `backend/tests/integration/test_search.py`

### Implementation for User Story 5

Backend:
- [ ] T048 [P] [US5] Add search/filter logic to GET /api/logs (keyword, category, level, date range) in `backend/src/api/routes.py`
- [ ] T049 [P] [US5] Add database indexes for search optimization

Frontend:
- [ ] T050 [P] [US5] Create SearchFilter component with level filter in `frontend/src/components/SearchFilter.tsx`
- [ ] T051 [US5] Integrate search/filter into LogList component

**Checkpoint**: User Story 5 fully functional and testable independently

---

## Phase 8: User Story 6 - 日志统计与摘要 (Priority: P3)

**Goal**: 提供日志统计功能，展示错误分布和趋势

**Independent Test**: 查看统计面板，验证统计数据与实际日志数据一致

### Tests for User Story 6

> NOTE: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T052 [P] [US6] Contract tests for GET /api/stats in `backend/tests/contract/test_stats.py`
- [ ] T053 [P] [US6] Integration test for statistics in `backend/tests/integration/test_statistics.py`

### Implementation for User Story 6

Backend:
- [ ] T054 [P] [US6] Implement GET /api/stats endpoint in `backend/src/api/routes.py`
- [ ] T055 [P] [US6] Implement LogStatistics aggregation in `backend/src/services/log_service.py`

Frontend:
- [ ] T056 [P] [US6] Create StatsPanel component in `frontend/src/components/StatsPanel.tsx`
- [ ] T057 [US6] Add trend visualization (simple bar chart or counts)

**Checkpoint**: User Story 6 fully functional and testable independently

---

## Phase 9: AI Mode - 规则引擎增强 (Priority: P2)

**Goal**: 支持规则引擎模式，用户可编辑规则代码进行文本解析

**Independent Test**: 创建自定义规则后发送日志，验证规则正确执行

### Tests for AI Mode

- [ ] T058 [P] [AI] Contract tests for rules CRUD in `backend/tests/contract/test_rules.py`
- [ ] T059 [P] [AI] Unit test for rule engine execution in `backend/tests/unit/test_rule_engine.py`

### Implementation for AI Mode

Backend:
- [ ] T060 [P] [AI] Create ParseRule CRUD endpoints in `backend/src/api/routes.py`
- [ ] T061 [P] [AI] Create RuleService in `backend/src/services/rule_service.py`
- [ ] T062 [AI] Implement regex rule execution in `backend/src/services/rule_engine.py`
- [ ] T063 [AI] Implement code rule execution with sandbox (eval timeout 1s)
- [ ] T064 [AI] Add validation for dangerous imports in code rules

**Checkpoint**: AI mode functional

---

## Phase 10: AI Mode - MiniMax 集成 (Priority: P2)

**Goal**: 支持AI模式，使用LangChain + Anthropic SDK调用MiniMax-M2.7进行日志分析

**Independent Test**: 配置API Key后发送日志，验证AI模式正确分类和去重

### Tests for AI Mode - AI

- [ ] T065 [P] [AI-MINIMAX] Unit test for AI analyzer prompt in `backend/tests/unit/test_ai_analyzer.py`
- [ ] T066 [P] [AI-MINIMAX] Mock integration test for AI classification in `backend/tests/integration/test_ai_mode.py`

### Implementation for AI Mode - AI

Backend:
- [ ] T067 [P] [AI-MINIMAX] Create AIAnalyzerService in `backend/src/services/ai_analyzer.py`
- [ ] T068 [P] [AI-MINIMAX] Configure ChatAnthropic with MiniMax base_url
- [ ] T069 [AI-MINIMAX] Implement AI prompt template from research.md
- [ ] T070 [AI-MINIMAX] Add AI mode switch to /api/classify endpoint
- [ ] T071 [AI-MINIMAX] Add AI service error handling (OBS-004)

Frontend:
- [ ] T072 [AI-MINIMAX] Add mode toggle in frontend for rule_engine/ai switch

**Checkpoint**: AI mode with MiniMax functional

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T072.5 [P] Add performance verification: classification <5s (SC-001) in `backend/tests/performance/test_classify_performance.py`
- [ ] T072.6 [P] Add performance verification: pagination 1000 logs (SC-004) in `backend/tests/performance/test_pagination_performance.py`
- [ ] T072.7 [P] Add performance verification: search <2s (SC-005) in `backend/tests/performance/test_search_performance.py`
- [ ] T073 [P] Add error handling for database failures with error logging (no retry per A1)
- [ ] T074 [P] Add input validation for malformed logs (skip with warning)
- [ ] T075 [P] Performance optimization: add database query indexes
- [ ] T075.5 [P] Add UI warning component in `frontend/src/components/RuleMatchWarning.tsx` to display when all logs are ignored (A2)
- [ ] T076 Add warning when ignore rules match all logs (display original error message via UI)
- [ ] T078.1 [P] Verify backend service starts successfully (http://localhost:8000/docs accessible)
- [ ] T078.2 [P] Verify frontend service starts successfully (http://localhost:5173 accessible)
- [ ] T078.3 [P] Verify database connection is working
- [ ] T078.4 [P] Verify log files output to /log directory
- [ ] T078.5 Verify rule engine mode works correctly
- [ ] T078.6 Verify AI mode works (after API key configuration)
- [ ] T078.7 Verify ParseRule CRUD operations work
- [ ] T078.8 Verify IgnoreRule CRUD operations work
- [ ] T079 Verify all user stories integrate properly
- [ ] T080 Update frontend types in `frontend/src/types/index.ts`

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends On | Description |
|-------|-----------|-------------|
| Phase 1 (Setup) | None | Project initialization |
| Phase 2 (Foundational) | Phase 1 | Core models and infrastructure |
| Phase 3-8 (US1-US6) | Phase 2 | User story implementation |
| Phase 9 (AI Rules) | Phase 2 | Rule engine enhancement |
| Phase 10 (AI MiniMax) | Phase 2 | AI integration |
| Phase 11 (Polish) | Phases 3-10 | Final polish |

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 - Core classification
- **User Story 2 (P1)**: Can start after Phase 2 - Depends on US1 classification
- **User Story 3 (P2)**: Can start after Phase 2 - Independent
- **User Story 4 (P2)**: Can start after Phase 2 - Depends on US1 storage
- **User Story 5 (P3)**: Can start after Phase 4 - Depends on US4 list
- **User Story 6 (P3)**: Can start after Phase 4 - Depends on US1 storage
- **AI Mode (P2)**: Can start after Phase 2 - Independent path

---

## Parallel Execution Opportunities

### Within Each Phase

**Phase 2 (Foundational)** - All entities (T007-T011) can run in parallel:
```bash
# Create all models simultaneously
Task T007: Create LogCategory entity
Task T008: Create LogEntry entity
Task T009: Create ParseRule entity
Task T010: Create IgnoreRule entity
Task T011: Create LogStatistics entity
```

**Phase 3 (US1)** - Classifier and LogService can be created in parallel:
```bash
Task T018: Create LogService
Task T019: Create ClassifierService
```

**Phase 4 (US2)** - RuleEngine and Deduplicator can be created in parallel:
```bash
Task T024: Create RuleEngine
Task T025: Create DeduplicatorService
```

**Phase 6 (US4 Backend)** - Both endpoints can be created in parallel:
```bash
Task T039: GET /api/logs endpoint
Task T040: GET /api/logs/{log_id} endpoint
```

### Across User Stories

Once Phase 2 is complete, these user stories can proceed in parallel:
- **US1** + **US2** (both P1, core functionality)
- **US3** (independent ignore rules)
- **AI Rules** (independent rule engine)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (MVP)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add AI Mode (Phase 9-10) → Test → Deploy
7. Add US5, US6 → Test → Deploy
8. Polish → Final release

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 93 |
| **User Stories** | 6 (US1-P1, US2-P1, US3-P2, US4-P2, US5-P3, US6-P3) |
| **AI Phases** | 2 (Rules, MiniMax) |
| **Parallelizable Tasks** | 39 (marked with [P]) |
| **MVP Scope** | User Story 1 (Phase 3) |
| **Independent Test Criteria** | Each user story has explicit test criteria |

**Fixes Applied**:
- C1: T005 marked as parallel, CONSTITUTION §VII reference added
- C2: Phase 2 infrastructure tests added (T015.1, T015.2) - verification only
- C3: Deduplication timeout task added (T027.5)
- C4: Performance verification tasks added (T072.5, T072.6, T072.7)
- A1: Database error handling changed to "error logging only" (T073)
- A2: UI warning component for ignored logs (T075.5, T076)
- A3: API response includes extracted_params (T015)
- T1: T078 split into 8 specific verification tasks
- T2: Level filter coverage added to US5 (T048, T050)
- D1: Removed duplicate T077 (deduplication timeout now only in T027.5)

---

## Verification Checklist

- [ ] All tasks follow checkbox format `- [ ]`
- [ ] All tasks have Task IDs (T001, T002, ...)
- [ ] All user story tasks have [Story] label
- [ ] All tasks include exact file paths
- [ ] [P] marker used only for parallelizable tasks
- [ ] Tests marked with ⚠️ are written first (TDD)
- [ ] Dependencies section shows completion order
- [ ] Each phase has checkpoint criteria
