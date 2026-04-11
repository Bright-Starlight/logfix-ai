"""
迁移脚本: 修改 log_entries.normalized_message 列类型

将 VARCHAR(500) 改为 TEXT 以支持长日志消息。
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
    """修改 normalized_message 列为 TEXT 类型"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查当前列类型
        result = conn.execute(text("""
            SELECT data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'log_entries' AND column_name = 'normalized_message'
        """))
        row = result.fetchone()

        if row:
            data_type = row[0]
            if data_type == 'character varying' or data_type == 'varchar':
                # 已经是 TEXT 或需要从 VARCHAR 转换
                char_max_length = row[1]
                if char_max_length and char_max_length < 10000:
                    conn.execute(text("""
                        ALTER TABLE log_entries
                        ALTER COLUMN normalized_message TYPE TEXT
                    """))
                    conn.commit()
                    print(f"已修改 log_entries.normalized_message 为 TEXT (原为 VARCHAR({char_max_length}))")
                else:
                    print(f"normalized_message 已是 TEXT 或类似类型，跳过")
            else:
                print(f"当前类型为 {data_type}，跳过")
        else:
            print("未找到 normalized_message 列")


def downgrade():
    """将 normalized_message 改回 VARCHAR(500)"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE log_entries
            ALTER COLUMN normalized_message TYPE VARCHAR(500)
        """))
        conn.commit()
        print("已修改 log_entries.normalized_message 为 VARCHAR(500)")


if __name__ == "__main__":
    upgrade()
