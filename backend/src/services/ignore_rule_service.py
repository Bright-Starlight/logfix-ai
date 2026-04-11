"""
忽略规则服务

负责检测日志是否应被忽略。
"""

import re
from typing import Optional

from backend.src.services.log_service import get_logger


_logger = get_logger("ignore_rule")


def match_ignore_rule(message: str, rule: dict) -> bool:
    """
    检测消息是否匹配忽略规则

    Args:
        message: 日志消息
        rule: 忽略规则字典

    Returns:
        是否匹配
    """
    match_type = rule.get("match_type", "")
    pattern = rule.get("pattern", "")

    if not pattern:
        return False

    try:
        if match_type == "contains":
            return pattern.lower() in message.lower()

        elif match_type == "exact":
            return message == pattern

        elif match_type == "regex":
            compiled = re.compile(pattern)
            return compiled.search(message) is not None

        else:
            _logger.warning(f"未知的匹配类型: {match_type}")
            return False

    except re.error as e:
        _logger.error(f"正则匹配错误: {e}")
        return False


def should_ignore(message: str, ignore_rules: list) -> tuple[bool, Optional[dict]]:
    """
    检测消息是否应被忽略

    Args:
        message: 日志消息
        ignore_rules: 忽略规则列表

    Returns:
        (should_ignore, matched_rule)
    """
    for rule in ignore_rules:
        if not rule.get("enabled", True):
            continue

        if match_ignore_rule(message, rule):
            _logger.debug(f"消息匹配忽略规则: {rule.get('name')}")
            return True, rule

    return False, None


def validate_ignore_pattern(match_type: str, pattern: str) -> tuple[bool, Optional[str]]:
    """
    验证忽略规则模式

    Args:
        match_type: 匹配类型
        pattern: 模式

    Returns:
        (is_valid, error_message)
    """
    if not pattern:
        return False, "模式不能为空"

    if match_type == "contains":
        if len(pattern) < 2:
            return False, "包含类型模式至少需要2个字符"
        return True, None

    elif match_type == "exact":
        return True, None

    elif match_type == "regex":
        try:
            re.compile(pattern)
            return True, None
        except re.error as e:
            return False, f"正则表达式语法错误: {e}"

    return False, f"未知的匹配类型: {match_type}"
