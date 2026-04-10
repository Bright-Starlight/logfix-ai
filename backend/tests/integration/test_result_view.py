"""
完整结果查看和复制流程集成测试

测试切分后查看结果和复制片段的流程。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_result_view_workflow():
    """测试完整结果查看工作流"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 上传文件
        content = b"2024-01-01 INFO Line 1\n" \
                  b"2024-01-01 DEBUG Line 2\n" \
                  b"2024-01-02 INFO Line 3\n" \
                  b"2024-01-02 ERROR Line 4\n"
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

        # 3. 获取结果列表（分页）
        results_response = await client.get(f"/api/results/{session_id}?page=1&page_size=10")

        assert results_response.status_code == 200
        results_data = results_response.json()
        assert results_data["data"]["total_chunks"] == 2
        assert results_data["data"]["page"] == 1
        assert results_data["data"]["total_pages"] == 1

        # 4. 点击第一个片段获取详情
        chunk_response = await client.get(f"/api/results/{session_id}/chunks/0")

        assert chunk_response.status_code == 200
        chunk_data = chunk_response.json()
        assert chunk_data["data"]["chunk_index"] == 0
        assert "Line 1" in chunk_data["data"]["content"]
        assert "Line 2" in chunk_data["data"]["content"]

        # 5. 点击第二个片段获取详情
        chunk2_response = await client.get(f"/api/results/{session_id}/chunks/1")

        assert chunk2_response.status_code == 200
        chunk2_data = chunk2_response.json()
        assert chunk2_data["data"]["chunk_index"] == 1
        assert "Line 3" in chunk2_data["data"]["content"]
        assert "Line 4" in chunk2_data["data"]["content"]
