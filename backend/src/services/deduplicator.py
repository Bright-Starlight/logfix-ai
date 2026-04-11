"""
去重服务

负责检测和处理重复日志条目。
"""

import hashlib
from typing import Optional
from datetime import datetime

from backend.src.services.log_service import get_logger


def compute_message_hash(normalized_message: str) -> str:
    """
    计算消息哈希

    Args:
        normalized_message: 归一化后的消息

    Returns:
        哈希值
    """
    return hashlib.md5(normalized_message.encode('utf-8')).hexdigest()


def find_duplicate_entry(
    normalized_message: str,
    db_session
) -> Optional[dict]:
    """
    在数据库中查找重复条目

    Args:
        normalized_message: 归一化后的消息
        db_session: 数据库会话

    Returns:
        重复条目字典，如果不存在则返回None
    """
    from backend.src.models.entities import LogEntry

    _logger = get_logger("deduplicator")

    # 使用归一化消息查找
    entry = db_session.query(LogEntry).filter(
        LogEntry.normalized_message == normalized_message
    ).first()

    if entry:
        _logger.info(f"发现重复条目: {entry.id}, occurrence_count={entry.occurrence_count}")
        return {
            "id": str(entry.id),
            "occurrence_count": entry.occurrence_count,
        }

    return None


def update_duplicate_entry(
    entry_id: str,
    db_session
) -> None:
    """
    更新重复条目的统计信息

    Args:
        entry_id: 条目ID
        db_session: 数据库会话
    """
    from backend.src.models.entities import LogEntry

    _logger = get_logger("deduplicator")

    entry = db_session.query(LogEntry).filter(
        LogEntry.id == entry_id
    ).first()

    if entry:
        entry.occurrence_count += 1
        entry.last_seen_at = datetime.now()
        _logger.info(f"更新重复条目 {entry_id}: occurrence_count={entry.occurrence_count}")
