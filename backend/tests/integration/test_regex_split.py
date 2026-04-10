"""
完整正则切分流程集成测试

测试从文件上传、正则校验、执行切分到获取结果的完整流程。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_regex_split_workflow():
    """测试完整正则切分工作流"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 准备测试文件
        content = b"2024-01-01 10:00:00 INFO Server started\n" \
                  b"2024-01-01 10:01:00 DEBUG Processing request from client\n" \
                  b"2024-01-01 10:02:00 DEBUG Database query executed\n" \
                  b"2024-01-02 10:00:00 INFO New connection established\n" \
                  b"2024-01-02 10:01:00 ERROR Connection timeout\n" \
                  b"2024-01-02 10:02:00 INFO Connection recovered\n"

        # 1. 上传文件
        files = {"file": ("app.log", content, "text/plain")}
        upload_response = await client.post("/api/upload", files=files)

        assert upload_response.status_code == 200
        file_id = upload_response.json()["data"]["file_id"]

        # 2. 校验正则表达式
        regex_response = await client.post(
            "/api/validate/regex",
            json={"pattern": r"^\d{4}-\d{2}-\d{2}"}
        )

        assert regex_response.status_code == 200
        assert regex_response.json()["data"]["valid"] is True

        # 3. 执行切分
        split_response = await client.post(
            "/api/split",
            json={
                "file_id": file_id,
                "rule_type": "regex",
                "rule_content": r"^\d{4}-\d{2}-\d{2}"
            }
        )

        assert split_response.status_code == 200
        split_data = split_response.json()
        session_id = split_data["data"]["session_id"]

        # 4. 获取切分状态
        status_response = await client.get(f"/api/sessions/{session_id}")

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["data"]["status"] == "completed"
        assert status_data["data"]["total_chunks"] == 2  # 2天 = 2个片段

        # 5. 获取切分结果
        results_response = await client.get(f"/api/results/{session_id}")

        assert results_response.status_code == 200
        results_data = results_response.json()
        assert results_data["data"]["total_chunks"] == 2
        assert len(results_data["data"]["results"]) == 2

        # 验证第一个片段包含第一天的日志
        first_chunk = results_data["data"]["results"][0]
        assert first_chunk["start_line"] == 1
        assert "Server started" in first_chunk["content"]
