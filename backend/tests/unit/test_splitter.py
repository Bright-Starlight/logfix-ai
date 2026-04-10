"""
splitter 服务单元测试

测试日志切分核心逻辑。
"""

import pytest
import tempfile
from pathlib import Path
from backend.src.services.splitter import LogSplitter, validate_regex_pattern


@pytest.fixture
def sample_log_file():
    """创建临时日志文件"""
    content = """2024-01-01 10:00:00 INFO Server started
2024-01-01 10:01:00 DEBUG Processing request
2024-01-01 10:02:00 DEBUG Database query executed
2024-01-02 10:00:00 INFO New connection established
2024-01-02 10:01:00 ERROR Connection timeout
2024-01-02 10:02:00 INFO Connection recovered
2024-01-03 10:00:00 DEBUG Health check passed
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = Path(f.name)

    yield temp_path

    # 清理
    temp_path.unlink(missing_ok=True)


def test_validate_regex_pattern_valid():
    """测试校验有效正则表达式"""
    valid, error = validate_regex_pattern(r"^\d{4}-\d{2}-\d{2}")
    assert valid is True
    assert error == ""


def test_validate_regex_pattern_invalid():
    """测试校验无效正则表达式"""
    valid, error = validate_regex_pattern(r"[invalid")
    assert valid is False
    assert "unexpected" in error or "unterminated" in error.lower()


def test_split_by_regex(sample_log_file):
    """测试按正则表达式切分"""
    splitter = LogSplitter(sample_log_file, encoding="utf-8")
    chunks = list(splitter.split_by_regex(r"^\d{4}-\d{2}-\d{2}"))

    assert len(chunks) == 3

    # 验证第一个片段
    assert chunks[0].chunk_index == 0
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert "Server started" in chunks[0].content
    assert "Database query" in chunks[0].content

    # 验证第二个片段
    assert chunks[1].chunk_index == 1
    assert chunks[1].start_line == 4
    assert chunks[2].chunk_index == 2


def test_split_by_fixed_string_with_delimiter(sample_log_file):
    """测试按固定分隔符切分"""
    splitter = LogSplitter(sample_log_file, encoding="utf-8")
    chunks = list(splitter.split_by_fixed_string("ERROR"))

    # 应该切分出包含 ERROR 的行
    assert len(chunks) >= 1
    assert any("ERROR" in chunk.content for chunk in chunks)


def test_split_by_fixed_string_empty_lines(sample_log_file):
    """测试按空行切分"""
    # 添加空行
    content = """2024-01-01 10:00:00 INFO Line 1

2024-01-01 10:01:00 DEBUG Line 2

2024-01-01 10:02:00 INFO Line 3
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = Path(f.name)

    try:
        splitter = LogSplitter(temp_path, encoding="utf-8")
        chunks = list(splitter.split_by_fixed_string(""))

        # 应该切分出非空片段
        assert len(chunks) == 3
    finally:
        temp_path.unlink(missing_ok=True)


def test_count_matches(sample_log_file):
    """测试估算匹配数量"""
    splitter = LogSplitter(sample_log_file, encoding="utf-8")
    count = splitter.count_matches(r"^\d{4}-\d{2}-\d{2}", sample_lines=100)

    # 应该匹配所有日期开头行
    assert count == 7
