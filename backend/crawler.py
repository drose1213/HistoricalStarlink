"""
Background web crawler for historical knowledge.
Fetches historical web pages daily and stores them into the knowledge base.

Features:
- Pulls crawl sources from the CrawlSource table (DB-driven, recommended sources)
- Falls back to the built-in RECOMMENDED_SOURCES list when DB is empty
- Deduplicates by event_name (per source_name) — same event from the same URL won't be inserted twice
- Records comprehensive version info for every entry
- Schedules a periodic daily crawl via start_crawl_scheduler
"""
import asyncio
import hashlib
import logging
import re
import urllib.request
from datetime import datetime, timedelta
from typing import Optional
from html.parser import HTMLParser

import httpx

logger = logging.getLogger("historical_starlink.crawler")
_crawl_execution_lock = asyncio.Lock()

RECOMMENDED_SOURCES = [
    {
        "url": "https://zh.wikipedia.org/wiki/%E4%B8%AD%E5%9B%BD%E5%8E%86%E5%8F%B2",
        "name": "中国历史 - 维基百科",
        "description": "中文维基百科中国历史总览",
        "category": "综合",
        "region": "china",
        "tags": ["中国", "历史", "综合"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E4%B8%96%E7%95%8C%E5%8E%86%E5%8F%B2",
        "name": "世界历史 - 维基百科",
        "description": "中文维基百科世界历史总览",
        "category": "综合",
        "region": "foreign",
        "tags": ["世界", "历史", "综合"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E4%B8%AD%E5%9B%BD%E7%A7%91%E6%8A%80%E5%8F%B2",
        "name": "中国科技史 - 维基百科",
        "description": "中国科技发展史, 涵盖四大发明等",
        "category": "科技",
        "region": "china",
        "tags": ["科技", "中国", "四大发明"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E5%A4%A7%E8%88%AA%E6%B5%B7%E6%97%B6%E4%BB%A3",
        "name": "大航海时代 - 维基百科",
        "description": "15-17 世纪欧洲航海大发现",
        "category": "军事",
        "region": "foreign",
        "tags": ["航海", "探索", "欧洲"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E4%B8%9D%E7%BB%B8%E4%B9%8B%E8%B7%AF",
        "name": "丝绸之路 - 维基百科",
        "description": "古代东西方贸易与文化交流通道",
        "category": "经济",
        "region": "china",
        "tags": ["贸易", "丝绸之路", "交流"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E5%B7%A5%E4%B8%9A%E9%9D%A9%E5%91%BD",
        "name": "工业革命 - 维基百科",
        "description": "18 世纪英国开始的工业化进程",
        "category": "科技",
        "region": "foreign",
        "tags": ["工业革命", "英国", "科技"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E6%96%87%E8%89%BA%E5%A4%8D%E5%85%B4",
        "name": "文艺复兴 - 维基百科",
        "description": "14-17 世纪欧洲思想与艺术革命",
        "category": "文化",
        "region": "foreign",
        "tags": ["文艺复兴", "艺术", "欧洲"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E6%B5%B7%E4%B8%8A%E4%B8%9D%E7%BB%B8%E4%B9%8B%E8%B7%AF",
        "name": "海上丝绸之路 - 维基百科",
        "description": "宋元明时期海上贸易航线",
        "category": "经济",
        "region": "china",
        "tags": ["贸易", "海上", "丝绸之路"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E4%BA%94%E5%9B%9B%E8%BF%90%E5%8A%A8",
        "name": "五四运动 - 维基百科",
        "description": "1919 年中国反帝反封建的爱国运动",
        "category": "政治",
        "region": "china",
        "tags": ["近代", "爱国", "新文化"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E4%BA%8C%E6%88%98",
        "name": "第二次世界大战 - 维基百科",
        "description": "1939-1945 年全球性战争",
        "category": "军事",
        "region": "foreign",
        "tags": ["二战", "全球", "反法西斯"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E9%98%BF%E6%B3%A2%E7%BD%9711%E5%8F%B7",
        "name": "阿波罗11号 - 维基百科",
        "description": "1969 年阿波罗 11 号登月任务",
        "category": "科技",
        "region": "foreign",
        "tags": ["航天", "美国", "登月"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E5%8D%97%E5%8C%97%E6%9C%9D",
        "name": "南北朝 - 维基百科",
        "description": "中国 4-6 世纪南北分裂时期",
        "category": "政治",
        "region": "china",
        "tags": ["分裂", "南北", "魏晋"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E5%94%90%E6%9C%9D",
        "name": "唐朝 - 维基百科",
        "description": "中国 7-10 世纪的黄金时代",
        "category": "政治",
        "region": "china",
        "tags": ["唐朝", "盛世", "国际"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E5%A4%A7%E8%90%A7%E6%9D%A1",
        "name": "经济大萧条 - 维基百科",
        "description": "1929-1933 年全球性经济危机",
        "category": "经济",
        "region": "foreign",
        "tags": ["危机", "美国", "全球"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E6%B0%91%E4%B8%BB%E9%9D%A9%E5%91%BD",
        "name": "民主革命 - 维基百科",
        "description": "近代中国反帝反封建革命",
        "category": "政治",
        "region": "china",
        "tags": ["近代", "革命", "民主"],
    },
]


class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text_parts: list[str] = []
        self._skip = False
        self._skip_tags = {"script", "style", "nav", "footer", "header", "aside", "form"}
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        self._tag_stack.append(tag)
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()
        if tag in self._skip_tags:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._text_parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._text_parts)


def extract_text_from_html(html: str) -> str:
    parser = SimpleHTMLTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            newline_pos = text.rfind("\n", start + max_chars // 2, end)
            if newline_pos > start:
                end = newline_pos
        chunks.append(text[start:end].strip())
        start = end - overlap if end < len(text) else end
    return [c for c in chunks if c]


async def crawl_page(url: str, timeout: float = 30.0) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        if _should_fallback_to_urllib(e):
            logger.info(f"httpx blocked for {url}, retrying with urllib fallback")
            fallback_html = await _crawl_page_with_urllib(url, headers, timeout)
            if fallback_html:
                return fallback_html
        logger.warning(f"Failed to crawl {url}: {e}")
        return None


def _should_fallback_to_urllib(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {401, 403}
    return False


async def _crawl_page_with_urllib(url: str, headers: dict[str, str], timeout: float) -> Optional[str]:
    def _fetch() -> Optional[str]:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="ignore")

    try:
        return await asyncio.to_thread(_fetch)
    except Exception as exc:
        logger.warning(f"urllib fallback failed for {url}: {exc}")
        return None


def _sync_recommended_source_row(row, source_def: dict) -> bool:
    expected_url_hash = hashlib.sha256(source_def["url"].encode("utf-8")).hexdigest()
    updates = {
        "name": source_def["name"],
        "url": source_def["url"],
        "url_hash": expected_url_hash,
        "category": source_def.get("category"),
        "region": source_def.get("region"),
        "tags": source_def.get("tags", []),
        "description": source_def.get("description", ""),
        "recommended": 1,
        "enabled": 1,
        "priority": 5,
    }
    changed = False
    for field_name, expected_value in updates.items():
        if getattr(row, field_name, None) != expected_value:
            setattr(row, field_name, expected_value)
            changed = True
    return changed

async def _ensure_default_sources(db) -> int:
    """Ensure recommended sources are present in the CrawlSource table. Returns count inserted."""
    from .models.knowledge_base import CrawlSource
    from sqlalchemy import select

    inserted = 0
    repaired = 0
    recommended_rows = (
        await db.execute(
            select(CrawlSource)
            .where(CrawlSource.recommended == 1)
            .order_by(CrawlSource.id)
        )
    ).scalars().all()
    if len(recommended_rows) == len(RECOMMENDED_SOURCES):
        for row, source_def in zip(recommended_rows, RECOMMENDED_SOURCES):
            if _sync_recommended_source_row(row, source_def):
                repaired += 1

    for src in RECOMMENDED_SOURCES:
        url_hash = hashlib.sha256(src["url"].encode("utf-8")).hexdigest()
        existing = await db.execute(select(CrawlSource).where(CrawlSource.url_hash == url_hash))
        if existing.scalar_one_or_none():
            continue
        db.add(CrawlSource(
            name=src["name"],
            url=src["url"],
            url_hash=url_hash,
            category=src.get("category"),
            region=src.get("region"),
            tags=src.get("tags", []),
            description=src.get("description", ""),
            recommended=1,
            enabled=1,
            priority=5,
            last_status="pending",
        ))
        inserted += 1
    if inserted or repaired:
        try:
            await db.flush()
        except Exception:
            pass
    return inserted


async def _gather_active_sources(db) -> list[dict]:
    """Return all enabled crawl sources (from DB if any, otherwise from the hard-coded list)."""
    from .models.knowledge_base import CrawlSource
    from sqlalchemy import select

    result = await db.execute(select(CrawlSource).where(CrawlSource.enabled == 1))
    rows = result.scalars().all()
    if rows:
        return [
            {
                "id": r.id,
                "url": r.url,
                "name": r.name,
                "category": r.category,
                "region": r.region,
                "tags": list(r.tags or []),
                "description": r.description,
            }
            for r in rows
        ]
    return [
        {
            "id": None,
            "url": s["url"],
            "name": s["name"],
            "category": s.get("category"),
            "region": s.get("region"),
            "tags": s.get("tags", []),
            "description": s.get("description", ""),
        }
        for s in RECOMMENDED_SOURCES
    ]


async def _get_todays_event_names(db, day: datetime) -> set[str]:
    """返回当天 0 点至次日 0 点之间已入库的 event_name 集合, 用于每日去重.

    Args:
        db: AsyncSession 实例
        day: 参考时间 (UTC), 取其 0 点作为当日起点

    Returns:
        当日已存在且非空的 event_name 集合
    """
    from .models.knowledge_base import KnowledgeEntry
    from sqlalchemy import select, distinct

    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    stmt = select(distinct(KnowledgeEntry.event_name)).where(
        KnowledgeEntry.created_at >= start,
        KnowledgeEntry.created_at < end,
        KnowledgeEntry.event_name.isnot(None),
    )
    rows = (await db.execute(stmt)).scalars().all()
    result = {name for name in rows if name and name.strip()}
    return result



def _build_crawl_stats() -> dict:
    return {
        "imported": 0,
        "updated": 0,
        "skipped_duplicates": 0,
        "skipped_short": 0,
        "failed": 0,
        "sources_processed": 0,
        "sources_failed": 0,
        "filtered_empty_event_name": 0,
        "skipped_daily_duplicate": 0,
        "todays_unique_count": 0,
    }


def _get_session_factory():
    from .database import AsyncSessionLocal

    return AsyncSessionLocal


async def _commit_session(db, *, context: str) -> bool:
    try:
        await db.commit()
        return True
    except Exception as exc:
        logger.error(f"Failed to commit {context}: {exc}")
        await db.rollback()
        return False


async def _set_source_status(db, crawl_source_model, source_id: Optional[int], *,
                             status: str, crawled_at: datetime, imported: int) -> None:
    from sqlalchemy import update

    if source_id is None:
        return

    await db.execute(
        update(crawl_source_model)
        .where(crawl_source_model.id == source_id)
        .values(
            last_status=status,
            last_crawled_at=crawled_at,
            last_imported=imported,
        )
    )


async def _mark_source_failed(db, crawl_source_model, source: dict, now: datetime) -> None:
    source_id = source.get("id")
    if source_id is None:
        return

    try:
        await _set_source_status(
            db,
            crawl_source_model,
            source_id,
            status="failed",
            crawled_at=now,
            imported=0,
        )
        await _commit_session(db, context=f"failed status for source {source_id}")
    except Exception as exc:
        logger.warning(f"Failed to persist failed status for source {source_id}: {exc}")
        await db.rollback()


async def _process_single_source(db, source: dict, today_events: set[str], stats: dict) -> None:
    from .models.knowledge_base import KnowledgeEntry, KnowledgeVersion, CrawlSource
    from sqlalchemy import select

    url = source["url"]
    source_name = source["name"]
    source_now = datetime.utcnow()
    source_stats = {
        "imported": 0,
        "updated": 0,
        "skipped_duplicates": 0,
        "skipped_short": 0,
        "filtered_empty_event_name": 0,
        "skipped_daily_duplicate": 0,
    }

    try:
        html = await crawl_page(url)
        if not html:
            stats["sources_failed"] += 1
            stats["failed"] += 1
            await _mark_source_failed(db, CrawlSource, source, source_now)
            return

        text = extract_text_from_html(html)
        if len(text) < 100:
            stats["sources_failed"] += 1
            stats["skipped_short"] += 1
            await _mark_source_failed(db, CrawlSource, source, source_now)
            return

        chunks = chunk_text(text)
        event_name_base = source_name.split(" - ")[0] if " - " in source_name else source_name
        if not event_name_base or not event_name_base.strip():
            logger.warning(
                f"Skip crawl source due to empty event_name_base: source_name={source_name!r}, "
                f"url={url!r}, chunks={len(chunks)}"
            )
            stats["sources_failed"] += 1
            stats["failed"] += 1
            stats["filtered_empty_event_name"] += len(chunks)
            await _mark_source_failed(db, CrawlSource, source, source_now)
            return

        for idx, chunk in enumerate(chunks):
            if event_name_base in today_events:
                source_stats["skipped_daily_duplicate"] += 1
                logger.debug(
                    f"Skip daily duplicate: event_name={event_name_base!r}, "
                    f"chunk={idx}, url={url!r}"
                )
                continue

            content_hash = KnowledgeEntry.compute_hash(chunk)
            existing = await db.execute(
                select(KnowledgeEntry).where(
                    KnowledgeEntry.event_name == event_name_base,
                    KnowledgeEntry.chunk_index == idx,
                    KnowledgeEntry.source_url == url,
                )
            )
            found = existing.scalar_one_or_none()
            if found:
                if found.content_hash == content_hash:
                    source_stats["skipped_duplicates"] += 1
                    continue
                found.content = chunk
                found.content_hash = content_hash
                found.version += 1
                found.version_count = (found.version_count or 1) + 1
                found.updated_at = source_now
                found.last_indexed_at = source_now
                db.add(KnowledgeVersion(
                    entry_id=found.id,
                    version=found.version,
                    title=found.title,
                    content=chunk,
                    content_hash=content_hash,
                    change_summary=f"Web crawl update from {url}",
                    change_source="web_crawl",
                    operator="crawler",
                    snapshot_meta={
                        "source_url": url,
                        "chunk_index": idx,
                        "chunk_total": len(chunks),
                    },
                    created_at=source_now,
                ))
                source_stats["updated"] += 1
                continue

            entry = KnowledgeEntry(
                title=source_name if idx == 0 else f"{source_name} (part {idx + 1})",
                content=chunk,
                content_hash=content_hash,
                source_type="web_crawl",
                source_url=url,
                file_name=None,
                file_type="html",
                event_name=event_name_base,
                year=None,
                region=source.get("region"),
                importance=5,
                category=source.get("category"),
                tags=source.get("tags", []),
                figures=[],
                keywords=[],
                language="zh-CN",
                source_reliability=7,
                chunk_index=idx,
                chunk_total=len(chunks),
                version=1,
                version_count=1,
                parent_event_id=None,
                status="active",
                is_locked=0,
                created_at=source_now,
                updated_at=source_now,
                last_indexed_at=source_now,
            )
            db.add(entry)
            await db.flush()
            db.add(KnowledgeVersion(
                entry_id=entry.id,
                version=1,
                title=entry.title,
                content=chunk,
                content_hash=content_hash,
                change_summary=f"Initial crawl from {url}",
                change_source="web_crawl",
                operator="crawler",
                snapshot_meta={
                    "source_url": url,
                    "chunk_index": idx,
                    "chunk_total": len(chunks),
                },
                created_at=source_now,
            ))
            await db.flush()
            source_stats["imported"] += 1

        await _set_source_status(
            db,
            CrawlSource,
            source.get("id"),
            status="success",
            crawled_at=source_now,
            imported=source_stats["imported"],
        )
        if not await _commit_session(db, context=f"crawl source {source_name}"):
            stats["sources_failed"] += 1
            stats["failed"] += 1
            await _mark_source_failed(db, CrawlSource, source, source_now)
            return

        for key, value in source_stats.items():
            stats[key] += value

        if source_stats["imported"] > 0:
            today_events.add(event_name_base)

        logger.info(
            f"Crawl source {source_name}: imported={source_stats['imported']}, "
            f"updated={source_stats['updated']}, skipped={source_stats['skipped_duplicates']}"
        )
    except Exception as exc:
        logger.error(f"Failed to process crawl source {source_name}: {exc}")
        await db.rollback()
        stats["sources_failed"] += 1
        stats["failed"] += 1
        await _mark_source_failed(db, CrawlSource, source, source_now)


async def _crawl_and_store_unlocked() -> dict:
    """Crawl all active sources, dedup by event_name+source_url, write new entries to DB."""
    logger.info("Starting knowledge base crawl job...")
    stats = _build_crawl_stats()

    async with _get_session_factory()() as db:
        try:
            await _ensure_default_sources(db)
        except Exception as e:
            logger.warning(f"Failed to seed default crawl sources: {e}")

        await _commit_session(db, context="default crawl source seed")

        sources = await _gather_active_sources(db)
        logger.info(f"Crawl job: {len(sources)} active sources")

        try:
            today_events = await _get_todays_event_names(db, datetime.utcnow())
            stats["todays_unique_count"] = len(today_events)
            logger.info(f"Daily dedup: {len(today_events)} event_names already imported today (UTC)")
        except Exception as e:
            logger.warning(f"Failed to load today's event names, dedup disabled: {e}")
            today_events = set()

        for source in sources:
            stats["sources_processed"] += 1
            await _process_single_source(db, source, today_events, stats)

    logger.info(
        f"Crawl job finished. imported={stats['imported']}, updated={stats['updated']}, "
        f"skipped={stats['skipped_duplicates']}, sources={stats['sources_processed']}, "
        f"failed={stats['sources_failed']}, "
        f"filtered_empty_event_name={stats.get('filtered_empty_event_name', 0)}, "
        f"skipped_daily_duplicate={stats.get('skipped_daily_duplicate', 0)}, "
        f"todays_unique_count={stats.get('todays_unique_count', 0)}"
    )
    return stats


async def crawl_and_store() -> dict:
    """Serialize crawl execution to avoid overlapping jobs and long-lived write locks."""
    if _crawl_execution_lock.locked():
        logger.info("Another crawl job is already running, waiting for the active job to finish")

    async with _crawl_execution_lock:
        return await _crawl_and_store_unlocked()

_crawl_task: Optional[asyncio.Task] = None
_crawl_interval_seconds = 86400  # 1 day


async def start_crawl_scheduler():
    """Start the periodic crawl scheduler. Runs an initial crawl then loops every 24h."""
    global _crawl_task

    try:
        result = await crawl_and_store()
        logger.info(f"Initial crawl result: {result}")
    except Exception as e:
        logger.error(f"Initial crawl failed: {e}")

    async def _periodic_crawl():
        while True:
            try:
                await asyncio.sleep(_crawl_interval_seconds)
                result = await crawl_and_store()
                logger.info(f"Periodic crawl result: {result}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic crawl failed: {e}")

    _crawl_task = asyncio.create_task(_periodic_crawl())
    logger.info("Crawl scheduler started (interval: 24h)")


def stop_crawl_scheduler():
    global _crawl_task
    if _crawl_task is not None:
        _crawl_task.cancel()
        _crawl_task = None



