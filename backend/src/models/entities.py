"""
实体模型定义

包含 LogFile、SplitSession、SplitResult、LogCategory、LogEntry、ParseRule、IgnoreRule、LogStatistics 实体。
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, BigInteger, Text, Integer, DateTime, ForeignKey, Index, Boolean, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.src.db.session import Base


class LogFile(Base):
    """日志文件实体"""

    __tablename__ = "log_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    encoding = Column(String(32), nullable=False, default="utf-8")
    storage_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关联关系
    sessions: Mapped[List["SplitSession"]] = relationship("SplitSession", back_populates="log_file")

    def __repr__(self) -> str:
        return f"<LogFile(id={self.id}, filename={self.filename})>"


class SplitSession(Base):
    """切分会话实体"""

    __tablename__ = "split_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("log_files.id"), nullable=False)
    rule_type = Column(String(32), nullable=False)
    rule_content = Column(Text, nullable=False)
    status = Column(String(16), nullable=False, default="pending")
    total_chunks = Column(Integer, default=0)
    processed_chunks = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    log_file: Mapped["LogFile"] = relationship("LogFile", back_populates="sessions")
    results: Mapped[List["SplitResult"]] = relationship("SplitResult", back_populates="session")

    # 索引
    __table_args__ = (
        Index("ix_split_sessions_file_id", "file_id"),
        Index("ix_split_sessions_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<SplitSession(id={self.id}, status={self.status})>"


class SplitResult(Base):
    """切分结果实体"""

    __tablename__ = "split_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("split_sessions.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # 关联关系
    session: Mapped["SplitSession"] = relationship("SplitSession", back_populates="results")

    # 索引
    __table_args__ = (
        Index("ix_split_results_session_id", "session_id"),
        Index("ix_split_results_session_chunk", "session_id", "chunk_index"),
    )

    def __repr__(self) -> str:
        return f"<SplitResult(session_id={self.session_id}, chunk={self.chunk_index})>"


# ============ 002-short-name-structured 新增实体 ============


class LogCategory(Base):
    """日志分类实体"""

    __tablename__ = "log_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    sort_order = Column(Integer, default=0)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    entries: Mapped[List["LogEntry"]] = relationship("LogEntry", back_populates="category")
    statistics: Mapped[List["LogStatistics"]] = relationship("LogStatistics", back_populates="category")

    def __repr__(self) -> str:
        return f"<LogCategory(id={self.id}, name={self.name})>"


class LogEntry(Base):
    """日志条目实体"""

    __tablename__ = "log_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_message = Column(Text, nullable=False)
    normalized_message = Column(String(500), nullable=False, index=True)
    stack_trace = Column(Text, nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("log_categories.id"), nullable=True, index=True)
    error_type = Column(String(100), nullable=True, index=True)
    extracted_params = Column(JSON, nullable=True)
    log_level = Column(String(20), nullable=True, index=True)
    occurrence_count = Column(Integer, default=1)
    first_seen_at = Column(DateTime, nullable=False, default=datetime.now)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.now)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    category: Mapped[Optional["LogCategory"]] = relationship("LogCategory", back_populates="entries")

    # 索引
    __table_args__ = (
        Index("idx_normalized_message", "normalized_message"),
        Index("idx_category_id", "category_id"),
        Index("idx_error_type", "error_type"),
        Index("idx_log_level", "log_level"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<LogEntry(id={self.id}, error_type={self.error_type}, occurrence_count={self.occurrence_count})>"


class ParseRule(Base):
    """解析规则实体（规则引擎模式）"""

    __tablename__ = "parse_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(20), nullable=False)  # regex / code
    pattern = Column(Text, nullable=True)
    code = Column(Text, nullable=True)
    group_index = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 索引
    __table_args__ = (
        Index("idx_enabled_priority", "enabled", "priority"),
    )

    def __repr__(self) -> str:
        return f"<ParseRule(id={self.id}, name={self.name}, rule_type={self.rule_type})>"


class IgnoreRule(Base):
    """忽略规则实体"""

    __tablename__ = "ignore_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    match_type = Column(String(20), nullable=False)  # contains / regex / exact
    pattern = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 索引
    __table_args__ = (
        Index("idx_enabled", "enabled"),
    )

    def __repr__(self) -> str:
        return f"<IgnoreRule(id={self.id}, name={self.name}, match_type={self.match_type})>"


class LogStatistics(Base):
    """日志统计实体"""

    __tablename__ = "log_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("log_categories.id"), nullable=True)
    entry_count = Column(Integer, nullable=False, default=0)
    unique_error_count = Column(Integer, nullable=False, default=0)
    total_occurrence = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    category: Mapped[Optional["LogCategory"]] = relationship("LogCategory", back_populates="statistics")

    # 索引
    __table_args__ = (
        Index("idx_date_category", "date", "category_id"),
    )

    def __repr__(self) -> str:
        return f"<LogStatistics(date={self.date}, entry_count={self.entry_count})>"
