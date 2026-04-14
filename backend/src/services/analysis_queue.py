"""
分析任务队列

管理 AI 修复计划分析任务的排队和执行。
"""

import asyncio
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

from backend.src.services.log_service import get_logger


_logger = get_logger("analysis_queue")

# 队列最大长度：1个执行中 + 4个排队中
MAX_QUEUE_SIZE = 5


@dataclass
class AnalysisTask:
    """分析任务"""
    log_entry_id: int
    session_id: int
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    status: str = "pending"  # pending, queued, processing, completed, failed, cancelled


class AnalysisQueue:
    """
    分析任务队列管理器

    管理任务的入队、出队、执行状态。
    队列最大容量为 5 个任务（1执行中 + 4排队中）。
    """

    def __init__(self):
        self._queue: list[AnalysisTask] = []
        self._processing: Optional[AnalysisTask] = None
        self._lock = asyncio.Lock()
        self._process_callback: Optional[Callable[[int], Awaitable[None]]] = None

    def set_process_callback(self, callback: Callable[[int], Awaitable[None]]) -> None:
        """
        设置任务处理回调

        当有任务需要处理时，会调用此回调。
        回调函数接收 log_entry_id 参数。
        """
        self._process_callback = callback

    async def enqueue(self, log_entry_id: int, session_id: int) -> tuple[bool, str, Optional[int]]:
        """
        将任务加入队列

        Args:
            log_entry_id: 日志条目ID
            session_id: 分析会话ID

        Returns:
            (success, error_code, queue_position)
            - success: 是否入队成功
            - error_code: 错误码（如果失败）
            - queue_position: 队列位置（如果成功，1-based）
        """
        async with self._lock:
            # 检查队列是否已满
            if len(self._queue) >= MAX_QUEUE_SIZE:
                _logger.warning(f"队列已满，拒绝入队: log_entry_id={log_entry_id}")
                return False, "QUEUE_FULL", None

            # 检查是否已有相同 log_entry_id 的任务在队列中
            for task in self._queue:
                if task.log_entry_id == log_entry_id:
                    if task.status in ("pending", "queued", "processing"):
                        _logger.warning(f"任务已存在: log_entry_id={log_entry_id}")
                        return False, "TASK_EXISTS", None

            # 创建新任务
            task = AnalysisTask(log_entry_id=log_entry_id, session_id=session_id)
            self._queue.append(task)

            queue_position = len(self._queue)
            _logger.info(f"任务入队: log_entry_id={log_entry_id}, session_id={session_id}, queue_position={queue_position}")

            return True, "", queue_position

    async def dequeue(self) -> Optional[AnalysisTask]:
        """
        获取下一个待执行的任务

        Returns:
            下一个任务，如果没有待执行的任务则返回 None
        """
        async with self._lock:
            if not self._queue:
                return None

            # 按创建时间排序
            self._queue.sort(key=lambda t: t.created_at)

            # 找到第一个 pending 或 queued 状态的任务
            for task in self._queue:
                if task.status in ("pending", "queued"):
                    task.status = "processing"
                    task.started_at = datetime.now()
                    self._processing = task
                    _logger.info(f"任务开始执行: log_entry_id={task.log_entry_id}, session_id={task.session_id}")
                    return task

            return None

    async def start_next_if_idle(self) -> bool:
        """
        如果当前没有执行中的任务，则启动下一个任务

        Returns:
            是否启动了新任务
        """
        if self._processing is not None:
            return False

        task = await self.dequeue()
        if task and self._process_callback:
            await self._process_callback(task.log_entry_id)
            return True

        return False

    async def mark_completed(self, log_entry_id: int) -> None:
        """
        标记任务为完成

        Args:
            log_entry_id: 日志条目ID
        """
        async with self._lock:
            if self._processing and self._processing.log_entry_id == log_entry_id:
                self._processing.status = "completed"
                _logger.info(f"任务完成: log_entry_id={log_entry_id}")
                self._processing = None

                # 触发下一个任务
                asyncio.create_task(self.start_next_if_idle())

    async def mark_failed(self, log_entry_id: int, error_message: str) -> None:
        """
        标记任务为失败

        Args:
            log_entry_id: 日志条目ID
            error_message: 错误信息
        """
        async with self._lock:
            if self._processing and self._processing.log_entry_id == log_entry_id:
                self._processing.status = "failed"
                _logger.error(f"任务失败: log_entry_id={log_entry_id}, error={error_message}")
                self._processing = None

                # 触发下一个任务
                asyncio.create_task(self.start_next_if_idle())

    async def cancel(self, log_entry_id: int) -> bool:
        """
        取消任务

        Args:
            log_entry_id: 日志条目ID

        Returns:
            是否取消成功
        """
        async with self._lock:
            # 检查是否正在执行
            if self._processing and self._processing.log_entry_id == log_entry_id:
                self._processing.status = "cancelled"
                _logger.info(f"任务已取消（执行中）: log_entry_id={log_entry_id}")
                self._processing = None

                # 触发下一个任务
                asyncio.create_task(self.start_next_if_idle())
                return True

            # 检查队列中的任务
            for task in self._queue:
                if task.log_entry_id == log_entry_id and task.status in ("pending", "queued"):
                    task.status = "cancelled"
                    _logger.info(f"任务已取消（队列中）: log_entry_id={log_entry_id}")
                    return True

            return False

    def get_queue_status(self) -> dict:
        """
        获取队列状态

        Returns:
            队列状态字典
        """
        return {
            "queue_size": len(self._queue),
            "max_size": MAX_QUEUE_SIZE,
            "is_processing": self._processing is not None,
            "processing_log_entry_id": self._processing.log_entry_id if self._processing else None,
            "tasks": [
                {
                    "log_entry_id": task.log_entry_id,
                    "session_id": task.session_id,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                }
                for task in self._queue
            ],
        }

    def get_queue_position(self, log_entry_id: int) -> Optional[int]:
        """
        获取任务的队列位置

        Args:
            log_entry_id: 日志条目ID

        Returns:
            队列位置（1-based），如果不在队列中则返回 None
        """
        for i, task in enumerate(self._queue, 1):
            if task.log_entry_id == log_entry_id and task.status in ("pending", "queued"):
                return i
        return None


# 全局队列实例
_global_queue: Optional[AnalysisQueue] = None


def get_analysis_queue() -> AnalysisQueue:
    """获取全局分析队列实例"""
    global _global_queue
    if _global_queue is None:
        _global_queue = AnalysisQueue()
    return _global_queue
