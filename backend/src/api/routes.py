"""
API 路由定义

包含所有 REST API 端点的实现。
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from backend.src.api.schemas import (
    RegexValidationRequest,
    SplitRequest,
    UploadResponse,
    FilePreviewResponse,
    RegexValidationResponse,
    SplitResponse,
    SessionStatusResponse,
    ResultsResponse,
    ChunkDetailResponse,
    # 002-short-name-structured 新增
    ClassifyRequest,
    LogEntryResponse,
    LogListItemResponse,
    LogDetailResponse,
    StatsResponse,
    ParseRuleResponse,
    CreateParseRuleRequest,
    UpdateParseRuleRequest,
    IgnoreRuleResponse,
    CreateIgnoreRuleRequest,
)
from backend.src.db.session import get_db_session
from backend.src.models.entities import (
    LogFile, SplitSession, SplitResult,
    LogEntry, LogCategory, ParseRule, IgnoreRule, LogStatistics
)
from backend.src.services.file_handler import get_file_handler, FileHandler
from backend.src.services.splitter import LogSplitter, validate_regex_pattern
from backend.src.services.log_service import (
    log_file_upload,
    log_split_rule_applied,
    log_error,
    get_logger,
)
from backend.src.services.classification_service import classify_logs
from backend.src.services.rule_engine import validate_rule_syntax
from backend.src.services.ignore_rule_service import validate_ignore_pattern
from backend.src.utils.path import safe_filename

router = APIRouter(prefix="/api")
logger = get_logger("routes")

# 内容截断限制
MAX_CONTENT_PREVIEW = 1000


def make_response(data=None, error=None, status_code=200):
    """构造统一响应格式"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": error is None,
            "data": data,
            "error": error,
        }
    )


def make_error(code: str, message: str, status_code: int = 400):
    """构造错误响应"""
    return make_response(error={"code": code, "message": message}, status_code=status_code)


# ============ API 端点 ============

@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    chunk_index: Optional[int] = Form(None),
    total_chunks: Optional[int] = Form(None),
    upload_id: Optional[str] = Form(None),
):
    """上传日志文件，支持分片上传"""
    try:
        file_handler = get_file_handler()

        # 检查文件类型
        if not file_handler.is_supported_file(file.filename):
            log_error("INVALID_FILE_TYPE", "非文本文件", {"filename": file.filename})
            return make_error("INVALID_FILE_TYPE", "仅支持 .log, .txt, .json 等文本文件")

        # 生成安全的文件名
        safe_name = safe_filename(file.filename or "unknown")

        # 读取文件内容（流式读取以支持大文件）
        content = await file.read()

        # 检查文件大小
        if len(content) > file_handler.MAX_FILE_SIZE:
            log_error("FILE_TOO_LARGE", "文件过大", {"size": len(content)})
            return make_error("FILE_TOO_LARGE", "文件大小超过100MB限制")

        # 生成文件ID
        file_id = upload_id or str(uuid.uuid4())

        # 创建存储目录
        storage_path = Path("storage") / file_id / safe_name
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存文件
        with open(storage_path, "wb") as f:
            f.write(content)

        # 检测编码
        encoding, confidence = file_handler.detect_encoding(storage_path)

        # 创建数据库记录
        with get_db_session() as db:
            log_file = LogFile(
                id=uuid.UUID(file_id),
                filename=safe_name,
                file_size=len(content),
                encoding=encoding,
                storage_path=str(storage_path),
            )
            db.add(log_file)

        # 统计行数
        total_lines = file_handler.count_lines(storage_path, encoding)

        # 记录日志
        log_file_upload(safe_name, len(content), encoding, file_id)

        return make_response({
            "file_id": file_id,
            "filename": safe_name,
            "file_size": len(content),
            "encoding": encoding,
            "preview_lines": min(100, total_lines),
            "upload_id": file_id,
        })

    except Exception as e:
        logger.error(f"上传失败: {e}")
        log_error("INTERNAL_ERROR", str(e), {})
        return make_error("INTERNAL_ERROR", "文件上传失败", 500)


