"""
Windows 兼容路径处理工具

提供跨平台的路径处理功能。
"""

import os
import sys
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Union


def to_pathlib_path(path: Union[str, Path]) -> Path:
    """
    将路径转换为标准的 Path 对象

    Args:
        path: 路径字符串或 Path 对象

    Returns:
        Path: 标准化的 Path 对象
    """
    if isinstance(path, Path):
        return path
    return Path(path)


def normalize_path(path: Union[str, Path]) -> str:
    """
    标准化路径，转换为适合当前操作系统的格式

    在 Windows 上，将正斜杠转换为反斜杠。
    在 Unix 上，将反斜杠转换为正斜杠。

    Args:
        path: 路径

    Returns:
        str: 标准化的路径字符串
    """
    p = to_pathlib_path(path)
    return str(p)


def to_posix_path(path: Union[str, Path]) -> str:
    """
    转换为 POSIX 路径格式（正斜杠）

    Args:
        path: 路径

    Returns:
        str: POSIX 格式路径
    """
    p = to_pathlib_path(path)
    return p.as_posix()


def to_windows_path(path: Union[str, Path]) -> str:
    """
    转换为 Windows 路径格式（反斜杠）

    Args:
        path: 路径

    Returns:
        str: Windows 格式路径
    """
    p = to_pathlib_path(path)
    return str(p)


def is_windows() -> bool:
    """判断是否为 Windows 系统"""
    return sys.platform.startswith("win") or os.name == "nt"


def get_path_separator() -> str:
    """获取路径分隔符"""
    return os.sep


def join_paths(*parts: str) -> str:
    """
    连接路径部分

    Args:
        *parts: 路径部分

    Returns:
        str: 连接后的路径
    """
    return normalize_path(Path(*parts))


def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """
    获取相对路径

    Args:
        path: 目标路径
        base: 基准路径

    Returns:
        Path: 相对路径
    """
    p = to_pathlib_path(path)
    b = to_pathlib_path(base)
    return p.relative_to(b)


# 用于创建目录的跨平台函数
def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，如不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path: 目录 Path 对象
    """
    p = to_pathlib_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


# 用于文件路径的跨平台函数
def safe_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符

    Args:
        filename: 原始文件名

    Returns:
        str: 安全的文件名
    """
    # Windows 不允许的字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, "_")
    return filename
