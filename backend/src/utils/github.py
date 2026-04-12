"""
GitHub 相关的工具函数

提供 GitHub URL 解析、API 请求头构建等通用功能。
"""

from typing import Optional


def parse_github_owner_repo(url_or_path: str) -> tuple[str, str]:
    """
    从 GitHub URL 或简写形式解析 owner 和 repo

    Args:
        url_or_path: 可以是以下格式:
            - 'owner/repo' 简写
            - 'https://github.com/owner/repo'
            - 'https://github.com/owner/repo.git'

    Returns:
        tuple[str, str]: (owner, repo)
    """
    # 去除 .git 后缀和末尾斜杠
    path = url_or_path.rstrip("/").replace(".git", "")
    parts = path.split("/")
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return "", url_or_path


def get_github_headers(token: Optional[str] = None) -> dict:
    """
    构建 GitHub API 请求头

    Args:
        token: 可选的 GitHub Personal Access Token

    Returns:
        dict: 包含 Accept 和可选 Authorization 的请求头
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers
