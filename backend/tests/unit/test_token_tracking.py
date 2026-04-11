"""
Token 消耗追踪单元测试

测试 TokenUsage 模型和 TokenTracker 追踪逻辑。
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestTokenUsageModel:
    """TokenUsage 模型测试"""

    def test_token_usage_creation(self):
        """测试 TokenUsage 创建"""
        from backend.src.models.entities import TokenUsage

        token_usage = TokenUsage(
            user_id="test_user",
            session_id=uuid.uuid4(),
            method="tool_call",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            model="MiniMax-M2.7",
            batch_size=10,
            processing_time_ms=500,
        )

        assert token_usage.user_id == "test_user"
        assert token_usage.method == "tool_call"
        assert token_usage.input_tokens == 100
        assert token_usage.output_tokens == 50
        assert token_usage.total_tokens == 150
        assert token_usage.model == "MiniMax-M2.7"
        assert token_usage.batch_size == 10
        assert token_usage.processing_time_ms == 500

    def test_token_usage_default_values(self):
        """测试 TokenUsage 默认值"""
        from backend.src.models.entities import TokenUsage

        token_usage = TokenUsage(
            method="prompt_engineering",
            model="MiniMax-M2.7",
            input_tokens=200,
            output_tokens=100,
            total_tokens=300,
        )

        assert token_usage.user_id is None
        assert token_usage.session_id is None
        assert token_usage.batch_size is None
        assert token_usage.processing_time_ms is None


class TestTokenMetrics:
    """Token 指标数据测试"""

    def test_token_metrics_creation(self):
        """测试 TokenMetrics 创建"""
        from backend.src.services.token_tracking import TokenMetrics

        metrics = TokenMetrics(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            processing_time_ms=500,
        )

        assert metrics.input_tokens == 100
        assert metrics.output_tokens == 50
        assert metrics.total_tokens == 150
        assert metrics.processing_time_ms == 500


class TestTokenTracker:
    """Token 追踪器测试"""

    def test_token_tracker_start_stop(self):
        """测试计时器开始和停止"""
        from backend.src.services.token_tracking import TokenTracker

        mock_db = MagicMock()
        tracker = TokenTracker(db=mock_db, user_id="test_user")

        # 开始计时
        tracker.start()
        import time
        time.sleep(0.01)  # 10ms

        # 停止计时
        elapsed = tracker.stop()
        assert elapsed >= 10  # 至少 10ms

    def test_token_tracker_record(self):
        """测试记录 token 消耗"""
        from backend.src.services.token_tracking import TokenTracker

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()

        tracker = TokenTracker(
            db=mock_db,
            user_id="test_user",
            session_id=str(uuid.uuid4()),
        )

        token_usage = tracker.record(
            method="tool_call",
            model="MiniMax-M2.7",
            input_tokens=100,
            output_tokens=50,
            batch_size=10,
        )

        # 验证 db.add 被调用
        assert mock_db.add.called
        assert mock_db.flush.called

    def test_token_tracker_measure_context(self):
        """测试上下文管理器测量"""
        from backend.src.services.token_tracking import TokenTracker

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()

        tracker = TokenTracker(db=mock_db, user_id="test_user")

        with tracker.measure("tool_call", "MiniMax-M2.7", batch_size=5) as metrics:
            metrics.input_tokens = 100
            metrics.output_tokens = 50

        # 验证记录被添加
        assert mock_db.add.called


class TestGetTokenComparison:
    """Token 对比数据测试"""

    def test_get_token_comparison_empty(self):
        """测试空结果的对比"""
        from backend.src.services.token_tracking import get_token_comparison

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.all.return_value = []

        result = get_token_comparison(mock_db)

        assert result["tool_call"]["count"] == 0
        assert result["prompt_engineering"]["count"] == 0
        assert result["tool_call"]["total_tokens"] == 0
        assert result["prompt_engineering"]["total_tokens"] == 0

    def test_get_token_comparison_with_data(self):
        """测试有数据时的对比"""
        from backend.src.services.token_tracking import get_token_comparison
        from backend.src.models.entities import TokenUsage

        # 创建模拟数据
        mock_usage1 = MagicMock(spec=TokenUsage)
        mock_usage1.method = "tool_call"
        mock_usage1.input_tokens = 100
        mock_usage1.output_tokens = 50
        mock_usage1.total_tokens = 150
        mock_usage1.processing_time_ms = 100

        mock_usage2 = MagicMock(spec=TokenUsage)
        mock_usage2.method = "prompt_engineering"
        mock_usage2.input_tokens = 200
        mock_usage2.output_tokens = 100
        mock_usage2.total_tokens = 300
        mock_usage2.processing_time_ms = 200

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.all.return_value = [mock_usage1, mock_usage2]

        result = get_token_comparison(mock_db)

        assert result["tool_call"]["count"] == 1
        assert result["tool_call"]["input_tokens"] == 100
        assert result["tool_call"]["output_tokens"] == 50
        assert result["tool_call"]["total_tokens"] == 150

        assert result["prompt_engineering"]["count"] == 1
        assert result["prompt_engineering"]["input_tokens"] == 200
        assert result["prompt_engineering"]["output_tokens"] == 100
        assert result["prompt_engineering"]["total_tokens"] == 300
