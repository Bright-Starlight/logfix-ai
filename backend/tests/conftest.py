"""
pytest 配置文件

设置数据库连接和测试环境。
"""

import os
import sys

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
