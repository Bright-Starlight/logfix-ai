"""
迁移脚本: 修改 ignore_rules 表 name 列长度

将 name 列从 varchar(100) 扩展到 varchar(500)，以容纳更长的规则名称。
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
    """扩展 name 列长度"""
    engine = get_engine()
    with engine.connect() as conn:
        # 检查当前列长度
        result = conn.execute(text("""
            SELECT character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'ignore_rules' AND column_name = 'name'
        """))
        row = result.fetchone()
        if row and row[0] < 500:
            conn.execute(text("""
                ALTER TABLE ignore_rules
                ALTER COLUMN name TYPE VARCHAR(500)
            """))
            conn.commit()
            print(f"已将 ignore_rules.name 从 varchar({row[0]}) 扩展到 varchar(500)")
        else:
            print("ignore_rules.name 长度已足够或无需修改，跳过")


def downgrade():
    """还原 name 列长度"""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE ignore_rules
            ALTER COLUMN name TYPE VARCHAR(100)
        """))
        conn.commit()
        print("已将 ignore_rules.name 还原到 varchar(100)")


if __name__ == "__main__":
    upgrade()
