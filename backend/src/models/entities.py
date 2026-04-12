"""
实体模型定义

包含 LogFile、SplitSession、SplitResult、LogCategory、LogEntry、ParseRule、IgnoreRule、LogStatistics 实体。
所有表必须包含表注释和字段注释，主键ID使用Long类型。
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, BigInteger, Text, Integer, DateTime, ForeignKey, Index, Boolean, Date, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.src.db.session import Base


class LogFile(Base):
    """日志文件实体"""

    __tablename__ = "log_files"
    __table_args__ = {"comment": "日志文件表，存储上传的日志文件元信息"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    filename = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")
    encoding = Column(String(32), nullable=False, default="utf-8", comment="文件编码")
    storage_path = Column(String(512), nullable=False, comment="存储路径")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    sessions: Mapped[List["SplitSession"]] = relationship("SplitSession", back_populates="log_file")

    def __repr__(self) -> str:
        return f"<LogFile(id={self.id}, filename={self.filename})>"


class SplitSession(Base):
    """切分会话实体"""

    __tablename__ = "split_sessions"
    __table_args__ = (
        Index("ix_split_sessions_file_id", "file_id"),
        Index("ix_split_sessions_status", "status"),
        {"comment": "日志切分会话表，记录每次切分任务的配置和状态"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    file_id = Column(BigInteger, ForeignKey("log_files.id"), nullable=False, comment="关联的日志文件ID")
    rule_type = Column(String(32), nullable=False, comment="规则类型")
    rule_content = Column(Text, nullable=False, comment="规则内容")
    status = Column(String(16), nullable=False, default="pending", comment="状态：pending/processing/completed/failed")
    total_chunks = Column(Integer, default=0, comment="总块数")
    processed_chunks = Column(Integer, default=0, comment="已处理块数")
    error_message = Column(Text, nullable=True, comment="错误信息")
    has_classification = Column(Boolean, default=False, comment="是否已完成AI分类")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    log_file: Mapped["LogFile"] = relationship("LogFile", back_populates="sessions")
    results: Mapped[List["SplitResult"]] = relationship("SplitResult", back_populates="session")
    classification_session: Mapped["ClassificationSession"] = relationship(
        "ClassificationSession", back_populates="split_session", uselist=False
    )

    def __repr__(self) -> str:
        return f"<SplitSession(id={self.id}, status={self.status})>"


class SplitResult(Base):
    """切分结果实体"""

    __tablename__ = "split_results"
    __table_args__ = (
        Index("ix_split_results_session_id", "session_id"),
        Index("ix_split_results_session_chunk", "session_id", "chunk_index"),
        {"comment": "日志切分结果表，存储每块日志的内容和位置信息"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    session_id = Column(BigInteger, ForeignKey("split_sessions.id"), nullable=False, comment="关联的切分会话ID")
    chunk_index = Column(Integer, nullable=False, comment="块索引")
    start_line = Column(Integer, nullable=False, comment="起始行号")
    end_line = Column(Integer, nullable=False, comment="结束行号")
    content = Column(Text, nullable=False, comment="日志内容")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    session: Mapped["SplitSession"] = relationship("SplitSession", back_populates="results")

    def __repr__(self) -> str:
        return f"<SplitResult(session_id={self.session_id}, chunk={self.chunk_index})>"


class LogCategory(Base):
    """日志分类实体"""

    __tablename__ = "log_categories"
    __table_args__ = {"comment": "日志分类表，定义日志的分类体系，如ERROR/WARN/INFO等"}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, unique=True, comment="分类名称")
    description = Column(Text, nullable=True, comment="分类描述")
    color = Column(String(7), nullable=True, comment="分类颜色（十六进制）")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    is_system = Column(Boolean, default=False, comment="是否为系统内置分类")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    entries: Mapped[List["LogEntry"]] = relationship("LogEntry", back_populates="category")
    statistics: Mapped[List["LogStatistics"]] = relationship("LogStatistics", back_populates="category")

    def __repr__(self) -> str:
        return f"<LogCategory(id={self.id}, name={self.name})>"


class LogEntry(Base):
    """日志条目实体"""

    __tablename__ = "log_entries"
    __table_args__ = (
        Index("idx_category_id", "category_id"),
        Index("idx_error_type", "error_type"),
        Index("idx_log_level", "log_level"),
        Index("idx_created_at", "created_at"),
        {"comment": "日志条目表，存储结构化后的单条日志信息"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    original_message = Column(Text, nullable=False, comment="原始日志消息")
    normalized_message = Column(Text, nullable=False, comment="归一化后的日志消息")
    stack_trace = Column(Text, nullable=True, comment="堆栈跟踪信息")
    category_id = Column(BigInteger, ForeignKey("log_categories.id"), nullable=True, index=True, comment="关联的分类ID")
    error_type = Column(String(100), nullable=True, index=True, comment="错误类型")
    extracted_params = Column(JSON, nullable=True, comment="提取的参数（JSON格式）")
    log_level = Column(String(20), nullable=True, index=True, comment="日志级别：DEBUG/INFO/WARN/ERROR")
    occurrence_count = Column(Integer, default=1, comment="出现次数")
    first_seen_at = Column(DateTime, nullable=False, default=datetime.now, comment="首次出现时间")
    last_seen_at = Column(DateTime, nullable=False, default=datetime.now, comment="最近出现时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    category: Mapped[Optional["LogCategory"]] = relationship("LogCategory", back_populates="entries")

    def __repr__(self) -> str:
        return f"<LogEntry(id={self.id}, error_type={self.error_type}, occurrence_count={self.occurrence_count})>"


class ParseRule(Base):
    """解析规则实体（规则引擎模式）"""

    __tablename__ = "parse_rules"
    __table_args__ = (
        Index("idx_enabled_priority", "enabled", "priority"),
        {"comment": "解析规则表，定义日志的解析规则（正则表达式或代码）"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, nullable=True, comment="规则描述")
    rule_type = Column(String(20), nullable=False, comment="规则类型：regex/code")
    pattern = Column(Text, nullable=True, comment="正则表达式模式")
    code = Column(Text, nullable=True, comment="解析代码")
    group_index = Column(Integer, default=0, comment="捕获组索引")
    priority = Column(Integer, default=0, comment="优先级，数值越大优先级越高")
    enabled = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否为系统内置规则")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self) -> str:
        return f"<ParseRule(id={self.id}, name={self.name}, rule_type={self.rule_type})>"


class IgnoreRule(Base):
    """忽略规则实体"""

    __tablename__ = "ignore_rules"
    __table_args__ = (
        Index("idx_enabled", "enabled"),
        {"comment": "忽略规则表，定义需要忽略的日志规则"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(500), nullable=False, comment="规则名称")
    match_type = Column(String(20), nullable=False, comment="匹配类型：contains/regex/exact")
    pattern = Column(String(500), nullable=False, comment="匹配模式")
    description = Column(Text, nullable=True, comment="规则描述")
    enabled = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self) -> str:
        return f"<IgnoreRule(id={self.id}, name={self.name}, match_type={self.match_type})>"


class LogStatistics(Base):
    """日志统计实体"""

    __tablename__ = "log_statistics"
    __table_args__ = (
        Index("idx_date_category", "date", "category_id"),
        {"comment": "日志统计表，按日期和分类统计日志数量"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    date = Column(Date, nullable=False, comment="统计日期")
    category_id = Column(BigInteger, ForeignKey("log_categories.id"), nullable=True, comment="关联的分类ID")
    entry_count = Column(Integer, nullable=False, default=0, comment="日志条目数")
    unique_error_count = Column(Integer, nullable=False, default=0, comment="唯一错误数")
    total_occurrence = Column(Integer, nullable=False, default=0, comment="总出现次数")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    category: Mapped[Optional["LogCategory"]] = relationship("LogCategory", back_populates="statistics")

    def __repr__(self) -> str:
        return f"<LogStatistics(date={self.date}, entry_count={self.entry_count})>"


class ClassificationSession(Base):
    """分类会话实体 - 用于进度跟踪"""

    __tablename__ = "classification_sessions"
    __table_args__ = (
        Index("idx_classification_session_status", "status"),
        Index("idx_classification_session_split", "split_session_id"),
        Index("idx_classification_session_created", "created_at"),
        {"comment": "AI分类会话表，记录分类任务的进度和统计信息"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    split_session_id = Column(BigInteger, ForeignKey("split_sessions.id"), nullable=False, comment="关联的切分会话ID")
    mode = Column(String(20), nullable=False, comment="分类模式：rule_engine/ai")
    status = Column(String(20), nullable=False, default="pending", comment="状态：pending/processing/completed/failed")
    total_items = Column(Integer, default=0, comment="待处理日志总数")
    processed_items = Column(Integer, default=0, comment="已处理数量")
    new_entries = Column(Integer, default=0, comment="新增条目数")
    duplicates = Column(Integer, default=0, comment="重复条目数")
    ignored = Column(Integer, default=0, comment="忽略条目数")
    current_phase = Column(String(50), nullable=True, comment="当前阶段名称")
    estimated_remaining_seconds = Column(Integer, nullable=True, comment="预估剩余秒数")
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    split_session: Mapped["SplitSession"] = relationship("SplitSession", back_populates="classification_session")

    def __repr__(self) -> str:
        return f"<ClassificationSession(id={self.id}, status={self.status}, mode={self.mode})>"


class TokenUsage(Base):
    """Token 使用记录实体 - 用于追踪 AI API 调用消耗"""

    __tablename__ = "token_usage"
    __table_args__ = (
        Index("idx_token_usage_user_id", "user_id"),
        Index("idx_token_usage_session_id", "session_id"),
        Index("idx_token_usage_method", "method"),
        Index("idx_token_usage_created", "created_at"),
        {"comment": "Token使用记录表，追踪AI API调用的token消耗"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(String(100), nullable=True, comment="用户标识")
    session_id = Column(BigInteger, ForeignKey("classification_sessions.id"), nullable=True, comment="关联的分类会话ID")
    method = Column(String(32), nullable=False, comment="调用方式：tool_call/prompt_engineering")
    input_tokens = Column(Integer, nullable=False, default=0, comment="输入Token数")
    output_tokens = Column(Integer, nullable=False, default=0, comment="输出Token数")
    total_tokens = Column(Integer, nullable=False, default=0, comment="总Token数")
    model = Column(String(50), nullable=False, comment="模型名称")
    batch_size = Column(Integer, nullable=True, comment="处理的批次大小")
    batch_index = Column(Integer, nullable=True, comment="批次索引")
    processing_time_ms = Column(Integer, nullable=True, comment="处理耗时（毫秒）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    classification_session: Mapped[Optional["ClassificationSession"]] = relationship(
        "ClassificationSession", backref="token_usages"
    )

    def __repr__(self) -> str:
        return f"<TokenUsage(id={self.id}, method={self.method}, total_tokens={self.total_tokens})>"
