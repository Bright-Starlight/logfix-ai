"""
数据库会话管理

提供数据库连接池和会话管理的功能。
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# 加载 .env 文件（从 backend/.env 加载）
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """从环境变量获取数据库URL"""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/logfix_ai"
    )
    return database_url


def init_db(database_url: Optional[str] = None) -> None:
    """初始化数据库引擎和会话工厂"""
    global _engine, _SessionLocal

    if database_url is None:
        database_url = get_database_url()

    _engine = create_engine(
        database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False,
    )

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_engine():
    """获取数据库引擎"""
    global _engine
    if _engine is None:
        init_db()
    return _engine


def get_session_factory():
    """获取会话工厂"""
    global _SessionLocal
    if _SessionLocal is None:
        init_db()
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话的依赖注入生成器"""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话的上下文管理器"""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    """创建所有表"""
    from backend.src.models.entities import (
        LogFile, SplitSession, SplitResult,
        LogCategory, LogEntry, ParseRule, IgnoreRule, LogStatistics
    )

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
