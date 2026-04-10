"""
实体模型定义

包含 LogFile、SplitSession、SplitResult 三个核心实体。
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, BigInteger, Text, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.src.db.session import Base


class LogFile(Base):
    """日志文件实体"""

    __tablename__ = "log_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    encoding = Column(String(32), nullable=False, default="utf-8")
    storage_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关联关系
    sessions: List["SplitSession"] = relationship("SplitSession", back_populates="log_file")

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    log_file: "LogFile" = relationship("LogFile", back_populates="sessions")
    results: List["SplitResult"] = relationship("SplitResult", back_populates="session")

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关联关系
    session: "SplitSession" = relationship("SplitSession", back_populates="results")

    # 索引
    __table_args__ = (
        Index("ix_split_results_session_id", "session_id"),
        Index("ix_split_results_session_chunk", "session_id", "chunk_index"),
    )

    def __repr__(self) -> str:
        return f"<SplitResult(session_id={self.session_id}, chunk={self.chunk_index})>"
