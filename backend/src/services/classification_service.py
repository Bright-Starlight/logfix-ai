"""
分类服务

协调分类、去重、规则引擎和AI模式的完整流程。
"""

import uuid
from datetime import datetime
from typing import Optional, Callable, Awaitable

from sqlalchemy.orm import Session

from backend.src.services.log_service import get_logger, log_classification_progress, log_deduplication_result, log_ignore_rule_match
from backend.src.services.classifier import (
    classify_message,
    normalize_message,
    extract_stack_trace,
    detect_log_level,
)
from backend.src.services.deduplicator import (
    find_duplicate_entry,
    update_duplicate_entry,
    compute_message_hash,
)
from backend.src.services.rule_engine import execute_rules_chain
from backend.src.services.ai_analyzer import analyze_logs_ai, classify_with_ai_result
from backend.src.services.ignore_rule_service import should_ignore
from backend.src.models.entities import (
    LogEntry,
    LogCategory,
    IgnoreRule,
    ParseRule,
    ClassificationSession,
)


_logger = get_logger("classification_service")


# 进度回调类型
ProgressCallback = Callable[[str, int, int, str], None]  # (session_id, processed, total, phase)

# 每条目预估处理时间（秒）- 用于估算剩余时间
SECONDS_PER_ITEM = 1


def get_or_create_category(db: Session, category_name: str) -> LogCategory:
    """获取或创建分类"""
    category = db.query(LogCategory).filter(
        LogCategory.name == category_name
    ).first()

    if not category:
        # 创建新分类
        category = LogCategory(
            name=category_name,
            is_system=False,
        )
        db.add(category)
        db.flush()
        _logger.info(f"创建新分类: {category_name}")

    return category


def get_enabled_ignore_rules(db: Session) -> list[dict]:
    """获取所有启用的忽略规则"""
    rules = db.query(IgnoreRule).filter(
        IgnoreRule.enabled == True
    ).all()

    return [
        {
            "id": str(rule.id),
            "name": rule.name,
            "match_type": rule.match_type,
            "pattern": rule.pattern,
        }
        for rule in rules
    ]


def get_enabled_parse_rules(db: Session) -> list[dict]:
    """获取所有启用的解析规则（按优先级排序）"""
    rules = db.query(ParseRule).filter(
        ParseRule.enabled == True
    ).order_by(ParseRule.priority.desc()).all()

    return [
        {
            "id": str(rule.id),
            "name": rule.name,
            "rule_type": rule.rule_type,
            "pattern": rule.pattern,
            "code": rule.code,
            "group_index": rule.group_index,
            "priority": rule.priority,
        }
        for rule in rules
    ]


def update_progress(db: Session, session_id: str, processed_items: int, current_phase: str) -> None:
    """
    更新分类会话进度

    Args:
        db: 数据库会话
        session_id: 分类会话ID
        processed_items: 已处理数量
        current_phase: 当前阶段名称
    """
    try:
        session = db.query(ClassificationSession).filter(
            ClassificationSession.id == uuid.UUID(session_id)
        ).first()

        if session:
            session.processed_items = processed_items
            session.current_phase = current_phase

            # 计算预估剩余时间
            if processed_items > 0 and session.total_items > 0:
                elapsed = processed_items
                remaining = session.total_items - processed_items
                if elapsed > 0:
                    seconds_per_item = SECONDS_PER_ITEM
                    session.estimated_remaining_seconds = max(0, int(remaining * seconds_per_item))

            # 记录进度日志
            log_classification_progress(
                session_id,
                session.status,
                processed_items,
                session.total_items,
                current_phase
            )

            # 提交到数据库，让轮询能读到
            db.commit()
    except Exception as e:
        _logger.warning(f"更新进度失败: {e}")


