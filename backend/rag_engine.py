"""
RAG (检索增强生成) 引擎
使用 MiniMax API 进行向量检索和问答生成
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


def _keyword_fallback_scores(query: str, events: list[dict]) -> list[tuple[int, float]]:
    query_lower = query.lower()
    scored: list[tuple[int, float]] = []
    for idx, event in enumerate(events):
        text = _event_to_text(event).lower()
        score = 0.0
        if event["name"] in query or event["name"].lower() in query_lower:
            score += 5.0
        for cause in event.get("causes", []):
            if any(kw in query_lower for kw in cause.split("，")):
                score += 1.0
        for consequence in event.get("consequences", []):
            if any(kw in query_lower for kw in consequence.split("，")):
                score += 1.0
        tokens = [ch for ch in query_lower if len(ch) > 1]
        for token in tokens:
            if token in text:
                score += 0.3
        if score > 0:
            scored.append((idx, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


async def build_index() -> dict:
    global _index_vectors, _index_built

    texts = [_event_to_text(e) for e in HISTORY_EVENTS]

    if MINIMAX_API_KEY:
        try:
            vectors = await _get_embedding(texts)
            if vectors and len(vectors) == len(texts):
                _index_vectors = np.array(vectors, dtype=np.float32)
                norms = np.linalg.norm(_index_vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1
                _index_vectors = _index_vectors / norms
                _index_built = True
                logger.info(f"RAG index built with MiniMax embeddings, {len(texts)} events")
                return {"mode": "embedding", "count": len(texts)}
            logger.warning("MiniMax embedding returned mismatched vectors, falling back to keyword mode")
        except Exception as e:
            logger.warning(f"MiniMax embedding failed: {e}, falling back to keyword mode")

    _index_built = True
    logger.info(f"RAG index built with keyword mode, {len(texts)} events")
    return {"mode": "keyword", "count": len(texts)}


async def search_similar(query: str, top_k: int = 5) -> list[dict]:
    if not _index_built:
        await build_index()

    if _index_vectors is not None:
        return await _embedding_search(query, top_k)

    return _keyword_search(query, top_k)


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
        event = HISTORY_EVENTS[int(idx)]
        results.append({
            "event": event,
            "score": round(float(similarities[idx]), 4),
        })
    return results


def _keyword_search(query: str, top_k: int) -> list[dict]:
    scored = _keyword_fallback_scores(query, HISTORY_EVENTS)
    results = []
    for idx, score in scored[:top_k]:
        event = HISTORY_EVENTS[idx]
        results.append({
            "event": event,
            "score": round(score, 4),
        })
    if not results:
        for event in HISTORY_EVENTS[:top_k]:
            results.append({"event": event, "score": 0.0})
    return results


async def generate_answer(query: str, context_events: list[dict]) -> str:
    if not MINIMAX_API_KEY:
        return _generate_fallback_answer(query, context_events)

    context_parts = []
    for item in context_events:
        ev = item["event"]
        year_str = f"公元前{abs(ev['year'])}年" if ev["year"] < 0 else f"公元{ev['year']}年"
        context_parts.append(
            f"【{ev['name']}】（{year_str}）{ev['description']}。"
            f"原因：{'；'.join(ev.get('causes', []))}。影响：{'；'.join(ev.get('consequences', []))}。"
        )
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
            content = data["choices"][0]["message"]["content"]
            return content
    except Exception as e:
        logger.error(f"MiniMax chat API failed: {e}")
        return _generate_fallback_answer(query, context_events)


def _generate_fallback_answer(query: str, context_events: list[dict]) -> str:
    if not context_events:
        return f"关于「{query}」，目前知识库中没有找到直接相关的历史事件。建议尝试更具体的关键词搜索。"

    parts = [f"关于「{query}」，以下是相关历史事件的分析：\n"]
    for item in context_events:
        ev = item["event"]
        year_str = f"公元前{abs(ev['year'])}年" if ev["year"] < 0 else f"公元{ev['year']}年"
        parts.append(f"▸ {ev['name']}（{year_str}）：{ev['description']}")
    parts.append(f"\n以上为知识库中检索到的 {len(context_events)} 个相关事件。")
    parts.append("（提示：未配置 MINIMAX_API_KEY，当前为关键词匹配模式，如需 AI 生成回答请配置 API Key。）")
    return "\n".join(parts)


async def full_rag_query(query: str, top_k: int = 5) -> dict:
    search_results = await search_similar(query, top_k=top_k)
    answer = await generate_answer(query, search_results)
    sources = []
    for item in search_results:
        ev = item["event"]
        sources.append({
            "id": ev["id"],
            "name": ev["name"],
            "year": ev["year"],
            "region": ev["region"],
            "importance": ev["importance"],
            "description": ev["description"],
            "score": item["score"],
        })
    return {"answer": answer, "sources": sources}
