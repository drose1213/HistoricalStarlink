"""Analytics 埋点接口黑盒测试.

注意: 整个 backend 项目的 main.py 通过 routers/dialogue.py 引用了一个
不存在的 backend.models.exploration_profile 模块, 导致 e2e 测试
无法 import backend.main.app.  这里使用一个最小化 FastAPI app,
只挂载 analytics router 来做黑盒测试, 不影响其他套件.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI


@pytest_asyncio.fixture(scope="function")
async def analytics_client(test_db):
    """只挂载 analytics router 的最小化测试客户端."""
    from backend.routers.analytics import router as analytics_router
    from backend.database import get_db

    app = FastAPI()
    app.include_router(analytics_router)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.e2e
class TestAnalyticsAPI:
    """测试 /api/analytics/event 端点"""

    _ALLOWED_EVENTS = [
        "app_enter",
        "dialogue_completed",
        "paywall_clicked",
        "feedback_submitted",
    ]

    async def test_post_4_valid_events(self, analytics_client, test_db):
        """4 个合法 event_name 都能成功上报"""
        for name in self._ALLOWED_EVENTS:
            res = await analytics_client.post(
                "/api/analytics/event",
                json={"event_name": name, "payload": {"x": 1}},
            )
            assert res.status_code == 200, f"{name} 返回 {res.status_code} {res.text}"
            body = res.json()
            assert body["success"] is True
            assert isinstance(body["event_id"], int)
            assert body["event_id"] > 0

    async def test_post_event_with_topic_and_ua(self, analytics_client, test_db):
        """带 topic / user_agent 也能成功"""
        res = await analytics_client.post(
            "/api/analytics/event",
            json={
                "event_name": "dialogue_completed",
                "topic": "qin_unification",
                "user_agent": "pytest-ua/1.0",
                "payload": {"round": 3},
            },
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["event_id"] > 0

    async def test_post_event_minimal_body(self, analytics_client, test_db):
        """只传 event_name 也应成功 (其他字段可选)"""
        res = await analytics_client.post(
            "/api/analytics/event",
            json={"event_name": "app_enter"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True

    async def test_post_event_invalid_name_returns_400(self, analytics_client, test_db):
        """非法 event_name -> 400"""
        res = await analytics_client.post(
            "/api/analytics/event",
            json={"event_name": "totally_random_event"},
        )
        assert res.status_code == 400

    async def test_post_event_missing_event_name_returns_422(self, analytics_client, test_db):
        """缺 event_name -> 422 (Pydantic)"""
        res = await analytics_client.post(
            "/api/analytics/event",
            json={"payload": {"x": 1}},
        )
        assert res.status_code == 422

    async def test_post_event_payload_must_be_dict(self, analytics_client, test_db):
        """payload 是字符串/数字 -> 422 (Pydantic 校验)"""
        for bad in ["string", 123, [1, 2, 3]]:
            res = await analytics_client.post(
                "/api/analytics/event",
                json={"event_name": "app_enter", "payload": bad},
            )
            assert res.status_code == 422, f"payload={bad!r} 应返回 422"


@pytest.mark.e2e
class TestAnalyticsSummaryAPI:
    """测试 /api/analytics/summary 端点 (PMF 基线报告)"""

    async def _seed(self, analytics_client, events: list[dict]):
        """直接 POST 上报 events 列表"""
        for ev in events:
            res = await analytics_client.post("/api/analytics/event", json=ev)
            assert res.status_code == 200, res.text

    async def test_summary_empty_db_returns_zeros(self, analytics_client, test_db):
        """空表: total_events=0, event_counts 全 0, top_topics=[], averages=0.0"""
        res = await analytics_client.get("/api/analytics/summary")
        assert res.status_code == 200
        body = res.json()
        assert body["total_events"] == 0
        assert body["unique_users"] == 0
        assert body["event_counts"] == {
            "app_enter": 0,
            "dialogue_completed": 0,
            "paywall_clicked": 0,
            "feedback_submitted": 0,
        }
        assert body["top_topics"] == []
        assert body["avg_dialogue_duration_seconds"] == 0.0
        assert body["avg_feedback_rating"] == 0.0

    async def test_summary_after_seeding_returns_correct_counts(
        self, analytics_client, test_db
    ):
        """seed 5 events: 3 app_enter / 2 dialogue_completed / 1 feedback_submitted"""
        await self._seed(analytics_client, [
            {"event_name": "app_enter", "user_agent": "ua-1", "payload": {}},
            {"event_name": "app_enter", "user_agent": "ua-1", "payload": {}},
            {"event_name": "app_enter", "user_agent": "ua-2", "payload": {}},
            {
                "event_name": "dialogue_completed",
                "user_agent": "ua-1",
                "topic": "qin_unification",
                "payload": {"duration_seconds": 60},
            },
            {
                "event_name": "dialogue_completed",
                "user_agent": "ua-2",
                "topic": "han_empire",
                "payload": {"duration_seconds": 120},
            },
            {
                "event_name": "feedback_submitted",
                "user_agent": "ua-1",
                "payload": {"rating": 4},
            },
        ])
        res = await analytics_client.get("/api/analytics/summary")
        assert res.status_code == 200
        body = res.json()
        assert body["total_events"] == 6  # 实际 seed 6 条
        assert body["event_counts"] == {
            "app_enter": 3,
            "dialogue_completed": 2,
            "paywall_clicked": 0,
            "feedback_submitted": 1,
        }
        # unique users: ua-1, ua-2 = 2
        assert body["unique_users"] == 2

    async def test_summary_top_topics_ordered(self, analytics_client, test_db):
        """seed 3 个不同 topic 的 dialogue_completed, 验证 top_topics 排序正确"""
        # topic A: 3 次, topic B: 1 次, topic C: 2 次
        await self._seed(analytics_client, [
            {"event_name": "dialogue_completed", "topic": "topic_A", "payload": {"duration_seconds": 10}},
            {"event_name": "dialogue_completed", "topic": "topic_A", "payload": {"duration_seconds": 20}},
            {"event_name": "dialogue_completed", "topic": "topic_A", "payload": {"duration_seconds": 30}},
            {"event_name": "dialogue_completed", "topic": "topic_B", "payload": {"duration_seconds": 40}},
            {"event_name": "dialogue_completed", "topic": "topic_C", "payload": {"duration_seconds": 50}},
            {"event_name": "dialogue_completed", "topic": "topic_C", "payload": {"duration_seconds": 60}},
        ])
        res = await analytics_client.get("/api/analytics/summary")
        assert res.status_code == 200
        body = res.json()
        top = body["top_topics"]
        # 应按 count 倒序: A(3) -> C(2) -> B(1)
        assert len(top) == 3
        assert top[0]["topic"] == "topic_A" and top[0]["count"] == 3
        assert top[1]["topic"] == "topic_C" and top[1]["count"] == 2
        assert top[2]["topic"] == "topic_B" and top[2]["count"] == 1
        # avg duration: (10+20+30+40+50+60)/6 = 35.0
        assert body["avg_dialogue_duration_seconds"] == 35.0

    async def test_summary_avg_metrics(self, analytics_client, test_db):
        """seed 2 个 feedback rating=4/5, 验证 avg_feedback_rating = 4.5"""
        await self._seed(analytics_client, [
            {"event_name": "feedback_submitted", "payload": {"rating": 4}},
            {"event_name": "feedback_submitted", "payload": {"rating": 5}},
        ])
        res = await analytics_client.get("/api/analytics/summary")
        assert res.status_code == 200
        body = res.json()
        assert body["avg_feedback_rating"] == 4.5
        # 没有 dialogue_completed -> 0.0
        assert body["avg_dialogue_duration_seconds"] == 0.0
        assert body["event_counts"]["feedback_submitted"] == 2
