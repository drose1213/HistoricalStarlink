"""RAG 引擎单元测试"""
import pytest
from backend.rag_engine import (
    HISTORY_EVENTS,
    build_index,
    search_similar,
    _keyword_search,
    _keyword_fallback_scores,
    _event_to_text,
    full_rag_query,
)


@pytest.mark.unit
class TestRagEngine:

    def test_history_events_not_empty(self):
        assert len(HISTORY_EVENTS) > 0

    @pytest.mark.asyncio
    async def test_keyword_fallback_returns_relevant_results(self):
        # _keyword_search 依赖 build_index 已构建索引
        await build_index(force=True)
        results = _keyword_search("商鞅", top_k=5)
        assert len(results) > 0
        # 实际返回 {"name": ..., "score": ...} 格式
        names = [r["name"] for r in results]
        assert any("商鞅" in n for n in names), f"未找到商鞅相关事件: {names}"

    def test_keyword_fallback_ranks_correctly(self):
        results = _keyword_search("统一", top_k=10)
        if len(results) > 1:
            assert results[0]["score"] >= results[-1]["score"]

    def test_keyword_fallback_empty_query(self):
        results = _keyword_search("", top_k=5)
        assert isinstance(results, list)

    def test_keyword_fallback_english_query(self):
        results = _keyword_search("reformation", top_k=5)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_similar_works(self):
        results = await search_similar("商鞅变法", top_k=3)
        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            # 实际返回 {"name": ..., "score": ..., ...}
            assert "name" in r
            assert "score" in r

    @pytest.mark.asyncio
    async def test_build_index_idempotent(self):
        idx1 = await build_index()
        idx2 = await build_index()
        assert idx1["count"] == idx2["count"]
        assert idx1["count"] == len(HISTORY_EVENTS)

    @pytest.mark.asyncio
    async def test_full_rag_query_returns_answer(self):
        result = await full_rag_query("商鞅变法的影响", top_k=3)
        assert "answer" in result
        assert "sources" in result
        assert isinstance(result["sources"], list)
        assert len(result["answer"]) > 0

    def test_event_to_text_includes_all_fields(self):
        ev = HISTORY_EVENTS[0]
        text = _event_to_text(ev)
        assert ev["name"] in text
        # 年份以中文格式出现（公元前N年 / 公元N年），不一定是 -221 原值
        year_abs = abs(ev["year"])
        assert (
            f"公元前{year_abs}年" in text
            or f"公元{year_abs}年" in text
            or f"公元{ev['year']}年" in text
        ), f"年份未在文本中体现: {text[:100]}"
        has_content = (
            ev.get("description", "") in text
            or any(c in text for c in ev.get("causes", []))
            or any(c in text for c in ev.get("consequences", []))
        )
        assert has_content, "event_to_text 必须包含至少一个关键字段"

    def test_search_top_k_respected(self):
        results = _keyword_search("历史", top_k=3)
        assert len(results) <= 3

    def test_keyword_scores_descending(self):
        # _keyword_fallback_scores 期望 items 为 [(text, meta), ...]
        items = [(_event_to_text(ev), ev) for ev in HISTORY_EVENTS]
        scores = _keyword_fallback_scores("变法", items)
        for i in range(len(scores) - 1):
            assert scores[i][1] >= scores[i+1][1], "分数必须降序"
