"""
ai_analyzer 单元测试

验证 AI 结果映射和结构化输出模型的基础行为。
"""

try:
    from backend.src.services.ai_analyzer import (
        AIAnalysisResult,
        _extract_json_candidate,
        _normalize_ai_payload,
        _parse_structured_ai_result,
        classify_with_ai_result,
    )
except ModuleNotFoundError:
    from src.services.ai_analyzer import (
        AIAnalysisResult,
        _extract_json_candidate,
        _normalize_ai_payload,
        _parse_structured_ai_result,
        classify_with_ai_result,
    )


def test_classify_with_ai_result_none_classification():
    """无法分类时返回默认值"""
    category, error_type, extracted_params = classify_with_ai_result("example log", None)

    assert category == "异常错误"
    assert error_type is None
    assert extracted_params == {}


def test_classify_with_ai_result_normal_mapping():
    """正常分类字典应被正确映射"""
    category, error_type, extracted_params = classify_with_ai_result(
        "example log",
        {
            "category": "数据库错误",
            "error_type": "ConnectionTimeout",
            "extracted_params": {"host": "db01", "port": "5432"},
        },
    )

    assert category == "数据库错误"
    assert error_type == "ConnectionTimeout"
    assert extracted_params == {"host": "db01", "port": "5432"}


def test_ai_analysis_result_accepts_nullable_classification_items():
    """结构化输出支持 null 分类项"""
    result = AIAnalysisResult.model_validate(
        {
            "classifications": [
                {
                    "original_index": 0,
                    "category": "异常错误",
                    "error_type": "NullPointerException",
                    "normalized_message": "Null pointer at line *",
                    "extracted_params": {"line": "10"},
                },
                None,
            ],
            "duplicates": [
                {"representative_index": 0, "duplicate_indices": [3, 7]},
            ],
        }
    )

    assert len(result.classifications) == 2
    assert result.classifications[1] is None
    assert result.duplicates[0].representative_index == 0
    assert result.duplicates[0].duplicate_indices == [3, 7]


def test_extract_json_candidate_strips_think_tags():
    """应能从 think 包裹文本中提取 JSON"""
    text = '<think>reasoning...</think>\n{"classifications":[null],"duplicates":[]}'
    candidate = _extract_json_candidate(text)

    assert candidate == '{"classifications":[null],"duplicates":[]}'


def test_parse_structured_ai_result_from_include_raw_payload():
    """include_raw 返回 parsed=None 时应回退解析 raw.content"""
    ai_result = {
        "parsed": None,
        "raw": type("RawMsg", (), {"content": '<think>x</think>{"classifications":[null],"duplicates":[]}'})(),
        "parsing_error": None,
    }

    parsed = _parse_structured_ai_result(ai_result)

    assert isinstance(parsed, AIAnalysisResult)
    assert parsed.classifications == [None]
    assert parsed.duplicates == []


def test_normalize_ai_payload_handles_loose_schema():
    """宽松 schema 应归一化为标准结构"""
    normalized = _normalize_ai_payload(
        {
            "classifications": ["IMAGE_RETRIEVAL_FAILURE", "PDF_IMAGE_PROCESSING_FAILURE"],
            "duplicates": [[0, 1]],
        },
        total_logs=2,
    )

    assert normalized["classifications"][0]["original_index"] == 0
    assert normalized["classifications"][0]["error_type"] == "IMAGE_RETRIEVAL_FAILURE"
    assert normalized["classifications"][1]["original_index"] == 1
    assert normalized["duplicates"] == [{"representative_index": 0, "duplicate_indices": [1]}]


def test_parse_structured_ai_result_accepts_loose_raw_json():
    """raw JSON 为简化格式时也应解析成功"""
    ai_result = {
        "parsed": None,
        "raw": type(
            "RawMsg",
            (),
            {
                "content": (
                    "<think>x</think>"
                    '{"classifications":["A","B"],"duplicates":[[0,1]]}'
                )
            },
        )(),
        "parsing_error": None,
    }

    parsed = _parse_structured_ai_result(ai_result, total_logs=2)

    assert parsed.classifications[0] is not None
    assert parsed.classifications[0].error_type == "A"
    assert parsed.duplicates[0].representative_index == 0
    assert parsed.duplicates[0].duplicate_indices == [1]
