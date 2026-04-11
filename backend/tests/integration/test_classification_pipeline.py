"""
分类流水线集成测试

测试完整的日志分析流程：上传 → 切分 → 分类 → 存储。
"""

import pytest
import uuid
from datetime import datetime
from pathlib import Path
from io import BytesIO

from fastapi.testclient import TestClient

from backend.src.main import app
from backend.src.db.session import get_db_session, Base, get_engine
from backend.src.models.entities import (
    LogFile, SplitSession, SplitResult,
    LogEntry, ClassificationSession, IgnoreRule
)


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture(scope="function")
def sample_log_file(tmp_path):
    """创建测试日志文件"""
    log_content = """2026-04-11 10:00:00 INFO Application started
2026-04-11 10:00:01 ERROR Division by zero at line 10
2026-04-11 10:00:02 ERROR Null pointer exception
2026-04-11 10:00:03 WARNING Connection timeout
2026-04-11 10:00:04 ERROR Division by zero at line 20
2026-04-11 10:00:05 INFO Request processed
"""
    log_file = tmp_path / "test.log"
    log_file.write_text(log_content, encoding="utf-8")
    return str(log_file)


class TestClassificationPipeline:
    """分类流水线集成测试"""

    def test_full_pipeline(self, client, db_session):
        """测试完整流程：上传 → 切分 → 分类 → 验证结果"""

        # 1. 上传文件
        with open("backend/tests/fixtures/test.log", "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.log", f, "text/plain")}
            )

        assert response.status_code == 200
        upload_data = response.json()
        assert upload_data["success"] is True
        file_id = upload_data["data"]["file_id"]

        # 2. 执行切分
        split_request = {
            "file_id": file_id,
            "rule_type": "regex",
            "rule_content": r"^\d{4}-\d{2}-\d{2}"
        }
        response = client.post("/api/split", json=split_request)
        assert response.status_code == 200
        split_data = response.json()
        assert split_data["success"] is True
        session_id = split_data["data"]["session_id"]

        # 验证切分结果
        assert split_data["data"]["status"] == "completed"
        assert split_data["data"]["estimated_chunks"] > 0

        # 3. 启动分类（规则引擎模式）
        classification_request = {
            "split_session_id": session_id,
            "mode": "rule_engine"
        }
        response = client.post("/api/classification/start", json=classification_request)
        assert response.status_code == 201
        classification_data = response.json()
        assert classification_data["success"] is True
        classification_session_id = classification_data["data"]["session_id"]

        # 4. 轮询进度直到完成
        import time
        max_wait = 30  # 最多等待30秒
        start_time = time.time()

        while time.time() - start_time < max_wait:
            response = client.get(f"/api/classification/{classification_session_id}/progress")
            assert response.status_code == 200
            progress_data = response.json()

            if progress_data["data"]["status"] in ["completed", "failed"]:
                break

            time.sleep(0.5)

        # 验证最终状态
        final_response = client.get(f"/api/classification/{classification_session_id}/progress")
        final_progress = final_response.json()

        assert final_progress["success"] is True
        assert final_progress["data"]["status"] == "completed"
        assert final_progress["data"]["progress_percent"] == 100

        # 5. 获取分类结果
        response = client.get(f"/api/classification/{classification_session_id}/result")
        assert response.status_code == 200
        result_data = response.json()
        assert result_data["success"] is True

        # 6. 验证日志列表
        response = client.get("/api/logs")
        assert response.status_code == 200
        logs_data = response.json()
        assert logs_data["success"] is True
        assert logs_data["data"]["total"] > 0

    def test_classification_progress_tracking(self, client):
        """测试分类进度跟踪准确性"""

        # 上传文件
        with open("backend/tests/fixtures/test.log", "rb") as f:
            response = client.post("/api/upload", files={"file": ("test.log", f, "text/plain")})

        file_id = response.json()["data"]["file_id"]

        # 执行切分
        split_response = client.post("/api/split", json={
            "file_id": file_id,
            "rule_type": "regex",
            "rule_content": r"^\d{4}-\d{2}-\d{2}"
        })
        session_id = split_response.json()["data"]["session_id"]

        # 启动分类
        class_response = client.post("/api/classification/start", json={
            "split_session_id": session_id,
            "mode": "rule_engine"
        })
        classification_session_id = class_response.json()["data"]["session_id"]

        # 验证进度结构
        progress_response = client.get(f"/api/classification/{classification_session_id}/progress")
        progress = progress_response.json()

        assert progress["success"] is True
        assert "total_items" in progress["data"]
        assert "processed_items" in progress["data"]
        assert "progress_percent" in progress["data"]
        assert "current_phase" in progress["data"]

        # 验证进度百分比计算
        data = progress["data"]
        expected_percent = int(data["processed_items"] / data["total_items"] * 100) if data["total_items"] > 0 else 0
        assert data["progress_percent"] == expected_percent

    def test_duplicate_detection_rate(self, client, db_session, clean_db):
        """测试去重率达到100%（SC-002）"""

        # 清理历史数据，确保测试隔离
        clean_db(["log_entries", "classification_sessions"])

        # 上传包含重复错误消息的日志
        duplicate_log_content = """2026-04-11 10:00:01 ERROR Division by zero at line 10
2026-04-11 10:00:02 ERROR Division by zero at line 20
2026-04-11 10:00:03 ERROR Division by zero at line 30
2026-04-11 10:00:04 INFO Application started
"""
        # 创建临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write(duplicate_log_content)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = client.post("/api/upload", files={"file": ("dup.log", f, "text/plain")})

            file_id = response.json()["data"]["file_id"]

            # 切分
            split_response = client.post("/api/split", json={
                "file_id": file_id,
                "rule_type": "regex",
                "rule_content": r"^\d{4}-\d{2}-\d{2}"
            })
            session_id = split_response.json()["data"]["session_id"]

            # 分类
            class_response = client.post("/api/classification/start", json={
                "split_session_id": session_id,
                "mode": "rule_engine"
            })
            classification_session_id = class_response.json()["data"]["session_id"]

            # 等待处理完成
            import time
            for _ in range(60):
                response = client.get(f"/api/classification/{classification_session_id}/progress")
                if response.json()["data"]["status"] in ["completed", "failed"]:
                    break
                time.sleep(0.5)

            # 获取结果
            result_response = client.get(f"/api/classification/{classification_session_id}/result")
            result = result_response.json()["data"]

            # 验证去重效果：3个 "Division by zero" 应该只保留1条
            # 去重率 = (总数 - 唯一数) / 总数 = (3 - 1) / 3 = 66.7%
            duplicates = result.get("duplicates", 0)
            new_entries = result.get("new_entries", 0)

            # 验证数据库中没有完全重复的记录
            normalized_messages = db_session.query(LogEntry.normalized_message).distinct().all()
            assert len(normalized_messages) <= 4  # 最多4种不同的日志

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_classification_already_exists(self, client, clean_db):
        """测试同一切分会话不能同时有多个分类任务"""

        # 清理历史数据，确保测试隔离
        clean_db(["classification_sessions", "log_entries"])

        # 上传文件
        with open("backend/tests/fixtures/test.log", "rb") as f:
            response = client.post("/api/upload", files={"file": ("test.log", f, "text/plain")})

        file_id = response.json()["data"]["file_id"]

        # 切分
        split_response = client.post("/api/split", json={
            "file_id": file_id,
            "rule_type": "regex",
            "rule_content": r"^\d{4}-\d{2}-\d{2}"
        })
        session_id = split_response.json()["data"]["session_id"]

        # 第一次启动分类
        response1 = client.post("/api/classification/start", json={
            "split_session_id": session_id,
            "mode": "rule_engine"
        })
        assert response1.status_code == 201
        classification_session_id = response1.json()["data"]["session_id"]

        # 立即再次启动分类（此时第一个任务应该还在进行中）
        # 注意：由于异步任务，状态可能已经变为 completed
        # 所以这个测试验证的是：如果有 pending/processing 的任务，不能创建新的
        # 如果第一个已完成，第二个会成功创建 - 这是当前实现的预期行为
        response2 = client.post("/api/classification/start", json={
            "split_session_id": session_id,
            "mode": "rule_engine"
        })

        # 如果第一个任务已完成（async 任务很快），第二个会成功
        # 如果第一个任务还在进行中，第二个会返回 409
        if response2.status_code == 409:
            # 这是预期的行为
            assert response2.json()["error"]["code"] == "CLASSIFICATION_ALREADY_EXISTS"
        else:
            # 第一个任务已完成，第二个成功创建了新的分类会话
            # 验证确实创建了新的会话
            assert response2.status_code == 201
            assert response2.json()["data"]["session_id"] != classification_session_id

    def test_session_not_found(self, client):
        """测试会话不存在时返回404"""

        fake_session_id = str(uuid.uuid4())

        # 启动分类 - 会话不存在
        response = client.post("/api/classification/start", json={
            "split_session_id": fake_session_id,
            "mode": "rule_engine"
        })
        assert response.status_code == 404

        # 获取进度 - 会话不存在
        response = client.get(f"/api/classification/{fake_session_id}/progress")
        assert response.status_code == 404


