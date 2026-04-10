"""
POST /api/upload 接口契约测试

测试文件上传功能。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_upload_text_file_success():
    """测试上传文本文件成功"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 准备测试文件
        files = {"file": ("test.log", b"2024-01-01 INFO Test log line\n", "text/plain")}

        response = await client.post("/api/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["filename"] == "test.log"
        assert data["data"]["encoding"] in ["utf-8", "gbk", "gb2312"]
        assert "file_id" in data["data"]


@pytest.mark.anyio
async def test_upload_invalid_file_type():
    """测试上传非文本文件被拒绝"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 准备二进制文件（模拟图片）
        files = {"file": ("image.png", b"\x89PNG\r\n\x1a\n", "image/png")}

        response = await client.post("/api/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_FILE_TYPE"


@pytest.mark.anyio
async def test_upload_large_file():
    """测试上传超大文件被拒绝"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 准备超大文件内容 (超过100MB)
        large_content = b"x" * (101 * 1024 * 1024)
        files = {"file": ("large.log", large_content, "text/plain")}

        response = await client.post("/api/upload", files=files)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FILE_TOO_LARGE"
