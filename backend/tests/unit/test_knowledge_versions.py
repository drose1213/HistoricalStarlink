"""Knowledge base versioning tests."""

import pytest
from sqlalchemy import select

from backend.models.knowledge_base import KnowledgeEntry, KnowledgeVersion


@pytest.mark.unit
@pytest.mark.asyncio
async def test_advance_entry_version_uses_existing_history_max(db_session):
    from backend.knowledge_versions import advance_entry_version

    entry = KnowledgeEntry(
        title="Industrial Revolution",
        content="Initial content",
        content_hash=KnowledgeEntry.compute_hash("Initial content"),
        source_type="web_crawl",
        source_url="https://example.com/industrial",
        event_name="Industrial Revolution",
        chunk_index=0,
        chunk_total=1,
        version=1,
        version_count=1,
        status="active",
    )
    db_session.add(entry)
    await db_session.flush()
    db_session.add_all([
        KnowledgeVersion(
            entry_id=entry.id,
            version=1,
            title=entry.title,
            content=entry.content,
            content_hash=entry.content_hash,
        ),
        KnowledgeVersion(
            entry_id=entry.id,
            version=2,
            title=entry.title,
            content="Previous update",
            content_hash=KnowledgeEntry.compute_hash("Previous update"),
        ),
    ])
    await db_session.flush()

    next_version = await advance_entry_version(db_session, entry)

    assert next_version == 3
    assert entry.version == 3
    assert entry.version_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_store_chunks_update_uses_unique_version_from_history(db_session):
    from backend.routers.rag import _store_chunks

    source_url = "https://example.com/silk-road"
    entry = KnowledgeEntry(
        title="Silk Road",
        content="Initial content",
        content_hash=KnowledgeEntry.compute_hash("Initial content"),
        source_type="web_crawl",
        source_url=source_url,
        event_name="Silk Road",
        category="trade",
        chunk_index=0,
        chunk_total=1,
        version=1,
        version_count=1,
        status="active",
    )
    db_session.add(entry)
    await db_session.flush()
    db_session.add(KnowledgeVersion(
        entry_id=entry.id,
        version=1,
        title=entry.title,
        content=entry.content,
        content_hash=entry.content_hash,
    ))
    db_session.add(KnowledgeVersion(
        entry_id=entry.id,
        version=2,
        title=entry.title,
        content="Previous update",
        content_hash=KnowledgeEntry.compute_hash("Previous update"),
    ))
    await db_session.flush()

    result = await _store_chunks(
        db_session,
        title="Silk Road",
        content="Updated content",
        source_type="web_crawl",
        source_url=source_url,
        event_name="Silk Road",
        category="trade",
        change_source="web_crawl",
    )
    await db_session.flush()

    assert result["updated"] == 1
    assert entry.version == 3
    version_rows = (
        await db_session.execute(
            select(KnowledgeVersion)
            .where(KnowledgeVersion.entry_id == entry.id)
            .order_by(KnowledgeVersion.version)
        )
    ).scalars().all()
    assert [row.version for row in version_rows] == [1, 2, 3]
