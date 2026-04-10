"""
POST /api/validate/regex 接口契约测试

测试正则表达式校验功能。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_validate_valid_regex():
    """测试校验有效正则表达式"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/validate/regex",
            json={"pattern": r"^\d{4}-\d{2}-\d{2}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["valid"] is True


@pytest.mark.anyio
async def test_validate_invalid_regex():
    """测试校验无效正则表达式"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/validate/regex",
            json={"pattern": "[invalid"}
        )

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_REGEX"
