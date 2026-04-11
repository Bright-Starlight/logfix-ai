"""
分类管道集成测试

测试工具调用完整流程。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestClassificationPipeline:
    """分类管道测试"""

    def test_ai_analyzer_module_imports(self):
        """测试 ai_analyzer 模块可正常导入"""
        from backend.src.services.ai_analyzer import (
            get_client,
            init_client,
            close_client,
            get_semaphore,
            parse_tool_call_response,
            stream_analyze_logs,
            analyze_logs_ai,
            classify_with_ai_result,
            ClassificationResult,
            CLASSIFY_LOG_TOOL_SCHEMA,
        )

        assert get_client is not None
        assert init_client is not None
        assert close_client is not None
        assert get_semaphore is not None
        assert parse_tool_call_response is not None
        assert stream_analyze_logs is not None
        assert analyze_logs_ai is not None
        assert classify_with_ai_result is not None
        assert ClassificationResult is not None
        assert CLASSIFY_LOG_TOOL_SCHEMA is not None

    def test_classification_result_dataclass(self):
        """测试 ClassificationResult 数据类"""
        from backend.src.services.ai_analyzer import ClassificationResult

        result = ClassificationResult(
            index=0,
            category="异常错误",
            error_type="NullPointerException",
            normalized_message="Null pointer at *",
            extracted_params={"line": "10"},
        )

        assert result.index == 0
        assert result.category == "异常错误"
        assert result.error_type == "NullPointerException"
        assert result.normalized_message == "Null pointer at *"
        assert result.extracted_params == {"line": "10"}

    def test_tool_schema_structure(self):
        """测试工具 schema 结构"""
        from backend.src.services.ai_analyzer import CLASSIFY_LOG_TOOL_SCHEMA

        assert CLASSIFY_LOG_TOOL_SCHEMA["name"] == "classify_log"
        assert "parameters" in CLASSIFY_LOG_TOOL_SCHEMA

        params = CLASSIFY_LOG_TOOL_SCHEMA["parameters"]
        assert params["type"] == "object"
        assert "log_entry" in params["properties"]
        assert "index" in params["properties"]


class TestStreamingPipeline:
    """流式管道测试"""

    @pytest.mark.asyncio
    async def test_stream_analyze_logs_empty_input(self):
        """测试空输入处理"""
        from backend.src.services.ai_analyzer import stream_analyze_logs

        events = []
        async for event in stream_analyze_logs([]):
            events.append(event)
            if event["event"] == "done":
                break

        # 空输入应该产生 done 事件
        assert any(e["event"] == "done" for e in events)

    def test_analyze_logs_ai_signature(self):
        """测试 analyze_logs_ai 函数签名"""
        from backend.src.services.ai_analyzer import analyze_logs_ai
        import inspect

        sig = inspect.signature(analyze_logs_ai)
        params = list(sig.parameters.keys())

        assert "log_entries" in params
        assert "batch_size" in params


class TestIntegration:
    """集成测试"""

    def test_routes_include_sse_endpoint(self):
        """测试路由包含 SSE 端点"""
        from backend.src.main import app

        routes = [route.path for route in app.routes]
        assert any("/classify/stream" in path for path in routes if path)

    def test_token_tracking_service_imports(self):
        """测试 token tracking 服务导入"""
        from backend.src.services.token_tracking import (
            TokenTracker,
            TokenMetrics,
            get_token_comparison,
        )

        assert TokenTracker is not None
        assert TokenMetrics is not None
        assert get_token_comparison is not None

    def test_token_usage_model_exists(self):
        """测试 TokenUsage 模型存在"""
        from backend.src.models.entities import TokenUsage

        assert TokenUsage is not None
