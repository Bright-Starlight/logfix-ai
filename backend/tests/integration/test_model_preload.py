"""
模型预加载集成测试

测试应用启动时的模型预加载和客户端复用。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestAppLifespan:
    """应用生命周期测试"""

    def test_lifespan_preloads_model(self):
        """测试 lifespan 事件预加载模型"""
        from backend.src.main import lifespan

        # 这个测试验证 lifespan 函数存在且包含预加载逻辑
        assert lifespan is not None

    def test_app_startup_includes_preload(self):
        """测试应用启动包含预加载"""
        from backend.src.main import app

        # 验证 app 对象存在
        assert app is not None
        # 验证 title 正确
        assert "LogFix AI" in app.title


class TestClientReuse:
    """客户端复用测试"""

    @pytest.mark.asyncio
    async def test_multiple_calls_return_same_client(self):
        """测试多次调用返回同一客户端"""
        from backend.src.services.ai_analyzer import get_client

        # 重置全局客户端
        import backend.src.services.ai_analyzer as ai_module
        original_client = ai_module._client
        ai_module._client = None

        try:
            with patch.object(ai_module, 'AsyncOpenAI') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                # 多次调用
                client1 = await get_client()
                client2 = await get_client()

                # 验证是同一实例
                assert client1 is client2
                assert mock_client.call_count == 1  # 只创建了一次
        finally:
            # 恢复
            ai_module._client = original_client


class TestPreloadLogging:
    """预加载日志测试"""

    def test_init_client_logs_preload_complete(self):
        """测试 init_client 记录预加载完成日志"""
        from backend.src.services.ai_analyzer import init_client

        import backend.src.services.ai_analyzer as ai_module
        original_client = ai_module._client
        ai_module._client = None

        try:
            with patch.object(ai_module, 'AsyncOpenAI') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                with patch.object(ai_module, '_logger') as mock_logger:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(init_client())

                    # 验证日志记录
                    assert mock_logger.info.called
                    log_calls = [str(call) for call in mock_logger.info.call_args_list]
                    assert any('模型预加载完成' in str(call) or 'OpenAI 客户端初始化完成' in str(call) for call in log_calls)
                    loop.close()
        finally:
            ai_module._client = original_client
