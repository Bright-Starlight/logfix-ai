"""
性能测试: 日志分类性能 (SC-001)

验证日志分类和存储在5秒内完成。
"""

import time
import pytest


def can_connect_to_db():
    """检查数据库是否可用"""
    try:
        from backend.src.db.session import get_db_session, init_db
        from sqlalchemy import text
        init_db()
        # 尝试实际连接
        with get_db_session() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# 模拟测试数据 - 100条典型日志
SAMPLE_LOGS = [
    "2024-01-15 10:23:45 ERROR [Database] Connection failed: timeout after 30s",
    "2024-01-15 10:23:46 ERROR [API] Request failed: 500 Internal Server Error",
    "2024-01-15 10:23:47 WARNING [Cache] Redis connection lost, reconnecting...",
    "2024-01-15 10:23:48 ERROR [Auth] Invalid token provided for user_id=12345",
    "2024-01-15 10:23:49 INFO [Server] Request processed successfully in 150ms",
    "2024-01-15 10:23:50 ERROR [Database] Query timeout: SELECT * FROM orders WHERE...",
    "2024-01-15 10:23:51 WARNING [RateLimit] User exceeded rate limit: 1000 req/min",
    "2024-01-15 10:23:52 ERROR [Payment] Transaction failed: insufficient funds",
    "2024-01-15 10:23:53 INFO [Email] Sent confirmation email to user@example.com",
    "2024-01-15 10:23:54 ERROR [FileUpload] Failed to upload file: size exceeds limit",
] * 10  # 重复10次达到100条


@pytest.mark.asyncio
class TestClassifyPerformance:
    """日志分类性能测试"""

    async def test_classify_100_logs_under_5_seconds(self):
        """
        SC-001: 验证100条日志分类在5秒内完成

        性能目标: <5秒
        测试数据: 100条典型日志条目
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.services.classification_service import classify_logs

        start_time = time.time()

        with get_db_session() as db:
            # 执行分类 (async function)
            result = await classify_logs(
                db=db,
                logs=SAMPLE_LOGS,
                mode="rule_engine",
                file_id=None,
            )

        elapsed_time = time.time() - start_time

        # 验证性能要求
        assert elapsed_time < 5.0, (
            f"分类性能不达标: {elapsed_time:.2f}s > 5.0s\n"
            f"结果: processed={result.get('processed')}, "
            f"new={result.get('new_entries')}, "
            f"duplicates={result.get('duplicates')}"
        )

        print(f"\n✓ 分类性能测试通过: {elapsed_time:.3f}s (目标: <5s)")
        print(f"  - 处理日志: {result.get('processed')}条")
        print(f"  - 新增条目: {result.get('new_entries')}条")
        print(f"  - 重复条目: {result.get('duplicates')}条")

    async def test_classify_500_logs_under_10_seconds(self):
        """
        SC-001 Extended: 验证500条日志分类在10秒内完成

        性能目标: 扩展测试，500条日志应该在10秒内完成
        测试数据: 500条日志条目
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.services.classification_service import classify_logs

        # 生成500条测试日志
        logs_500 = SAMPLE_LOGS * 5  # 100 * 5 = 500

        start_time = time.time()

        with get_db_session() as db:
            result = await classify_logs(
                db=db,
                logs=logs_500,
                mode="rule_engine",
                file_id=None,
            )

        elapsed_time = time.time() - start_time

        # 扩展目标: 500条日志应在10秒内
        assert elapsed_time < 10.0, (
            f"批量分类性能不达标: {elapsed_time:.2f}s > 10.0s\n"
            f"结果: processed={result.get('processed')}"
        )

        print(f"\n✓ 批量分类性能测试通过: {elapsed_time:.3f}s (目标: <10s)")
        print(f"  - 处理日志: {result.get('processed')}条")


@pytest.mark.asyncio
class TestClassifyThroughput:
    """分类吞吐量测试"""

    async def test_classification_throughput(self):
        """
        验证分类吞吐量

        目标: 处理速度应该足够快，以支持每天10万条日志的处理需求
        计算: 100000 / 86400 ≈ 1.16条/秒 (最小需求)
        """
        if not can_connect_to_db():
            pytest.skip("数据库未配置或无法连接")

        from backend.src.db.session import get_db_session
        from backend.src.services.classification_service import classify_logs

        start_time = time.time()

        with get_db_session() as db:
            result = await classify_logs(
                db=db,
                logs=SAMPLE_LOGS,
                mode="rule_engine",
                file_id=None,
            )

        elapsed_time = time.time() - start_time

        # 计算吞吐量
        processed = result.get('processed', 0)
        throughput = processed / elapsed_time if elapsed_time > 0 else 0

        # 最小吞吐量要求: 1条/秒 (以支持10万条/天)
        min_throughput = 1.0

        assert throughput >= min_throughput, (
            f"分类吞吐量不足: {throughput:.2f}条/秒 < {min_throughput:.2f}条/秒\n"
            f"以当前速度，每天只能处理 {throughput * 86400:.0f} 条日志"
        )

        print(f"\n✓ 分类吞吐量测试通过: {throughput:.2f}条/秒")
        print(f"  - 支持每天处理: {throughput * 86400:.0f} 条日志")
        print(f"  - 目标: 100000 条/天")
