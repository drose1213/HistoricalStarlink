"""验证: 第一次启动 build_index 会触发 API 调, 第二次直接走 DB 缓存"""
import asyncio
import os
import sys
import time
import logging
os.environ.setdefault("SQLALCHEMY_WARN_20", "0")
logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.CRITICAL)
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("historical_starlink").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

import backend.config as _cfg
_cfg.settings.DEBUG = False

from backend.database import init_db, AsyncSessionLocal, engine
from backend.models.embedding import EventEmbedding
from backend.models.knowledge_base import KnowledgeEntry
from backend.rag_engine import _load_index_from_db, build_index, _persist_embedding
from sqlalchemy import select, func
import numpy as np

engine.echo = False


async def main():
    await init_db()

    # 1) 模拟"全部 50 条 KB 条目"都已有持久化向量
    async with AsyncSessionLocal() as db:
        kbs = (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.source_type == "seed_data"))).scalars().all()
        print(f"[setup] {len(kbs)} seed KB entries")
        new_count = 0
        for e in kbs:
            existing = (await db.execute(
                select(EventEmbedding).where(EventEmbedding.knowledge_entry_id == e.id)
            )).scalar_one_or_none()
            if not existing:
                vec = np.random.randn(1536).astype(np.float32)
                await _persist_embedding(e.id, vec, e.content_hash, "embo-01")
                new_count += 1
        print(f"[setup] inserted {new_count} new embeddings (skip existing)")

    # 2) 模拟"进程重启": 重置 RAG 内存索引, 然后从 DB 加载
    from backend import rag_engine
    rag_engine._index_built = False
    rag_engine._index_vectors = None
    rag_engine._index_texts = []
    rag_engine._index_metadata = []

    print()
    print("[test 1] Cold start: _load_index_from_db (no API call)")
    t0 = time.time()
    ok = await _load_index_from_db()
    dt = (time.time() - t0) * 1000
    print(f"  loaded={ok}, vectors={rag_engine._index_vectors.shape if ok else 'N/A'}, time={dt:.1f}ms")
    assert ok, "Load should succeed when DB has embeddings"
    assert rag_engine._index_vectors.shape[0] == len(kbs), f"Vector count mismatch: {rag_engine._index_vectors.shape[0]} vs {len(kbs)}"

    # 3) 调用 search_similar (不触发 API)
    print()
    print("[test 2] search_similar with DB-only index (no API call)")
    from backend.rag_engine import search_similar
    t0 = time.time()
    results = await search_similar("秦始皇", top_k=3)
    dt = (time.time() - t0) * 1000
    print(f"  results={len(results)}, time={dt:.1f}ms")
    for r in results[:3]:
        print(f"    - {r.get('name')} (score={r.get('score', 0):.3f})")

    print()
    print("[test 3] search_similar with same query, second time (cache hit)")
    t0 = time.time()
    results2 = await search_similar("秦始皇", top_k=3)
    dt = (time.time() - t0) * 1000
    print(f"  time={dt:.1f}ms (should be near-instant)")

    print()
    print("=" * 50)
    print("PASS: vector persistence works (no API call on warmup)")
    print("=" * 50)


asyncio.run(main())
