"""
分类服务

负责将日志条目分类到对应类别。
"""

import re
from typing import Optional
from loguru import logger

from backend.src.services.log_service import get_logger


# 预置分类映射
CATEGORY_PATTERNS = {
    "异常错误": [
        r"Exception",
        r"Error",
        r"Traceback",
        r"java\.",
        r"python",
        r"TypeError",
        r"ValueError",
        r"NullPointerException",
        r"IndexError",
        r"KeyError",
    ],
    "警告": [
        r"Warning",
        r"WARN",
        r"DeprecationWarning",
    ],
    "信息": [
        r"INFO",
        r"Information",
    ],
    "调试": [
        r"DEBUG",
        r"Debug",
    ],
    "致命错误": [
        r"FATAL",
        r"CRITICAL",
        r"PANIC",
    ],
}


def detect_log_level(message: str) -> str:
    """检测日志级别"""
    upper_message = message.upper()
    if "FATAL" in upper_message or "CRITICAL" in upper_message:
        return "FATAL"
    if "ERROR" in upper_message:
        return "ERROR"
    if "WARN" in upper_message:
        return "WARNING"
    if "INFO" in upper_message:
        return "INFO"
    if "DEBUG" in upper_message:
        return "DEBUG"
    return "UNKNOWN"


def extract_error_type(message: str) -> Optional[str]:
    """从消息中提取错误类型"""
    patterns = [
        r"(\w+(?:Exception|Error|Fault))",
        r"([A-Z]\w*(?:Exception|Error))",
        r"(\w+Error)",
    ]

    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1)

    return None


def classify_message(message: str) -> tuple[str, Optional[str]]:
    """
    对日志消息进行分类

    Args:
        message: 日志消息

    Returns:
        (category_name, error_type)
    """
    _logger = get_logger("classifier")

    log_level = detect_log_level(message)

    # 根据日志级别快速分类
    if log_level == "FATAL":
        error_type = extract_error_type(message)
        _logger.debug(f"分类为致命错误: {error_type}")
        return "致命错误", error_type

    if log_level == "ERROR":
        error_type = extract_error_type(message)
        if error_type:
            _logger.debug(f"分类为异常错误: {error_type}")
            return "异常错误", error_type
        # 检查是否有异常关键字
        for category, patterns in CATEGORY_PATTERNS.items():
            if category == "异常错误":
                for pattern in patterns:
                    if re.search(pattern, message, re.IGNORECASE):
                        _logger.debug(f"分类为{category}: 匹配 {pattern}")
                        return category, extract_error_type(message)
        _logger.debug("分类为异常错误: 默认")
        return "异常错误", None

    if log_level == "WARNING":
        _logger.debug("分类为警告")
        return "警告", None

    if log_level == "INFO":
        _logger.debug("分类为信息")
        return "信息", None

    if log_level == "DEBUG":
        _logger.debug("分类为调试")
        return "调试", None

    # 默认归类为异常错误
    error_type = extract_error_type(message)
    _logger.debug(f"默认分类为异常错误: {error_type}")
    return "异常错误", error_type


def normalize_message(message: str) -> str:
    """
    归一化消息 - 去除动态参数

    Args:
        message: 原始消息

    Returns:
        归一化后的消息
    """
    normalized = message

    # 去除数字序列
    normalized = re.sub(r'\d+', '*', normalized)

    # 去除路径中的目录，只保留文件名
    normalized = re.sub(r'(?:/[a-zA-Z0-9_-]+)+/([a-zA-Z0-9_-]+\.py)', r'\1', normalized)
    normalized = re.sub(r'(?:/[a-zA-Z0-9_-]+)+/([a-zA-Z0-9_-]+\.java)', r'\1', normalized)
    normalized = re.sub(r'(?:/[a-zA-Z0-9_-]+)+/([a-zA-Z0-9_-]+\.js)', r'\1', normalized)
    normalized = re.sub(r'([A-Za-z]:\\[^\s]+)', lambda m: m.group(1).split('\\')[-1], normalized)

    # 去除尾随空白
    normalized = normalized.strip()

    return normalized


def extract_stack_trace(message: str) -> Optional[str]:
    """提取堆栈跟踪信息"""
    lines = message.split('\n')

    stack_lines = []
    in_stack = False

    for line in lines:
        if re.search(r'(?:at |^\s+at |Traceback|^\s+File )', line):
            in_stack = True
            stack_lines.append(line)
        elif in_stack and not line.strip():
            break

    return '\n'.join(stack_lines) if stack_lines else None
