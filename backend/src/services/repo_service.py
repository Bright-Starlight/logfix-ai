"""
仓库导入服务

提供本地仓库和 GitHub 仓库的验证和导入功能。
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import requests

from backend.src.services.log_service import get_logger
from backend.src.utils.github import get_github_headers
from backend.src.core.constants import RepoSourceType, RepoStatus, RepoErrorCode


@dataclass
class RepoValidationResult:
    """仓库验证结果"""
    is_valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    repo_name: Optional[str] = None
    description: Optional[str] = None
    remote_url: Optional[str] = None


@dataclass
class RepoImportResult:
    """仓库导入结果"""
    success: bool
    repo_id: Optional[int] = None
    local_path: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


def validate_local_repo(local_path: str) -> RepoValidationResult:
    """
    验证本地仓库有效性

    验证规则:
    1. 路径必须为绝对路径
    2. 路径对应的目录必须存在
    3. 目录必须包含 .git 子目录
    4. 应用进程必须对目录有读取权限

    Args:
        local_path: 本地仓库的绝对路径

    Returns:
        RepoValidationResult: 验证结果
    """
    path = Path(local_path)

    # 检查是否为绝对路径
    if not path.is_absolute():
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.INVALID_PATH.value,
            error_message="路径必须是绝对路径"
        )

    # 检查目录是否存在
    if not path.exists():
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.PATH_NOT_ACCESSIBLE.value,
            error_message="目录不存在"
        )

    if not path.is_dir():
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.PATH_NOT_ACCESSIBLE.value,
            error_message="路径不是有效的目录"
        )

    # 检查是否为 Git 仓库（包含 .git 目录）
    git_dir = path / ".git"
    if not git_dir.exists():
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.NOT_A_GIT_REPO.value,
            error_message="所选目录不是有效的 Git 仓库"
        )

    # 检查读取权限
    try:
        list(path.iterdir())
    except PermissionError:
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.PATH_NOT_ACCESSIBLE.value,
            error_message="没有读取目录的权限"
        )

    # 提取仓库名称
    repo_name = path.name

    return RepoValidationResult(
        is_valid=True,
        repo_name=repo_name
    )


def import_local_repo(local_path: str, repo_name: str) -> RepoImportResult:
    """
    导入本地仓库

    将本地仓库记录到数据库。

    Args:
        local_path: 本地仓库的绝对路径
        repo_name: 仓库名称

    Returns:
        RepoImportResult: 导入结果
    """
    from backend.src.db.session import get_db_session
    from backend.src.models.entities import Repository, ImportSession

    try:
        with get_db_session() as db:
            # 创建仓库记录
            repository = Repository(
                source_type=RepoSourceType.LOCAL.value,
                name=repo_name,
                local_path=local_path,
                is_valid=True,
            )
            db.add(repository)
            db.flush()

            # 创建导入会话记录
            session = ImportSession(
                repo_id=repository.id,
                source_type=RepoSourceType.LOCAL.value,
                status=RepoStatus.SUCCESS.value,
            )
            db.add(session)
            db.flush()

            return RepoImportResult(
                success=True,
                repo_id=repository.id,
                local_path=local_path,
            )

    except Exception as e:
        return RepoImportResult(
            success=False,
            error_code=RepoErrorCode.INTERNAL_ERROR.value,
            error_message=f"导入仓库失败: {str(e)}",
        )


def validate_github_repo(owner: str, repo: str, token: Optional[str] = None) -> RepoValidationResult:
    """
    验证 GitHub 仓库有效性

    验证规则:
    1. owner 和 repo 不能为空
    2. 使用 GitHub API 验证仓库存在性
    3. 检查仓库是否为私有（私有仓库需要 Token）

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        token: 可选的 GitHub Token

    Returns:
        RepoValidationResult: 验证结果
    """
    if not owner or not repo:
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.INVALID_GITHUB_URL.value,
            error_message="无效的 GitHub 仓库地址"
        )

    # GitHub API URL
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = get_github_headers(token)

    try:
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 404:
            # GitHub 对私有仓库可能返回 404 以避免泄露仓库存在性
            # 如果没有 Token，提示用户可能需要配置 Token
            if not token:
                return RepoValidationResult(
                    is_valid=False,
                    error_code=RepoErrorCode.GITHUB_REPO_NOT_FOUND_OR_PRIVATE.value,
                    error_message="仓库不存在或为私有仓库，请配置 GitHub Token 后重试"
                )
            return RepoValidationResult(
                is_valid=False,
                error_code=RepoErrorCode.GITHUB_REPO_NOT_FOUND.value,
                error_message="仓库不存在"
            )

        if response.status_code == 403:
            # 可能是私有仓库或 rate limit
            data = response.json() if response.content else {}
            message = data.get("message", "").lower()
            if "private" in message or "not found" in message:
                return RepoValidationResult(
                    is_valid=False,
                    error_code=RepoErrorCode.GITHUB_REPO_PRIVATE.value,
                    error_message="该仓库为私有仓库，请配置 GitHub Token"
                )
            return RepoValidationResult(
                is_valid=False,
                error_code=RepoErrorCode.GITHUB_TOKEN_INVALID.value,
                error_message="GitHub Token 无效或权限不足"
            )

        if response.status_code != 200:
            return RepoValidationResult(
                is_valid=False,
                error_code=RepoErrorCode.NETWORK_ERROR.value,
                error_message="GitHub API 请求失败"
            )

        data = response.json()
        return RepoValidationResult(
            is_valid=True,
            repo_name=data.get("name"),
            description=data.get("description"),
            remote_url=data.get("html_url"),
        )

    except requests.Timeout:
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.NETWORK_ERROR.value,
            error_message="网络超时，请检查网络连接"
        )
    except requests.RequestException as e:
        return RepoValidationResult(
            is_valid=False,
            error_code=RepoErrorCode.NETWORK_ERROR.value,
            error_message=f"网络错误: {str(e)}"
        )


def import_github_repo(
    owner: str,
    repo: str,
    local_clone_path: str,
    token: Optional[str] = None,
    description: Optional[str] = None,
) -> RepoImportResult:
    """
    导入 GitHub 仓库

    执行 git clone 将仓库克隆到本地。

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        local_clone_path: 克隆目标目录
        token: 可选的 GitHub Token

    Returns:
        RepoImportResult: 导入结果
    """
    from backend.src.db.session import get_db_session
    from backend.src.models.entities import Repository, ImportSession

    clone_url = f"https://github.com/{owner}/{repo}.git"
    clone_env = None
    if token:
        # 使用 GIT_ASKPASS 环境变量安全传递 Token，避免 Token 在命令行中暴露
        # 创建临时脚本来提供凭证
        import tempfile
        import os
        askpass_script = tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False)
        askpass_script.write(f"#!/bin/sh\necho password={token}\n")
        askpass_script.close()
        os.chmod(askpass_script.name, 0o700)
        clone_env = os.environ.copy()
        clone_env["GIT_ASKPASS"] = askpass_script.name
        clone_env["GITHUB_TOKEN"] = token

    try:
        # 执行 git clone
        result = subprocess.run(
            ["git", "clone", "--depth", "1", clone_url, local_clone_path],
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
            env=clone_env,
        )

        # 清理临时脚本
        if clone_env and "GIT_ASKPASS" in clone_env:
            import os
            try:
                os.unlink(clone_env["GIT_ASKPASS"])
            except OSError:
                pass

        if result.returncode != 0:
            error_msg = result.stderr or "克隆失败"
            if "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                return RepoImportResult(
                    success=False,
                    error_code=RepoErrorCode.GITHUB_TOKEN_INVALID.value,
                    error_message="GitHub Token 无效或权限不足"
                )
            return RepoImportResult(
                success=False,
                error_code=RepoErrorCode.GITHUB_CLONE_FAILED.value,
                error_message=f"克隆仓库失败: {error_msg}"
            )

        # 验证克隆目录包含 .git
        if not Path(local_clone_path).exists():
            return RepoImportResult(
                success=False,
                error_code=RepoErrorCode.GITHUB_CLONE_FAILED.value,
                error_message="克隆目录不存在"
            )

        git_dir = Path(local_clone_path) / ".git"
        if not git_dir.exists():
            return RepoImportResult(
                success=False,
                error_code=RepoErrorCode.GITHUB_CLONE_FAILED.value,
                error_message="克隆的不是有效的 Git 仓库"
            )

        # 创建数据库记录（description 已在验证时获取，直接传入）
        with get_db_session() as db:
            repository = Repository(
                source_type=RepoSourceType.GITHUB.value,
                name=repo,
                description=description,
                local_path=local_clone_path,
                remote_url=f"https://github.com/{owner}/{repo}",
                is_valid=True,
            )
            db.add(repository)
            db.flush()

            session = ImportSession(
                repo_id=repository.id,
                source_type=RepoSourceType.GITHUB.value,
                status=RepoStatus.SUCCESS.value,
            )
            db.add(session)
            db.flush()

            return RepoImportResult(
                success=True,
                repo_id=repository.id,
                local_path=local_clone_path,
            )

    except subprocess.TimeoutExpired:
        return RepoImportResult(
            success=False,
            error_code=RepoErrorCode.GITHUB_CLONE_FAILED.value,
            error_message="克隆超时（5分钟），请检查网络连接"
        )
    except Exception as e:
        return RepoImportResult(
            success=False,
            error_code=RepoErrorCode.INTERNAL_ERROR.value,
            error_message=f"导入仓库失败: {str(e)}"
        )


def get_current_repo() -> Optional[dict]:
    """
    获取当前仓库

    Returns:
        当前仓库信息，如果不存在则返回 None
    """
    from backend.src.db.session import get_db_session
    from backend.src.models.entities import Repository

    with get_db_session() as db:
        repo = db.query(Repository).order_by(Repository.created_at.desc()).first()
        if not repo:
            return None

        return {
            "id": repo.id,
            "type": repo.source_type,
            "local_path": repo.local_path,
            "remote_url": repo.remote_url,
            "name": repo.name,
            "description": repo.description,
            "imported_at": repo.created_at.isoformat(),
        }