@router.get("/files/{file_id}")
async def get_file_preview(
    file_id: str,
    lines: int = Query(100, ge=1, le=10000),
):
    """获取文件预览"""
    try:
        with get_db_session() as db:
            log_file = db.query(LogFile).filter(LogFile.id == uuid.UUID(file_id)).first()

            if not log_file:
                return make_error("FILE_NOT_FOUND", "文件不存在", 404)

            storage_path = Path(log_file.storage_path)

            if not storage_path.exists():
                return make_error("FILE_NOT_FOUND", "文件不存在", 404)

            file_handler = get_file_handler()
            preview_lines = file_handler.read_lines(storage_path, log_file.encoding, 0, lines)
            total_lines = file_handler.count_lines(storage_path, log_file.encoding)

            return make_response({
                "file_id": file_id,
                "filename": log_file.filename,
                "total_lines": total_lines,
                "preview": preview_lines,
                "encoding": log_file.encoding,
            })

    except Exception as e:
        logger.error(f"获取预览失败: {e}")
        log_error("INTERNAL_ERROR", str(e), {})
        return make_error("INTERNAL_ERROR", "获取文件预览失败", 500)


@router.post("/validate/regex")
async def validate_regex(request: RegexValidationRequest):
    """校验正则表达式"""
    try:
        valid, error_msg = validate_regex_pattern(request.pattern)

        if not valid:
            return make_error("INVALID_REGEX", "正则表达式语法错误")

        return make_response({
            "valid": True,
            "sample_matches": 0,
        })

    except Exception as e:
        logger.error(f"正则校验失败: {e}")
        return make_error("INVALID_REGEX", "正则表达式校验失败")


@router.post("/split")
async def execute_split(request: SplitRequest):
    """执行切分"""
    try:
        # 验证正则表达式
        if request.rule_type == "regex":
            is_valid, _ = validate_regex_pattern(request.rule_content)
            if not is_valid:
                return make_error("INVALID_REGEX", "正则表达式语法错误")

        # 使用事务确保状态一致性
        with get_db_session() as db:
            # 检查文件是否存在
            log_file = db.query(LogFile).filter(LogFile.id == uuid.UUID(request.file_id)).first()

            if not log_file:
                return make_error("FILE_NOT_FOUND", "文件不存在", 404)

            # 检查是否有进行中的切分任务
            existing = db.query(SplitSession).filter(
                SplitSession.file_id == uuid.UUID(request.file_id),
                SplitSession.status.in_(["pending", "processing"])
            ).first()

            if existing:
                return make_error("SPLIT_IN_PROGRESS", "该文件已有切分任务进行中", 409)

            # 执行切分
            storage_path = Path(log_file.storage_path)
            splitter = LogSplitter(storage_path, log_file.encoding)

            # 根据规则类型执行切分
            if request.rule_type == "regex":
                chunks = list(splitter.split_by_regex(request.rule_content))
            else:
                delimiter = request.rule_content if request.rule_content else None
                chunks = list(splitter.split_by_fixed_string(delimiter))

            # 创建切分会话（状态为 processing）
            session = SplitSession(
                file_id=uuid.UUID(request.file_id),
                rule_type=request.rule_type,
                rule_content=request.rule_content,
                status="processing",
                total_chunks=len(chunks),
                processed_chunks=len(chunks),
            )
            db.add(session)
            db.flush()
            session_id = str(session.id)

            # 保存切分结果
            for chunk in chunks:
                result = SplitResult(
                    session_id=session.id,
                    chunk_index=chunk.chunk_index,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    content=chunk.content,
                )
                db.add(result)

            # 更新状态为已完成
            session.status = "completed"

            # 记录日志
            log_split_rule_applied(request.rule_type, request.rule_content, len(chunks), session_id)

            return make_response({
                "session_id": session_id,
                "status": "completed",
                "estimated_chunks": len(chunks),
            })

    except SQLAlchemyError as e:
        logger.error(f"数据库错误: {e}")
        log_error("INTERNAL_ERROR", str(e), {"file_id": request.file_id})
        return make_error("INTERNAL_ERROR", "数据库操作失败", 500)
    except Exception as e:
        logger.error(f"切分失败: {e}")
        log_error("INTERNAL_ERROR", str(e), {"file_id": request.file_id})
        return make_error("INTERNAL_ERROR", "切分执行失败", 500)


@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str):
    """获取切分状态"""
    try:
        with get_db_session() as db:
            session = db.query(SplitSession).filter(
                SplitSession.id == uuid.UUID(session_id)
            ).first()

            if not session:
                return make_error("SESSION_NOT_FOUND", "会话不存在", 404)

            total = session.total_chunks or 1
            processed = session.processed_chunks or 0
            progress = int(processed / total * 100) if total > 0 else 0

            return make_response({
                "session_id": session_id,
                "file_id": str(session.file_id),
                "status": session.status,
                "total_chunks": total,
                "processed_chunks": processed,
                "progress_percent": progress,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
            })

    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        return make_error("INTERNAL_ERROR", "获取会话状态失败", 500)


