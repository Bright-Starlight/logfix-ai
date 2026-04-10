"""
POST /api/split 接口契约测试

测试执行切分功能。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_execute_regex_split():
    """测试执行正则切分"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 上传文件
        content = b"2024-01-01 INFO Line 1\n" \
                  b"2024-01-01 DEBUG Line 2\n" \
                  b"2024-01-02 INFO Line 3\n" \
                  b"2024-01-02 ERROR Line 4\n"
        files = {"file": ("app.log", content, "text/plain")}
        upload_response = await client.post("/api/upload", files=files)

        assert upload_response.status_code == 200
        file_id = upload_response.json()["data"]["file_id"]

        # 2. 执行切分
        split_response = await client.post(
            "/api/split",
            json={
                "file_id": file_id,
                "rule_type": "regex",
                "rule_content": r"^\d{4}-\d{2}-\d{2}"
            }
        )

        assert split_response.status_code == 200
        data = split_response.json()
        assert data["success"] is True
        assert "session_id" in data["data"]
        assert data["data"]["status"] == "completed"


@pytest.mark.anyio
async def test_execute_split_with_invalid_regex():
    """测试用无效正则执行切分"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 上传文件
        files = {"file": ("app.log", b"2024-01-01 INFO Line\n", "text/plain")}
        upload_response = await client.post("/api/upload", files=files)
        file_id = upload_response.json()["data"]["file_id"]

        # 2. 执行切分（无效正则）
        split_response = await client.post(
            "/api/split",
            json={
                "file_id": file_id,
                "rule_type": "regex",
                "rule_content": "[invalid"
            }
        )

        assert split_response.status_code == 400
        data = split_response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_REGEX"


@pytest.mark.anyio
async def test_split_nonexistent_file():
    """测试对不存在的文件执行切分"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_id = "00000000-0000-0000-0000-000000000000"
        split_response = await client.post(
            "/api/split",
            json={
                "file_id": fake_id,
                "rule_type": "regex",
                "rule_content": r"^\d{4}-\d{2}-\d{2}"
            }
        )

        assert split_response.status_code == 404
        data = split_response.json()
        assert data["error"]["code"] == "FILE_NOT_FOUND"
