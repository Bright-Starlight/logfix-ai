"""
GET /api/results/{session_id}/chunks/{chunk_index} 接口契约测试

测试获取单个切分片段详情功能。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_chunk_detail_success():
    """测试获取片段详情成功"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 上传文件
        content = b"2024-01-01 INFO Line 1\n" \
                  b"2024-01-01 DEBUG Line 2\n" \
                  b"2024-01-02 INFO Line 3\n"
        files = {"file": ("app.log", content, "text/plain")}
        upload_response = await client.post("/api/upload", files=files)
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
        session_id = split_response.json()["data"]["session_id"]

        # 3. 获取片段详情
        detail_response = await client.get(f"/api/results/{session_id}/chunks/0")

        assert detail_response.status_code == 200
        data = detail_response.json()
        assert data["success"] is True
        assert data["data"]["chunk_index"] == 0
        assert "Line 1" in data["data"]["content"]
        assert data["data"]["line_count"] == 2


@pytest.mark.anyio
async def test_get_nonexistent_chunk():
    """测试获取不存在的片段"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 先上传并切分
        content = b"2024-01-01 INFO Line\n"
        files = {"file": ("app.log", content, "text/plain")}
        upload_response = await client.post("/api/upload", files=files)
        file_id = upload_response.json()["data"]["file_id"]

        split_response = await client.post(
            "/api/split",
            json={
                "file_id": file_id,
                "rule_type": "regex",
                "rule_content": r"^\d{4}-\d{2}-\d{2}"
            }
        )
        session_id = split_response.json()["data"]["session_id"]

        # 请求不存在的片段
        response = await client.get(f"/api/results/{session_id}/chunks/999")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "CHUNK_NOT_FOUND"
