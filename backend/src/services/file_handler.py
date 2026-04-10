"""
文件处理服务

负责文件上传、编码检测、文件读取等核心功能。
"""

from itertools import islice
from pathlib import Path
from typing import Tuple, Optional

import chardet


class FileHandler:
    """文件处理服务类"""

    # 支持的文本文件扩展名
    SUPPORTED_EXTENSIONS = {".log", ".txt", ".json", ".xml", ".csv"}

    # 最大文件大小 (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # 编码检测配置
    ENCODING_CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def is_supported_file(self, filename: str) -> bool:
        """检查文件是否支持"""
        if not filename:
            return False
        suffix = Path(filename).suffix.lower()
        return suffix in self.SUPPORTED_EXTENSIONS

    def detect_encoding(self, file_path: Path) -> Tuple[str, float]:
        """
        检测文件编码

        Returns:
            Tuple[str, float]: (编码名称, 置信度)
        """
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # 读取前10KB进行检测

        result = chardet.detect(raw_data)
        encoding = result.get("encoding", "utf-8") or "utf-8"
        confidence = result.get("confidence", 0.0)

        # 如果置信度低于阈值，使用 UTF-8 作为后备
        if confidence < self.ENCODING_CONFIDENCE_THRESHOLD:
            encoding = "utf-8"

        return encoding, confidence

    def read_lines(
        self,
        file_path: Path,
        encoding: str = "utf-8",
        start_line: int = 0,
        max_lines: Optional[int] = None
    ) -> list[str]:
        """
        读取文件行

        Args:
            file_path: 文件路径
            encoding: 编码
            start_line: 起始行号 (0-indexed)
            max_lines: 最大读取行数

        Returns:
            list[str]: 行列表
        """
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            # 使用 islice 高效跳过起始行
            lines_iter = islice(f, start_line, max_lines if max_lines else None)

            return [line.rstrip("\n\r") for line in lines_iter]

    def count_lines(self, file_path: Path, encoding: str = "utf-8") -> int:
        """统计文件总行数"""
        count = 0
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            for _ in f:
                count += 1
        return count

    def validate_file_size(self, file_size: int) -> bool:
        """验证文件大小"""
        return 0 < file_size <= self.MAX_FILE_SIZE

    def get_storage_path(self, file_id: str, original_filename: str) -> Path:
        """生成存储路径"""
        # 使用文件ID作为子目录，避免文件名冲突
        return self.storage_dir / file_id / original_filename


# 全局单例
_file_handler: Optional[FileHandler] = None


def get_file_handler() -> FileHandler:
    """获取文件处理器单例"""
    global _file_handler
    if _file_handler is None:
        _file_handler = FileHandler()
    return _file_handler
