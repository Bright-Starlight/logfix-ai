# Data Model: 003 日志分析流水线

> 扩展现有数据模型，新增分类会话和进度跟踪实体。

## 新增实体

### ClassificationSession（分类会话）

关联切分结果与分类处理过程。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 会话唯一标识 |
| split_session_id | UUID | FK → SplitSession | 关联的切分会话 |
| mode | VARCHAR(20) | NOT NULL | 分类模式：`rule_engine` 或 `ai` |
| status | VARCHAR(20) | NOT NULL | 状态：`pending`、`processing`、`completed`、`failed` |
| total_items | INT | DEFAULT 0 | 待处理日志总数 |
| processed_items | INT | DEFAULT 0 | 已处理数量 |
| current_phase | VARCHAR(50) | | 当前阶段名称 |
| estimated_remaining_seconds | INT | | 预估剩余时间（秒） |
| error_message | TEXT | NULL | 失败时的错误信息 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 最后更新时间 |
| completed_at | DATETIME | NULL | 完成时间 |

**状态转换**:
```
pending → processing → completed
                   ↘ failed
```

### 扩展现有实体

#### SplitSession（已在001定义）

新增字段支持与 ClassificationSession 的关联：

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| has_classification | BOOLEAN | DEFAULT FALSE | 是否已启动分类 |
| classification_session_id | UUID | NULL, FK → ClassificationSession | 关联的分类会话 |

## 关系

```
SplitSession (1) ←→ (0..1) ClassificationSession
     ↓
SplitResult (1) ←→ (N) LogEntry（002已有）
```

## 验证规则

1. **ClassificationSession.mode**: 只能是 `rule_engine` 或 `ai`
2. **ClassificationSession.status**: 必须是有效状态枚举值
3. **ClassificationSession.processed_items**: 不能超过 total_items
4. **ClassificationSession.estimated_remaining_seconds**: 处理完成后应为0或NULL

## 索引

- `idx_classification_session_status`: (status) - 用于查询进行中的分类任务
- `idx_classification_session_split`: (split_session_id) - 用于查找某切分会话的分类结果
- `idx_classification_session_created`: (created_at) - 用于按时间排序

## 约束

- 同一 SplitSession 同时只能有一个进行中的 ClassificationSession（pending 或 processing）
