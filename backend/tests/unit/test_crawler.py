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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_default_sources_persists_updates_after_rollback(monkeypatch):
    """Regression test: 推荐源更新后必须 commit, 否则数据丢失.

    复现:
      1. mock 让 len(recommended_rows) == len(RECOMMENDED_SOURCES) 成立
      2. 预插入 N 行, name 故意是脏的, 但 url/url_hash 与真源一致
      3. _ensure_default_sources 会走 update 分支, 修复 name
      4. 用新 session 查询: 修复后看到新 name; bug 存在时仍看到旧 name
    """
    from backend.models.knowledge_base import CrawlSource, Base
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    import hashlib

    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    # 预插入 N 行 (N = len(RECOMMENDED_SOURCES)), name 故意是脏的
    sources = crawler.RECOMMENDED_SOURCES
    for i, src in enumerate(sources):
        url_hash = hashlib.sha256(src["url"].encode("utf-8")).hexdigest()
        async with SessionLocal() as db:
            db.add(CrawlSource(
                name=f"旧名-{i}",
                url=src["url"],
                url_hash=url_hash,
                category="旧分类",
                region="foreign",
                tags=[],
                description="旧描述",
                recommended=1,
                enabled=1,
                priority=1,
                last_status="pending",
            ))
            await db.commit()

    # 调 _ensure_default_sources 走 update 分支 (因数量匹配)
    async with SessionLocal() as db:
        await crawler._ensure_default_sources(db)

    # 用新 session 验证: 所有行的 name 应该是真源的 name, 不是旧名
    async with SessionLocal() as db:
        result = await db.execute(
            select(CrawlSource).order_by(CrawlSource.id)
        )
        rows = result.scalars().all()
        assert len(rows) == len(sources)
        for i, (row, src) in enumerate(zip(rows, sources)):
            assert row.name == src["name"], (
                f"行 {i} 修复丢失: name 期望 {src['name']!r} 实际 {row.name!r}. "
                "Bug: _ensure_default_sources 只 flush 未 commit"
            )

    await test_engine.dispose()


@pytest.mark.unit
async def test_run_source_in_session_concurrency(monkeypatch):
    """验证 _run_source_in_session 在 Semaphore(4) 限流下并发跑多个源, 总耗时 < 串行耗时."""
    sources = [
        {"id": None, "url": f"https://example.com/{i}", "name": f"src-{i}",
         "category": None, "region": None, "tags": [], "description": ""}
        for i in range(4)
    ]

    async def _slow_process(db, source, today_events, stats):
        await asyncio.sleep(0.4)
        stats["imported"] += 1

    class _NoopAsyncCtx:
        async def __aenter__(self):
            return None
        async def __aexit__(self, *args):
            return False

    # mock session factory, 避免真实 DB 连接 (虽然 _run_source_in_session 现在复用 db,
    # 但保留此 stub 以防未来重构)
    monkeypatch.setattr(crawler, "_get_session_factory", lambda: lambda: _NoopAsyncCtx())
    monkeypatch.setattr(crawler, "_process_single_source", _slow_process)
    # 把 semaphore 显式置为 4, 保证与模块默认一致
    monkeypatch.setattr(crawler, "_crawl_concurrency_limit", 4)
    import time
    t0 = time.monotonic()
    # _run_source_in_session 现在复用外层 db, 传 None 即可 (_process_single_source 已被 mock)
    results = await asyncio.gather(*[crawler._run_source_in_session(None, s, set()) for s in sources])
    elapsed = time.monotonic() - t0

    # 4 个源 × 0.4s 串行需要 ~1.6s; 并发 4 路理想 ~0.4s + 启动开销
    # 实际允许最大 1.2s (远小于 1.6s)
    assert elapsed < 1.2, f"Expected concurrent execution, but elapsed={elapsed:.2f}s"
    assert len(results) == 4
    assert sum(r["imported"] for r in results) == 4
    assert all(r["sources_processed"] == 1 for r in results)


@pytest.mark.unit
async def test_initial_crawl_retries_on_total_failure(monkeypatch):
    """首次抓取全部失败时, 验证 _run_initial_crawl_with_retry 至少尝试 3 次, backoff 正确."""
    call_count = {"n": 0}

    async def _failing_crawl():
        call_count["n"] += 1
        # 模拟 processed=2, failed=2 (全失败)
        return {
            "imported": 0, "updated": 0, "skipped_duplicates": 0,
            "skipped_short": 0, "failed": 2, "sources_processed": 2,
            "sources_failed": 2, "filtered_empty_event_name": 0,
            "skipped_daily_duplicate": 0, "todays_unique_count": 0,
        }

    sleeps: list[float] = []
    real_sleep = asyncio.sleep  # 备份原生 sleep, fake 内部不能调已被 monkeypatch 的 asyncio.sleep

    async def _fake_sleep(d):
        if d in (30, 300, 3600):
            sleeps.append(d)
            return await real_sleep(0)
        return await real_sleep(d)

    monkeypatch.setattr(crawler, "crawl_and_store", _failing_crawl)
    monkeypatch.setattr(crawler.asyncio, "sleep", _fake_sleep)

    result = await crawler._run_initial_crawl_with_retry()

    # backoff 序列 [30, 300] => 3 次尝试, 2 次 sleep(30, 300)
    assert call_count["n"] == 3, f"Expected 3 attempts, got {call_count['n']}"
    assert sleeps == [30, 300], f"Expected backoff sequence [30, 300], got {sleeps}"
    # 全失败时返回空 dict (因 last_exc 为 None, 走末尾 return {})
    assert result == {}


@pytest.mark.unit
async def test_initial_crawl_succeeds_on_partial_success(monkeypatch):
    """首次抓取部分成功时, 不应再重试, 立即返回."""
    call_count = {"n": 0}

    async def _partial_crawl():
        call_count["n"] += 1
        return {
            "imported": 1, "updated": 0, "skipped_duplicates": 0,
            "skipped_short": 0, "failed": 1, "sources_processed": 2,
            "sources_failed": 1, "filtered_empty_event_name": 0,
            "skipped_daily_duplicate": 0, "todays_unique_count": 0,
        }

    monkeypatch.setattr(crawler, "crawl_and_store", _partial_crawl)

    result = await crawler._run_initial_crawl_with_retry()

    assert call_count["n"] == 1, f"Expected 1 attempt on partial success, got {call_count['n']}"
    assert result["imported"] == 1
    assert result["sources_processed"] == 2

