"""
迁移脚本: 添加分类统计字段到 classification_sessions 表

添加 new_entries, duplicates, ignored 字段。
"""

from sqlalchemy import text
import os
import sys

# 添加 backend 目录到路径
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.db.session import get_engine


def upgrade():
    """添加分类统计字段"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查列是否已存在
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'classification_sessions' AND column_name = 'new_entries'
        """))
        if result.fetchone() is None:
            conn.execute(text("""
                ALTER TABLE classification_sessions
                ADD COLUMN new_entries INTEGER DEFAULT 0
            """))
            conn.execute(text("""
                ALTER TABLE classification_sessions
                ADD COLUMN duplicates INTEGER DEFAULT 0
            """))
            conn.execute(text("""
                ALTER TABLE classification_sessions
                ADD COLUMN ignored INTEGER DEFAULT 0
            """))
            conn.commit()
            print("已添加 classification_sessions 统计字段")
        else:
            print("classification_sessions 统计字段已存在，跳过")


def downgrade():
    """移除分类统计字段"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE classification_sessions
            DROP COLUMN IF EXISTS ignored
        """))
        conn.execute(text("""
            ALTER TABLE classification_sessions
            DROP COLUMN IF EXISTS duplicates
        """))
        conn.execute(text("""
            ALTER TABLE classification_sessions
            DROP COLUMN IF EXISTS new_entries
        """))
        conn.commit()
        print("已移除 classification_sessions 统计字段")


if __name__ == "__main__":
    upgrade()
