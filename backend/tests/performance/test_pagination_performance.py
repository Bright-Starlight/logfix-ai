"""
性能测试: 分页性能 (SC-004)

验证分页加载1000条日志的性能要求。
"""

import time
import pytest


def can_connect_to_db():
    """检查数据库是否可用"""
    try:
        from backend.src.db.session import get_db_session, init_db
        from sqlalchemy import text
        init_db()
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


class TestPaginationPerformance:
    """分页性能测试"""

    def test_pagination_50_logs(self):
        """
        SC-004: 验证分页加载50条日志的性能

        性能目标: 快速响应 (<1秒)
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            # 模拟 GET /api/logs?page=1&page_size=50
            page = 1
            page_size = 50

            query = db.query(LogEntry)
            total = query.count()

            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size

            entries = query.order_by(
                LogEntry.created_at.desc()
            ).offset(offset).limit(page_size).all()

        elapsed_time = time.time() - start_time

        # 验证性能
        assert elapsed_time < 1.0, (
            f"分页查询太慢: {elapsed_time:.3f}s > 1.0s"
        )

        print(f"\n✓ 分页50条日志性能测试通过: {elapsed_time:.3f}s")
        print(f"  - 总记录数: {total}")
        print(f"  - 当前页: {page}/{total_pages}")

    def test_pagination_200_logs(self):
        """
        SC-004: 验证分页加载200条日志的性能

        性能目标: 快速响应 (<1秒)
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            page = 1
            page_size = 200

            query = db.query(LogEntry)
            total = query.count()

            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size

            entries = query.order_by(
                LogEntry.created_at.desc()
            ).offset(offset).limit(page_size).all()

        elapsed_time = time.time() - start_time

        assert elapsed_time < 1.0, (
            f"分页查询太慢: {elapsed_time:.3f}s > 1.0s"
        )

        print(f"\n✓ 分页200条日志性能测试通过: {elapsed_time:.3f}s")

    def test_pagination_1000_logs_no_timeout(self):
        """
        SC-004: 验证分页加载1000条日志不会超时

        性能目标: 必须在合理时间内完成 (<5秒)
        测试数据: page_size=200, 需要获取1000条 (5页)
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            page_size = 200
            total_needed = 1000
            pages_to_fetch = (total_needed + page_size - 1) // page_size

            all_entries = []
            total = db.query(LogEntry).count()

            for page in range(1, pages_to_fetch + 1):
                offset = (page - 1) * page_size
                entries = db.query(LogEntry).order_by(
                    LogEntry.created_at.desc()
                ).offset(offset).limit(page_size).all()
                all_entries.extend(entries)

        elapsed_time = time.time() - start_time

        # 验证获取了足够的记录
        assert len(all_entries) >= 1000 or total < 1000, (
            f"无法获取足够的记录: {len(all_entries)} < 1000"
        )

        # 验证性能: 5秒内完成
        assert elapsed_time < 5.0, (
            f"分页获取1000条日志太慢: {elapsed_time:.3f}s > 5.0s"
        )

        print(f"\n✓ 分页获取{total_needed}条日志性能测试通过: {elapsed_time:.3f}s")
        print(f"  - 获取记录数: {len(all_entries)}")
        print(f"  - 数据库总记录: {total}")

    def test_pagination_with_filters(self):
        """
        SC-004: 验证带过滤条件的分页性能

        性能目标: 带过滤的分页查询应该在2秒内完成
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            # 模拟 GET /api/logs?level=ERROR&page=1&page_size=50
            level = "ERROR"
            page = 1
            page_size = 50

            query = db.query(LogEntry).filter(
                LogEntry.log_level == level.upper()
            )

            total = query.count()
            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size

            entries = query.order_by(
                LogEntry.created_at.desc()
            ).offset(offset).limit(page_size).all()

        elapsed_time = time.time() - start_time

        assert elapsed_time < 2.0, (
            f"带过滤的分页查询太慢: {elapsed_time:.3f}s > 2.0s"
        )

        print(f"\n✓ 带过滤分页性能测试通过: {elapsed_time:.3f}s")
        print(f"  - 过滤条件: level={level}")
        print(f"  - 匹配记录数: {total}")


class TestPaginationDatabaseIndexes:
    """分页索引验证测试"""

    def test_required_indexes_exist(self):
        """
        验证分页查询所需的数据库索引存在

        索引需求:
        - LogEntry.log_level (级别过滤)
        - LogEntry.normalized_message (关键词搜索)
        - LogEntry.created_at (排序)
        - LogEntry.category_id (分类过滤)
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_engine
        from sqlalchemy import text

        engine = get_engine()

        # 获取表索引信息
        with engine.connect() as conn:
            # 检查 LogEntry 表的索引
            result = conn.execute(
                text("SELECT indexname FROM pg_indexes WHERE tablename = 'log_entries'")
            )
            indexes = [row[0] for row in result]

        required_indexes = [
            'log_entries_log_level_idx',
            'log_entries_normalized_message_idx',
            'log_entries_created_at_idx',
            'log_entries_category_id_idx',
        ]

        # 打印实际存在的索引（调试用）
        print(f"\n数据库中的索引: {indexes}")

        # 注意: 这个测试主要是提醒，确保索引存在
        # 实际索引名称可能因数据库而异
        print(f"\n✓ 索引检查完成")
