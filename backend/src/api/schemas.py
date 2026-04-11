"""
API 请求/响应模型定义

使用 Pydantic 定义 API 的请求和响应数据结构。
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class RegexValidationRequest(BaseModel):
    """正则表达式校验请求"""
    pattern: str


class RegexValidationResponse(BaseModel):
    """正则表达式校验响应"""
    valid: bool
    sample_matches: int = Field(default=0, description="估算匹配数量")


class SplitRequest(BaseModel):
    """执行切分请求"""
    file_id: str
    rule_type: str = Field(pattern="^(regex|fixed_string)$")
    rule_content: str


class SplitResponse(BaseModel):
    """执行切分响应"""
    session_id: str
    status: str
    estimated_chunks: int


class SessionStatusResponse(BaseModel):
    """会话状态响应"""
    session_id: str
    file_id: str
    status: str
    total_chunks: int
    processed_chunks: int
    progress_percent: int
    created_at: str
    updated_at: str


class ChunkResult(BaseModel):
    """切分片段结果"""
    chunk_index: int
    start_line: int
    end_line: int
    content: str
    truncated: bool = Field(default=False, description="内容是否被截断")


class ResultsResponse(BaseModel):
    """切分结果列表响应"""
    session_id: str
    status: str
    total_chunks: int
    page: int
    page_size: int
    total_pages: int
    results: list[ChunkResult]


class ChunkDetailResponse(BaseModel):
    """单个片段详情响应"""
    chunk_index: int
    start_line: int
    end_line: int
    content: str
    line_count: int


class UploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: Optional[str]
    file_size: int
    encoding: str
    preview_lines: int
    upload_id: str


class FilePreviewResponse(BaseModel):
    """文件预览响应"""
    file_id: str
    filename: str
    total_lines: int
    preview: list[str]
    encoding: str


# ============ 002-short-name-structured 新增 Schema ============


class ClassifyRequest(BaseModel):
    """日志分类请求"""
    logs: list[str] = Field(..., description="日志条目列表")
    mode: str = Field(..., pattern="^(rule_engine|ai)$", description="处理模式: rule_engine 或 ai")
    file_id: Optional[str] = Field(None, description="来源文件ID（用于关联）")


class LogEntryResponse(BaseModel):
    """日志条目响应"""
    id: str
    original_message: Optional[str] = None
    normalized_message: str
    stack_trace: Optional[str] = None
    category: Optional[str] = None
    error_type: Optional[str] = None
    extracted_params: Optional[dict] = None
    log_level: Optional[str] = None
    occurrence_count: int = 1
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class ClassifyResponse(BaseModel):
    """日志分类响应"""
    processed: int
    new_entries: int
    duplicates: int
    entries: list[LogEntryResponse]


class LogListItemResponse(BaseModel):
    """日志列表项响应"""
    id: str
    normalized_message: str
    stack_trace: Optional[str] = None
    category: Optional[str] = None
    error_type: Optional[str] = None
    log_level: Optional[str] = None
    occurrence_count: int = 1
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class LogListResponse(BaseModel):
    """日志列表响应"""
    total: int
    page: int
    page_size: int
    total_pages: int
    entries: list[LogListItemResponse]


class LogDetailResponse(BaseModel):
    """日志详情响应"""
    id: str
    original_message: Optional[str] = None
    normalized_message: str
    stack_trace: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    error_type: Optional[str] = None
    extracted_params: Optional[dict] = None
    log_level: Optional[str] = None
    occurrence_count: int = 1
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class CategoryStatsResponse(BaseModel):
    """分类统计响应"""
    name: str
    count: int
    percentage: float


class DailyTrendResponse(BaseModel):
    """每日趋势响应"""
    date: str
    count: int


class StatsResponse(BaseModel):
    """统计信息响应"""
    total_entries: int
    unique_errors: int
    categories: list[CategoryStatsResponse]
    daily_trend: list[DailyTrendResponse]


class ParseRuleResponse(BaseModel):
    """解析规则响应"""
    id: str
    name: str
    rule_type: str
    pattern: Optional[str] = None
    code: Optional[str] = None
    priority: int = 0
    enabled: bool = True
    is_system: bool = False


class ParseRuleListResponse(BaseModel):
    """解析规则列表响应"""
    rules: list[ParseRuleResponse]


class CreateParseRuleRequest(BaseModel):
    """创建解析规则请求"""
    name: str
    rule_type: str = Field(..., pattern="^(regex|code)$")
    pattern: Optional[str] = None
    code: Optional[str] = None
    group_index: int = 0
    priority: int = 0
    enabled: bool = True


class UpdateParseRuleRequest(BaseModel):
    """更新解析规则请求"""
    name: Optional[str] = None
    pattern: Optional[str] = None
    code: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class IgnoreRuleResponse(BaseModel):
    """忽略规则响应"""
    id: str
    name: str
    match_type: str
    pattern: str
    description: Optional[str] = None
    enabled: bool = True


class IgnoreRuleListResponse(BaseModel):
    """忽略规则列表响应"""
    rules: list[IgnoreRuleResponse]


class CreateIgnoreRuleRequest(BaseModel):
    """创建忽略规则请求"""
    name: str
    match_type: str = Field(..., pattern="^(contains|regex|exact)$")
    pattern: str
    description: Optional[str] = None
    enabled: bool = True
