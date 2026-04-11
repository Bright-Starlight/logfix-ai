# Task List: 日志分析完整流程集成

**Feature**: 003-log-analysis-pipeline
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

## 任务统计

- **总任务数**: 28
- **用户故事数**: 5
- **MVP 任务数**: 12（US1 + US2.1 核心）

## 阶段结构

### Phase 1: 基础设施

> 铺垫工作，为所有用户故事准备条件

### Phase 2: 基础层

> 必须完成才能开始用户故事的前置任务

### Phase 3: 用户故事 1 - 完整日志分析流程 (P1)

> 核心集成场景：上传→切分→分类→存储→展示

### Phase 4: 用户故事 2 - 切分结果直接分类 (P1)

> 切分完成后自动进入分类流程

### Phase 5: 用户故事 2.1 - 后台处理进度显示 (P1)

> 实时显示分类处理进度条

### Phase 6: 用户故事 3 - 分类结果页面查看 (P2)

> 日志列表搜索过滤

### Phase 7: 用户故事 4 - 忽略规则配置 (P2)

> 噪音日志过滤配置

### Phase 8: 用户故事 5 - 分类统计概览 (P3)

> 统计面板

### Phase 9: 收尾与跨领域

> 文档、测试补全、配置

---

## Phase 1: 基础设施

- [ ] T001 新增 ClassificationSession 实体字段 in `backend/src/models/entities.py`
  - 新增字段: mode, status, total_items, processed_items, current_phase, estimated_remaining_seconds, error_message, completed_at
  - 参考 `specs/003-log-analysis-pipeline/data-model.md`

- [ ] T002 新增 ClassificationSession Pydantic Schema in `backend/src/api/schemas.py`
  - 新增: ClassificationStartRequest, ClassificationProgressResponse, ClassificationResultResponse

- [ ] T003 [P] 创建后端进度跟踪单元测试骨架 in `backend/tests/unit/test_classification_progress.py`
  - 测试用例: 测试进度状态枚举, 测试进度计算逻辑

- [ ] T004 [P] 创建前端进度 hook 单元测试骨架 in `frontend/tests/unit/test_classification_progress.ts`
  - 测试用例: 测试轮询逻辑, 测试状态转换

---

## Phase 2: 基础层

- [ ] T005 实现 ClassificationSession 数据库更新 in `backend/src/models/entities.py`
  - 修改 SplitSession entity: 新增 classification_session_id 外键
  - 添加数据库索引

- [ ] T006 实现 POST /api/classification/start 端点 in `backend/src/api/routes.py`
  - 参数验证: split_session_id, mode
  - 冲突检测: 同一切分会话只能有一个进行中的分类任务
  - 返回: session_id, status

- [ ] T007 实现 GET /api/classification/{session_id}/progress 端点 in `backend/src/api/routes.py`
  - 进度计算: processed_items / total_items * 100
  - 预估时间: 基于已处理速度计算
  - 状态枚举转换

- [ ] T008 [P] 实现 GET /api/classification/{session_id}/result 端点 in `backend/src/api/routes.py`
  - 返回分类结果摘要: new_entries, duplicates, ignored, completed_at

- [ ] T009 修改 classification_service.py 支持异步进度上报 in `backend/src/services/classification_service.py`
  - 新增 update_progress() 函数: 更新 processed_items, current_phase
  - 分类循环中调用 update_progress(): 每个日志处理后更新进度
  - 支持阶段名称: "去重检测中", "忽略规则过滤中", "分类分析中", "存储中"

- [ ] T010 新增 useClassificationProgress hook in `frontend/src/hooks/useClassificationProgress.ts`
  - 轮询逻辑: 每2秒请求一次 /api/classification/{session_id}/progress
  - 状态管理: pending → processing → completed/failed
  - 自动停止: 状态为 completed 或 failed 时停止轮询

---

## Phase 3: 用户故事 1 - 完整日志分析流程 (P1)

**故事目标**: 用户完成从文件上传到分类存储的完整流程

**独立测试标准**: 可通过上传日志→切分→分类→验证数据库记录完成全流程测试