async def classify_logs(
    db: Session,
    logs: list[str],
    mode: str = "rule_engine",
    file_id: Optional[str] = None,
    classification_session_id: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> dict:
    """
    分类日志条目

    Args:
        db: 数据库会话
        logs: 日志条目列表
        mode: 处理模式 (rule_engine 或 ai)
        file_id: 来源文件ID
        classification_session_id: 分类会话ID（用于进度更新）
        progress_callback: 进度回调函数

    Returns:
        分类结果字典
    """
    _logger = get_logger("classification").bind(
        entry_count=len(logs),
        mode=mode,
    )

    # 如果有 classification_session_id，先更新状态为 processing
    if classification_session_id:
        try:
            session = db.query(ClassificationSession).filter(
                ClassificationSession.id == uuid.UUID(classification_session_id)
            ).first()
            if session:
                session.status = "processing"
                session.current_phase = "准备中"
                db.flush()
        except Exception as e:
            _logger.warning(f"更新分类会话状态失败: {e}")

    # AI 模式预处理：在循环前调用一次 AI 分析
    effective_mode = mode
    ai_classifications = None
    ai_duplicates = None

    if mode == "ai":
        ai_classifications, ai_duplicates, ai_error = await analyze_logs_ai(logs)
        if ai_error:
            if "AI_MODE_UNAVAILABLE" in ai_error:
                _logger.warning(f"AI 模式不可用，自动降级到规则引擎模式")
                effective_mode = "rule_engine"
            else:
                _logger.error(f"AI 分析失败: {ai_error}，自动降级到规则引擎模式")
                effective_mode = "rule_engine"

    # 获取启用的忽略规则
    ignore_rules = get_enabled_ignore_rules(db)
    _logger.debug(f"忽略规则数量: {len(ignore_rules)}")

    processed = 0
    new_entries = 0
    duplicates = 0
    ignored_count = 0
    entries = []
    total = len(logs)

    for idx, log_entry in enumerate(logs):
        processed += 1

        # 阶段：去重检测中
        if classification_session_id and processed == 1:
            update_progress(db, classification_session_id, processed, "去重检测中")
            if progress_callback:
                progress_callback(processed, total, "去重检测中")

        # 检查忽略规则
        ignored, matched_rule = should_ignore(log_entry, ignore_rules)
        if ignored:
            ignored_count += 1
            _logger.debug(f"日志被忽略: {matched_rule.get('name')}")
            if classification_session_id:
                log_ignore_rule_match(classification_session_id, matched_rule.get('name', ''), matched_rule.get('pattern', ''))
            continue

        # 阶段：分类分析中
        if classification_session_id and processed % 5 == 0:
            update_progress(db, classification_session_id, processed, "分类分析中")
            if progress_callback:
                progress_callback(processed, total, "分类分析中")

        # 归一化消息
        normalized = normalize_message(log_entry)

        # 提取堆栈跟踪
        stack_trace = extract_stack_trace(log_entry)

        # 检测日志级别
        log_level = detect_log_level(log_entry)

        if effective_mode == "ai" and ai_classifications:
            # AI 模式 - 使用预分析的分类结果
            if idx < len(ai_classifications):
                category_name, error_type, extracted_params = classify_with_ai_result(
                    log_entry, ai_classifications[idx]
                )
            else:
                category_name, error_type = classify_message(log_entry)
                extracted_params = {}
        elif effective_mode == "rule_engine":
            # 规则引擎模式
            # 获取解析规则
            parse_rules = get_enabled_parse_rules(db)

            if parse_rules:
                # 使用规则引擎
                rule_result = execute_rules_chain(log_entry, parse_rules)
                if rule_result:
                    error_type = rule_result.get("error_type")
                    extracted_params = rule_result.get("params", {})
                else:
                    # 未匹配规则，使用默认分类
                    category_name, error_type = classify_message(log_entry)
                    extracted_params = {}
            else:
                # 无规则，使用默认分类
                category_name, error_type = classify_message(log_entry)
                extracted_params = {}

        else:
            _logger.error(f"未知模式: {effective_mode}")
            category_name, error_type = classify_message(log_entry)
            extracted_params = {}

        # 阶段：存储中
        if classification_session_id:
            update_progress(db, classification_session_id, processed, "存储中")
            if progress_callback:
                progress_callback(processed, total, "存储中")

        # 去重检查
        existing = find_duplicate_entry(normalized, db)
        if existing:
            # 更新重复记录
            update_duplicate_entry(existing["id"], db)
            duplicates += 1
            _logger.debug(f"重复条目: {existing['id']}")

            if classification_session_id:
                log_deduplication_result(classification_session_id, True, existing['id'])

            entries.append({
                "id": existing["id"],
                "original_message": log_entry,
                "normalized_message": normalized,
                "stack_trace": stack_trace,
                "category": category_name,
                "error_type": error_type,
                "log_level": log_level,
                "occurrence_count": existing["occurrence_count"] + 1,
            })
        else:
            # 创建新记录
            category = get_or_create_category(db, category_name)

            entry = LogEntry(
                original_message=log_entry,
                normalized_message=normalized,
                stack_trace=stack_trace,
                category_id=category.id,
                error_type=error_type,
                extracted_params=extracted_params,
                log_level=log_level,
                occurrence_count=1,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
            )
            db.add(entry)
            db.flush()

            new_entries += 1
            _logger.debug(f"新条目: {entry.id}")

            if classification_session_id:
                log_deduplication_result(classification_session_id, False, str(entry.id))

            entries.append({
                "id": str(entry.id),
                "original_message": log_entry,
                "normalized_message": normalized,
                "stack_trace": stack_trace,
                "category": category_name,
                "error_type": error_type,
                "extracted_params": extracted_params,
                "log_level": log_level,
                "occurrence_count": 1,
                "first_seen_at": entry.first_seen_at,
                "last_seen_at": entry.last_seen_at,
            })

        # 每处理10条或最后一条时更新进度
        if classification_session_id and (processed % 10 == 0 or processed == total):
            update_progress(db, classification_session_id, processed, "分类分析中")

    # 更新完成状态
    if classification_session_id:
        try:
            session = db.query(ClassificationSession).filter(
                ClassificationSession.id == uuid.UUID(classification_session_id)
            ).first()
            if session:
                session.status = "completed"
                session.processed_items = processed
                session.current_phase = "完成"
                session.completed_at = datetime.now()
                session.estimated_remaining_seconds = 0
                log_classification_progress(
                    classification_session_id,
                    "completed",
                    processed,
                    total,
                    "完成"
                )
        except Exception as e:
            _logger.warning(f"更新分类会话完成状态失败: {e}")

    _logger.info(
        f"分类完成: processed={processed}, new={new_entries}, duplicates={duplicates}, ignored={ignored_count}"
    )

    return {
        "processed": processed,
        "new_entries": new_entries,
        "duplicates": duplicates,
        "ignored": ignored_count,
        "entries": entries,
    }
