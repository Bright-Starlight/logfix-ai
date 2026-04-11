"""
结构化日志服务

根据宪法 V. 可观测性 要求:
- 日志文件必须输出到 /log 目录下
- 日志文件命名规范为 {项目名}_{日期}.log，例如 logfix-ai_20260407.log
- 控制台（stdout/stderr）仅用于人类可读的进度输出
- 必须使用标准日志级别：DEBUG、INFO、WARNING、ERROR
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

LOG_DIR = Path("log")
LOG_DIR.mkdir(exist_ok=True)


def get_log_filename() -> str:
    """生成日志文件名，格式: logfix-ai_{日期}.log"""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"logfix-ai_{date_str}.log"


def setup_logging(log_level: str = None) -> None:
    """
    配置 loguru 日志系统

    Args:
        log_level: 日志级别，默认从环境变量读取或 INFO
    """
    if log_level is None:
        import os
        log_level = os.getenv("LOG_LEVEL", "INFO")
    # 移除默认的 handler
    logger.remove()

    # 移除所有现有 handlers
    logger.configure(handlers=[])

    # 控制台 handler - 仅用于进度输出（人类可读）
    logger.add(
        sys.stderr,
        format="<level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # 文件 handler - 结构化日志输出到 /log 目录
    log_path = LOG_DIR / get_log_filename()
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation="00:00",  # 每天零点轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,  # 线程安全
    )

    logger.info("日志服务初始化完成", extra={"log_file": str(log_path)})


def get_logger(name: str = __name__):
    """
    获取配置好的 logger 实例

    Args:
        name: 模块名称

    Returns:
        配置好的 logger 实例
    """
    return logger.bind(module=name)


# 文件上传事件日志
def log_file_upload(filename: str, file_size: int, encoding: str, file_id: str) -> None:
    """记录文件上传事件"""
    get_logger().info(
        f"文件上传事件: filename={filename}, size={file_size}, encoding={encoding}, file_id={file_id}"
    )


# 切分规则应用事件日志
def log_split_rule_applied(rule_type: str, rule_content: str, match_count: int, session_id: str) -> None:
    """记录切分规则应用事件"""
    get_logger().info(
        f"切分规则应用: rule_type={rule_type}, rule_content={rule_content}, "
        f"match_count={match_count}, session_id={session_id}"
    )


# 错误事件日志
def log_error(error_type: str, error_message: str, context: dict) -> None:
    """记录错误事件"""
    get_logger().error(
        f"错误事件: type={error_type}, message={error_message}, context={context}"
    )


# 切分进度事件日志
def log_split_progress(session_id: str, processed_chunks: int, total_chunks: int) -> None:
    """记录切分进度"""
    get_logger().info(
        f"切分进度: session_id={session_id}, "
        f"processed={processed_chunks}/{total_chunks}, "
        f"percent={int(processed_chunks/total_chunks*100) if total_chunks > 0 else 0}%"
    )


# ============ 003-log-analysis-pipeline 新增日志函数 ============

# 分类模式选择事件日志
def log_classification_mode_selected(mode: str, session_id: str) -> None:
    """记录分类模式选择事件"""
    get_logger().info(
        f"分类模式选择: mode={mode}, session_id={session_id}"
    )


# 分类进度更新事件日志
def log_classification_progress(
    session_id: str,
    status: str,
    processed_items: int,
    total_items: int,
    current_phase: str
) -> None:
    """记录分类进度更新"""
    progress_percent = int(processed_items / total_items * 100) if total_items > 0 else 0
    get_logger().info(
        f"分类进度: session_id={session_id}, status={status}, "
        f"processed={processed_items}/{total_items}, "
        f"percent={progress_percent}%, phase={current_phase}"
    )


# 分类结果事件日志
def log_classification_result(
    session_id: str,
    new_entries: int,
    duplicates: int,
    ignored: int
) -> None:
    """记录分类结果"""
    get_logger().info(
        f"分类结果: session_id={session_id}, "
        f"new_entries={new_entries}, duplicates={duplicates}, ignored={ignored}"
    )


# 去重检测结果日志
def log_deduplication_result(session_id: str, is_duplicate: bool, entry_id: str) -> None:
    """记录去重检测结果"""
    result_type = "duplicate" if is_duplicate else "new"
    get_logger().debug(
        f"去重检测: session_id={session_id}, result={result_type}, entry_id={entry_id}"
    )


# 忽略规则匹配日志
def log_ignore_rule_match(session_id: str, rule_name: str, pattern: str) -> None:
    """记录忽略规则匹配"""
    get_logger().debug(
        f"忽略规则匹配: session_id={session_id}, rule={rule_name}, pattern={pattern}"
    )


# 初始化默认 logger
setup_logging("DEBUG")