@router.get("/results/{session_id}")
async def get_split_results(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
):
    """获取切分结果（分页）"""
    try:
        with get_db_session() as db:
            session = db.query(SplitSession).filter(
                SplitSession.id == uuid.UUID(session_id)
            ).first()

            if not session:
                return make_error("SESSION_NOT_FOUND", "会话不存在", 404)

            # 查询结果总数
            total_chunks = db.query(SplitResult).filter(
                SplitResult.session_id == uuid.UUID(session_id)
            ).count()

            total_pages = (total_chunks + page_size - 1) // page_size

            # 分页查询
            offset = (page - 1) * page_size
            results = db.query(SplitResult).filter(
                SplitResult.session_id == uuid.UUID(session_id)
            ).order_by(SplitResult.chunk_index).offset(offset).limit(page_size).all()

            # 构建响应，包含 truncated 标志
            result_items = []
            for r in results:
                is_truncated = len(r.content) > MAX_CONTENT_PREVIEW
                result_items.append({
                    "chunk_index": r.chunk_index,
                    "start_line": r.start_line,
                    "end_line": r.end_line,
                    "content": r.content[:MAX_CONTENT_PREVIEW],
                    "truncated": is_truncated,
                })

            return make_response({
                "session_id": session_id,
                "status": session.status,
                "total_chunks": total_chunks,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "results": result_items,
            })

    except Exception as e:
        logger.error(f"获取结果失败: {e}")
        return make_error("INTERNAL_ERROR", "获取切分结果失败", 500)


@router.get("/results/{session_id}/chunks/{chunk_index}")
async def get_chunk_detail(session_id: str, chunk_index: int):
    """获取单个切分片段详情"""
    try:
        with get_db_session() as db:
            result = db.query(SplitResult).filter(
                SplitResult.session_id == uuid.UUID(session_id),
                SplitResult.chunk_index == chunk_index
            ).first()

            if not result:
                return make_error("CHUNK_NOT_FOUND", "片段不存在", 404)

            return make_response({
                "chunk_index": result.chunk_index,
                "start_line": result.start_line,
                "end_line": result.end_line,
                "content": result.content,
                "line_count": result.end_line - result.start_line + 1,
            })

    except Exception as e:
        logger.error(f"获取片段详情失败: {e}")
        return make_error("INTERNAL_ERROR", "获取片段详情失败", 500)


# ============ 002-short-name-structured 新增端点 ============


@router.post("/classify")
async def classify_logs_endpoint(request: ClassifyRequest):
    """日志分类与存储"""
    try:
        with get_db_session() as db:
            result = await classify_logs(
                db=db,
                logs=request.logs,
                mode=request.mode,
                file_id=request.file_id,
            )

            return make_response(result)

    except Exception as e:
        logger.error(f"分类失败: {e}")
        log_error("INTERNAL_ERROR", str(e), {"mode": request.mode})
        return make_error("INTERNAL_ERROR", "分类处理失败", 500)


@router.get("/logs")
async def get_logs_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    category: Optional[str] = None,
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """获取日志列表（分页）"""
    try:
        with get_db_session() as db:
            query = db.query(LogEntry)

            # 分类过滤
            if category:
                cat = db.query(LogCategory).filter(
                    LogCategory.name == category
                ).first()
                if cat:
                    query = query.filter(LogEntry.category_id == cat.id)

            # 级别过滤
            if level:
                query = query.filter(LogEntry.log_level == level.upper())

            # 关键词搜索
            if keyword:
                query = query.filter(
                    LogEntry.normalized_message.ilike(f"%{keyword}%")
                )

            # 日期范围过滤
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(LogEntry.created_at >= start_dt)

            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(LogEntry.created_at <= end_dt)

            # 总数
            total = query.count()

            # 分页
            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size

            entries = query.order_by(
                LogEntry.created_at.desc()
            ).offset(offset).limit(page_size).all()

            # 构建响应
            items = []
            for entry in entries:
                cat_name = None
                if entry.category:
                    cat_name = entry.category.name

                items.append({
                    "id": str(entry.id),
                    "normalized_message": entry.normalized_message,
                    "stack_trace": entry.stack_trace,
                    "category": cat_name,
                    "error_type": entry.error_type,
                    "log_level": entry.log_level,
                    "occurrence_count": entry.occurrence_count,
                    "first_seen_at": entry.first_seen_at.isoformat() if entry.first_seen_at else None,
                    "last_seen_at": entry.last_seen_at.isoformat() if entry.last_seen_at else None,
                })

            return make_response({
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "entries": items,
            })

    except Exception as e:
        logger.error(f"获取日志列表失败: {e}")
        return make_error("INTERNAL_ERROR", "获取日志列表失败", 500)


