"""健康检查与基础 API 黑盒测试"""
import pytest


@pytest.mark.e2e
class TestHealthAPI:
    """测试 /health 和 / 接口"""

    async def test_root_endpoint(self, client, test_db):
        res = await client.get("/")
        assert res.status_code == 200
        body = res.json()
        assert "name" in body
        assert "version" in body
        assert body["status"] == "running"

    async def test_health_check(self, client, test_db):
        res = await client.get("/health")
        assert res.status_code == 200
        body = res.json()
        assert "status" in body
        assert "database" in body
        assert body["database"] == "connected"

    async def test_docs_endpoint_accessible(self, client, test_db):
        res = await client.get("/docs")
        assert res.status_code == 200


@pytest.mark.e2e
class TestConfigAPI:
    """测试 /api/config 系列接口"""

    async def test_list_configs(self, client, test_db):
        res = await client.get("/api/config")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0, "应至少有一条配置"

    async def test_filter_configs_by_group(self, client, test_db):
        res = await client.get("/api/config?group=database")
        body = res.json()
        for cfg in body["data"]:
            assert cfg["group"] == "database"

    async def test_get_single_config(self, client, test_db):
        res = await client.get("/api/config/mysql.host")
        body = res.json()
        assert body["code"] == 200
        assert body["data"]["key"] == "mysql.host"

    async def test_get_nonexistent_config(self, client, test_db):
        res = await client.get("/api/config/xxx.nonexistent.key")
        body = res.json()
        assert body["code"] == 404

    async def test_get_config_groups(self, client, test_db):
        res = await client.get("/api/config/groups")
        body = res.json()
        assert isinstance(body["data"], list)
        assert "database" in body["data"] or "redis" in body["data"]
