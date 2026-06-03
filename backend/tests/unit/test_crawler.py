"""Crawler unit tests."""
import asyncio

import pytest
import httpx

from backend import crawler


class _DummyResponse:
    status_code = 403
    request = httpx.Request("GET", "https://example.com")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_crawl_page_falls_back_to_urllib_on_403(monkeypatch):
    class _BlockedClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers=None):
            raise httpx.HTTPStatusError(
                "blocked",
                request=_DummyResponse.request,
                response=_DummyResponse(),
            )

    async def _fake_fallback(url, headers, timeout):
        return "<html>ok</html>"

    monkeypatch.setattr(crawler.httpx, "AsyncClient", lambda **kwargs: _BlockedClient())
    monkeypatch.setattr(crawler, "_crawl_page_with_urllib", _fake_fallback)

    html = await crawler.crawl_page("https://example.com")

    assert html == "<html>ok</html>"


@pytest.mark.unit
def test_should_fallback_to_urllib_only_for_auth_like_http_errors():
    response_403 = httpx.Response(403, request=httpx.Request("GET", "https://example.com"))
    response_500 = httpx.Response(500, request=httpx.Request("GET", "https://example.com"))

    exc_403 = httpx.HTTPStatusError("blocked", request=response_403.request, response=response_403)
    exc_500 = httpx.HTTPStatusError("server", request=response_500.request, response=response_500)

    assert crawler._should_fallback_to_urllib(exc_403) is True
    assert crawler._should_fallback_to_urllib(exc_500) is False
    assert crawler._should_fallback_to_urllib(RuntimeError("boom")) is False


class _DummyScalarResult:
    def __init__(self, value=None):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return []


class _FakeSession:
    def __init__(self):
        self.added = []
        self.commit_calls = 0
        self.rollback_calls = 0

    async def execute(self, stmt):
        return _DummyScalarResult()

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


class _FakeSessionFactory:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def __call__(self):
        return self


@pytest.mark.unit
@pytest.mark.asyncio
async def test_crawl_and_store_serializes_overlapping_runs(monkeypatch):
    session = _FakeSession()
    entered = asyncio.Event()
    release = asyncio.Event()
    active_runs = 0
    max_active_runs = 0

    monkeypatch.setattr(crawler, "_get_session_factory", lambda: _FakeSessionFactory(session))
    monkeypatch.setattr(crawler, "_ensure_default_sources", lambda db: asyncio.sleep(0, result=0))
    monkeypatch.setattr(
        crawler,
        "_gather_active_sources",
        lambda db: asyncio.sleep(
            0,
            result=[{"id": None, "url": "https://example.com", "name": "Example Source"}],
        ),
    )
    monkeypatch.setattr(crawler, "_get_todays_event_names", lambda db, day: asyncio.sleep(0, result=set()))
    monkeypatch.setattr(crawler, "extract_text_from_html", lambda html: "x" * 300)
    monkeypatch.setattr(crawler, "chunk_text", lambda text, max_chars=2000, overlap=200: [text])

    async def _fake_crawl_page(url, timeout=30.0):
        nonlocal active_runs, max_active_runs
        active_runs += 1
        max_active_runs = max(max_active_runs, active_runs)
        entered.set()
        await release.wait()
        active_runs -= 1
        return "<html>ok</html>"

    monkeypatch.setattr(crawler, "crawl_page", _fake_crawl_page)

    first_task = asyncio.create_task(crawler.crawl_and_store())
    await entered.wait()
    second_task = asyncio.create_task(crawler.crawl_and_store())
    await asyncio.sleep(0.05)
    release.set()

    first_result, second_result = await asyncio.gather(first_task, second_task)

    assert max_active_runs == 1
    assert first_result["sources_processed"] == 1
    assert second_result["sources_processed"] == 1


@pytest.mark.unit
def test_sync_recommended_source_row_repairs_mismatched_metadata():
    class _Row:
        name = "乱码名称"
        url = "https://bad.example.com"
        url_hash = "old"
        category = "旧分类"
        region = "foreign"
        tags = ["old"]
        description = "old"
        recommended = 0
        enabled = 0
        priority = 1

    source_def = {
        "name": "中国历史 - 维基百科",
        "url": "https://zh.wikipedia.org/wiki/%E4%B8%AD%E5%9B%BD%E5%8E%86%E5%8F%B2",
        "category": "综合",
        "region": "china",
        "tags": ["中国", "历史", "综合"],
        "description": "中文维基百科中国历史总览",
    }

    changed = crawler._sync_recommended_source_row(_Row, source_def)

    assert changed is True
    assert _Row.name == source_def["name"]
    assert _Row.url == source_def["url"]
    assert _Row.category == source_def["category"]
    assert _Row.region == source_def["region"]
    assert _Row.tags == source_def["tags"]
    assert _Row.description == source_def["description"]
    assert _Row.recommended == 1
    assert _Row.enabled == 1
    assert _Row.priority == 5