@router.get("/logs/{log_id}")
async def get_log_detail(log_id: str):
    """获取日志详情"""
    try:
        with get_db_session() as db:
            entry = db.query(LogEntry).filter(
                LogEntry.id == uuid.UUID(log_id)
            ).first()

            if not entry:
                return make_error("LOG_NOT_FOUND", "日志条目不存在", 404)

            cat_name = None
            if entry.category:
                cat_name = entry.category.name

            return make_response({
                "id": str(entry.id),
                "original_message": entry.original_message,
                "normalized_message": entry.normalized_message,
                "stack_trace": entry.stack_trace,
                "category": cat_name,
                "category_id": str(entry.category_id) if entry.category_id else None,
                "error_type": entry.error_type,
                "extracted_params": entry.extracted_params,
                "log_level": entry.log_level,
                "occurrence_count": entry.occurrence_count,
                "first_seen_at": entry.first_seen_at.isoformat() if entry.first_seen_at else None,
                "last_seen_at": entry.last_seen_at.isoformat() if entry.last_seen_at else None,
            })

    except Exception as e:
        logger.error(f"获取日志详情失败: {e}")
        return make_error("INTERNAL_ERROR", "获取日志详情失败", 500)


@router.get("/stats")
async def get_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """获取统计信息"""
    try:
        with get_db_session() as db:
            query = db.query(LogEntry)

            # 日期范围过滤
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(LogEntry.created_at >= start_dt)

            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(LogEntry.created_at <= end_dt)

            # 总条目数和唯一错误数
            total_entries = query.count()
            unique_errors = query.distinct(LogEntry.normalized_message).count()

            # 分类统计
            category_stats = db.query(
                LogCategory.name,
                func.count(LogEntry.id).label("count")
            ).join(
                LogEntry, LogEntry.category_id == LogCategory.id
            ).group_by(LogCategory.name).all()

            categories = []
            for name, count in category_stats:
                percentage = (count / total_entries * 100) if total_entries > 0 else 0
                categories.append({
                    "name": name,
                    "count": count,
                    "percentage": round(percentage, 2),
                })

            # 每日趋势（最近7天）
            daily_trend = []
            for i in range(7):
                day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                from datetime import timedelta
                day = day - timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")

                count = query.filter(
                    func.date(LogEntry.created_at) == day.date()
                ).count()

                daily_trend.append({
                    "date": day_str,
                    "count": count,
                })

            daily_trend.reverse()

            return make_response({
                "total_entries": total_entries,
                "unique_errors": unique_errors,
                "categories": categories,
                "daily_trend": daily_trend,
            })

    except Exception as e:
        logger.error(f"获取统计失败: {e}")
        return make_error("INTERNAL_ERROR", "获取统计信息失败", 500)


# ============ 规则管理端点 ============


@router.get("/rules")
async def get_rules():
    """获取解析规则列表"""
    try:
        with get_db_session() as db:
            rules = db.query(ParseRule).order_by(
                ParseRule.priority.desc()
            ).all()

            return make_response({
                "rules": [
                    {
                        "id": str(rule.id),
                        "name": rule.name,
                        "rule_type": rule.rule_type,
                        "pattern": rule.pattern,
                        "code": rule.code,
                        "priority": rule.priority,
                        "enabled": rule.enabled,
                        "is_system": rule.is_system,
                    }
                    for rule in rules
                ]
            })

    except Exception as e:
        logger.error(f"获取规则列表失败: {e}")
        return make_error("INTERNAL_ERROR", "获取规则列表失败", 500)


