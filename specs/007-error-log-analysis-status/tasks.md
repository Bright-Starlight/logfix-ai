# Tasks: 错误日志修复计划状态

**Branch**: `007-error-log-analysis-status` | **Date**: 2026-04-14
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## 任务总览

| 用户故事 | 任务数 | 独立测试标准 |
|----------|--------|--------------|
| User Story 1 (P1) | 12 | 选中日志 → 点击生成 → 状态变分析中 → 分析完成 → 查看修复计划 |
| User Story 2 (P2) | 3 | 同时触发多条日志 → 验证排队顺序 → 队列满时拒绝新请求 |
| User Story 3 (P3) | 3 | 分析完成日志 → 点击查看修复计划 |
| 基础设施 | 1 | - |

**总任务数**: 19
**MVP范围**: User Story 1 全部 + User Story 2 队列基础 + US3 修复计划查看

## 实现策略

**MVP优先**: 先实现User Story 1（核心功能），再实现User Story 2（队列管理），最后User Story 3（查看修复计划）

---

## Phase 1: Setup（项目初始化）

- [x] T001 创建数据库迁移脚本，添加 analysis_status 字段到 log_entries 表
  `backend/src/models/entities.py`
- [x] T002 创建数据库迁移脚本，新建 analysis_sessions 表（AnalysisSession实体）
  `backend/src/models/entities.py`
- [x] T003 创建数据库迁移脚本，新建 fix_plans 表（FixPlan实体）
  `backend/src/models/entities.py`
- [x] T004 前端添加 AnalysisStatus 和 FixPlan 类型定义
  `frontend/src/types/index.ts`

---

## Phase 2: Foundational（用户故事前置依赖）

- [x] T005 创建 AnalysisQueue 类，实现入队/出队/取消逻辑
  `backend/src/services/analysis_queue.py`
- [x] T006 创建 FixPlanService 基础结构（空方法）
  `backend/src/services/fix_plan_service.py`
- [x] T007 扩展 AI Agent Tool Call Schema，新增 generate_fix_plan 工具
  `backend/src/services/ai_analyzer.py`
- [x] T008 后端API路由：POST /api/analysis/start
  `backend/src/api/routes.py`
- [x] T009 后端API路由：GET /api/analysis/status/{log_entry_id}
  `backend/src/api/routes.py`
- [x] T010 后端API路由：GET /api/analysis/fix-plan/{log_entry_id}
  `backend/src/api/routes.py`
- [x] T011 后端API路由：POST /api/analysis/cancel/{log_entry_id}
  `backend/src/api/routes.py`
- [x] T012 后端SSE端点：GET /api/analysis/stream/{session_id}
  `backend/src/api/routes.py`

---

## Phase 3: User Story 1 - 单条日志修复计划生成 [US1]

**目标**: 用户点击"生成修复计划"按钮 → AI分析 → 生成修复计划

### 3.1 实体关系 [US1]

- [x] T013 [P] [US1] 在 LogEntry 实体添加 analysis_status 字段和关系定义
  `backend/src/models/entities.py`

### 3.2 服务层 [US1]

- [x] T014 [US1] 实现 FixPlanService.generate_fix_plan() 方法
  `backend/src/services/fix_plan_service.py`
- [x] T015 [US1] 实现 AnalysisQueue 与 FixPlanService 的集成
  `backend/src/services/analysis_queue.py`

### 3.3 API端点 [US1]

- [x] T016 [US1] 实现 POST /api/analysis/start 的完整逻辑（检查仓库→入队→返回）
  `backend/src/api/routes.py`
- [x] T017 [US1] 实现 GET /api/analysis/status/{log_entry_id} 的完整逻辑
  `backend/src/api/routes.py`
- [x] T018 [US1] 实现 SSE /api/analysis/stream/{session_id} 的完整逻辑
  `backend/src/api/routes.py`

### 3.4 前端组件 [US1]

- [x] T019 [P] [US1] 创建 useAnalysisProgress hook
  `frontend/src/hooks/useAnalysisProgress.ts`
