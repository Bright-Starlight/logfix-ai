"""
修复计划服务

生成错误日志的 AI 修复计划。
"""

import json
import os
import time
from typing import Optional, AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI

from backend.src.services.log_service import get_logger


_logger = get_logger("fix_plan_service")


# Tool Call Schema for fix plan generation
GENERATE_FIX_PLAN_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_fix_plan",
        "description": "生成错误日志的修复计划",
        "parameters": {
            "type": "object",
            "properties": {
                "root_cause": {
                    "type": "string",
                    "description": "问题根因分析",
                },
                "fix_steps": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "修复步骤建议列表",
                },
                "code_locations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "相关代码文件路径",
                            },
                            "line_range": {
                                "type": "string",
                                "description": "相关代码行号范围",
                            },
                            "description": {
                                "type": "string",
                                "description": "代码位置说明",
                            },
                        },
                        "required": ["file_path"],
                    },
                    "description": "相关代码位置列表",
                },
                "confidence": {
                    "type": "number",
                    "description": "置信度 0-1",
                },
                "impact_assessment": {
                    "type": "string",
                    "description": "影响范围评估",
                },
            },
            "required": ["root_cause", "fix_steps", "code_locations", "confidence", "impact_assessment"],
            "additionalProperties": False,
        },
    },
}


@dataclass
class FixPlanResult:
    """修复计划结果"""
    root_cause: str
    fix_steps: list[str]
    code_locations: list[dict]
    confidence: float
    impact_assessment: str


async def get_client() -> AsyncOpenAI:
    """获取 OpenAI 客户端"""
    from backend.src.services.ai_analyzer import get_client as get_ai_client
    return await get_ai_client()


async def generate_fix_plan(
    log_entry_id: int,
    error_message: str,
    stack_trace: Optional[str],
    repo_path: Optional[str] = None,
) -> AsyncIterator[dict]:
    """
    生成修复计划的流式方法

    Args:
        log_entry_id: 日志条目ID
        error_message: 错误消息
        stack_trace: 堆栈跟踪（可选）
        repo_path: 代码仓库路径（可选）

    Yields:
        SSE 事件字典
    """
    client = await get_client()
    start_time = time.perf_counter()

    # 构建系统提示词
    system_prompt = """你是一个代码错误修复助手。根据提供的错误日志信息，分析问题根因并生成修复计划。

请调用 generate_fix_plan 工具返回以下信息：
- root_cause: 问题根因分析
- fix_steps: 修复步骤建议列表
- code_locations: 相关代码位置列表（包含文件路径、行号范围、说明）
- confidence: 置信度 0-1
- impact_assessment: 影响范围评估

注意：
1. 如果提供了 stack_trace，优先分析堆栈跟踪定位问题
2. 如果提供了 repo_path，应尝试分析相关代码文件
3. fix_steps 应该具体且可操作
4. code_locations 应尽可能精确"""

    # 构建用户消息
    user_content = f"错误消息：{error_message}\n\n"
    if stack_trace:
        user_content += f"堆栈跟踪：\n{stack_trace}\n\n"
    if repo_path:
        user_content += f"代码仓库路径：{repo_path}\n\n"
    user_content += "请分析以上信息，生成修复计划。"

    _logger.info(f"开始生成修复计划: log_entry_id={log_entry_id}")

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        response = await client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=messages,
            tools=[GENERATE_FIX_PLAN_TOOL_SCHEMA],
            stream=False,
            temperature=0.3,
            tool_choice="required",
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        usage = getattr(response, "usage", None)
        _logger.info(
            f"修复计划生成完成: log_entry_id={log_entry_id}, elapsed_ms={elapsed_ms}, "
            f"prompt_tokens={getattr(usage, 'prompt_tokens', None)}, "
            f"completion_tokens={getattr(usage, 'completion_tokens', None)}, "
            f"total_tokens={getattr(usage, 'total_tokens', None)}"
        )

        if not response.choices:
            raise ValueError("响应为空")

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            raise ValueError("未返回 tool_calls")

        # 解析第一个 tool_call
        tool_call = tool_calls[0]
        if tool_call.function.name != "generate_fix_plan":
            raise ValueError(f"收到非预期工具调用: {tool_call.function.name}")

        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            _logger.error(f"tool_call arguments 解析失败: {e}")
            raise ValueError(f"tool_call arguments 解析失败: {e}")

        result = FixPlanResult(
            root_cause=arguments.get("root_cause", "无法分析根因"),
            fix_steps=arguments.get("fix_steps", []),
            code_locations=arguments.get("code_locations", []),
            confidence=arguments.get("confidence", 0.0),
            impact_assessment=arguments.get("impact_assessment", "无法评估"),
        )

        yield {
            "event": "result",
            "data": {
                "log_entry_id": log_entry_id,
                "root_cause": result.root_cause,
                "fix_steps": result.fix_steps,
                "code_locations": result.code_locations,
                "confidence": result.confidence,
                "impact_assessment": result.impact_assessment,
            },
        }

    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        _logger.error(f"修复计划生成失败: log_entry_id={log_entry_id}, elapsed_ms={elapsed_ms}, error={e}")
        yield {
            "event": "error",
            "data": {
                "log_entry_id": log_entry_id,
                "code": "FIX_PLAN_GENERATION_FAILED",
                "message": str(e),
            },
        }


async def get_fix_plan_sync(
    log_entry_id: int,
    error_message: str,
    stack_trace: Optional[str],
    repo_path: Optional[str] = None,
) -> tuple[Optional[FixPlanResult], Optional[str]]:
    """
    同步获取修复计划

    Returns:
        (FixPlanResult, error_message)
    """
    result = None
    error_message = None

    async for event in generate_fix_plan(log_entry_id, error_message, stack_trace, repo_path):
        if event["event"] == "result":
            data = event["data"]
            result = FixPlanResult(
                root_cause=data["root_cause"],
                fix_steps=data["fix_steps"],
                code_locations=data["code_locations"],
                confidence=data["confidence"],
                impact_assessment=data["impact_assessment"],
            )
        elif event["event"] == "error":
            error_message = event["data"]["message"]

    return result, error_message
