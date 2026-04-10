"""
数据库初始化脚本

用于创建数据库表和初始化数据。
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.src.db.session import init_db, create_tables, get_engine
from backend.src.models.entities import LogFile, SplitSession, SplitResult


def init_database(database_url: str | None = None) -> None:
    """
    初始化数据库

    Args:
        database_url: 数据库连接URL，如果为None则从环境变量读取
    """
    if database_url:
        os.environ["DATABASE_URL"] = database_url

    print("初始化数据库...")
    init_db()
    print("创建表结构...")
    create_tables()
    print("数据库初始化完成!")


def drop_all_tables() -> None:
    """删除所有表（危险操作）"""
    print("警告: 即将删除所有表!")
    confirm = input("确认删除? (yes/no): ")
    if confirm.lower() == "yes":
        engine = get_engine()
        LogFile.__table__.drop(engine, checkfirst=True)
        SplitSession.__table__.drop(engine, checkfirst=True)
        SplitResult.__table__.drop(engine, checkfirst=True)
        print("所有表已删除")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库初始化工具")
    parser.add_argument("--url", help="数据库连接URL")
    parser.add_argument("--drop", action="store_true", help="删除所有表")

    args = parser.parse_args()

    if args.drop:
        drop_all_tables()
    else:
        init_database(args.url)
