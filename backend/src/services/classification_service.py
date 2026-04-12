"""
分类服务

协调分类、去重、规则引擎和AI模式的完整流程。
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.src.services.log_service import get_logger
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
from backend.src.services.ai_analyzer import analyze_logs_ai, classify_with_ai_result, ClassificationResult
from backend.src.services.ignore_rule_service import should_ignore
from backend.src.models.entities import (
    LogEntry,
    LogCategory,
    IgnoreRule,
    ParseRule,
)


_logger = get_logger("classification_service")


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


async def classify_logs(
    db: Session,
    logs: list[str],
    mode: str = "rule_engine",
    file_id: Optional[str] = None,
    classification_session_id: Optional[str] = None,
) -> dict:
    """
    分类日志条目

    Args:
        db: 数据库会话
        logs: 日志条目列表
        mode: 处理模式 (rule_engine 或 ai)
        file_id: 来源文件ID
        classification_session_id: 可选的分类会话ID，用于进度更新

    Returns:
        分类结果字典
    """
    _logger = get_logger("classification").bind(
        entry_count=len(logs),
        mode=mode,
    )

    # 获取启用的忽略规则
    ignore_rules = get_enabled_ignore_rules(db)
    _logger.debug(f"忽略规则数量: {len(ignore_rules)}")

    processed = 0
    new_entries = 0
    duplicates = 0
    ignored_count = 0
    entries = []
    _ai_results: Optional[list] = None  # AI 批量结果缓存
    _ai_error: Optional[str] = None      # AI 错误信息缓存
    total = len(logs)
    start_time = datetime.now()

    # 进度更新间隔：每处理 5% 或每条日志（取较大值）
    update_interval = max(1, total // 20) if total > 0 else 1

    # 更新当前阶段
    def update_progress(phase: str, processed: int):
        if classification_session_id:
            try:
                ClassificationSession = __import__(
                    "backend.src.models.entities",
                    fromlist=["ClassificationSession"]
                ).ClassificationSession
                elapsed = (datetime.now() - start_time).total_seconds()
                if processed > 0:
                    avg_time_per_item = elapsed / processed
                    remaining_items = total - processed
                    estimated_remaining = int(avg_time_per_item * remaining_items)
                else:
                    estimated_remaining = None

                session = db.query(ClassificationSession).filter(
                    ClassificationSession.id == uuid.UUID(classification_session_id)
                ).first()
                if session:
                    session.current_phase = phase
                    session.processed_items = processed
                    session.estimated_remaining_seconds = estimated_remaining
                    db.commit()
            except Exception as e:
                _logger.warning(f"更新进度失败: {e}")

    # 初始阶段：去重检测
    update_progress("去重检测中", 0)

    for log_entry in logs:
        processed += 1

        # 检查忽略规则
        ignored, matched_rule = should_ignore(log_entry, ignore_rules)
        if ignored:
            ignored_count += 1
            _logger.debug(f"日志被忽略: {matched_rule.get('name')}")
            continue

        # 归一化消息
        normalized = normalize_message(log_entry)

        # 提取堆栈跟踪
        stack_trace = extract_stack_trace(log_entry)

        # 检测日志级别
        log_level = detect_log_level(log_entry)

        if mode == "rule_engine":
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

        elif mode == "ai":
            # AI 模式 - 批量处理
            # 注意：AI 分析已在循环外批量调用，这里直接使用结果
            if _ai_results is None:
                # 首次进入 AI 模式，预获取 AI 结果
                update_progress("AI 分析中", processed - 1)
                _ai_results, _ai_error = await analyze_logs_ai(logs)
                if _ai_error:
                    _logger.error(f"AI 分析失败: {_ai_error}")

            if _ai_results:
                # 使用 AI 结果查找对应索引
                found = False
                for classification in _ai_results:
                    if classification.index == processed - 1:
                        category_name, error_type, extracted_params = classify_with_ai_result(
                            log_entry, classification
                        )
                        found = True
                        break
                if not found:
                    category_name, error_type = classify_message(log_entry)
                    extracted_params = {}
            else:
                # AI 失败，降级到规则引擎
                category_name, error_type = classify_message(log_entry)
                extracted_params = {}
        else:
            _logger.error(f"未知模式: {mode}")
            category_name, error_type = classify_message(log_entry)
            extracted_params = {}

        # 去重检查
        update_progress("分类分析中", processed)
        existing = find_duplicate_entry(normalized, db)
        if existing:
            # 更新重复记录
            update_duplicate_entry(existing["id"], db)
            duplicates += 1
            _logger.debug(f"重复条目: {existing['id']}")

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
            update_progress("存储中", processed)
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

        # 定期更新分类会话进度
        if classification_session_id and processed % update_interval == 0:
            update_progress("处理中", processed)

    # 最终进度更新（确保最后一次进度被保存）
    if classification_session_id and processed > 0:
        update_progress("已完成", processed)

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
