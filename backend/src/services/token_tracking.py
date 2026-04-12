"""
Token 消耗追踪服务

记录 AI API 调用的 token 消耗，支持 tool_call 和 prompt_engineering 两种方式对比。
"""

import time
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager

from sqlalchemy.orm import Session

from backend.src.models.entities import TokenUsage
from backend.src.services.log_service import get_logger


_logger = get_logger("token_tracking")


@dataclass
class TokenMetrics:
    """Token 指标数据"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    processing_time_ms: int


class TokenTracker:
    """Token 消耗追踪器"""

    def __init__(self, db: Session, user_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        初始化 Token 追踪器

        Args:
            db: 数据库会话
            user_id: 用户标识
            session_id: 分类会话 ID
        """
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self._start_time: Optional[float] = None

    def start(self) -> None:
        """开始计时"""
        self._start_time = time.time()

    def stop(self) -> int:
        """停止计时并返回处理耗时（毫秒）"""
        if self._start_time is None:
            return 0
        elapsed = time.time() - self._start_time
        return int(elapsed * 1000)

    def record(
        self,
        method: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        batch_size: Optional[int] = None,
        batch_index: Optional[int] = None,
    ) -> TokenUsage:
        """
        记录一次 token 消耗

        Args:
            method: 调用方式 (tool_call / prompt_engineering)
            model: 模型名称
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            batch_size: 批次大小
            batch_index: 批次索引

        Returns:
            创建的 TokenUsage 记录
        """
        total_tokens = input_tokens + output_tokens
        processing_time = self.stop()

        token_usage = TokenUsage(
            user_id=self.user_id,
            session_id=int(self.session_id) if self.session_id else None,
            method=method,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            model=model,
            batch_size=batch_size,
            batch_index=batch_index,
            processing_time_ms=processing_time,
        )

        self.db.add(token_usage)
        self.db.flush()

        _logger.debug(
            f"Token 消耗记录: method={method}, model={model}, "
            f"input={input_tokens}, output={output_tokens}, total={total_tokens}, "
            f"processing_time={processing_time}ms"
        )

        return token_usage

    @contextmanager
    def measure(self, method: str, model: str, batch_size: Optional[int] = None, batch_index: Optional[int] = None):
        """
        上下文管理器，用于测量和记录 token 消耗

        Args:
            method: 调用方式
            model: 模型名称
            batch_size: 批次大小
            batch_index: 批次索引

        Usage:
            with tracker.measure("tool_call", "MiniMax-M2.7") as metrics:
                # 调用 AI
                metrics.input_tokens = 100
                metrics.output_tokens = 50
        """
        self.start()

        class MetricsContext:
            def __init__(self):
                self.input_tokens = 0
                self.output_tokens = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        metrics = MetricsContext()
        try:
            yield metrics
        finally:
            self.record(
                method=method,
                model=model,
                input_tokens=metrics.input_tokens,
                output_tokens=metrics.output_tokens,
                batch_size=batch_size,
                batch_index=batch_index,
            )


def get_token_comparison(
    db: Session,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """
    获取 token 消耗对比数据

    Args:
        db: 数据库会话
        session_id: 可选的会话 ID 过滤
        user_id: 可选的用户 ID 过滤

    Returns:
        包含 tool_call 和 prompt_engineering 各自消耗的字典
    """
    query = db.query(TokenUsage)

    if session_id:
        query = query.filter(TokenUsage.session_id == int(session_id))
    if user_id:
        query = query.filter(TokenUsage.user_id == user_id)

    all_usage = query.all()

    tool_call_stats = {
        "count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "avg_processing_time_ms": 0,
    }

    prompt_stats = {
        "count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "avg_processing_time_ms": 0,
    }

    total_processing_time_tool = 0
    total_processing_time_prompt = 0

    for usage in all_usage:
        if usage.method == "tool_call":
            tool_call_stats["count"] += 1
            tool_call_stats["input_tokens"] += usage.input_tokens
            tool_call_stats["output_tokens"] += usage.output_tokens
            tool_call_stats["total_tokens"] += usage.total_tokens
            if usage.processing_time_ms:
                total_processing_time_tool += usage.processing_time_ms
        else:
            prompt_stats["count"] += 1
            prompt_stats["input_tokens"] += usage.input_tokens
            prompt_stats["output_tokens"] += usage.output_tokens
            prompt_stats["total_tokens"] += usage.total_tokens
            if usage.processing_time_ms:
                total_processing_time_prompt += usage.processing_time_ms

    # 计算平均处理时间
    if tool_call_stats["count"] > 0:
        tool_call_stats["avg_processing_time_ms"] = total_processing_time_tool // tool_call_stats["count"]
    if prompt_stats["count"] > 0:
        prompt_stats["avg_processing_time_ms"] = total_processing_time_prompt // prompt_stats["count"]

    return {
        "tool_call": tool_call_stats,
        "prompt_engineering": prompt_stats,
    }
