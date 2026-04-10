"""
日志切分核心服务

负责按正则表达式或固定分隔符切分日志文件。
"""

import re
from pathlib import Path
from typing import Iterator, Optional, Callable

from backend.src.services.log_service import get_logger


class SplitChunk:
    """切分片段"""

    __slots__ = ("chunk_index", "start_line", "end_line", "content")

    def __init__(self, chunk_index: int, start_line: int, end_line: int, content: str):
        self.chunk_index = chunk_index
        self.start_line = start_line
        self.end_line = end_line
        self.content = content

    def to_dict(self) -> dict:
        return {
            "chunk_index": self.chunk_index,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
        }


class LogSplitter:
    """日志切分器"""

    __slots__ = ("file_path", "encoding", "progress_callback", "logger")

    def __init__(
        self,
        file_path: Path,
        encoding: str = "utf-8",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        self.file_path = file_path
        self.encoding = encoding
        self.progress_callback = progress_callback
        self.logger = get_logger("splitter")

    def split_by_regex(
        self,
        pattern: str,
        flags: int = 0
    ) -> Iterator[SplitChunk]:
        """
        按正则表达式切分日志

        Args:
            pattern: 正则表达式
            flags: 正则标志

        Yields:
            SplitChunk: 切分片段
        """
        compiled_pattern = re.compile(pattern, flags)

        chunk_index = 0
        current_content: list[str] = []
        start_line = 1
        line_number = 0

        try:
            with open(self.file_path, "r", encoding=self.encoding, errors="replace") as f:
                for line in f:
                    line_number += 1
                    line = line.rstrip("\n\r")

                    if compiled_pattern.match(line):
                        # 匹配到新片段起始行，保存当前片段
                        if current_content:
                            chunk = SplitChunk(
                                chunk_index=chunk_index,
                                start_line=start_line,
                                end_line=line_number - 1,
                                content="\n".join(current_content)
                            )
                            yield chunk
                            chunk_index += 1
                            current_content = []
                            start_line = line_number

                    current_content.append(line)

                    # 报告进度
                    if self.progress_callback and line_number % 100 == 0:
                        self.progress_callback(line_number, -1)  # -1 表示未知总行数

                # 处理最后一片段
                if current_content:
                    chunk = SplitChunk(
                        chunk_index=chunk_index,
                        start_line=start_line,
                        end_line=line_number,
                        content="\n".join(current_content)
                    )
                    yield chunk

        except re.error as e:
            self.logger.error(f"正则表达式错误: {e}")
            raise ValueError(f"正则表达式错误: {e}")

    def split_by_fixed_string(
        self,
        delimiter: str | None,
        include_empty: bool = True
    ) -> Iterator[SplitChunk]:
        """
        按固定字符串切分日志

        Args:
            delimiter: 分隔符（空字符串表示按空行切分）
            include_empty: 是否包含空片段

        Yields:
            SplitChunk: 切分片段
        """
        chunk_index = 0
        current_content: list[str] = []
        start_line = 1
        line_number = 0

        try:
            with open(self.file_path, "r", encoding=self.encoding, errors="replace") as f:
                for line in f:
                    line_number += 1
                    stripped = line.rstrip("\n\r")

                    # 判断是否为分隔符
                    is_delimiter = (
                        (not delimiter and not stripped) or  # 空行分隔
                        (delimiter and delimiter in stripped)  # 字符串分隔
                    )

                    if is_delimiter:
                        if current_content or include_empty:
                            chunk = SplitChunk(
                                chunk_index=chunk_index,
                                start_line=start_line,
                                end_line=line_number - 1,
                                content="\n".join(current_content)
                            )
                            yield chunk
                            chunk_index += 1
                        current_content = []
                        start_line = line_number + 1
                    else:
                        current_content.append(stripped)

                    # 报告进度
                    if self.progress_callback and line_number % 100 == 0:
                        self.progress_callback(line_number, -1)

                # 处理最后一片段
                if current_content:
                    chunk = SplitChunk(
                        chunk_index=chunk_index,
                        start_line=start_line,
                        end_line=line_number,
                        content="\n".join(current_content)
                    )
                    yield chunk

        except Exception as e:
            self.logger.error(f"切分错误: {e}")
            raise

    def count_matches(self, pattern: str, sample_lines: int = 1000) -> int:
        """
        估算匹配数量（用于校验）

        Args:
            pattern: 正则表达式
            sample_lines: 采样行数

        Returns:
            int: 估算的匹配数
        """
        compiled_pattern = re.compile(pattern)
        count = 0

        try:
            with open(self.file_path, "r", encoding=self.encoding, errors="replace") as f:
                for i, line in enumerate(f):
                    if i >= sample_lines:
                        break
                    if compiled_pattern.match(line.rstrip("\n\r")):
                        count += 1

            return count

        except re.error:
            raise ValueError("正则表达式语法错误")

    def validate_regex(self, pattern: str) -> tuple[bool, int]:
        """
        校验正则表达式并估算匹配数

        Args:
            pattern: 正则表达式

        Returns:
            tuple[bool, int]: (是否有效, 估算匹配数)
        """
        try:
            re.compile(pattern)
            count = self.count_matches(pattern)
            return True, count
        except re.error:
            return False, 0


def validate_regex_pattern(pattern: str) -> tuple[bool, str]:
    """
    校验正则表达式

    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        re.compile(pattern)
        return True, ""
    except re.error as e:
        return False, str(e)
