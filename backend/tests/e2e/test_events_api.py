"""事件 API 黑盒测试"""
import pytest


@pytest.mark.e2e
class TestEventsAPI:
    """测试 /api/events 系列接口"""

    async def test_list_events(self, client, test_db):
        """GET /api/events 返回事件列表"""
        res = await client.get("/api/events")
        assert res.status_code == 200
        body = res.json()
        assert body["code"] == 200
        assert "data" in body
        assert "list" in body["data"]
        assert "total" in body["data"]
        assert body["data"]["total"] >= 3, "种子数据应至少 3 条"

    async def test_list_events_pagination(self, client, test_db):
        """分页参数生效"""
        res = await client.get("/api/events?page=1&page_size=1")
        body = res.json()
        assert body["data"]["page"] == 1
        assert body["data"]["page_size"] == 1
        assert len(body["data"]["list"]) <= 1

    async def test_list_events_filter_by_region(self, client, test_db):
        res = await client.get("/api/events?region=china")
        body = res.json()
        for ev in body["data"]["list"]:
            assert ev["region"] == "china"

    async def test_list_events_filter_by_importance(self, client, test_db):
        res = await client.get("/api/events?min_importance=8")
        body = res.json()
        for ev in body["data"]["list"]:
            assert ev["importance"] >= 8

    async def test_list_events_invalid_region_returns_empty_or_all(self, client, test_db):
        res = await client.get("/api/events?region=mars")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body["data"]["list"], list)

    async def test_get_event_by_id(self, client, test_db):
        res = await client.get("/api/events/qin_unification")
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["id"] == "qin_unification"
        assert body["data"]["name"]
        assert "description" in body["data"]

    async def test_get_event_not_found(self, client, test_db):
        res = await client.get("/api/events/nonexistent_event_xyz")
        assert res.status_code == 200  # BaseResponse 包装，code=404
        body = res.json()
        assert body["code"] == 404
        assert body["data"] is None

    async def test_search_events_by_keyword(self, client, test_db):
        res = await client.get("/api/events/search?q=秦")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0
        assert any("秦" in ev["name"] for ev in body["data"])

    async def test_search_events_no_results(self, client, test_db):
        res = await client.get("/api/events/search?q=xyzzz_nothing_found")
        assert res.status_code == 200
        body = res.json()
        assert body["data"] == []

    async def test_search_events_missing_query(self, client, test_db):
        res = await client.get("/api/events/search")
        # FastAPI 应返回 422
        assert res.status_code == 422

    async def test_event_response_schema(self, client, test_db):
        """验证事件响应字段完整"""
        res = await client.get("/api/events/qin_unification")
        body = res.json()
        data = body["data"]
        required = {"id", "name", "year", "region", "importance", "description", "causes", "consequences"}
        for field in required:
            assert field in data, f"事件响应缺少字段: {field}"
