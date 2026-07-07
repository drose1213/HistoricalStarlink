"""Shared helpers for knowledge entry version bookkeeping."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models.knowledge_base import KnowledgeEntry, KnowledgeVersion


async def advance_entry_version(db: AsyncSession, entry: KnowledgeEntry) -> int:
    """Advance an entry to the next version that is free in version history."""
    if entry.id is None:
        entry.version = max(int(entry.version or 0), 1)
        entry.version_count = max(int(entry.version_count or 0), entry.version)
        return entry.version

    result = await db.execute(
        select(func.max(KnowledgeVersion.version)).where(KnowledgeVersion.entry_id == entry.id)
    )
    history_max = int(result.scalar() or 0)
    next_version = max(int(entry.version or 0), history_max) + 1
    entry.version = next_version
    entry.version_count = max(int(entry.version_count or 0), history_max) + 1
    return next_version
