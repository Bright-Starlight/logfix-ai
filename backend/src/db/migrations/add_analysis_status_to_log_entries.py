"""
迁移脚本: 添加 analysis_status 字段到 log_entries 表

此迁移在 007-error-log-analysis-status 特性中添加，用于跟踪日志的分析状态。
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
    """添加 analysis_status 字段到 log_entries 表"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'log_entries' AND column_name = 'analysis_status'
        """))
        if result.fetchone() is None:
            conn.execute(text("""
                ALTER TABLE log_entries
                ADD COLUMN analysis_status VARCHAR(20) NOT NULL DEFAULT 'un_analyzed'
            """))
            # 添加字段注释
            conn.execute(text("""
                COMMENT ON COLUMN log_entries.analysis_status IS '分析状态：un_analyzed/analyzing/completed/failed'
            """))
            conn.commit()
            print("已添加 analysis_status 字段到 log_entries 表")
        else:
            print("analysis_status 字段已存在，跳过")


def downgrade():
    """删除 analysis_status 字段"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE log_entries DROP COLUMN IF EXISTS analysis_status
        """))
        conn.commit()
        print("已删除 analysis_status 字段")


if __name__ == "__main__":
    upgrade()
