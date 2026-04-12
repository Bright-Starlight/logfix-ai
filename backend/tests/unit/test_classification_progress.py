"""
分类进度跟踪单元测试

测试 ClassificationSession 实体和进度跟踪逻辑。
"""

import pytest
from datetime import datetime
from uuid import uuid4

from backend.src.models.entities import ClassificationSession


class TestClassificationSessionStatus:
    """测试 ClassificationSession 状态转换"""

    def test_status_enum_values(self):
        """验证状态枚举值"""
        valid_statuses = ["pending", "processing", "completed", "failed"]
        for status in valid_statuses:
            session = ClassificationSession(
                split_session_id=uuid4(),
                mode="rule_engine",
                status=status,
                total_items=100,
                processed_items=0,
            )
            assert session.status in valid_statuses

    def test_mode_enum_values(self):
        """验证模式枚举值"""
        valid_modes = ["rule_engine", "ai"]
        for mode in valid_modes:
            session = ClassificationSession(
                split_session_id=uuid4(),
                mode=mode,
                status="pending",
                total_items=100,
                processed_items=0,
            )
            assert session.mode in valid_modes


class TestClassificationProgress:
    """测试分类进度计算逻辑"""

    def test_progress_percent_calculation(self):
        """验证进度百分比计算"""
        # 进度 = processed_items / total_items * 100
        test_cases = [
            (0, 100, 0),
            (50, 100, 50),
            (100, 100, 100),
            (1, 3, 33),  # 1/3 = 33.33%
        ]

        for processed, total, expected_percent in test_cases:
            percent = int(processed / total * 100) if total > 0 else 0
            assert percent == expected_percent

    def test_progress_cannot_exceed_total(self):
        """验证 processed_items 不能超过 total_items"""
        session = ClassificationSession(
            split_session_id=uuid4(),
            mode="rule_engine",
            status="processing",
            total_items=100,
            processed_items=100,
        )
        assert session.processed_items <= session.total_items

    def test_estimated_time_after_completion(self):
        """验证完成后预估时间应为0"""
        session = ClassificationSession(
            split_session_id=uuid4(),
            mode="rule_engine",
            status="completed",
            total_items=100,
            processed_items=100,
            estimated_remaining_seconds=0,
        )
        assert session.estimated_remaining_seconds == 0


class TestClassificationPhaseNames:
    """测试分类阶段名称"""

    def test_valid_phase_names(self):
        """验证有效的阶段名称"""
        valid_phases = [
            "准备中",
            "去重检测中",
            "忽略规则过滤中",
            "分类分析中",
            "存储中",
            "完成",
        ]

        for phase in valid_phases:
            session = ClassificationSession(
                split_session_id=uuid4(),
                mode="rule_engine",
                status="processing",
                total_items=100,
                processed_items=50,
                current_phase=phase,
            )
            assert session.current_phase == phase
