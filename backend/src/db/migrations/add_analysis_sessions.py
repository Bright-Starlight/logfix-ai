"""
迁移脚本: 创建 analysis_sessions 表

此迁移在 007-error-log-analysis-status 特性中添加，用于跟踪修复计划分析任务的队列和执行状态。
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
    """创建 analysis_sessions 表"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查表是否已存在
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'analysis_sessions'
        """))
        if result.fetchone() is None:
            conn.execute(text("""
                CREATE TABLE analysis_sessions (
                    id BIGSERIAL PRIMARY KEY,
                    log_entry_id BIGINT NOT NULL REFERENCES log_entries(id),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    queue_position INTEGER,
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
            # 添加索引
            conn.execute(text("""
                CREATE INDEX idx_analysis_session_log_entry ON analysis_sessions(log_entry_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_analysis_session_status ON analysis_sessions(status)
            """))
            conn.execute(text("""
                CREATE INDEX idx_analysis_session_created ON analysis_sessions(created_at)
            """))
            # 添加表注释
            conn.execute(text("""
                COMMENT ON TABLE analysis_sessions IS '修复计划分析会话表，记录分析任务的队列和执行状态'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.id IS '主键ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.log_entry_id IS '关联的日志条目ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.status IS '状态：pending/queued/processing/completed/failed/cancelled'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.queue_position IS '队列位置（仅queued时有效）'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.error_message IS '失败时的错误信息'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.created_at IS '创建时间'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.started_at IS '开始执行时间'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN analysis_sessions.completed_at IS '完成时间'
            """))
            conn.commit()
            print("已创建 analysis_sessions 表")
        else:
            print("analysis_sessions 表已存在，跳过")


def downgrade():
    """删除 analysis_sessions 表"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS analysis_sessions CASCADE
        """))
        conn.commit()
        print("已删除 analysis_sessions 表")


if __name__ == "__main__":
    upgrade()
