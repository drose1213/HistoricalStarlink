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
from datetime import datetime, timedelta
from typing import Optional
from html.parser import HTMLParser

import httpx

logger = logging.getLogger("historical_starlink.crawler")


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
        "url": "https://zh.wikipedia.org/wiki/%E4%BA%BA%E7%B1%BB%E7%99%BB%E6%9C%88",
        "name": "人类登月 - 维基百科",
        "description": "1969 年阿波罗 11 号登月任务",
        "category": "科技",
        "region": "foreign",
        "tags": ["航天", "美国", "登月"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E5%8D%97%E5%8D%97%E5%8C%97%E5%8C%97%E5%92%8C%E8%A7%84",
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
        "url": "https://zh.wikipedia.org/wiki/%E7%BB%8F%E6%B5%8E%E5%A4%A7%E9%99%A8%E5%9D%A1",
        "name": "经济大萧条 - 维基百科",
        "description": "1929-1933 年全球性经济危机",
        "category": "经济",
        "region": "foreign",
        "tags": ["危机", "美国", "全球"],
    },
    {
        "url": "https://zh.wikipedia.org/wiki/%E5%85%A8%E6%B0%91%E4%B8%BB%E4%B8%BB%E4%B9%89%E9%9D%A9%E5%91%BD",
        "name": "民主主义革命 - 维基百科",
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
        logger.warning(f"Failed to crawl {url}: {e}")
        return None


async def _ensure_default_sources(db) -> int:
    """Ensure recommended sources are present in the CrawlSource table. Returns count inserted."""
    from .models.knowledge_base import CrawlSource
    from sqlalchemy import select

    inserted = 0
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
    if inserted:
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


async def crawl_and_store() -> dict:
    """Crawl all active sources, dedup by event_name+source_url, write new entries to DB."""
    from .database import AsyncSessionLocal
    from .models.knowledge_base import KnowledgeEntry, KnowledgeVersion, CrawlSource
    from sqlalchemy import select, update

    logger.info("Starting knowledge base crawl job...")
    stats = {
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

    async with AsyncSessionLocal() as db:
        try:
            await _ensure_default_sources(db)
        except Exception as e:
            logger.warning(f"Failed to seed default crawl sources: {e}")

        try:
            await db.commit()
        except Exception:
            await db.rollback()

        sources = await _gather_active_sources(db)
        logger.info(f"Crawl job: {len(sources)} active sources")

        # 一次性加载今日已存在的 event_name 集合, 用于每日去重
        try:
            today_events = await _get_todays_event_names(db, datetime.utcnow())
            stats["todays_unique_count"] = len(today_events)
            logger.info(f"Daily dedup: {len(today_events)} event_names already imported today (UTC)")
        except Exception as e:
            logger.warning(f"Failed to load today's event names, dedup disabled: {e}")
            today_events = set()

        for source in sources:
            url = source["url"]
            source_name = source["name"]
            stats["sources_processed"] += 1

            html = await crawl_page(url)
            if not html:
                stats["sources_failed"] += 1
                stats["failed"] += 1
                if source.get("id") is not None:
                    try:
                        await db.execute(
                            update(CrawlSource)
                            .where(CrawlSource.id == source["id"])
                            .values(last_status="failed", last_crawled_at=datetime.utcnow(), last_imported=0)
                        )
                    except Exception:
                        pass
                continue

            text = extract_text_from_html(html)
            if len(text) < 100:
                stats["sources_failed"] += 1
                stats["skipped_short"] += 1
                if source.get("id") is not None:
                    try:
                        await db.execute(
                            update(CrawlSource)
                            .where(CrawlSource.id == source["id"])
                            .values(last_status="failed", last_crawled_at=datetime.utcnow(), last_imported=0)
                        )
                    except Exception:
                        pass
                continue

            chunks = chunk_text(text)
            now = datetime.utcnow()
            event_name_base = source_name.split(" - ")[0] if " - " in source_name else source_name
            # event_name_base 为空或仅含空白字符时, 整批 chunk 跳过写入, 但仍计入 sources_processed
            if not event_name_base or not event_name_base.strip():
                logger.warning(
                    f"Skip crawl source due to empty event_name_base: source_name={source_name!r}, "
                    f"url={url!r}, chunks={len(chunks)}"
                )
                stats["filtered_empty_event_name"] = stats.get("filtered_empty_event_name", 0) + len(chunks)
                stats["sources_processed"] += 0  # 仍计入 source
                if source.get("id") is not None:
                    try:
                        await db.execute(
                            update(CrawlSource)
                            .where(CrawlSource.id == source["id"])
                            .values(last_status="failed", last_crawled_at=now, last_imported=0)
                        )
                    except Exception:
                        pass
                continue
            imported_this_source = 0
            skipped_this_source = 0
            updated_this_source = 0

            for idx, chunk in enumerate(chunks):
                # 每日去重: 同一 event_name 当日已存在则跳过整个 chunk
                if event_name_base in today_events:
                    stats["skipped_daily_duplicate"] += 1
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
                        skipped_this_source += 1
                        stats["skipped_duplicates"] += 1
                        continue
                    # Content changed -> version bump
                    found.content = chunk
                    found.content_hash = content_hash
                    found.version += 1
                    found.version_count = (found.version_count or 1) + 1
                    found.updated_at = now
                    found.last_indexed_at = now
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
                        created_at=now,
                    ))
                    updated_this_source += 1
                    stats["updated"] += 1
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
                    created_at=now,
                    updated_at=now,
                    last_indexed_at=now,
                )
                db.add(entry)
                try:
                    await db.flush()
                except Exception:
                    pass
                try:
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
                        created_at=now,
                    ))
                    await db.flush()
                except Exception:
                    pass
                imported_this_source += 1
                stats["imported"] += 1

            if source.get("id") is not None:
                try:
                    await db.execute(
                        update(CrawlSource)
                        .where(CrawlSource.id == source["id"])
                        .values(
                            last_status="success",
                            last_crawled_at=now,
                            last_imported=imported_this_source,
                        )
                    )
                except Exception:
                    pass

            logger.info(
                f"Crawl source {source_name}: imported={imported_this_source}, "
                f"updated={updated_this_source}, skipped={skipped_this_source}"
            )

        try:
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to commit crawled data: {e}")
            await db.rollback()

    logger.info(
        f"Crawl job finished. imported={stats['imported']}, updated={stats['updated']}, "
        f"skipped={stats['skipped_duplicates']}, sources={stats['sources_processed']}, "
        f"failed={stats['sources_failed']}, "
        f"filtered_empty_event_name={stats.get('filtered_empty_event_name', 0)}, "
        f"skipped_daily_duplicate={stats.get('skipped_daily_duplicate', 0)}, "
        f"todays_unique_count={stats.get('todays_unique_count', 0)}"
    )
    return stats


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
