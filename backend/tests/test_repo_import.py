"""
仓库导入功能测试

测试本地仓库和 GitHub 仓库的验证和导入功能。
"""

import os
import sys
import tempfile
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 确保 backend 模块可导入
backend_path = os.path.dirname(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


class TestValidateLocalRepo:
    """本地仓库验证测试"""

    def test_validate_local_repo_path_not_exists(self, clean_db):
        """T010: 验证本地仓库 - 路径不存在"""
        from backend.src.services.repo_service import validate_local_repo

        result = validate_local_repo("D:/nonexistent/path/nowhere")

        assert result.is_valid is False
        assert result.error_code == "PATH_NOT_ACCESSIBLE"
        assert "不存在" in result.error_message

    def test_validate_local_repo_not_git_repo(self, clean_db):
        """T010: 验证本地仓库 - 路径不是 Git 仓库"""
        from backend.src.services.repo_service import validate_local_repo

        # 创建一个临时目录但不是 Git 仓库
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_local_repo(tmpdir)

        assert result.is_valid is False
        assert result.error_code == "NOT_A_GIT_REPO"
        assert "不是有效的 Git 仓库" in result.error_message

    def test_validate_local_repo_success(self, clean_db):
        """T011: 验证本地仓库 - 成功验证"""
        from backend.src.services.repo_service import validate_local_repo

        # 创建一个真实的 Git 仓库
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            repo_path.mkdir()

            # 初始化 Git 仓库
            import subprocess
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)

            result = validate_local_repo(str(repo_path))

        assert result.is_valid is True
        assert result.repo_name == "test_repo"
        assert result.error_code is None

    def test_validate_local_repo_relative_path(self, clean_db):
        """T010: 验证本地仓库 - 相对路径应被拒绝"""
        from backend.src.services.repo_service import validate_local_repo

        result = validate_local_repo("relative/path")

        assert result.is_valid is False
        assert result.error_code == "INVALID_PATH"
        assert "绝对路径" in result.error_message


class TestImportLocalRepo:
    """本地仓库导入测试"""

    def test_import_local_repo_success(self, clean_db):
        """T012: 导入本地仓库 - 成功导入"""
        from backend.src.services.repo_service import import_local_repo
        from backend.src.db.session import get_db_session
        from backend.src.models.entities import Repository, ImportSession

        # 创建一个真实的 Git 仓库
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            repo_path.mkdir()

            # 初始化 Git 仓库
            import subprocess
            subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)

            # 清理之前的测试数据
            clean_db(["import_sessions", "repositories"])

            result = import_local_repo(str(repo_path), "test_repo")

        assert result.success is True
        assert result.repo_id is not None
        assert result.local_path == str(repo_path)

        # 验证数据库记录
        with get_db_session() as db:
            repo = db.query(Repository).filter(Repository.id == result.repo_id).first()
            assert repo is not None
            assert repo.name == "test_repo"
            assert repo.source_type == "local"

            session = db.query(ImportSession).filter(ImportSession.repo_id == repo.id).first()
            assert session is not None
            assert session.status == "success"


class TestValidateGithubRepo:
    """GitHub 仓库验证测试"""

    def test_validate_github_repo_invalid_url(self, clean_db):
        """T023: 验证 GitHub 仓库 - 无效 URL"""
        from backend.src.services.repo_service import validate_github_repo

        result = validate_github_repo("invalid-url", "", None)

        assert result.is_valid is False
        assert result.error_code == "INVALID_GITHUB_URL"

    @patch("requests.head")
    def test_validate_github_repo_not_found(self, mock_head, clean_db):
        """T023: 验证 GitHub 仓库 - 仓库不存在"""
        from backend.src.services.repo_service import validate_github_repo

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        result = validate_github_repo("nonexistent-owner", "nonexistent-repo", None)

        assert result.is_valid is False
        assert result.error_code == "GITHUB_REPO_NOT_FOUND"

    @patch("requests.get")
    def test_validate_github_repo_private_without_token(self, mock_get, clean_db):
        """T023: 验证 GitHub 仓库 - 私有仓库无 Token"""
        from backend.src.services.repo_service import validate_github_repo

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.content = b'{"message": "Not Found"}'
        mock_response.json.return_value = {"message": "Not Found"}
        mock_get.return_value = mock_response

        result = validate_github_repo("owner", "private-repo", None)

        assert result.is_valid is False
        assert result.error_code == "GITHUB_REPO_PRIVATE"

    @patch("requests.get")
    def test_validate_github_repo_success(self, mock_get, clean_db):
        """T024: 验证 GitHub 仓库 - 成功验证"""
        from backend.src.services.repo_service import validate_github_repo

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "description": "A test repository",
            "private": False,
            "html_url": "https://github.com/owner/test-repo",
        }
        mock_get.return_value = mock_response

        result = validate_github_repo("owner", "test-repo", None)

        assert result.is_valid is True
        assert result.repo_name == "test-repo"
        assert result.description == "A test repository"
        assert result.remote_url == "https://github.com/owner/test-repo"


class TestImportGithubRepo:
    """GitHub 仓库导入测试"""

    @patch("subprocess.run")
    @patch("requests.get")
    @patch("pathlib.Path.exists")
    def test_import_github_repo_success(self, mock_exists, mock_get, mock_run, clean_db):
        """T025: 导入 GitHub 仓库 - 成功克隆"""
        from backend.src.services.repo_service import import_github_repo
        from backend.src.db.session import get_db_session
        from backend.src.models.entities import Repository, ImportSession

        # Mock GitHub API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "description": "A test repository",
            "private": False,
        }
        mock_get.return_value = mock_response

        # Mock git clone
        mock_run.return_value = MagicMock(returncode=0)
        # Mock Path.exists to return True for .git directory
        mock_exists.return_value = True

        # 清理之前的测试数据
        clean_db(["import_sessions", "repositories"])

        with tempfile.TemporaryDirectory() as tmpdir:
            clone_path = str(Path(tmpdir) / "test-repo")
            # 创建目标目录
            Path(clone_path).mkdir(parents=True, exist_ok=True)

            result = import_github_repo("owner", "test-repo", clone_path, None)

        assert result.success is True
        assert result.repo_id is not None
        assert result.local_path == clone_path

    @patch("subprocess.run")
    def test_import_github_repo_clone_failed(self, mock_run, clean_db):
        """T025: 导入 GitHub 仓库 - 克隆失败"""
        from backend.src.services.repo_service import import_github_repo

        # Mock git clone 失败 - subprocess.run with check=False returns CompletedProcess with non-zero returncode
        mock_run.return_value = MagicMock(returncode=1, stderr="fatal: repository not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            clone_path = str(Path(tmpdir) / "clone")
            # 创建目标目录
            Path(clone_path).mkdir(parents=True, exist_ok=True)

            result = import_github_repo("owner", "test-repo", clone_path, None)

        assert result.success is False
        assert result.error_code == "GITHUB_CLONE_FAILED"
