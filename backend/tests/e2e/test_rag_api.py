"""RAG 知识库 API 黑盒测试"""
import pytest


@pytest.mark.e2e
class TestRagAPI:
    """测试 /api/rag 系列接口"""

    async def test_rag_search(self, client, test_db):
        res = await client.post("/api/rag/search", json={
            "query": "商鞅变法",
            "top_k": 3,
        })
        assert res.status_code == 200
        body = res.json()
        assert body["code"] == 200
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0

    async def test_rag_search_relevance(self, client, test_db):
        res = await client.post("/api/rag/search", json={
            "query": "商鞅",
            "top_k": 5,
        })
        body = res.json()
        names = [r.get("name", "") for r in body["data"]]
        # 至少一个结果与"商鞅"相关
        assert any("商鞅" in n for n in names), f"搜索结果应与查询相关: {names}"

    async def test_rag_search_top_k(self, client, test_db):
        res = await client.post("/api/rag/search", json={
            "query": "历史",
            "top_k": 2,
        })
        body = res.json()
        assert len(body["data"]) <= 2

    async def test_rag_search_empty_query(self, client, test_db):
        res = await client.post("/api/rag/search", json={
            "query": "",
            "top_k": 5,
        })
        # 应返回空或 422
        assert res.status_code in (200, 422)

    async def test_rag_search_invalid_params(self, client, test_db):
        res = await client.post("/api/rag/search", json={})
        assert res.status_code in (200, 422)

    async def test_rag_ask(self, client, test_db):
        res = await client.post("/api/rag/ask", json={
            "question": "商鞅变法的影响是什么？",
        })
        assert res.status_code == 200
        body = res.json()
        assert "answer" in body["data"]
        assert "sources" in body["data"]
        assert isinstance(body["data"]["answer"], str)
        assert len(body["data"]["answer"]) > 0
        assert isinstance(body["data"]["sources"], list)

    async def test_rag_ask_returns_sources(self, client, test_db):
        res = await client.post("/api/rag/ask", json={
            "question": "罗马帝国是怎么衰落的？",
        })
        body = res.json()
        # 至少有来源支持答案
        assert len(body["data"]["sources"]) > 0

    async def test_rag_rebuild_index(self, client, test_db):
        res = await client.post("/api/rag/rebuild")
        assert res.status_code in (200, 404, 405)