- [x] T020 [P] [US1] 创建 useAnalysisQueue hook
  `frontend/src/hooks/useAnalysisQueue.ts`
- [x] T021 [US1] 扩展 LogList 组件，添加分析状态标签
  `frontend/src/components/LogList.tsx`
- [x] T022 [US1] 扩展 LogList 组件，添加"生成修复计划"按钮
  `frontend/src/components/LogList.tsx`
- [x] T023 [US1] 添加前端API调用方法 startAnalysis, getAnalysisStatus
  `frontend/src/services/api.ts`

---

## Phase 4: User Story 2 - AI Agent排队分析 [US2]

**目标**: 队列管理（最大5个任务：1执行中+4排队中）、队列满拒绝

- [x] T024 [US2] 实现 AnalysisQueue 队列满检查（max=5，含1执行中+4排队中）
  `backend/src/services/analysis_queue.py`
- [x] T025 [US2] 实现队列满时返回 QUEUE_FULL 错误
  `backend/src/api/routes.py`
- [x] T026 [US2] 实现分析完成自动出队并处理下一任务
  `backend/src/services/analysis_queue.py`

---

## Phase 5: User Story 3 - 修复计划查看 [US3]

**目标**: 查看已生成的修复计划

- [x] T027 [US3] 创建 FixPlanViewer 组件
  `frontend/src/components/FixPlanViewer.tsx`
- [x] T028 [US3] 实现 GET /api/analysis/fix-plan/{log_entry_id} 返回修复计划
  `backend/src/api/routes.py`
- [x] T029 [US3] LogList 中"分析完成"状态显示"查看修复计划"按钮
  `frontend/src/components/LogList.tsx`

---

## Phase 6: Integration Verification（宪法VIII要求 - MVP必须）

> 宪法VIII条要求 `/speckit.implement` 完成后必须执行集成验证

- [x] T030 集成验证：确认 LogList 正确导入并使用新组件
  `frontend/src/pages/AnalysisPipeline.tsx`
  **验证项**: 代码阅读确认组件导入、渲染、状态连接、用户入口

---

## 依赖关系图

```
Phase 1 (Setup)
    │
    ├── T001, T002, T003（数据库迁移）
    │
    ▼
Phase 2 (Foundational)
    │
    ├── T005（队列基类）
    ├── T007（AI扩展）
    ├── T008-T012（API路由）
    │
    ▼
Phase 3 (US1 - 核心分析流程) ──► Phase 5 (US3 - 查看修复计划)
    │
    ▼
Phase 4 (US2 - 队列管理)
    │
    ├── T024, T025, T026（队列逻辑）
    │
    ▼
Phase 6 (Integration Verification)
```

---

## 独立测试场景

### US1 独立测试

1. 日志状态为 un_analyzed → 点击"生成修复计划" → 状态变为 analyzing
2. 状态为 analyzing → SSE返回进度 → 进度更新到UI
3. SSE返回 result → 修复计划生成 → 状态变为 completed
4. 状态为 completed → 查看修复计划 → 显示根因、步骤、代码位置

### US2 独立测试

1. 触发一条分析 → 队列长度=1
2. 触发5条分析 → 队列长度=5
3. 触发第6条分析 → 返回 QUEUE_FULL 错误

### US3 独立测试

1. 状态为 completed → 点击"查看修复计划" → 弹出/显示修复计划详情

---

## MVP交付范围

**MVP = US1 完整 + US2 队列基础 + US3 修复计划查看**

**MVP必须包含**:
- Phase 1: T001-T004（数据库实体 + 前端类型）
- Phase 2: T005-T012（核心服务 + API路由）
- Phase 3: T013-T023（US1 完整功能）
- Phase 4: T024-T026（US2 队列管理）
- Phase 5: T027-T029（US3 修复计划查看）
- Phase 6: T030（集成验证 - 宪法VIII要求）

**不包括（可后续迭代）**:
- 取消功能（用户可取消排队中的任务）
- 重新分析功能（状态重置为un_analyzed）
- 前端 Loading/Error 状态组件
- 前端错误处理优化
- 日志埋点（OBS相关）

**MVP任务数**: T001-T030 = 30个任务
