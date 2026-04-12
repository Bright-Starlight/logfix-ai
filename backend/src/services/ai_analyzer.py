"""
AI分析服务

使用 OpenAI SDK 调用 MiniMax-M2.7 进行日志分析，支持 Tool Call 和流式输出。
"""

import json
import asyncio
import os
import time
from typing import Optional, AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageToolCall

from backend.src.services.log_service import get_logger


_logger = get_logger("ai_analyzer")

# 全局 OpenAI 客户端单例
_client: Optional[AsyncOpenAI] = None

# 并发控制信号量
_semaphore: Optional[asyncio.Semaphore] = None

# 默认配置
DEFAULT_MAX_CONCURRENT = 5
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 100  # 限制批次大小防止上下文溢出（每条日志产生2条消息：user + assistant）


def get_default_config() -> dict:
    """获取默认配置"""
    return {
        "max_concurrent": int(os.getenv("AI_MAX_CONCURRENT", DEFAULT_MAX_CONCURRENT)),
        "batch_size": int(os.getenv("AI_BATCH_SIZE", DEFAULT_BATCH_SIZE)),
    }


async def get_client() -> AsyncOpenAI:
    """
    获取全局 OpenAI 客户端单例

    Returns:
        AsyncOpenAI 客户端实例

    Raises:
        ValueError: 当 API 密钥未设置时
    """
    global _client

    if _client is None:
        api_key = os.getenv("MINIMAX_API_KEY")
        base_url = os.getenv("MINIMAX_API_HOST", "https://api.minimaxi.com/v1")

        if not api_key:
            raise ValueError("MINIMAX_API_KEY 环境变量未设置")

        _client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=600.0,
            max_retries=3,
        )
        _logger.info(f"OpenAI 客户端初始化完成, base_url={base_url}")

    return _client


async def init_client() -> AsyncOpenAI:
    """
    初始化 OpenAI 客户端（用于 lifespan 预加载）

    Returns:
        AsyncOpenAI 客户端实例
    """
    client = await get_client()
    _logger.info("模型预加载完成, model=MiniMax-M2.7")
    return client


async def close_client() -> None:
    """关闭 OpenAI 客户端"""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
        _logger.info("OpenAI 客户端已关闭")


def get_semaphore() -> asyncio.Semaphore:
    """获取并发控制信号量"""
    global _semaphore
    if _semaphore is None:
        config = get_default_config()
        _semaphore = asyncio.Semaphore(config["max_concurrent"])
        _logger.info(f"并发控制信号量初始化完成, max_concurrent={config['max_concurrent']}")
    return _semaphore


# Tool Call Schema
CLASSIFY_LOG_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "classify_log",
        "description": "对单条日志进行结构化分类，返回分类结果",
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "日志在列表中的索引",
                },
                "category": {
                    "type": "string",
                    "description": "分类名称（如：异常错误、警告、信息、调试）",
                },
                "error_type": {
                    "type": ["string", "null"],
                    "description": "错误类型（如：NullPointerException、TimeoutException）",
                },
                "normalized_message": {
                    "type": "string",
                    "description": "归一化消息（数字等参数应被替换为 *）",
                },
                "extracted_params": {
                    "type": "object",
                    "description": "从日志中提取的参数字典",
                    "additionalProperties": True,
                },
            },
            "required": ["index", "category", "normalized_message", "extracted_params"],
            "additionalProperties": False,
        },
    },
}


@dataclass
class ClassificationResult:
    """分类结果数据结构"""
    index: int
    category: str
    error_type: Optional[str]
    normalized_message: str
    extracted_params: dict


def parse_tool_call_response(tool_calls: list[ChatCompletionMessageToolCall]) -> Optional[ClassificationResult]:
    """
    解析 Tool Call 响应

    Args:
        tool_calls: OpenAI 返回的 tool_calls 列表

    Returns:
        ClassificationResult 或 None（解析失败时）
    """
    if not tool_calls:
        return None

    try:
        tool_call = tool_calls[0]
        return parse_tool_call_arguments(tool_call.function.arguments)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        _logger.error(f"Tool Call 响应解析失败: {e}")
        return None


def parse_tool_call_arguments(arguments_text: str) -> Optional[ClassificationResult]:
    """
    解析 tool_call 的 arguments JSON 字符串

    Args:
        arguments_text: tool_call.function.arguments

    Returns:
        ClassificationResult 或 None（解析失败时）
    """
    try:
        arguments = json.loads(arguments_text)
        return ClassificationResult(
            index=arguments.get("index", 0),
            category=arguments.get("category", "未知"),
            error_type=arguments.get("error_type"),
            normalized_message=arguments.get("normalized_message", ""),
            extracted_params=arguments.get("extracted_params", {}),
        )
    except (json.JSONDecodeError, TypeError) as e:
        _logger.error(f"tool_call arguments 解析失败: {e}")
        return None


