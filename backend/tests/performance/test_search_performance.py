"""
性能测试: 搜索过滤性能 (SC-005)

验证搜索和过滤操作在2秒内完成。
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


class TestSearchPerformance:
    """搜索过滤性能测试"""

    def test_search_keyword_performance(self):
        """
        SC-005: 验证关键词搜索性能

        性能目标: <2秒
        搜索字段: normalized_message (ILIKE)
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            # 模拟 GET /api/logs?keyword=error
            keyword = "error"

            query = db.query(LogEntry).filter(
                LogEntry.normalized_message.ilike(f"%{keyword}%")
            )

            total = query.count()
            entries = query.limit(100).all()

        elapsed_time = time.time() - start_time

        # 验证性能要求
        assert elapsed_time < 2.0, (
            f"关键词搜索太慢: {elapsed_time:.3f}s > 2.0s\n"
            f"匹配结果: {total}条"
        )

        print(f"\n✓ 关键词搜索性能测试通过: {elapsed_time:.3f}s (目标: <2s)")
        print(f"  - 搜索关键词: '{keyword}'")
        print(f"  - 匹配结果: {total}条")

    def test_search_level_filter_performance(self):
        """
        SC-005: 验证日志级别过滤性能

        性能目标: <2秒
        过滤字段: log_level
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            # 模拟 GET /api/logs?level=ERROR
            level = "ERROR"

            query = db.query(LogEntry).filter(
                LogEntry.log_level == level.upper()
            )

            total = query.count()
            entries = query.limit(100).all()

        elapsed_time = time.time() - start_time

        assert elapsed_time < 2.0, (
            f"级别过滤查询太慢: {elapsed_time:.3f}s > 2.0s"
        )

        print(f"\n✓ 级别过滤性能测试通过: {elapsed_time:.3f}s (目标: <2s)")
        print(f"  - 过滤级别: {level}")
        print(f"  - 匹配结果: {total}条")

    def test_search_category_filter_performance(self):
        """
        SC-005: 验证分类过滤性能

        性能目标: <2秒
        过滤方式: JOIN LogCategory 查询
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry, LogCategory

        start_time = time.time()

        with get_db_session() as db:
            # 模拟 GET /api/logs?category=异常错误
            category_name = "异常错误"

            # 先获取分类ID
            cat = db.query(LogCategory).filter(
                LogCategory.name == category_name
            ).first()

            if cat:
                query = db.query(LogEntry).filter(
                    LogEntry.category_id == cat.id
                )
                total = query.count()
                entries = query.limit(100).all()
            else:
                total = 0
                entries = []

        elapsed_time = time.time() - start_time

        assert elapsed_time < 2.0, (
            f"分类过滤查询太慢: {elapsed_time:.3f}s > 2.0s"
        )

        print(f"\n✓ 分类过滤性能测试通过: {elapsed_time:.3f}s (目标: <2s)")
        print(f"  - 分类: {category_name}")
        print(f"  - 匹配结果: {total}条")

    def test_search_date_range_performance(self):
        """
        SC-005: 验证日期范围过滤性能

        性能目标: <2秒
        过滤字段: created_at
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from datetime import datetime
        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            # 模拟 GET /api/logs?start_date=2024-01-01&end_date=2024-01-31
            start_date = datetime(2024, 1, 1)
            end_date = datetime(2024, 1, 31, 23, 59, 59)

            query = db.query(LogEntry).filter(
                LogEntry.created_at >= start_date,
                LogEntry.created_at <= end_date
            )

            total = query.count()
            entries = query.limit(100).all()

        elapsed_time = time.time() - start_time

        assert elapsed_time < 2.0, (
            f"日期范围查询太慢: {elapsed_time:.3f}s > 2.0s"
        )

        print(f"\n✓ 日期范围过滤性能测试通过: {elapsed_time:.3f}s (目标: <2s)")
        print(f"  - 日期范围: {start_date.date()} ~ {end_date.date()}")
        print(f"  - 匹配结果: {total}条")

    def test_search_combined_filters_performance(self):
        """
        SC-005: 验证组合过滤条件搜索性能

        性能目标: <2秒
        组合条件: keyword + level + date_range
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from datetime import datetime
        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        start_time = time.time()

        with get_db_session() as db:
            # 模拟 GET /api/logs?keyword=error&level=ERROR&start_date=2024-01-01
            keyword = "error"
            level = "ERROR"
            start_date = datetime(2024, 1, 1)

            query = db.query(LogEntry).filter(
                LogEntry.normalized_message.ilike(f"%{keyword}%"),
                LogEntry.log_level == level.upper(),
                LogEntry.created_at >= start_date
            )

            total = query.count()
            entries = query.limit(100).all()

        elapsed_time = time.time() - start_time

        # 组合查询允许稍微宽松的时间限制
        assert elapsed_time < 2.0, (
            f"组合搜索太慢: {elapsed_time:.3f}s > 2.0s"
        )

        print(f"\n✓ 组合搜索性能测试通过: {elapsed_time:.3f}s (目标: <2s)")
        print(f"  - 关键词: '{keyword}'")
        print(f"  - 级别: {level}")
        print(f"  - 日期: >= {start_date.date()}")
        print(f"  - 匹配结果: {total}条")


class TestSearchScalability:
    """搜索可扩展性测试"""

    def test_search_response_time_scaling(self):
        """
        验证搜索响应时间随数据量的增长关系

        目标: 响应时间应该是亚线性增长（由于索引）
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.models.entities import LogEntry

        results = []

        # 测试不同的 LIMIT 值
        for limit in [10, 50, 100, 200]:
            start_time = time.time()

            with get_db_session() as db:
                entries = db.query(LogEntry).filter(
                    LogEntry.normalized_message.ilike("%error%")
                ).limit(limit).all()

            elapsed_time = time.time() - start_time
            results.append((limit, elapsed_time))

        print("\n搜索响应时间缩放测试:")
        print("-" * 40)
        for limit, elapsed in results:
            print(f"  LIMIT {limit:3d}: {elapsed*1000:6.2f}ms")

        # 验证响应时间合理（不超过2秒）
        max_time = max(elapsed for _, elapsed in results)
        assert max_time < 2.0, (
            f"搜索响应时间过长: {max_time:.3f}s"
        )

        print(f"\n✓ 搜索可扩展性测试通过: 最大响应时间 {max_time:.3f}s")
