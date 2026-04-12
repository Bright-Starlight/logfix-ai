"""
迁移脚本: 创建 repositories 和 import_sessions 表

此迁移在 006-repo-import 特性中添加，用于存储仓库导入信息。
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
    """创建 repositories 和 import_sessions 表"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查 repositories 表是否已存在
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'repositories'
        """))
        if result.fetchone() is None:
            # 创建 repositories 表
            conn.execute(text("""
                CREATE TABLE repositories (
                    id BIGSERIAL PRIMARY KEY,
                    source_type VARCHAR(16) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    local_path VARCHAR(1024) NOT NULL,
                    remote_url VARCHAR(1024),
                    is_valid BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # 添加表注释
            conn.execute(text("""
                COMMENT ON TABLE repositories IS '仓库表，记录用户导入的代码仓库信息'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.id IS '主键ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.source_type IS '来源类型：local/github'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.name IS '仓库名称'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.description IS '仓库描述（GitHub 仓库时填充）'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.local_path IS '本地绝对路径（本地仓库为原始路径，GitHub 仓库为克隆目标路径）'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.remote_url IS '远程地址（GitHub 仓库的原始 URL）'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.is_valid IS '仓库是否有效'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.created_at IS '创建时间'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN repositories.updated_at IS '更新时间'
            """))
            conn.commit()
            print("已创建 repositories 表")
        else:
            print("repositories 表已存在，跳过")

        # 检查 import_sessions 表是否已存在
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_name = 'import_sessions'
        """))
        if result.fetchone() is None:
            # 创建 import_sessions 表
            conn.execute(text("""
                CREATE TABLE import_sessions (
                    id BIGSERIAL PRIMARY KEY,
                    repo_id BIGINT NOT NULL REFERENCES repositories(id),
                    source_type VARCHAR(16) NOT NULL,
                    status VARCHAR(16) NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # 添加索引
            conn.execute(text("""
                CREATE INDEX ix_import_sessions_repo_id ON import_sessions(repo_id)
            """))
            conn.execute(text("""
                CREATE INDEX ix_import_sessions_status ON import_sessions(status)
            """))
            # 添加表注释
            conn.execute(text("""
                COMMENT ON TABLE import_sessions IS '导入会话表，记录每次仓库导入操作的上下文和结果'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN import_sessions.id IS '主键ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN import_sessions.repo_id IS '关联的仓库ID'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN import_sessions.source_type IS '导入来源类型：local/github'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN import_sessions.status IS '状态：pending/success/failed'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN import_sessions.error_message IS '失败时的错误信息'
            """))
            conn.execute(text("""
                COMMENT ON COLUMN import_sessions.created_at IS '创建时间'
            """))
            conn.commit()
            print("已创建 import_sessions 表")
        else:
            print("import_sessions 表已存在，跳过")


def downgrade():
    """删除 repositories 和 import_sessions 表"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            DROP TABLE IF EXISTS import_sessions CASCADE
        """))
        conn.execute(text("""
            DROP TABLE IF EXISTS repositories CASCADE
        """))
        conn.commit()
        print("已删除 repositories 和 import_sessions 表")


if __name__ == "__main__":
    upgrade()
