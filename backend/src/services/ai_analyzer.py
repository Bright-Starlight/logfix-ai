"""
AI分析服务

使用 LangChain + Anthropic SDK 调用 MiniMax-M2.7 进行日志分析。
"""

import json
from typing import Optional

from backend.src.services.log_service import get_logger


_logger = get_logger("ai_analyzer")


def get_anthropic_client():
    """获取 Anthropic 客户端"""
    import os
    from anthropic import Anthropic

    api_key = os.getenv("MINIMAX_API_KEY")
    base_url = os.getenv("MINIMAX_API_HOST", "https://api.minimaxi.com/anthropic")

    if not api_key:
        raise ValueError("MINIMAX_API_KEY 环境变量未设置")

    return Anthropic(
        api_key=api_key,
        base_url=base_url,
    )


def build_analysis_prompt(log_entries: list[str]) -> str:
    """
    构建分析 Prompt

    Args:
        log_entries: 日志条目列表

    Returns:
        格式化的 prompt 字符串
    """
    logs_text = "\n".join([f"{i}. {log}" for i, log in enumerate(log_entries)])

    prompt = f"""你是一个日志分析助手。请分析以下日志条目，进行分类和去重。

日志条目：
{logs_text}

请以 JSON 格式输出分析结果：
{{
  "classifications": [
    {{
      "original_index": 0,
      "category": "异常错误",
      "error_type": "NullPointerException",
      "normalized_message": "Null pointer at line *",
      "extracted_params": {{"line": "10"}}
    }}
  ],
  "duplicates": [
    {{
      "representative_index": 0,
      "duplicate_indices": [3, 7]
    }}
  ]
}}

注意：
1. 相同错误消息（仅参数不同）应归为同一组
2. normalized_message 应去除参数，保留错误模式（数字用*代替）
3. extracted_params 应提取所有参数
4. 如果日志无法分类，请返回 null

请直接输出 JSON，不要有其他内容。"""

    return prompt


def parse_ai_response(response_text: str) -> tuple[Optional[list], Optional[list]]:
    """
    解析 AI 响应

    Args:
        response_text: AI 返回的原始文本

    Returns:
        (classifications, duplicates)
    """
    try:
        # 尝试提取 JSON
        # 去除 markdown 代码块标记
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        data = json.loads(text)

        classifications = data.get("classifications", [])
        duplicates = data.get("duplicates", [])

        return classifications, duplicates

    except json.JSONDecodeError as e:
        _logger.error(f"JSON 解析失败: {e}")
        return None, None


async def analyze_logs_ai(log_entries: list[str]) -> tuple[Optional[list], Optional[list], Optional[str]]:
    """
    使用 AI 分析日志

    Args:
        log_entries: 日志条目列表

    Returns:
        (classifications, duplicates, error_message)
    """
    _logger = get_logger("ai_analyzer").bind(entry_count=len(log_entries))

    try:
        client = get_anthropic_client()
        prompt = build_analysis_prompt(log_entries)

        _logger.info("调用 MiniMax API...")

        response = client.messages.create(
            model="MiniMax-M2.7",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = response.content[0].text
        _logger.debug(f"AI 响应: {response_text[:200]}...")

        classifications, duplicates = parse_ai_response(response_text)

        if classifications is None:
            return None, None, "AI 响应解析失败"

        _logger.info(f"AI 分析完成: {len(classifications)} 条分类")

        return classifications, duplicates, None

    except ValueError as e:
        _logger.error(f"配置错误: {e}")
        return None, None, str(e)
    except Exception as e:
        _logger.error(f"AI 分析失败: {e}")
        return None, None, f"AI 服务调用失败: {str(e)}"


def classify_with_ai_result(
    log_entry: str,
    classification: dict
) -> tuple[str, Optional[str], dict]:
    """
    根据 AI 分类结果处理单条日志

    Args:
        log_entry: 原始日志条目
        classification: AI 返回的分类字典

    Returns:
        (category, error_type, extracted_params)
    """
    category = classification.get("category", "异常错误")
    error_type = classification.get("error_type")
    extracted_params = classification.get("extracted_params", {})

    return category, error_type, extracted_params
