"""
完整文件上传预览流程集成测试

测试从文件上传到预览的完整流程。
"""

import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_upload_preview_workflow():
    """测试完整上传预览工作流"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 准备测试文件内容
        content = b"2024-01-01 10:00:00 INFO Server started\n" \
                  b"2024-01-01 10:01:00 DEBUG Processing request\n" \
                  b"2024-01-01 10:02:00 ERROR Connection failed\n"

        # 1. 上传文件
        files = {"file": ("app.log", content, "text/plain")}
        upload_response = await client.post("/api/upload", files=files)

        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert upload_data["success"] is True

        file_id = upload_data["data"]["file_id"]
        assert upload_data["data"]["filename"] == "app.log"
        assert upload_data["data"]["file_size"] == len(content)
        assert "encoding" in upload_data["data"]

        # 2. 获取文件预览
        preview_response = await client.get(f"/api/files/{file_id}")

        assert preview_response.status_code == 200
        preview_data = preview_response.json()
        assert preview_data["success"] is True
        assert preview_data["data"]["filename"] == "app.log"
        assert preview_data["data"]["total_lines"] == 3
        assert len(preview_data["data"]["preview"]) == 3

        # 3. 验证预览内容与原文件一致
        assert "Server started" in preview_data["data"]["preview"][0]
        assert "Processing request" in preview_data["data"]["preview"][1]
        assert "Connection failed" in preview_data["data"]["preview"][2]
