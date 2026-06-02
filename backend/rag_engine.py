"""
RAG (检索增强生成) 引擎
使用 MiniMax API 进行向量检索和问答生成
支持从数据库知识库加载条目 + 条件检索
"""
import logging
import os
from typing import Optional

import httpx
import numpy as np

from .data.events_data import events_data

logger = logging.getLogger("historical_starlink.rag")

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_EMBEDDING_URL = "https://api.minimax.chat/v1/embeddings"
MINIMAX_CHAT_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

HISTORY_EVENTS = events_data

_query_cache: dict[str, list[float]] = {}
_index_vectors: Optional[np.ndarray] = None
_index_texts: list[str] = []
_index_metadata: list[dict] = []
_index_built = False


def _event_to_text(event: dict) -> str:
    year_str = f"公元前{abs(event['year'])}年" if event["year"] < 0 else f"公元{event['year']}年"
    region_str = "中国" if event["region"] == "china" else "外国"
    causes = "；".join(event.get("causes", []))
    consequences = "；".join(event.get("consequences", []))
    return (
        f"{event['name']}（{year_str}，{region_str}，重要性{event['importance']}/10）：{event['description']}。"
        f"原因：{causes}。影响：{consequences}。"
    )


def _kb_entry_to_text(entry) -> str:
    year_str = ""
    if entry.year is not None:
        year_str = f"公元前{abs(entry.year)}年" if entry.year < 0 else f"公元{entry.year}年"
    region_str = {"china": "中国", "foreign": "外国"}.get(entry.region or "", entry.region or "")
    parts = [f"{entry.title}"]
    if year_str:
        parts[0] += f"（{year_str}"
        if region_str:
            parts[0] += f"，{region_str}"
        parts[0] += "）"
    parts.append(entry.content[:500])
    return "：".join(parts)


async def _get_embedding(texts: list[str]) -> list[list[float]]:
    if not MINIMAX_API_KEY:
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            MINIMAX_EMBEDDING_URL,
            headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
            json={"model": "embo-01", "texts": texts},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("vectors", [])


