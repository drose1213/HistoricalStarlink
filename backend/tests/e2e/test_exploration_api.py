"""探索记录 API 黑盒测试"""
import pytest


@pytest.mark.e2e
class TestExplorationAPI:
    """测试 /api/exploration 系列接口"""

    async def test_get_exploration_stats_empty(self, client, test_db):
        """新用户统计应为 0"""
        res = await client.get("/api/exploration/stats?session_id=session_test_001")
        assert res.status_code == 200
        body = res.json()
        assert body["code"] == 200
        assert body["data"]["total_records"] == 0

    async def test_get_exploration_records_empty(self, client, test_db):
        res = await client.get("/api/exploration/records?session_id=session_test_001")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 0

    async def test_exploration_flow(self, client, test_db, db_session):
        """完整探索流程：插入记录 → 统计 → 列表"""
        from backend.models.exploration_record import ExplorationRecord
        from datetime import datetime, timedelta

        sid = "session_test_002"
        for i in range(3):
            db_session.add(ExplorationRecord(
                session_id=sid,
                event_id="qin_unification",
                event_name="秦始皇统一六国",
                event_year=-221,
                event_region="china",
                stay_duration=60,
                depth=0,
                is_deleted=False,
                created_at=datetime.utcnow() - timedelta(minutes=i * 10),
            ))
        await db_session.commit()

        # 1. 统计
        res = await client.get(f"/api/exploration/stats?session_id={sid}")
        body = res.json()
        assert body["data"]["total_records"] == 3
        assert body["data"]["total_stay_duration"] == 180

        # 2. 列表
        res = await client.get(f"/api/exploration/records?session_id={sid}")
        body = res.json()
        assert len(body["data"]) == 3

    async def test_exploration_pagination(self, client, test_db, db_session):
        from backend.models.exploration_record import ExplorationRecord

        sid = "session_test_003"
        for i in range(5):
            db_session.add(ExplorationRecord(
                session_id=sid,
                event_id="han_empire",
                event_name="大汉帝国建立",
                event_year=-202,
                event_region="china",
                stay_duration=30,
                depth=0,
                is_deleted=False,
            ))
        await db_session.commit()

        res = await client.get(f"/api/exploration/records?session_id={sid}&page=1&page_size=2")
        body = res.json()
        assert len(body["data"]) == 2

    async def test_soft_deleted_records_excluded(self, client, test_db, db_session):
        from backend.models.exploration_record import ExplorationRecord

        sid = "session_test_004"
        for deleted in (False, True, False):
            db_session.add(ExplorationRecord(
                session_id=sid,
                event_id="han_empire",
                event_name="大汉帝国建立",
                event_year=-202,
                event_region="china",
                stay_duration=30,
                depth=0,
                is_deleted=deleted,
            ))
        await db_session.commit()

        res = await client.get(f"/api/exploration/records?session_id={sid}")
        body = res.json()
        # 软删除的应该被排除
        assert len(body["data"]) == 2
@pytest.mark.e2e
class TestExplorationNotesAPI:
    async def test_end_exploration_persists_notes(self, client, test_db):
        start_res = await client.post("/api/exploration/start", json={
            "event_id": "qin_unification",
            "event_name": "Qin unification",
            "session_id": "session_test_notes",
        })
        assert start_res.status_code == 200, start_res.text
        record_id = start_res.json()["data"]["id"]

        end_res = await client.post("/api/exploration/end", json={
            "record_id": record_id,
            "duration_seconds": 45,
            "path_depth": 2,
            "notes": "Chose centralization and completed the dialogue.",
        })

        assert end_res.status_code == 200, end_res.text
        body = end_res.json()["data"]
        assert body["notes"] == "Chose centralization and completed the dialogue."
        assert body["explore_path"]["notes"] == "Chose centralization and completed the dialogue."