- [ ] T011 [P] [US1] 新增 ClassificationModeSelect 组件 in `frontend/src/components/ClassificationModeSelect.tsx`
  - 两个选项: "规则引擎模式" 和 "AI 模式"
  - 选中状态样式
  - 确认按钮触发分类启动

- [ ] T012 [US1] 修改 LogSplit 切分完成后逻辑 in `frontend/src/components/ResultList.tsx`
  - 切分状态变为 completed 后自动显示 ClassificationModeSelect 组件
  - 传递 split_session_id 给分类流程

- [ ] T013 [US1] 串联切分和分类流程 in `frontend/src/components/ResultList.tsx`
  - 用户选择分类模式后调用 POST /api/classification/start
  - 获取 classification_session_id
  - 启动进度轮询

- [ ] T014 [US1] 验证切分→分类完整流程 in `backend/tests/integration/test_classification_pipeline.py`
  - 测试用例: 上传文件→切分→启动分类→验证分类结果
  - 验证数据一致性: 切分片段数 vs 分类输入数

---

## Phase 4: 用户故事 2 - 切分结果直接分类 (P1)

**故事目标**: 切分完成后自动进入分类，无需手动触发

**独立测试标准**: 切分状态完成后自动显示分类选择界面，不需用户额外操作

- [ ] T015 [US2] 验证自动显示分类选择 in `frontend/src/components/ResultList.tsx`
  - 监听切分状态变化
  - 状态为 completed 时自动渲染 ClassificationModeSelect

- [ ] T016 [US2] 分类模式切换重置进度 in `frontend/src/components/ClassificationModeSelect.tsx`
  - 用户切换分类模式后重新调用 /api/classification/start
  - 保留之前的分类结果或清除

---

## Phase 5: 用户故事 2.1 - 后台处理进度显示 (P1)

**故事目标**: 实时显示分类处理进度，包括百分比、阶段名称、预估剩余时间

**独立测试标准**: 启动分类后进度条实时更新，刷新页面进度恢复

- [ ] T017 [P] [US2.1] 新增 ProgressBar 组件 in `frontend/src/components/ProgressBar.tsx`
  - 显示: 百分比数字, 进度条, 当前阶段名称, 预估剩余时间
  - 动画: 进度条平滑过渡
  - 完成状态: 显示100%并展示处理结果摘要

- [ ] T018 [US2.1] 集成 ProgressBar 到分类流程 in `frontend/src/components/ResultList.tsx`
  - 启动分类后显示 ProgressBar
  - 接收 useClassificationProgress hook 的状态和数据
  - 刷新后进度条恢复而非重置

- [ ] T019 [US2.1] 验证进度恢复 in `frontend/tests/unit/test_classification_progress.ts`
  - 测试用例: 刷新页面后进度条显示正确进度而非0%

---

## Phase 6: 用户故事 3 - 分类结果页面查看 (P2)

**故事目标**: 用户可查看已存储的分类日志列表，支持搜索过滤

**独立测试标准**: 可通过 GET /api/logs 验证分页、搜索、过滤功能

- [ ] T020 [P] [US3] 验证 LogList 组件可显示分类结果 in `frontend/src/components/LogList.tsx`
  - 检查 LogList 是否使用 /api/logs 数据源
  - 验证字段映射: normalized_message, category, error_type, occurrence_count

- [ ] T021 [P] [US3] 验证 SearchFilter 组件集成 in `frontend/src/components/SearchFilter.tsx`
  - 关键词搜索: 调用 /api/logs?keyword=xxx
  - 分类过滤: 调用 /api/logs?category=xxx
  - 时间范围: 调用 /api/logs?start_date=xxx&end_date=xxx

- [ ] T022 [US3] 新增 AnalysisPipeline 汇总页面 in `frontend/src/pages/AnalysisPipeline.tsx`
  - 整合: 文件上传 → 切分配置 → 切分结果 → 分类模式选择 → 进度条 → 分类结果列表
  - 统一状态管理

