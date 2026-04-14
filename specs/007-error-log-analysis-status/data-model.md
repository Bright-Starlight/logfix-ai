# Data Model: 错误日志修复计划状态

**Branch**: `007-error-log-analysis-status` | **Date**: 2026-04-14

## 1. 实体设计

### 1.1 AnalysisSession（分析会话）

```python
class AnalysisSession(Base):
    """分析会话实体 - 用于修复计划分析任务跟踪"""

    __tablename__ = "analysis_sessions"
    __table_args__ = (
        Index("idx_analysis_session_log_entry", "log_entry_id"),
        Index("idx_analysis_session_status", "status"),
        Index("idx_analysis_session_created", "created_at"),
        {"comment": "修复计划分析会话表，记录分析任务的队列和执行状态"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    log_entry_id = Column(BigInteger, ForeignKey("log_entries.id"), nullable=False, comment="关联的日志条目ID")
    status = Column(String(20), nullable=False, default="pending", comment="状态：pending/queued/processing/completed/failed/cancelled")
    queue_position = Column(Integer, nullable=True, comment="队列位置（仅queued时有效）")
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    started_at = Column(DateTime, nullable=True, comment="开始执行时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
```

**状态转换**：
```
pending → queued → processing → completed
                    → failed
          → cancelled（用户取消）
```

### 1.2 FixPlan（修复计划）

```python
class FixPlan(Base):
    """修复计划实体"""

    __tablename__ = "fix_plans"
    __table_args__ = (
        Index("idx_fix_plan_log_entry", "log_entry_id"),
        Index("idx_fix_plan_session", "session_id"),
        {"comment": "修复计划表，存储AI生成的修复计划详情"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    log_entry_id = Column(BigInteger, ForeignKey("log_entries.id"), nullable=False, unique=True, comment="关联的日志条目ID")
    session_id = Column(BigInteger, ForeignKey("analysis_sessions.id"), nullable=True, comment="关联的分析会话ID")
    root_cause = Column(Text, nullable=False, comment="问题根因分析")
    fix_steps = Column(JSON, nullable=False, comment="修复步骤建议列表（JSON数组）")
    code_locations = Column(JSON, nullable=False, comment="相关代码位置列表（JSON数组）")
    confidence = Column(Float, nullable=False, comment="置信度 0-1")
    impact_assessment = Column(Text, nullable=False, comment="影响范围评估")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    log_entry: Mapped["LogEntry"] = relationship("LogEntry", back_populates="fix_plan")
    session: Mapped["AnalysisSession"] = relationship("AnalysisSession", back_populates="fix_plan")
```

### 1.3 LogEntry 扩展

```python
class LogEntry(Base):
    # ... 现有字段 ...

    # 新增字段
    analysis_status = Column(String(20), nullable=False, default="un_analyzed", comment="分析状态：un_analyzed/analyzing/completed/failed")

    # 关系
    fix_plan: Mapped[Optional["FixPlan"]] = relationship("FixPlan", back_populates="log_entry", uselist=False)
    analysis_sessions: Mapped[List["AnalysisSession"]] = relationship("AnalysisSession", back_populates="log_entry")
```

## 2. 数据关系

```
LogEntry (1) ────── (1) FixPlan
    │                      │
    │                      │
    └──── (1) ───── AnalysisSession ──── (0..1) FixPlan
                   │
                   └── queue_position: Int?
                   └── status: pending/queued/processing/completed/failed/cancelled
```

## 3. 验证规则

| 字段 | 验证规则 |
|------|----------|
| `analysis_status` | 仅允许：un_analyzed, analyzing, completed, failed |
| `FixPlan.confidence` | 范围 0.0 - 1.0 |
| `FixPlan.fix_steps` | 非空数组，每个步骤非空字符串 |
| `FixPlan.code_locations` | 非空数组，每个位置包含 file_path |
| `AnalysisSession.queue_position` | 仅在 status=queued 时有效，正整数 |

## 4. 索引设计

| 索引名 | 字段 | 用途 |
|--------|------|------|
| idx_fix_plan_log_entry | log_entry_id | 查找某日志的修复计划 |
| idx_analysis_session_log_entry | log_entry_id | 查找某日志的分析历史 |
| idx_analysis_session_status | status | 按状态查询任务 |

## 5. 枚举值说明

### analysis_status（日志分析状态）
- `un_analyzed`：未分析
- `analyzing`：分析中
- `completed`：分析完成
- `failed`：分析失败

**Note**: 与 spec.md FR-001 保持一致，使用 un_analyzed 而非 pending

### AnalysisSession.status（任务状态）
- `pending`：等待入队
- `queued`：排队中
- `processing`：执行中
- `completed`：已完成
- `failed`：失败
- `cancelled`：已取消
