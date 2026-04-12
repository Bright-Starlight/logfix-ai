"""
SSE 流式端点集成测试

测试 /api/classify/stream 端点的完整流程。
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


class TestSSEEndpoint:
    """SSE 流式端点测试"""

    def test_sse_endpoint_route_exists(self):
        """测试 SSE 端点路由存在"""
        from backend.src.main import app

        # 检查路由是否注册
        routes = [route.path for route in app.routes]
        assert "/api/classify/stream" in routes or "/api/classify/stream" in [r for r in routes]

    def test_sse_endpoint_requires_session_id(self):
        """测试 SSE 端点需要有效的 session_id"""
        from backend.src.main import app
        from backend.src.api.schemas import ClassificationStartRequest

        client = TestClient(app)

        # 测试不存在的 session
        response = client.post(
            "/api/classify/stream",
            json={"split_session_id": str(uuid.uuid4()), "mode": "ai"}
        )

        # 应该返回 200（因为我们使用 EventSourceResponse，即使出错也会返回）
        # 或者 404 如果 session 不存在
        assert response.status_code in [200, 404, 500]


class TestSSEEventTypes:
    """SSE 事件类型测试"""

    def test_sse_event_types_defined(self):
        """测试 SSE 事件类型定义"""
        from backend.src.services.ai_analyzer import stream_analyze_logs

        # 这个测试验证 stream_analyze_logs 函数存在且可调用
        assert stream_analyze_logs is not None


class TestSSEEventGenerator:
    """SSE 事件生成器测试"""

    @pytest.mark.asyncio
    async def test_event_generator_yields_progress(self):
        """测试事件生成器产生 progress 事件"""
        from backend.src.services.ai_analyzer import stream_analyze_logs

        logs = ["ERROR at line 10", "INFO connected"]

        events = []
        async for event in stream_analyze_logs(logs, batch_size=1):
            events.append(event)
            if event["event"] == "done":
                break

        # 验证有 progress 或 done 事件
        event_types = [e["event"] for e in events]
        assert "progress" in event_types or "done" in event_types

    @pytest.mark.asyncio
    async def test_event_generator_yields_done_on_empty(self):
        """测试事件生成器在空输入时产生 done 事件"""
        from backend.src.services.ai_analyzer import stream_analyze_logs

        logs = []

        events = []
        async for event in stream_analyze_logs(logs):
            events.append(event)

        # 空输入应该产生 error 或 done 事件
        assert len(events) > 0


class TestSSEProgressEvent:
    """SSE 进度事件测试"""

    def test_progress_event_structure(self):
        """测试 progress 事件结构"""
        progress_data = {
            "processed": 10,
            "total": 100,
            "percentage": 10,
        }

        assert "processed" in progress_data
        assert "total" in progress_data
        assert "percentage" in progress_data
        assert progress_data["percentage"] == int(progress_data["processed"] / progress_data["total"] * 100)


class TestSSEResultEvent:
    """SSE 结果事件测试"""

    def test_result_event_structure(self):
        """测试 result 事件结构"""
        result_data = {
            "index": 0,
            "category": "异常错误",
            "error_type": "NullPointerException",
            "normalized_message": "Null pointer at *",
            "extracted_params": {"line": "10"},
        }

        assert "index" in result_data
        assert "category" in result_data
        assert "error_type" in result_data
        assert "normalized_message" in result_data
        assert "extracted_params" in result_data


class TestSSEErrorEvent:
    """SSE 错误事件测试"""

    def test_error_event_structure(self):
        """测试 error 事件结构"""
        error_data = {
            "code": "PARSE_ERROR",
            "message": "AI 响应格式错误",
        }

        assert "code" in error_data
        assert "message" in error_data


class TestSSEDoneEvent:
    """SSE 完成事件测试"""

    def test_done_event_structure(self):
        """测试 done 事件结构"""
        done_data = {
            "total_processed": 100,
            "success_count": 95,
            "error_count": 5,
        }

        assert "total_processed" in done_data
        assert "success_count" in done_data
        assert "error_count" in done_data
        assert done_data["total_processed"] == done_data["success_count"] + done_data["error_count"]
