"""
迁移脚本: 创建 fix_plans 表

此迁移在 007-error-log-analysis-status 特性中添加，用于存储AI生成的修复计划详情。
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
    """创建 fix_plans 表"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查表是否已存在
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'fix_plans'
        """))
        if result.fetchone() is None:
            conn.execute(text("""
                CREATE TABLE fix_plans (
                    id BIGSERIAL PRIMARY KEY,
                    log_entry_id BIGINT NOT NULL UNIQUE REFERENCES log_entries(id),
                    session_id BIGINT REFERENCES analysis_sessions(id),
                    root_cause TEXT NOT NULL,
                    fix_steps JSONB NOT NULL,
                    code_locations JSONB NOT NULL,
                    confidence FLOAT NOT NULL,
                    impact_assessment TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # 添加索引
            conn.execute(text("""
                CREATE INDEX idx_fix_plan_log_entry ON fix_plans(log_entry_id)
            """))
            conn.execute(text("""
                CREATE INDEX idx_fix_plan_session ON fix_plans(session_id)
            """))
            # 添加表注释
            conn.execute(text("""
                COMMENT ON TABLE fix_plans IS '修复计划表，存储AI生成的修复计划详情'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.id IS '主键ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.log_entry_id IS '关联的日志条目ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.session_id IS '关联的分析会话ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.root_cause IS '问题根因分析'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.fix_steps IS '修复步骤建议列表（JSON数组）'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.code_locations IS '相关代码位置列表（JSON数组）'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.confidence IS '置信度 0-1'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.impact_assessment IS '影响范围评估'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.created_at IS '创建时间'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN fix_plans.updated_at IS '更新时间'
            """))
            conn.commit()
            print("已创建 fix_plans 表")
        else:
            print("fix_plans 表已存在，跳过")


def downgrade():
    """删除 fix_plans 表"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS fix_plans CASCADE
        """))
        conn.commit()
        print("已删除 fix_plans 表")


if __name__ == "__main__":
    upgrade()
