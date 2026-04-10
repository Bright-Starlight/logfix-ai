"""
API 请求/响应模型定义

使用 Pydantic 定义 API 的请求和响应数据结构。
"""

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
    filename: str | None
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
