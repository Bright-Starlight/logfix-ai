"""
迁移脚本: 添加 has_classification 列到 split_sessions 表

此迁移在 003-log-analysis-pipeline 特性中添加，用于标记切分会话是否已完成分类。
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
    """添加 has_classification 列"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查列是否已存在
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'split_sessions' AND column_name = 'has_classification'
        """))
        if result.fetchone() is None:
            conn.execute(text("""
                ALTER TABLE split_sessions
                ADD COLUMN has_classification BOOLEAN DEFAULT FALSE
            """))
            conn.commit()
            print("已添加 split_sessions.has_classification 列")
        else:
            print("split_sessions.has_classification 列已存在，跳过")


def downgrade():
    """移除 has_classification 列"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE split_sessions
            DROP COLUMN IF EXISTS has_classification
        """))
        conn.commit()
        print("已移除 split_sessions.has_classification 列")


if __name__ == "__main__":
    upgrade()
