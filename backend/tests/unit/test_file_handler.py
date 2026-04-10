"""
file_handler 服务单元测试

测试文件处理服务。
"""

import pytest
import tempfile
from pathlib import Path
from backend.src.services.file_handler import FileHandler


@pytest.fixture
def file_handler():
    """创建文件处理器实例"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield FileHandler(storage_dir=tmpdir)


def test_is_supported_file(file_handler):
    """测试文件类型支持检查"""
    assert file_handler.is_supported_file("test.log") is True
    assert file_handler.is_supported_file("test.txt") is True
    assert file_handler.is_supported_file("test.json") is True
    assert file_handler.is_supported_file("test.csv") is True
    assert file_handler.is_supported_file("test.xml") is True
    assert file_handler.is_supported_file("test.png") is False
    assert file_handler.is_supported_file("test.jpg") is False
    assert file_handler.is_supported_file("test.pdf") is False


def test_validate_file_size(file_handler):
    """测试文件大小验证"""
    assert file_handler.validate_file_size(1000) is True
    assert file_handler.validate_file_size(0) is False
    assert file_handler.validate_file_size(101 * 1024 * 1024) is False  # 超过100MB


def test_detect_encoding_utf8(file_handler):
    """测试 UTF-8 编码检测"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        f.write("中文测试内容\nHello World\n")
        temp_path = Path(f.name)

    try:
        encoding, confidence = file_handler.detect_encoding(temp_path)
        assert encoding == "utf-8"
        assert confidence > 0.5
    finally:
        temp_path.unlink(missing_ok=True)


def test_read_lines(file_handler):
    """测试读取文件行"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        temp_path = Path(f.name)

    try:
        lines = file_handler.read_lines(temp_path, "utf-8", start_line=0, max_lines=3)
        assert len(lines) == 3
        assert lines[0] == "Line 1"
        assert lines[2] == "Line 3"
    finally:
        temp_path.unlink(missing_ok=True)


def test_count_lines(file_handler):
    """测试统计文件行数"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
        f.write("Line 1\nLine 2\nLine 3\n")
        temp_path = Path(f.name)

    try:
        count = file_handler.count_lines(temp_path, "utf-8")
        assert count == 3
    finally:
        temp_path.unlink(missing_ok=True)


def test_get_storage_path(file_handler):
    """测试生成存储路径"""
    path = file_handler.get_storage_path("abc123", "test.log")
    assert "abc123" in str(path)
    assert "test.log" in str(path)