@router.post("/rules")
async def create_rule(request: CreateParseRuleRequest):
    """创建解析规则"""
    try:
        # 验证规则语法
        is_valid, error_msg = validate_rule_syntax(
            request.rule_type,
            request.pattern,
            request.code,
        )

        if not is_valid:
            return make_error("INVALID_RULE", error_msg)

        with get_db_session() as db:
            rule = ParseRule(
                name=request.name,
                rule_type=request.rule_type,
                pattern=request.pattern,
                code=request.code,
                group_index=request.group_index,
                priority=request.priority,
                enabled=request.enabled,
            )
            db.add(rule)
            db.flush()

            return make_response({
                "id": str(rule.id),
                "name": rule.name,
                "rule_type": rule.rule_type,
                "pattern": rule.pattern,
                "code": rule.code,
                "priority": rule.priority,
                "enabled": rule.enabled,
            })

    except Exception as e:
        logger.error(f"创建规则失败: {e}")
        return make_error("INTERNAL_ERROR", "创建规则失败", 500)


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, request: UpdateParseRuleRequest):
    """更新解析规则"""
    try:
        with get_db_session() as db:
            rule = db.query(ParseRule).filter(
                ParseRule.id == uuid.UUID(rule_id)
            ).first()

            if not rule:
                return make_error("RULE_NOT_FOUND", "规则不存在", 404)

            # 如果是系统规则，禁止修改
            if rule.is_system:
                return make_error("SYSTEM_RULE_CANNOT_MODIFY", "系统预置规则不可修改")

            # 更新字段
            if request.name is not None:
                rule.name = request.name
            if request.pattern is not None:
                rule.pattern = request.pattern
            if request.code is not None:
                rule.code = request.code
            if request.priority is not None:
                rule.priority = request.priority
            if request.enabled is not None:
                rule.enabled = request.enabled

            return make_response({
                "id": str(rule.id),
                "name": rule.name,
                "rule_type": rule.rule_type,
                "pattern": rule.pattern,
                "priority": rule.priority,
                "enabled": rule.enabled,
            })

    except Exception as e:
        logger.error(f"更新规则失败: {e}")
        return make_error("INTERNAL_ERROR", "更新规则失败", 500)


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """删除解析规则"""
    try:
        with get_db_session() as db:
            rule = db.query(ParseRule).filter(
                ParseRule.id == uuid.UUID(rule_id)
            ).first()

            if not rule:
                return make_error("RULE_NOT_FOUND", "规则不存在", 404)

            # 系统规则不可删除
            if rule.is_system:
                return make_error("SYSTEM_RULE_CANNOT_DELETE", "系统预置规则不可删除")

            db.delete(rule)

            return make_response(None)

    except Exception as e:
        logger.error(f"删除规则失败: {e}")
        return make_error("INTERNAL_ERROR", "删除规则失败", 500)


# ============ 忽略规则端点 ============


@router.get("/ignore-rules")
async def get_ignore_rules():
    """获取忽略规则列表"""
    try:
        with get_db_session() as db:
            rules = db.query(IgnoreRule).all()

            return make_response({
                "rules": [
                    {
                        "id": str(rule.id),
                        "name": rule.name,
                        "match_type": rule.match_type,
                        "pattern": rule.pattern,
                        "description": rule.description,
                        "enabled": rule.enabled,
                    }
                    for rule in rules
                ]
            })

    except Exception as e:
        logger.error(f"获取忽略规则列表失败: {e}")
        return make_error("INTERNAL_ERROR", "获取忽略规则列表失败", 500)


@router.post("/ignore-rules")
async def create_ignore_rule(request: CreateIgnoreRuleRequest):
    """创建忽略规则"""
    try:
        # 验证模式
        is_valid, error_msg = validate_ignore_pattern(
            request.match_type,
            request.pattern,
        )

        if not is_valid:
            return make_error("INVALID_RULE", error_msg)

        with get_db_session() as db:
            rule = IgnoreRule(
                name=request.name,
                match_type=request.match_type,
                pattern=request.pattern,
                description=request.description,
                enabled=request.enabled,
            )
            db.add(rule)
            db.flush()

            return make_response({
                "id": str(rule.id),
                "name": rule.name,
                "match_type": rule.match_type,
                "pattern": rule.pattern,
                "description": rule.description,
                "enabled": rule.enabled,
            })

    except Exception as e:
        logger.error(f"创建忽略规则失败: {e}")
        return make_error("INTERNAL_ERROR", "创建忽略规则失败", 500)


@router.delete("/ignore-rules/{rule_id}")
async def delete_ignore_rule(rule_id: str):
    """删除忽略规则"""
    try:
        with get_db_session() as db:
            rule = db.query(IgnoreRule).filter(
                IgnoreRule.id == uuid.UUID(rule_id)
            ).first()

            if not rule:
                return make_error("RULE_NOT_FOUND", "规则不存在", 404)

            db.delete(rule)

            return make_response(None)

    except Exception as e:
        logger.error(f"删除忽略规则失败: {e}")
        return make_error("INTERNAL_ERROR", "删除忽略规则失败", 500)
