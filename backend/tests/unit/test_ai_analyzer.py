"""
AI Analyzer 单元测试

测试 OpenAI SDK Tool Call 解析逻辑。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from backend.src.services.ai_analyzer import (
    parse_tool_call_response,
    parse_tool_call_arguments,
    ClassificationResult,
    CLASSIFY_LOG_TOOL_SCHEMA,
    get_semaphore,
    get_default_config,
)


class TestToolCallParsing:
    """Tool Call 解析测试"""

    def test_parse_tool_call_response_valid(self):
        """测试有效 Tool Call 响应解析"""
        # 模拟 OpenAI 的 tool_call 格式
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "classify_log"
        mock_tool_call.function.arguments = json.dumps({
            "index": 0,
            "category": "异常错误",
            "error_type": "NullPointerException",
            "normalized_message": "Null pointer at *",
            "extracted_params": {"line": "10"},
        })

        result = parse_tool_call_response([mock_tool_call])

        assert result is not None
        assert isinstance(result, ClassificationResult)
        assert result.index == 0
        assert result.category == "异常错误"
        assert result.error_type == "NullPointerException"
        assert result.normalized_message == "Null pointer at *"
        assert result.extracted_params == {"line": "10"}

    def test_parse_tool_call_response_empty(self):
        """测试空 Tool Call 列表"""
        result = parse_tool_call_response([])
        assert result is None

    def test_parse_tool_call_response_invalid_json(self):
        """测试无效 JSON 格式"""
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "classify_log"
        mock_tool_call.function.arguments = "invalid json"

        result = parse_tool_call_response([mock_tool_call])
        assert result is None

    def test_parse_tool_call_response_missing_fields(self):
        """测试缺少字段的响应"""
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "classify_log"
        mock_tool_call.function.arguments = json.dumps({
            "index": 5,
        })

        result = parse_tool_call_response([mock_tool_call])

        assert result is not None
        assert result.index == 5
        assert result.category == "未知"  # 默认值
        assert result.error_type is None
        assert result.normalized_message == ""
        assert result.extracted_params == {}

    def test_parse_tool_call_response_with_special_chars(self):
        """测试包含特殊字符的响应"""
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "classify_log"
        mock_tool_call.function.arguments = json.dumps({
            "index": 3,
            "category": "错误",
            "error_type": "SQLException: Connection refused",
            "normalized_message": "SQLException: Connection *",
            "extracted_params": {"host": "localhost", "port": 5432},
        })

        result = parse_tool_call_response([mock_tool_call])

        assert result is not None
        assert result.index == 3
        assert result.category == "错误"
        assert result.error_type == "SQLException: Connection refused"
        assert result.extracted_params == {"host": "localhost", "port": 5432}

    def test_parse_tool_call_arguments_valid(self):
        """测试直接解析 arguments JSON"""
        result = parse_tool_call_arguments(json.dumps({
            "index": 2,
            "category": "警告",
            "error_type": "TimeoutException",
            "normalized_message": "Request timeout at *",
            "extracted_params": {"timeout": 30},
        }))

        assert result is not None
        assert result.index == 2
        assert result.category == "警告"


class TestClassificationResult:
    """ClassificationResult 数据类测试"""

    def test_classification_result_creation(self):
        """测试 ClassificationResult 创建"""
        result = ClassificationResult(
            index=1,
            category="警告",
            error_type="TimeoutException",
            normalized_message="Request timeout at *",
            extracted_params={"timeout": 30},
        )

        assert result.index == 1
        assert result.category == "警告"
        assert result.error_type == "TimeoutException"
        assert result.normalized_message == "Request timeout at *"
        assert result.extracted_params == {"timeout": 30}

    def test_classification_result_mutable_extracted_params(self):
        """测试 extracted_params 可以是可变类型"""
        result = ClassificationResult(
            index=0,
            category="信息",
            error_type=None,
            normalized_message="User logged in",
            extracted_params={"user_id": 123, "items": ["a", "b"]},
        )

        assert result.extracted_params["user_id"] == 123
        assert result.extracted_params["items"] == ["a", "b"]


class TestToolSchema:
    """Tool Schema 测试"""

    def test_classify_log_tool_schema_structure(self):
        """测试 classify_log 工具 schema 结构"""
        assert CLASSIFY_LOG_TOOL_SCHEMA["type"] == "function"
        assert CLASSIFY_LOG_TOOL_SCHEMA["function"]["name"] == "classify_log"
        assert "description" in CLASSIFY_LOG_TOOL_SCHEMA["function"]
        assert "parameters" in CLASSIFY_LOG_TOOL_SCHEMA["function"]

        params = CLASSIFY_LOG_TOOL_SCHEMA["function"]["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params

        # 验证必需字段
        assert "index" in params["required"]
        assert "category" in params["required"]
        assert "normalized_message" in params["required"]
        assert "extracted_params" in params["required"]

        # 验证字段类型
        assert params["properties"]["index"]["type"] == "integer"

    def test_classify_log_tool_schema_descriptions(self):
        """测试 classify_log 工具字段描述"""
        params = CLASSIFY_LOG_TOOL_SCHEMA["function"]["parameters"]["properties"]

        assert "description" in params["index"]
        assert "description" in params["category"]
        assert "description" in params["normalized_message"]


class TestConcurrency:
    """并发控制测试"""

    def test_get_semaphore_returns_semaphore(self):
        """测试 get_semaphore 返回信号量"""
        semaphore = get_semaphore()
        assert semaphore is not None
        from asyncio import Semaphore
        assert isinstance(semaphore, Semaphore)

    def test_get_semaphore_same_instance(self):
        """测试 get_semaphore 返回同一实例"""
        sem1 = get_semaphore()
        sem2 = get_semaphore()
        assert sem1 is sem2

    def test_default_config(self):
        """测试默认配置"""
        config = get_default_config()

        assert "max_concurrent" in config
        assert "batch_size" in config
        assert isinstance(config["max_concurrent"], int)
        assert isinstance(config["batch_size"], int)
        assert config["max_concurrent"] > 0
        assert config["batch_size"] > 0


class TestClassifyWithAIResult:
    """classify_with_ai_result 函数测试"""

    def test_classify_with_ai_result_dict(self):
        """测试传入字典格式"""
        from backend.src.services.ai_analyzer import classify_with_ai_result

        log_entry = "ERROR at line 10"
        classification = {
            "category": "异常错误",
            "error_type": "NullPointerException",
            "extracted_params": {"line": "10"},
        }

        category, error_type, extracted_params = classify_with_ai_result(
            log_entry, classification
        )

        assert category == "异常错误"
        assert error_type == "NullPointerException"
        assert extracted_params == {"line": "10"}

    def test_classify_with_ai_result_classification_result(self):
        """测试传入 ClassificationResult 格式"""
        from backend.src.services.ai_analyzer import classify_with_ai_result

        log_entry = "ERROR at line 10"
        classification = ClassificationResult(
            index=0,
            category="异常错误",
            error_type="NullPointerException",
            normalized_message="Null pointer at *",
            extracted_params={"line": "10"},
        )

        category, error_type, extracted_params = classify_with_ai_result(
            log_entry, classification
        )

        assert category == "异常错误"
        assert error_type == "NullPointerException"
        assert extracted_params == {"line": "10"}