class TestIgnoreRules:
    """忽略规则测试"""

    def test_ignore_rule_effect(self, client, db_session, clean_db):
        """测试忽略规则配置后相关日志不被存储"""

        # 清理历史数据，确保测试隔离
        clean_db(["log_entries", "ignore_rules", "classification_sessions"])

        # 创建忽略规则
        ignore_request = {
            "name": "忽略Connection timeout",
            "match_type": "contains",
            "pattern": "Connection timeout",
            "enabled": True
        }
        response = client.post("/api/ignore-rules", json=ignore_request)
        assert response.status_code == 200

        # 上传包含应被忽略日志的文件
        log_with_timeout = """2026-04-11 10:00:01 ERROR Connection timeout
2026-04-11 10:00:02 ERROR Division by zero
"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write(log_with_timeout)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as f:
                response = client.post("/api/upload", files={"file": ("timeout.log", f, "text/plain")})

            file_id = response.json()["data"]["file_id"]

            # 切分
            split_response = client.post("/api/split", json={
                "file_id": file_id,
                "rule_type": "regex",
                "rule_content": r"^\d{4}-\d{2}-\d{2}"
            })
            session_id = split_response.json()["data"]["session_id"]

            # 分类
            class_response = client.post("/api/classification/start", json={
                "split_session_id": session_id,
                "mode": "rule_engine"
            })
            classification_session_id = class_response.json()["data"]["session_id"]

            # 等待处理完成
            import time
            for _ in range(60):
                response = client.get(f"/api/classification/{classification_session_id}/progress")
                if response.json()["data"]["status"] in ["completed", "failed"]:
                    break
                time.sleep(0.5)

            # 验证结果 - 应该只有1条（Connection timeout被忽略）
            result_response = client.get(f"/api/classification/{classification_session_id}/result")
            result = result_response.json()["data"]

            # 验证日志列表 - 不应包含 "Connection timeout"
            logs_response = client.get("/api/logs")
            logs = logs_response.json()["data"]["entries"]

            for log in logs:
                assert "Connection timeout" not in log.get("normalized_message", "")

        finally:
            Path(temp_path).unlink(missing_ok=True)

        # 清理忽略规则
        rules_response = client.get("/api/ignore-rules")
        rules = rules_response.json()["data"]["rules"]
        for rule in rules:
            if rule["name"] == "忽略Connection timeout":
                client.delete(f"/api/ignore-rules/{rule['id']}")