def _keyword_fallback_scores(query: str, items: list[tuple[str, dict]]) -> list[tuple[int, float]]:
    query_lower = query.lower()
    scored: list[tuple[int, float]] = []
    for idx, (text, meta) in enumerate(items):
        text_lower = text.lower()
        score = 0.0
        name = meta.get("name", meta.get("title", ""))
        if name and (name in query or name.lower() in query_lower):
            score += 5.0
        for q_token in [query, query_lower]:
            if q_token and q_token in text_lower:
                score += 3.0
        tokens = [ch for ch in query_lower if ch.strip()]
        for token in tokens:
            if token in text_lower:
                score += 0.3
        if score > 0:
            scored.append((idx, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


async def build_index(region: Optional[str] = None, category: Optional[str] = None,
                      year_min: Optional[int] = None, year_max: Optional[int] = None) -> dict:
    global _index_vectors, _index_built, _index_texts, _index_metadata

    texts = []
    metadata = []

    for ev in HISTORY_EVENTS:
        if region and ev.get("region") != region:
            continue
        if year_min and ev.get("year", 0) < year_min:
            continue
        if year_max and ev.get("year", 0) > year_max:
            continue
        texts.append(_event_to_text(ev))
        metadata.append({
            "source": "seed_data",
            "id": ev["id"],
            "name": ev["name"],
            "year": ev.get("year"),
            "region": ev.get("region"),
            "importance": ev.get("importance"),
        })

    try:
        from .database import AsyncSessionLocal
        from .models.knowledge_base import KnowledgeEntry
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            conditions = [KnowledgeEntry.status == "active"]
            if region:
                conditions.append(KnowledgeEntry.region == region)
            if category:
                conditions.append(KnowledgeEntry.category == category)
            if year_min is not None:
                conditions.append(KnowledgeEntry.year >= year_min)
            if year_max is not None:
                conditions.append(KnowledgeEntry.year <= year_max)

            stmt = select(KnowledgeEntry).where(*conditions).order_by(KnowledgeEntry.id)
            result = await db.execute(stmt)
            entries = result.scalars().all()

            for entry in entries:
                texts.append(_kb_entry_to_text(entry))
                metadata.append({
                    "source": "knowledge_base",
                    "id": entry.id,
                    "title": entry.title,
                    "name": entry.event_name or entry.title,
                    "year": entry.year,
                    "region": entry.region,
                    "category": entry.category,
                    "tags": entry.tags or [],
                    "importance": entry.importance,
                    "source_type": entry.source_type,
                    "source_url": entry.source_url,
                })

        logger.info(f"Loaded {len(entries)} knowledge base entries for RAG index")
    except Exception as e:
        logger.warning(f"Failed to load knowledge base entries: {e}")

    if not texts:
        _index_built = True
        _index_texts = []
        _index_metadata = []
        _index_vectors = None
        return {"mode": "empty", "count": 0}

    if MINIMAX_API_KEY:
        try:
            batch_size = 16
            all_vectors = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                vectors = await _get_embedding(batch)
                all_vectors.extend(vectors)

            if all_vectors and len(all_vectors) == len(texts):
                _index_vectors = np.array(all_vectors, dtype=np.float32)
                norms = np.linalg.norm(_index_vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1
                _index_vectors = _index_vectors / norms
                _index_built = True
                _index_texts = texts
                _index_metadata = metadata
                logger.info(f"RAG index built with MiniMax embeddings, {len(texts)} entries")
                return {"mode": "embedding", "count": len(texts)}
            logger.warning("MiniMax embedding returned mismatched vectors, falling back to keyword mode")
        except Exception as e:
            logger.warning(f"MiniMax embedding failed: {e}, falling back to keyword mode")

    _index_built = True
    _index_texts = texts
    _index_metadata = metadata
    _index_vectors = None
    logger.info(f"RAG index built with keyword mode, {len(texts)} entries")
    return {"mode": "keyword", "count": len(texts)}


async def search_similar(query: str, top_k: int = 5,
                         region: Optional[str] = None,
                         category: Optional[str] = None,
                         year_min: Optional[int] = None,
                         year_max: Optional[int] = None) -> list[dict]:
    if region or category or year_min is not None or year_max is not None:
        await build_index(region=region, category=category, year_min=year_min, year_max=year_max)

    if not _index_built:
        await build_index()

    if _index_vectors is not None and len(_index_texts) > 0:
        return await _embedding_search(query, top_k)

    if _index_texts:
        return _keyword_search(query, top_k)

    return _keyword_search_events_only(query, top_k)


async def _embedding_search(query: str, top_k: int) -> list[dict]:
    if query in _query_cache:
        query_vec = np.array(_query_cache[query], dtype=np.float32)
    else:
        vectors = await _get_embedding([query])
        if not vectors:
            return _keyword_search(query, top_k)
        query_vec = np.array(vectors[0], dtype=np.float32)
        _query_cache[query] = vectors[0]

    query_norm = np.linalg.norm(query_vec)
    if query_norm > 0:
        query_vec = query_vec / query_norm

    similarities = _index_vectors @ query_vec
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        idx = int(idx)
        meta = _index_metadata[idx]
        results.append({
            "source": meta.get("source", "unknown"),
            "id": meta.get("id"),
            "name": meta.get("name", meta.get("title", "")),
            "title": meta.get("title", ""),
            "year": meta.get("year"),
            "region": meta.get("region"),
            "category": meta.get("category"),
            "importance": meta.get("importance"),
            "tags": meta.get("tags", []),
            "score": round(float(similarities[idx]), 4),
        })
    return results


def _keyword_search(query: str, top_k: int) -> list[dict]:
    items = [(text, meta) for text, meta in zip(_index_texts, _index_metadata)]
    scored = _keyword_fallback_scores(query, items)
    results = []
    for idx, score in scored[:top_k]:
        meta = _index_metadata[idx]
        results.append({
            "source": meta.get("source", "unknown"),
            "id": meta.get("id"),
            "name": meta.get("name", meta.get("title", "")),
            "title": meta.get("title", ""),
            "year": meta.get("year"),
            "region": meta.get("region"),
            "category": meta.get("category"),
            "importance": meta.get("importance"),
            "tags": meta.get("tags", []),
            "score": round(score, 4),
        })
    if not results:
        for idx, meta in enumerate(_index_metadata[:top_k]):
            results.append({
                "source": meta.get("source", "unknown"),
                "id": meta.get("id"),
                "name": meta.get("name", meta.get("title", "")),
                "title": meta.get("title", ""),
                "year": meta.get("year"),
                "region": meta.get("region"),
                "category": meta.get("category"),
                "importance": meta.get("importance"),
                "tags": meta.get("tags", []),
                "score": 0.0,
            })
    return results


def _keyword_search_events_only(query: str, top_k: int) -> list[dict]:
    items = [(_event_to_text(ev), {"id": ev["id"], "name": ev["name"], "year": ev.get("year"),
                                    "region": ev.get("region"), "importance": ev.get("importance"),
                                    "source": "seed_data"})
             for ev in HISTORY_EVENTS]
    scored = _keyword_fallback_scores(query, items)
    results = []
    for idx, score in scored[:top_k]:
        meta = items[idx][1]
        results.append({**meta, "score": round(score, 4)})
    if not results:
        for ev in HISTORY_EVENTS[:top_k]:
            results.append({
                "source": "seed_data", "id": ev["id"], "name": ev["name"],
                "year": ev.get("year"), "region": ev.get("region"),
                "importance": ev.get("importance"), "score": 0.0,
            })
    return results


async def generate_answer(query: str, context_events: list[dict]) -> str:
    if not MINIMAX_API_KEY:
        return _generate_fallback_answer(query, context_events)

    context_parts = []
    for item in context_events:
        name = item.get("name", item.get("title", "未知"))
        year = item.get("year")
        year_str = ""
        if year is not None:
            year_str = f"公元前{abs(year)}年" if year < 0 else f"公元{year}年"
        desc = item.get("description", item.get("content", ""))
        context_parts.append(f"【{name}】（{year_str}）{desc}")
    context_text = "\n".join(context_parts)

    system_prompt = (
        "你是「历史星链探索」的历史知识助手。请基于提供的历史事件资料回答用户的问题。"
        "回答要求：准确、有深度、条理清晰，适当分析事件之间的因果关系和历史意义。"
        "如果提供的资料不足以回答问题，请坦诚说明并基于已有资料给出最相关的分析。"
        "回答使用中文，长度控制在300字以内。"
    )

    user_message = f"以下是相关的历史事件资料：\n\n{context_text}\n\n用户问题：{query}"

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                MINIMAX_CHAT_URL,
                headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
                json={
                    "model": "MiniMax-M2.1",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"MiniMax chat API failed: {e}")
        return _generate_fallback_answer(query, context_events)


def _generate_fallback_answer(query: str, context_events: list[dict]) -> str:
    if not context_events:
        return f"关于「{query}」，目前知识库中没有找到直接相关的历史事件。建议尝试更具体的关键词搜索。"

    parts = [f"关于「{query}」，以下是相关历史事件的分析：\n"]
    for item in context_events:
        name = item.get("name", item.get("title", "未知"))
        year = item.get("year")
        year_str = ""
        if year is not None:
            year_str = f"公元前{abs(year)}年" if year < 0 else f"公元{year}年"
        desc = item.get("description", item.get("content", ""))[:200]
        parts.append(f"▸ {name}（{year_str}）：{desc}")
    parts.append(f"\n以上为知识库中检索到的 {len(context_events)} 个相关事件。")
    parts.append("（提示：未配置 MINIMAX_API_KEY，当前为关键词匹配模式，如需 AI 生成回答请配置 API Key。）")
    return "\n".join(parts)


async def full_rag_query(query: str, top_k: int = 5,
                         region: Optional[str] = None,
                         category: Optional[str] = None,
                         year_min: Optional[int] = None,
                         year_max: Optional[int] = None) -> dict:
    search_results = await search_similar(query, top_k=top_k,
                                          region=region, category=category,
                                          year_min=year_min, year_max=year_max)
    answer = await generate_answer(query, search_results)
    sources = []
    for item in search_results:
        sources.append({
            "id": item.get("id"),
            "name": item.get("name", item.get("title", "")),
            "year": item.get("year"),
            "region": item.get("region"),
            "category": item.get("category"),
            "importance": item.get("importance"),
            "tags": item.get("tags", []),
            "score": item.get("score", 0),
            "source": item.get("source", "unknown"),
        })
    return {"answer": answer, "sources": sources}
