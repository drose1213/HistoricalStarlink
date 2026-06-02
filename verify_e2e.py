"""端到端验证: 直接重定向到文件以避免 SQLAlchemy echo 刷屏"""
import asyncio
import logging
import os
import sys

# 在 import backend.database 之前, 强制关闭 SQLAlchemy echo
os.environ.setdefault("SQLALCHEMY_WARN_20", "0")
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)

# 必须在 import backend 之前 patch settings.DEBUG, 否则 engine echo=True 不可逆
import backend.config as _cfg
_cfg.settings.DEBUG = False

from backend.database import init_db, AsyncSessionLocal, engine
from backend.models.embedding import EventEmbedding
from backend.models.knowledge_base import KnowledgeEntry
from backend.models.event import HistoryEvent
from backend.models.exploration_record import ExplorationRecord
from backend.rag_engine import _load_index_from_db, _persist_embedding, _get_existing_embedding_map
from sqlalchemy import select, func
import numpy as np

# 即使 settings.DEBUG 已被读取, 也要再设一次 engine.echo
engine.echo = False


async def main():
    print("=" * 60)
    print("Phase 1: init_db()")
    print("=" * 60)
    await init_db()
    print("  done")

    async with AsyncSessionLocal() as db:
        cnt_emb = (await db.execute(select(func.count()).select_from(EventEmbedding))).scalar() or 0
        cnt_kb = (await db.execute(select(func.count()).select_from(KnowledgeEntry))).scalar() or 0
        cnt_ev = (await db.execute(select(func.count()).select_from(HistoryEvent))).scalar() or 0
        cnt_ex = (await db.execute(select(func.count()).select_from(ExplorationRecord))).scalar() or 0
        print(f"  history_events = {cnt_ev} (seed=50)")
        print(f"  knowledge_entries = {cnt_kb}")
        print(f"  exploration_records = {cnt_ex}")
        print(f"  event_embeddings = {cnt_emb}")

    if cnt_kb == 0:
        print("\nNo KB entries; will seed via lifespan-like flow.")
        # 模拟 _seed_knowledge_base 的行为: 直接 import data.events_data
        from backend.data.events_data import events_data
        async with AsyncSessionLocal() as db:
            from datetime import datetime
            now = datetime.utcnow()
            for ev in events_data:
                ev_name = ev.get("name")
                if not ev_name or not ev_name.strip():
                    continue
                text = f"{ev_name}（测试）"
                content_hash = KnowledgeEntry.compute_hash(text)
                e = KnowledgeEntry(
                    title=ev_name, content=text, content_hash=content_hash,
                    source_type="seed_data", event_name=ev_name,
                    year=ev.get("year"), region=ev.get("region"),
                    importance=ev.get("importance"),
                    category=ev.get("category") or "综合",
                    tags=ev.get("tags", []),
                    figures=ev.get("figures", []),
                    chunk_index=0, chunk_total=1, version=1, version_count=1,
                    status="active", is_locked=0,
                    created_at=now, updated_at=now, last_indexed_at=now,
                )
                db.add(e)
            await db.commit()
            cnt_kb = (await db.execute(select(func.count()).select_from(KnowledgeEntry))).scalar() or 0
            print(f"  after seed, knowledge_entries = {cnt_kb}")

    print("\n" + "=" * 60)
    print("Phase 2: _persist_embedding")
    print("=" * 60)
    async with AsyncSessionLocal() as db:
        first = (await db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.source_type == "seed_data").limit(1)
        )).scalar_one_or_none() or (await db.execute(select(KnowledgeEntry).limit(1))).scalar_one()

        vec = np.random.randn(1536).astype(np.float32)
        ok = await _persist_embedding(first.id, vec, first.content_hash, "embo-01")
        print(f"  persist(entry={first.id}, hash={first.content_hash[:8]}...) -> {ok}")

        # 重复相同 hash 不应变更
        ok2 = await _persist_embedding(first.id, vec, first.content_hash, "embo-01")
        print(f"  persist duplicate -> {ok2} (skip path)")

        cnt_emb_after = (await db.execute(select(func.count()).select_from(EventEmbedding))).scalar() or 0
        print(f"  event_embeddings rows = {cnt_emb_after} (expect 1)")

    print("\n" + "=" * 60)
    print("Phase 3: _load_index_from_db")
    print("=" * 60)
    loaded = await _load_index_from_db()
    print(f"  _load_index_from_db -> {loaded}")
    if loaded:
        from backend import rag_engine
        print(f"  _index_vectors.shape = {rag_engine._index_vectors.shape}")
        print(f"  _index_texts count = {len(rag_engine._index_texts)}")
        print(f"  _index_metadata count = {len(rag_engine._index_metadata)}")

    print("\n" + "=" * 60)
    print("Phase 4: _get_existing_embedding_map")
    print("=" * 60)
    emap = await _get_existing_embedding_map()
    print(f"  entries = {len(emap)}, sample keys = {list(emap.keys())[:3]}")
    for k, (ch, mn) in list(emap.items())[:2]:
        print(f"    entry {k}: model={mn}, hash={ch[:8]}...")

    print("\n" + "=" * 60)
    print("Phase 5: Router registration")
    print("=" * 60)
    from backend.main import app
    routes = []
    for r in app.routes:
        if hasattr(r, "methods") and hasattr(r, "path"):
            for m in r.methods:
                if m != "HEAD":
                    routes.append((m, r.path))
    new_eps = [r for r in routes if "/api/events/home" in r[1] or "/api/rag/search-hybrid" in r[1]]
    print("  New endpoints:")
    for m, p in new_eps:
        print(f"    {m:6s} {p}")

    home_idx = next((i for i, r in enumerate(routes) if "/api/events/home" in r[1] and r[0] == "GET"), -1)
    widx = next((i for i, r in enumerate(routes) if "/api/events/{event_id}" in r[1]), -1)
    if home_idx >= 0 and widx >= 0:
        verdict = "OK" if home_idx < widx else "BAD"
        print(f"  [{verdict}] /api/events/home (idx={home_idx}) vs /api/events/{{event_id}} (idx={widx})")

    # 验证 _store_chunks 空 event_name 过滤
    print("\n" + "=" * 60)
    print("Phase 6: _store_chunks empty event_name guard")
    print("=" * 60)
    from backend.routers.rag import _store_chunks
    class _DummySession:
        async def commit(self): pass
        async def flush(self): pass
        async def execute(self, *a, **k):
            class _R:
                def scalar_one_or_none(self_): return None
            return _R()
    res = await _store_chunks(_DummySession(), title="空测试", content="正文", event_name="", source_type="test")
    print(f"  empty event_name -> {res}")
    assert res.get("filtered_reason") == "empty_event_name", f"Expected filtered_reason, got {res}"
    res2 = await _store_chunks(_DummySession(), title="空白", content="正文", event_name="   ", source_type="test")
    print(f"  whitespace event_name -> {res2}")
    assert res2.get("filtered_reason") == "empty_event_name"
    print("  PASS")

    print("\n" + "=" * 60)
    print("ALL CHECKS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
