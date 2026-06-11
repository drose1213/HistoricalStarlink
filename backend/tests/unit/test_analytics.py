# -*- coding: utf-8 -*-
"""Analytics 模型 + Pydantic schema 单元测试 (不入库)"""
import pytest
from backend.routers.analytics import (
    AnalyticsEventRequest,
    ALLOWED_EVENTS,
)
from backend.models.analytics import AnalyticsEvent


@pytest.mark.unit
class TestAnalyticsSchema:
    """Pydantic 校验 - 不走 HTTP"""

    def test_all_allowed_event_names_accepted(self):
        for name in ALLOWED_EVENTS:
            req = AnalyticsEventRequest(event_name=name)
            assert req.event_name == name

    def test_invalid_event_name_passes_pydantic(self):
        """非法 event_name 在 schema 层不再被拦截 (移到 endpoint 业务层校验)"""
        # 白名单校验改在 endpoint 内 raise HTTPException(400), 避免 Pydantic 返回 422
        req = AnalyticsEventRequest(event_name="not_in_whitelist")
        assert req.event_name == "not_in_whitelist"

    def test_missing_event_name_rejected(self):
        with pytest.raises(Exception):
            AnalyticsEventRequest()

    def test_payload_default_is_empty_dict(self):
        req = AnalyticsEventRequest(event_name="app_enter")
        assert req.payload == {}

    def test_payload_must_be_dict_string_rejected(self):
        with pytest.raises(ValueError):
            AnalyticsEventRequest(event_name="app_enter", payload="oops")

    def test_payload_must_be_dict_int_rejected(self):
        with pytest.raises(ValueError):
            AnalyticsEventRequest(event_name="app_enter", payload=123)

    def test_payload_must_be_dict_list_rejected(self):
        with pytest.raises(ValueError):
            AnalyticsEventRequest(event_name="app_enter", payload=[1, 2])

    def test_topic_optional_and_accepted(self):
        req = AnalyticsEventRequest(event_name="dialogue_completed", topic="秦统一")
        assert req.topic == "秦统一"

    def test_topic_too_long_rejected(self):
        with pytest.raises(Exception):
            AnalyticsEventRequest(
                event_name="dialogue_completed",
                topic="x" * 201,
            )

    def test_user_agent_optional(self):
        req = AnalyticsEventRequest(event_name="app_enter")
        assert req.user_agent is None
        req2 = AnalyticsEventRequest(
            event_name="app_enter", user_agent="Mozilla/5.0"
        )
        assert req2.user_agent == "Mozilla/5.0"


@pytest.mark.unit
class TestAnalyticsModel:
    """Model to_dict 与字段默认行为"""

    def test_to_dict_keys(self):
        ev = AnalyticsEvent(
            id=42,
            event_name="app_enter",
            user_agent="ua",
            topic="t",
            payload={"k": 1},
        )
        d = ev.to_dict()
        assert d["id"] == 42
        assert d["event_name"] == "app_enter"
        assert d["user_agent"] == "ua"
        assert d["topic"] == "t"
        assert d["payload"] == {"k": 1}
        assert "created_at" in d

    def test_to_dict_default_payload(self):
        ev = AnalyticsEvent(id=1, event_name="app_enter")
        d = ev.to_dict()
        assert d["payload"] == {}
