"""
GET /api/files/{file_id} 接口契约测试

测试文件预览功能。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_file_preview_success():
    """测试获取文件预览成功"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 先上传文件
        files = {"file": ("test.log", b"Line 1\nLine 2\nLine 3\n", "text/plain")}
        upload_response = await client.post("/api/upload", files=files)

        assert upload_response.status_code == 200
        file_id = upload_response.json()["data"]["file_id"]

        # 获取预览
        response = await client.get(f"/api/files/{file_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["filename"] == "test.log"
        assert data["data"]["total_lines"] == 3
        assert len(data["data"]["preview"]) == 3
        assert data["data"]["encoding"] == "utf-8"


@pytest.mark.anyio
async def test_get_file_preview_with_lines_param():
    """测试获取文件预览指定行数"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 先上传文件
        files = {"file": ("test.log", b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n", "text/plain")}
        upload_response = await client.post("/api/upload", files=files)

        file_id = upload_response.json()["data"]["file_id"]

        # 获取预览前2行
        response = await client.get(f"/api/files/{file_id}?lines=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["preview"]) == 2


@pytest.mark.anyio
async def test_get_nonexistent_file():
    """测试获取不存在的文件"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/files/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FILE_NOT_FOUND"
