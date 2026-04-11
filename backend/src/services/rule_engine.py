"""
规则引擎服务

负责执行用户定义的解析规则。
"""

import re
import signal
from typing import Optional, Callable
from contextlib import contextmanager

from backend.src.services.log_service import get_logger


_logger = get_logger("rule_engine")

# 危险导入列表
DANGEROUS_IMPORTS = [
    'os', 'sys', 'subprocess', 'socket',
    'urllib', 'http', 'requests',
    'importlib', '__import__',
    'eval', 'exec', 'compile',
    'open', 'file', 'input',
    'pathlib', 'glob', 'shutil',
]

# 执行超时时间（秒）
EXECUTION_TIMEOUT = 1


class ExecutionTimeoutError(Exception):
    """执行超时异常"""
    pass


@contextmanager
def timeout_handler(seconds: int = EXECUTION_TIMEOUT):
    """超时处理上下文管理器"""
    def handler(signum, frame):
        raise ExecutionTimeoutError(f"执行超时（{seconds}秒）")

    # 设置信号处理器
    old_handler = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def validate_rule_syntax(rule_type: str, pattern: Optional[str] = None, code: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    验证规则语法

    Args:
        rule_type: 规则类型 (regex/code)
        pattern: 正则表达式
        code: 代码片段

    Returns:
        (is_valid, error_message)
    """
    if rule_type == "regex":
        if not pattern:
            return False, "正则规则必须提供 pattern"

        try:
            re.compile(pattern)
            return True, None
        except re.error as e:
            return False, f"正则表达式语法错误: {e}"

    elif rule_type == "code":
        if not code:
            return False, "代码规则必须提供 code"

        # 检查危险导入
        code_upper = code.upper()
        for dangerous in DANGEROUS_IMPORTS:
            if dangerous.upper() in code_upper:
                return False, f"代码规则禁止导入: {dangerous}"

        return True, None

    return False, f"未知的规则类型: {rule_type}"


def execute_regex_rule(message: str, pattern: str, group_index: int = 0) -> Optional[dict]:
    """
    执行正则规则

    Args:
        message: 日志消息
        pattern: 正则表达式
        group_index: 提取分组索引

    Returns:
        提取结果字典，如果匹配失败则返回None
    """
    try:
        compiled = re.compile(pattern)
        match = compiled.search(message)

        if match:
            groups = match.groups()
            if groups and len(groups) > group_index:
                return {
                    "matched": True,
                    "error_type": groups[group_index] if groups else None,
                    "params": {},
                }

            return {
                "matched": True,
                "error_type": match.group(0),
                "params": {},
            }

        return None

    except re.error as e:
        _logger.error(f"正则执行错误: {e}")
        return None


def execute_code_rule(message: str, code: str) -> Optional[dict]:
    """
    执行代码规则（沙箱限制）

    Args:
        message: 日志消息
        code: Python代码片段

    Returns:
        提取结果字典，如果执行失败则返回None
    """
    # 构建安全的执行环境
    safe_globals = {
        "__builtins__": {
            # 只允许基本内置函数
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "range": range,
            "re": re,
            "match": re.match,
            "search": re.search,
            "findall": re.findall,
            "sub": re.sub,
        }
    }

    safe_locals = {
        "message": message,
        "result": None,
    }

    # 构建执行函数
    exec_code = f"""
def parse(message):
    {code}
    return result

result = parse(message)
"""

    try:
        with timeout_handler(EXECUTION_TIMEOUT):
            exec(exec_code, safe_globals, safe_locals)

        return safe_locals.get("result")

    except ExecutionTimeoutError:
        _logger.error(f"代码执行超时: {EXECUTION_TIMEOUT}秒")
        return None
    except Exception as e:
        _logger.error(f"代码执行错误: {e}")
        return None


def execute_rule(message: str, rule: dict) -> Optional[dict]:
    """
    执行单条规则

    Args:
        message: 日志消息
        rule: 规则字典，包含 rule_type, pattern/code, group_index

    Returns:
        提取结果字典
    """
    rule_type = rule.get("rule_type")

    if rule_type == "regex":
        pattern = rule.get("pattern", "")
        group_index = rule.get("group_index", 0)
        return execute_regex_rule(message, pattern, group_index)

    elif rule_type == "code":
        code = rule.get("code", "")
        return execute_code_rule(message, code)

    return None


def execute_rules_chain(message: str, rules: list) -> Optional[dict]:
    """
    按优先级执行规则链

    Args:
        message: 日志消息
        rules: 排序后的规则列表

    Returns:
        首次匹配的结果，或None
    """
    for rule in rules:
        if not rule.get("enabled", True):
            continue

        result = execute_rule(message, rule)
        if result and result.get("matched"):
            _logger.debug(f"规则匹配成功: {rule.get('name')}")
            return result

    return None
