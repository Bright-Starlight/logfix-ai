"""
pytest 配置文件

设置数据库连接和测试环境。
"""

import os
import sys
import pytest

# 确保 backend 模块可导入
backend_path = os.path.join(os.path.dirname(__file__), '..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_path, '.env'))


# 验证数据库连接
def pytest_configure(config):
    """验证测试前数据库连接"""
    try:
        from backend.src.db.session import init_db, get_db_session
        from sqlalchemy import text
        init_db()
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        print("\n数据库连接验证通过")
    except Exception as e:
        print(f"\n警告: 数据库连接验证失败: {e}")


@pytest.fixture(scope="function")
def db_session():
    """
    数据库会话 fixture

    提供数据库会话，测试结束后自动回滚。
    """
    from backend.src.db.session import get_db_session

    with get_db_session() as session:
        yield session


@pytest.fixture(scope="function")
def clean_db():
    """
    清理数据库 fixture

    在测试前清理相关表，确保测试从干净状态开始。
    """
    from backend.src.db.session import get_session_factory
    from sqlalchemy import text

    def _clean(tables: list[str]):
        """清理指定表（按依赖顺序反向清理）"""
        session_factory = get_session_factory()
        with session_factory() as session:
            # 按依赖顺序反向清理表
            for table in reversed(tables):
                try:
                    session.execute(text(f"DELETE FROM {table}"))
                except Exception:
                    pass
            session.commit()

    return _clean
