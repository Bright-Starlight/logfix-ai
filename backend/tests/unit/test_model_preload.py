"""
模型预加载单元测试

测试 OpenAI 客户端单例模式和预加载逻辑。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestClientSingleton:
    """客户端单例测试"""

    def test_get_client_returns_same_instance(self):
        """测试 get_client 返回同一实例"""
        import backend.src.services.ai_analyzer as ai_module
        from backend.src.services.ai_analyzer import get_client

        # 重置全局客户端以进行测试
        ai_module._client = None

        # Mock OpenAI 客户端
        with patch.object(ai_module, 'AsyncOpenAI') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance

            # 第一次调用
            loop = asyncio.new_event_loop()
            client1 = loop.run_until_complete(get_client())

            # 第二次调用
            client2 = loop.run_until_complete(get_client())

            # 应该返回同一实例
            assert client1 is client2
            loop.close()

            # 重置
            ai_module._client = None

    def test_get_client_raises_when_no_api_key(self):
        """测试未设置 API 密钥时抛出异常"""
        import backend.src.services.ai_analyzer as ai_module
        from backend.src.services.ai_analyzer import get_client

        ai_module._client = None

        with patch.dict('os.environ', {}, clear=True):
            with patch.object(ai_module, 'AsyncOpenAI') as mock_client:
                mock_client.side_effect = ValueError("MINIMAX_API_KEY 环境变量未设置")

                loop = asyncio.new_event_loop()
                with pytest.raises(ValueError, match="MINIMAX_API_KEY"):
                    loop.run_until_complete(get_client())
                loop.close()

                # 重置
                ai_module._client = None


class TestSemaphore:
    """并发控制信号量测试"""

    def test_semaphore_limits_concurrency(self):
        """测试信号量限制并发数"""
        import backend.src.services.ai_analyzer as ai_module
        from backend.src.services.ai_analyzer import get_semaphore

        # 重置信号量
        ai_module._semaphore = None

        semaphore = get_semaphore()
        assert semaphore._value == 5  # 默认并发数为 5

        # 再次获取应返回同一实例
        semaphore2 = get_semaphore()
        assert semaphore is semaphore2

        # 重置
        ai_module._semaphore = None

    def test_semaphore_from_config(self):
        """测试信号量从配置读取并发数"""
        import backend.src.services.ai_analyzer as ai_module
        from backend.src.services.ai_analyzer import get_semaphore

        ai_module._semaphore = None

        with patch.dict('os.environ', {'AI_MAX_CONCURRENT': '10'}):
            semaphore = get_semaphore()
            assert semaphore._value == 10

        # 重置
        ai_module._semaphore = None


class TestInitClient:
    """客户端初始化测试"""

    def test_init_client_calls_get_client(self):
        """测试 init_client 调用 get_client"""
        import backend.src.services.ai_analyzer as ai_module
        ai_module._client = None

        with patch.object(ai_module, 'get_client', new_callable=AsyncMock) as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client

            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(ai_module.init_client())

            assert result is mock_client
            assert mock_get.called
            loop.close()

            # 重置
            ai_module._client = None


class TestCloseClient:
    """客户端关闭测试"""

    def test_close_client_closes_connection(self):
        """测试 close_client 关闭连接"""
        import backend.src.services.ai_analyzer as ai_module
        ai_module._client = None

        mock_client = MagicMock()
        mock_client.close = AsyncMock()

        loop = asyncio.new_event_loop()
        ai_module._client = mock_client

        loop.run_until_complete(ai_module.close_client())

        assert mock_client.close.called
        assert ai_module._client is None
        loop.close()
