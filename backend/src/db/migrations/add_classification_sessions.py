"""
迁移脚本: 创建 classification_sessions 表

此迁移在 003-log-analysis-pipeline 特性中添加，用于跟踪分类任务的进度。
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
    """创建 classification_sessions 表"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查表是否已存在
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'classification_sessions'
        """))
        if result.fetchone() is None:
            conn.execute(text("""
                CREATE TABLE classification_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    split_session_id UUID NOT NULL REFERENCES split_sessions(id),
                    mode VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    total_items INTEGER DEFAULT 0,
                    processed_items INTEGER DEFAULT 0,
                    current_phase VARCHAR(50),
                    estimated_remaining_seconds INTEGER,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE INDEX idx_classification_session_status ON classification_sessions(status)
            """))
            conn.execute(text("""
                CREATE INDEX idx_classification_session_split ON classification_sessions(split_session_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_classification_session_created ON classification_sessions(created_at)
            """))
            conn.commit()
            print("已创建 classification_sessions 表")
        else:
            print("classification_sessions 表已存在，跳过")


def downgrade():
    """删除 classification_sessions 表"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS classification_sessions CASCADE
        """))
        conn.commit()
        print("已删除 classification_sessions 表")


if __name__ == "__main__":
    upgrade()