async def stream_analyze_logs(
    log_entries: list[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> AsyncIterator[dict]:
    """
    流式分析日志条目，通过 SSE 推送进度和结果

    Args:
        log_entries: 日志条目列表
        batch_size: 每批处理的条目数（自动限制到 MAX_BATCH_SIZE）

    Yields:
        SSE 事件字典，包含 event 和 data 字段
    """
    client = await get_client()
    semaphore = get_semaphore()
    total = len(log_entries)
    processed = 0
    success_count = 0
    error_count = 0

    # 限制批次大小防止上下文溢出
    effective_batch_size = min(batch_size, MAX_BATCH_SIZE)
    if batch_size > MAX_BATCH_SIZE:
        _logger.warning(f"batch_size={batch_size} 超过限制，已限制为 {MAX_BATCH_SIZE}")

    _logger.info(f"开始流式分析, total={total}, batch_size={batch_size}")

    # 构建系统提示词
    system_prompt = """你是一个日志分析助手。请分析每条日志，进行结构化分类。

对于每条日志，你需要调用 classify_log 工具返回以下信息：
- category: 分类名称（如：异常错误、警告、信息、调试）
- error_type: 错误类型（如：NullPointerException、TimeoutException）
- normalized_message: 归一化消息（去除具体参数，保留错误模式）
- extracted_params: 提取的参数字典

注意：
1. 相同错误消息（仅参数不同）应归为同一组
2. normalized_message 应去除参数，数字用 * 代替
3. extracted_params 应提取所有参数"""

    async def process_batch(batch_start_index: int, batch_num: int, total_batches: int) -> list[dict]:
        batch = log_entries[batch_start_index:batch_start_index + effective_batch_size]
        batch_payload = [
            {"index": batch_start_index + idx, "log_entry": log_entry}
            for idx, log_entry in enumerate(batch)
        ]

        _logger.debug(f"处理批次 {batch_num}/{total_batches}, size={len(batch)}")

        async with semaphore:
            batch_start = time.perf_counter()
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "请分析以下日志数组，并对每条日志各调用一次 classify_log。\n"
                            "输入 JSON:\n"
                            f"{json.dumps(batch_payload, ensure_ascii=False)}"
                        ),
                    },
                ]

                _logger.info(f"批次 {batch_num}/{total_batches} 调用AI开始, size={len(batch_payload)}")
                response = await client.chat.completions.create(
                    model="MiniMax-M2.7",
                    messages=messages,
                    tools=[CLASSIFY_LOG_TOOL_SCHEMA],
                    stream=False,
                    temperature=0.3,
                    tool_choice="required",
                )
                request_elapsed_ms = int((time.perf_counter() - batch_start) * 1000)
                usage = getattr(response, "usage", None)
                _logger.info(
                    f"批次 {batch_num}/{total_batches} 调用AI结束, "
                    f"size={len(batch_payload)}, elapsed_ms={request_elapsed_ms}, "
                    f"prompt_tokens={getattr(usage, 'prompt_tokens', None)}, "
                    f"completion_tokens={getattr(usage, 'completion_tokens', None)}, "
                    f"total_tokens={getattr(usage, 'total_tokens', None)}"
                )

                if not response.choices:
                    raise ValueError(f"批次 {batch_num} 响应为空")

                message = response.choices[0].message
                tool_calls = message.tool_calls or []
                if not tool_calls:
                    raise ValueError(f"批次 {batch_num} 未返回 tool_calls")

                results_by_index: dict[int, ClassificationResult] = {}
                batch_events: list[dict] = []
                parse_fail_count = 0
                unexpected_tool_names: list[str] = []
                for tc in tool_calls:
                    if not tc.function:
                        continue
                    if tc.function.name != "classify_log":
                        unexpected_tool_names.append(tc.function.name or "unknown")
                        _logger.warning(
                            f"批次 {batch_num} 收到非预期工具调用: {tc.function.name}"
                        )
                        continue

                    result = parse_tool_call_arguments(tc.function.arguments)
                    if not result:
                        parse_fail_count += 1
                        _logger.warning(
                            f"批次 {batch_num} tool_call解析失败: tool_call_id={tc.id}, "
                            f"arguments_preview={str(tc.function.arguments)[:200]}"
                        )
                        continue
                    results_by_index[result.index] = result

                expected_indices = [item["index"] for item in batch_payload]
                missing_indices = [idx for idx in expected_indices if idx not in results_by_index]
                if missing_indices:
                    _logger.warning(
                        f"批次 {batch_num}/{total_batches} 存在未命中: "
                        f"expected={len(expected_indices)}, tool_calls={len(tool_calls)}, "
                        f"parsed={len(results_by_index)}, parse_fail={parse_fail_count}, "
                        f"unexpected_tool_calls={len(unexpected_tool_names)}, "
                        f"missing={len(missing_indices)}, missing_indices_preview={missing_indices[:20]}"
                    )

                for item in batch_payload:
                    actual_idx = item["index"]
                    result = results_by_index.get(actual_idx)
                    if not result:
                        batch_events.append({
                            "event": "error",
                            "data": {
                                "code": "ITEM_ERROR",
                                "message": "该日志未返回有效分类结果",
                                "index": actual_idx,
                            },
                        })
                        continue

                    batch_events.append({
                        "event": "result",
                        "data": {
                            "index": result.index,
                            "category": result.category,
                            "error_type": result.error_type,
                            "normalized_message": result.normalized_message,
                            "extracted_params": result.extracted_params,
                        },
                    })

                total_elapsed_ms = int((time.perf_counter() - batch_start) * 1000)
                batch_success = len(results_by_index)
                batch_error = len(batch_payload) - batch_success
                _logger.info(
                    f"批次 {batch_num}/{total_batches} 批次处理完成, "
                    f"size={len(batch_payload)}, tool_calls={len(tool_calls)}, "
                    f"parsed={len(results_by_index)}, parse_fail={parse_fail_count}, "
                    f"success={batch_success}, error={batch_error}, elapsed_ms={total_elapsed_ms}"
                )
                return batch_events

            except Exception as e:
                total_elapsed_ms = int((time.perf_counter() - batch_start) * 1000)
                _logger.error(
                    f"批次 {batch_num}/{total_batches} 调用AI失败, "
                    f"size={len(batch_payload)}, elapsed_ms={total_elapsed_ms}, error={e}"
                )
                return [
                    {
                        "event": "error",
                        "data": {
                            "code": "BATCH_ERROR",
                            "message": str(e),
                            "index": item["index"],
                        },
                    }
                    for item in batch_payload
                ]

    total_batches = (total + effective_batch_size - 1) // effective_batch_size if total > 0 else 0
    batch_tasks = [
        asyncio.create_task(
            process_batch(batch_start_index=i, batch_num=i // effective_batch_size + 1, total_batches=total_batches)
        )
        for i in range(0, total, effective_batch_size)
    ]

    for batch_future in asyncio.as_completed(batch_tasks):
        batch_events = await batch_future
        for event in batch_events:
            if event["event"] == "result":
                processed += 1
                success_count += 1
                yield event
                percentage = int(processed / total * 100) if total > 0 else 0
                yield {
                    "event": "progress",
                    "data": {
                        "processed": processed,
                        "total": total,
                        "percentage": percentage,
                    },
                }
            else:
                error_count += 1
                yield event

    # 推送完成事件
    _logger.info(f"流式分析完成, processed={processed}, success={success_count}, error={error_count}")
    yield {
        "event": "done",
        "data": {
            "total_processed": processed,
            "success_count": success_count,
            "error_count": error_count,
        },
    }


async def analyze_logs_ai(
    log_entries: list[str],
    batch_size: Optional[int] = None,
) -> tuple[Optional[list[ClassificationResult]], Optional[str]]:
    """
    使用 AI 分析日志（非流式版本，用于兼容现有代码）

    Args:
        log_entries: 日志条目列表
        batch_size: 每批处理的条目数

    Returns:
        (results, error_message)
    """
    if batch_size is None:
        config = get_default_config()
        batch_size = config["batch_size"]

    results: list[ClassificationResult] = []
    error_message: Optional[str] = None

    try:
        async for event in stream_analyze_logs(log_entries, batch_size):
            if event["event"] == "result":
                data = event["data"]
                results.append(ClassificationResult(
                    index=data["index"],
                    category=data["category"],
                    error_type=data["error_type"],
                    normalized_message=data["normalized_message"],
                    extracted_params=data["extracted_params"],
                ))
            elif event["event"] == "error":
                error_message = event["data"]["message"]
            elif event["event"] == "done":
                if event["data"]["error_count"] > 0:
                    error_message = f"部分处理失败，error_count={event['data']['error_count']}"

    except Exception as e:
        _logger.error(f"AI 分析失败: {e}")
        return None, str(e)

    if not results and error_message:
        return None, error_message

    return results, None


def classify_with_ai_result(
    log_entry: str,
    classification: dict | ClassificationResult,
) -> tuple[str, Optional[str], dict]:
    """
    根据 AI 分类结果处理单条日志

    Args:
        log_entry: 原始日志条目
        classification: AI 返回的分类字典或 ClassificationResult

    Returns:
        (category, error_type, extracted_params)
    """
    if isinstance(classification, ClassificationResult):
        return (
            classification.category,
            classification.error_type,
            classification.extracted_params,
        )

    category = classification.get("category", "异常错误")
    error_type = classification.get("error_type")
    extracted_params = classification.get("extracted_params", {})

    return category, error_type, extracted_params