- [ ] T023 [US3] 修改 App.tsx 添加路由 in `frontend/src/App.tsx`
  - 添加 /pipeline 路由指向 AnalysisPipeline 页面
  - 保持现有路由兼容

---

## Phase 7: 用户故事 4 - 忽略规则配置 (P2)

**故事目标**: 管理员可配置忽略规则过滤噪音日志

**独立测试标准**: 配置忽略规则后相关日志不被存储

- [ ] T024 [US4] 验证 ignore_rules API 集成 in `backend/src/api/routes.py`
  - GET /api/ignore-rules 已存在
  - POST /api/ignore-rules 已存在
  - DELETE /api/ignore-rules/{id} 已存在

- [ ] T025 [US4] 验证前端忽略规则管理界面 in `frontend/src/components`
  - 检查是否有 ignore-rule 管理组件
  - 如无: 创建 IgnoreRuleManager 组件

---

## Phase 8: 用户故事 5 - 分类统计概览 (P3)

**故事目标**: 显示分类分布和趋势统计

**独立测试标准**: 可通过 GET /api/stats 验证统计数据正确性

- [ ] T026 [P] [US5] 验证 StatsPanel 组件 in `frontend/src/components/StatsPanel.tsx`
  - 验证调用 /api/stats API
  - 验证图表数据格式

- [ ] T027 [P] [US5] 验证统计组件集成到 AnalysisPipeline in `frontend/src/pages/AnalysisPipeline.tsx`
  - 分类完成后显示统计面板入口
  - 可切换查看统计视图

---

## Phase 9: 收尾与跨领域

- [ ] T028 验证 flow.md 流程图 in `specs/003-log-analysis-pipeline/flow.md`
  - 确认 Mermaid 语法正确
  - 确认所有用户故事流程已覆盖

- [ ] T029 更新后端 API 文档注释 in `backend/src/api/routes.py`
  - 新增端点: /api/classification/start, /api/classification/{id}/progress, /api/classification/{id}/result

- [ ] T030 运行后端单元测试 in `backend/tests/`
  - pytest tests/unit/test_classification_progress.py
  - pytest tests/integration/test_classification_pipeline.py

- [ ] T031 运行前端单元测试 in `frontend/tests/`
  - vitest tests/unit/test_classification_progress.ts

---

## 并行执行机会

| 任务组合 | 可并行原因 | 依赖 |
|----------|-----------|------|
| T003 + T004 | 测试骨架创建，无依赖 | 无 |
| T006 + T007 + T008 | 不同 API 端点，无数据依赖 | T001, T002 |
| T011 + T017 | 不同组件，无共享状态 | 无 |
| T020 + T021 | 不同功能模块，无共享状态 | 无 |
| T026 + T027 | 不同功能模块，无共享状态 | 无 |

---

## MVP 范围

**MVP 交付**: US1 + US2.1（任务 T001-T019）

MVP 验收标准:
1. 后端进度 API 正常工作
2. 前端显示进度条
3. 完整流程: 上传→切分→分类→存储→展示

---

## 依赖关系图

```
Phase 1 (基础设施)
├── T001: ClassificationSession 实体
├── T002: Pydantic Schema
├── T003: 后端测试骨架
└── T004: 前端测试骨架
    ↓
Phase 2 (基础层)
├── T005: 数据库更新
├── T006: POST /classification/start
├── T007: GET /classification/{id}/progress
├── T008: GET /classification/{id}/result
├── T009: 异步进度上报
└── T010: useClassificationProgress hook
    ↓
Phase 3-8 (用户故事，按优先级)
└── US1 → US2 → US2.1 → US3 → US4 → US5
```

---

## 快速验证命令

```bash
# 后端测试
cd backend && pytest tests/unit/test_classification_progress.py -v

# 前端测试
cd frontend && vitest run tests/unit/test_classification_progress.ts

# 手动 API 测试
curl -X POST http://localhost:8000/api/classification/start \
  -H "Content-Type: application/json" \
  -d '{"split_session_id": "<id>", "mode": "rule_engine"}'

curl http://localhost:8000/api/classification/<session_id>/progress
```
