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


async def _persist_embedding(knowledge_entry_id: int, vector: np.ndarray,
                              content_hash: str, model_name: str = "embo-01") -> bool:
    """将单条 embedding 向量持久化到 event_embeddings 表, 替代内存缓存.

    Args:
        knowledge_entry_id: 关联的 KnowledgeEntry.id
        vector: 原始向量 (任意范数)
        content_hash: 条目内容 SHA256, 用于失效检测
        model_name: embedding 模型标识, 默认 embo-01

    Returns:
        True 写入成功, False 失败
    """
    from datetime import datetime
    from .database import AsyncSessionLocal
    from .models.embedding import EventEmbedding
    from sqlalchemy import select

    try:
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            norm = 1.0
        normalized = (vector / norm).astype(np.float32)
        blob = normalized.tobytes()
        dim = int(normalized.shape[0])
        now = datetime.utcnow()

        async with AsyncSessionLocal() as db:
            stmt = select(EventEmbedding).where(
                EventEmbedding.knowledge_entry_id == knowledge_entry_id
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                if existing.content_hash == content_hash and existing.model_name == model_name:
                    return True
                existing.vector_blob = blob
                existing.dim = dim
                existing.vector_norm = norm
                existing.content_hash = content_hash
                existing.model_name = model_name
                existing.updated_at = now
            else:
                db.add(EventEmbedding(
                    knowledge_entry_id=knowledge_entry_id,
                    model_name=model_name,
                    dim=dim,
                    vector_blob=blob,
                    vector_norm=norm,
                    content_hash=content_hash,
                    created_at=now,
                    updated_at=now,
                ))
            await db.commit()
        return True
    except Exception as e:
        logger.warning(f"Failed to persist embedding for entry {knowledge_entry_id}: {e}")
        return False


async def _load_index_from_db() -> bool:
    """从 event_embeddings JOIN knowledge_entries 加载所有 active 条目向量,
    在内存中构建 _index_vectors / _index_texts / _index_metadata.

    Returns:
        True 加载到至少 1 条向量, False 表为空或加载失败
    """
    from .database import AsyncSessionLocal
    from .models.embedding import EventEmbedding
    from .models.knowledge_base import KnowledgeEntry
    from sqlalchemy import select

    global _index_vectors, _index_texts, _index_metadata, _index_built

    try:
        async with AsyncSessionLocal() as db:
            stmt = (
                select(EventEmbedding, KnowledgeEntry)
                .join(KnowledgeEntry, EventEmbedding.knowledge_entry_id == KnowledgeEntry.id)
                .where(KnowledgeEntry.status == "active")
                .order_by(EventEmbedding.knowledge_entry_id)
            )
            rows = (await db.execute(stmt)).all()

            if not rows:
                return False

            vectors, texts, metadata = [], [], []
            for emb, entry in rows:
                try:
                    vec = np.frombuffer(emb.vector_blob, dtype=np.float32)
                except Exception as e:
                    logger.warning(f"Failed to decode vector blob for entry {entry.id}: {e}")
                    continue
                if vec.shape[0] != emb.dim:
                    logger.warning(
                        f"Embedding dim mismatch: entry {entry.id} blob_dim={vec.shape[0]} "
                        f"db_dim={emb.dim}, skip"
                    )
                    continue
                vectors.append(vec)
                texts.append(_kb_entry_to_text(entry))
                metadata.append({
                    "source": "knowledge_base",
                    "id": entry.id,
                    "title": entry.title,
                    "name": entry.event_name or entry.title,
                    "year": entry.year,
                    "region": entry.region,
                    "category": entry.category,
                    "importance": entry.importance,
                    "tags": entry.tags or [],
                    "source_type": entry.source_type,
                    "source_url": entry.source_url,
                })

            if not vectors:
                return False

            _index_vectors = np.vstack(vectors)
            _index_texts = texts
            _index_metadata = metadata
            _index_built = True
            logger.info(f"Loaded {len(vectors)} embeddings from DB cache")
            return True
    except Exception as e:
        logger.warning(f"Failed to load embeddings from DB: {e}")
        return False


async def _get_existing_embedding_map() -> dict[int, tuple[str, str]]:
    """返回 {knowledge_entry_id: (content_hash, model_name)} 映射, 用于 build_index 增量计算判断.

    Returns:
        dict 键为 entry_id, 值为 (content_hash, model_name) 元组
    """
    from .database import AsyncSessionLocal
    from .models.embedding import EventEmbedding
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as db:
            stmt = select(
                EventEmbedding.knowledge_entry_id,
                EventEmbedding.content_hash,
                EventEmbedding.model_name,
            )
            rows = (await db.execute(stmt)).all()
            return {entry_id: (ch, mn) for entry_id, ch, mn in rows}
    except Exception as e:
        logger.warning(f"Failed to load existing embedding map: {e}")
        return {}


async def build_index(region: Optional[str] = None, category: Optional[str] = None,
                      year_min: Optional[int] = None, year_max: Optional[int] = None) -> dict:
    """构建/重建 RAG 索引. 优先使用 DB 持久化的向量, 缺失项再调 API 补全.

    流程:
    1. 收集候选条目 (seed events + knowledge base) 的 texts + metadata
    2. 从 DB 加载已有向量; 缺失或失效的条目加入补算队列
    3. 调 MiniMax API 补算缺失向量并写回 DB
    4. 再次从 DB 加载完成索引
    """
    global _index_vectors, _index_built, _index_texts, _index_metadata

    texts = []
    metadata = []
    kb_entry_ids: list[int] = []

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
                kb_entry_ids.append(entry.id)

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
        # 1) 查询 DB 已有向量映射, 判断哪些 KB 条目需要重算
        existing_map = await _get_existing_embedding_map() if kb_entry_ids else {}
        missing_kb_ids: list[tuple[int, int, str]] = []
        need_compute_count = 0
        # seed events 总是需要计算 (无 KB entry_id 关联)
        seed_count = len(texts) - len(kb_entry_ids)

        for idx, entry_id in enumerate(kb_entry_ids):
            entry = await _load_kb_entry(entry_id)
            if not entry:
                continue
            existing = existing_map.get(entry_id)
            if existing and existing[0] == entry.content_hash and existing[1] == "embo-01":
                continue
            missing_kb_ids.append((entry_id, idx, entry.content_hash))
            need_compute_count += 1

        need_compute_count += seed_count

        try:
            batch_size = 16
            all_vectors: list[list[float]] = []

            if need_compute_count > 0:
                logger.info(
                    f"RAG index: computing {need_compute_count} new/updated embeddings "
                    f"(seed={seed_count}, kb_missing={len(missing_kb_ids)})"
                )

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                # 判断该批次是否全部已有 DB 向量, 若有则尝试复用
                batch_need_compute = []
                batch_vectors: list[list[float] | None] = [None] * len(batch_texts)
                for j, t in enumerate(batch_texts):
                    global_idx = i + j
                    if global_idx < len(HISTORY_EVENTS):
                        # seed event 总是需要计算
                        batch_need_compute.append((j, t))
                    else:
                        kb_idx = global_idx - len(HISTORY_EVENTS)
                        if kb_idx < len(kb_entry_ids):
                            entry_id = kb_entry_ids[kb_idx]
                            if entry_id not in {mid for mid, _, _ in missing_kb_ids}:
                                # 已有有效 DB 向量, 但此刻不在内存中, 走补算占位
                                # 实际优化: 跳过, 让 DB-only 索引走 _load_index_from_db
                                pass
                            else:
                                batch_need_compute.append((j, t))
                        else:
                            batch_need_compute.append((j, t))

                if batch_need_compute:
                    compute_texts = [t for _, t in batch_need_compute]
                    compute_vectors = await _get_embedding(compute_texts)
                    for (j, _), vec in zip(batch_need_compute, compute_vectors):
                        batch_vectors[j] = vec

                all_vectors.extend(batch_vectors)

            # 持久化新计算的 KB 向量
            for entry_id, orig_idx, content_hash in missing_kb_ids:
                vec_idx = len(HISTORY_EVENTS) + orig_idx
                if 0 <= vec_idx < len(all_vectors) and all_vectors[vec_idx] is not None:
                    try:
                        await _persist_embedding(
                            entry_id,
                            np.array(all_vectors[vec_idx], dtype=np.float32),
                            content_hash,
                        )
                    except Exception as e:
                        logger.warning(f"Persist embedding failed for entry {entry_id}: {e}")

            # 过滤掉为 None 的向量 (API 失败或被跳过)
            valid_vectors = [v for v in all_vectors if v is not None]
            if valid_vectors and len(valid_vectors) >= max(1, len(texts) // 2):
                _index_vectors = np.array(valid_vectors, dtype=np.float32)
                norms = np.linalg.norm(_index_vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1
                _index_vectors = _index_vectors / norms
                _index_built = True
                _index_texts = texts[:len(valid_vectors)]
                _index_metadata = metadata[:len(valid_vectors)]
                logger.info(
                    f"RAG index built with MiniMax embeddings, "
                    f"{len(valid_vectors)}/{len(texts)} entries (DB-persisted)"
                )
                return {"mode": "embedding", "count": len(valid_vectors)}
            # 嵌入失败 -> 尝试从 DB 加载已持久化的向量
            logger.warning("Insufficient embedding vectors, trying DB cache fallback")
            if await _load_index_from_db():
                return {"mode": "embedding_db_cache", "count": len(_index_texts)}
            logger.warning("No DB cache available, falling back to keyword mode")
        except Exception as e:
            logger.warning(f"MiniMax embedding failed: {e}, falling back to keyword mode")
            if await _load_index_from_db():
                return {"mode": "embedding_db_cache", "count": len(_index_texts)}

    _index_built = True
    _index_texts = texts
    _index_metadata = metadata
    _index_vectors = None
    logger.info(f"RAG index built with keyword mode, {len(texts)} entries")
    return {"mode": "keyword", "count": len(texts)}


async def _load_kb_entry(entry_id: int):
    """辅助函数: 按 id 加载 KnowledgeEntry, 用于 build_index 增量判断"""
    from .database import AsyncSessionLocal
    from .models.knowledge_base import KnowledgeEntry
    from sqlalchemy import select
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
            return (await db.execute(stmt)).scalar_one_or_none()
    except Exception:
        return None


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


async def generate_answer(
    query: str,
    context_events: list[dict],
    npc_persona: Optional[dict] = None,
) -> str:
    """基于检索结果和 (可选) persona 生成回答.

    Args:
        query: 用户问题
        context_events: RAG检索到的事件列表
        npc_persona: 英雄 persona (可选), 传入时使用古风沉浸式 prompt
    """
    # 过滤低相关度结果: score=0 表示无实际匹配, 仅是兜底数据
    relevant_events = [
        item for item in context_events
        if item.get("score", 0) > 0
    ]

    # 构造 context_text (供 persona prompt 使用)
    context_parts = []
    for item in relevant_events:
        name = item.get("name", item.get("title", "未知"))
        year = item.get("year")
        year_str = ""
        if year is not None:
            year_str = f"公元前{abs(year)}年" if year < 0 else f"公元{year}年"
        desc = item.get("description", item.get("content", ""))
        context_parts.append(f"【{name}】（{year_str}）{desc}")
    context_text = "\n".join(context_parts)

    # 根据是否有 persona 选择 system prompt
    if npc_persona:
        # 延迟导入避免循环依赖
        system_prompt = None
        try:
            from .dialogue_engine import _build_persona_prompt
            system_prompt = _build_persona_prompt(npc_persona, context_text)
        except ImportError:
            # 独立运行时回退
            try:
                from dialogue_engine import _build_persona_prompt
                system_prompt = _build_persona_prompt(npc_persona, context_text)
            except ImportError:
                system_prompt = _build_persona_prompt_fallback(npc_persona, context_text)
    else:
        has_relevant = bool(context_text.strip())
        if has_relevant:
            system_prompt = (
                "你是「历史星链探索」的历史知识助手。\n\n"
                "【回答规则】\n"
                "- 如果参考资料与用户问题相关，请优先引用资料进行回答，做到准确、有深度、条理清晰\n"
                "- 如果参考资料与用户问题无关或不足，请凭自身历史知识回答，不要说\"根据资料\"\n"
                "- 适当分析事件之间的因果关系和历史意义\n"
                "- 回答使用中文，长度控制在300字以内。"
            )
        else:
            system_prompt = (
                "你是「历史星链探索」的历史知识助手。当前暂无参考资料，请凭自身知识回答。\n"
                "回答要求：准确、有深度、条理清晰，适当分析事件之间的因果关系和历史意义。\n"
                "回答使用中文，长度控制在300字以内。"
            )

    user_message = f"以下是检索到的参考资料（可能与问题相关, 也可能不相关）：\n\n{context_text}\n\n用户问题：{query}"

    if not MINIMAX_API_KEY:
        return _generate_fallback_answer(query, context_events)

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


def _build_persona_prompt_fallback(persona: dict, context_text: str) -> str:
    """无 dialogue_engine 依赖时的兜底 prompt 构造器."""
    name = persona.get("name", "历史人物")
    role = persona.get("role", "")
    era = persona.get("era", "")
    speaking = persona.get("speaking_pattern", "吾")
    desc = persona.get("description", "")
    instructions = (
        f"你是【{name}】, {role}, {era}。自称「{speaking}」。\n"
        f"背景: {desc}。\n"
    )
    if context_text:
        instructions += (
            f"参考资料: {context_text}\n"
            f"- 如果参考资料与用户问题相关, 请优先引用\n"
            f"- 如果不相关或不足, 凭自身知识回答, 不要提及\"根据资料\"\n"
        )
    else:
        instructions += f"暂无参考资料, 请凭{name}的历史知识回答。\n"
    instructions += f"请以{name}身份用古风语气回答。"
    return instructions


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
                         year_max: Optional[int] = None,
                         npc_persona: Optional[dict] = None) -> dict:
    search_results = await search_similar(query, top_k=top_k,
                                          region=region, category=category,
                                          year_min=year_min, year_max=year_max)
    answer = await generate_answer(query, search_results, npc_persona=npc_persona)
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
