"""
RAG API 路由 — 搜索相关事件 & RAG 问答 & 知识库管理
"""
import os
import json
import csv
import io
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update, delete

from ..schemas import BaseResponse, PaginationResponse
from ..rag_engine import search_similar, full_rag_query, build_index
from ..database import get_db
from ..models.knowledge_base import KnowledgeEntry, KnowledgeVersion, CrawlSource

logger = logging.getLogger("historical_starlink.rag")

router = APIRouter(prefix="/api/rag", tags=["RAG知识库"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    region: Optional[str] = Field(default=None, description="区域过滤: china/foreign")
    category: Optional[str] = Field(default=None, description="分类过滤")
    year_min: Optional[int] = Field(default=None, description="起始年份")
    year_max: Optional[int] = Field(default=None, description="结束年份")
    importance_min: Optional[int] = Field(default=None, ge=1, le=10, description="最低重要性")
    event_name: Optional[str] = Field(default=None, description="事件名称精确过滤")
    tag: Optional[str] = Field(default=None, description="标签过滤")
    status: Optional[str] = Field(default=None, description="状态过滤")
    include_seed: Optional[bool] = Field(default=True, description="是否包含种子数据事件")


class AskRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    region: Optional[str] = Field(default=None, description="区域过滤")
    category: Optional[str] = Field(default=None, description="分类过滤")
    year_min: Optional[int] = Field(default=None, description="起始年份")
    year_max: Optional[int] = Field(default=None, description="结束年份")
    importance_min: Optional[int] = Field(default=None, ge=1, le=10, description="最低重要性")
    event_name: Optional[str] = Field(default=None, description="事件名称精确过滤")
    tag: Optional[str] = Field(default=None, description="标签过滤")
    include_seed: Optional[bool] = Field(default=True, description="是否包含种子数据事件")


class ConditionalSearchRequest(BaseModel):
    """通用条件检索接口 — 支持任意条件组合, 用于前端页面查询."""
    text: Optional[str] = Field(default=None, description="全文检索关键词(可选)")
    region: Optional[str] = Field(default=None, description="区域过滤: china/foreign/other")
    category: Optional[str] = Field(default=None, description="分类过滤")
    year_min: Optional[int] = Field(default=None, description="起始年份")
    year_max: Optional[int] = Field(default=None, description="结束年份")
    importance_min: Optional[int] = Field(default=None, ge=1, le=10, description="最低重要性")
    event_name: Optional[str] = Field(default=None, description="事件名称精确过滤")
    event_name_like: Optional[str] = Field(default=None, description="事件名称模糊过滤")
    tag: Optional[str] = Field(default=None, description="标签过滤")
    source_type: Optional[str] = Field(default=None, description="来源类型过滤")
    status: Optional[str] = Field(default=None, description="状态过滤")
    language: Optional[str] = Field(default=None, description="语言过滤")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
    order_by: Optional[str] = Field(default="relevance", description="排序: relevance/importance/year/updated_at")
    include_seed: Optional[bool] = Field(default=True, description="是否包含种子数据事件")


class ManualEntryRequest(BaseModel):
    title: str = Field(..., max_length=256, description="标题")
    content: str = Field(..., description="内容")
    event_name: Optional[str] = Field(default=None, max_length=256, description="事件名称(去重主键)")
    year: Optional[int] = Field(default=None, description="年份")
    year_end: Optional[int] = Field(default=None, description="结束年份")
    region: Optional[str] = Field(default=None, description="区域")
    category: Optional[str] = Field(default=None, description="分类")
    tags: Optional[list[str]] = Field(default=None, description="标签")
    figures: Optional[list[str]] = Field(default=None, description="相关人物")
    keywords: Optional[list[str]] = Field(default=None, description="关键词")
    importance: Optional[int] = Field(default=None, ge=1, le=10, description="重要性")
    language: Optional[str] = Field(default="zh-CN", description="语言")
    source_reliability: Optional[int] = Field(default=None, ge=1, le=10, description="来源可信度")
    parent_event_id: Optional[str] = Field(default=None, description="来源事件ID")


class KnowledgeEntryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=256)
    content: Optional[str] = Field(default=None)
    event_name: Optional[str] = Field(default=None, max_length=256)
    year: Optional[int] = Field(default=None)
    year_end: Optional[int] = Field(default=None)
    region: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    tags: Optional[list[str]] = Field(default=None)
    figures: Optional[list[str]] = Field(default=None)
    keywords: Optional[list[str]] = Field(default=None)
    importance: Optional[int] = Field(default=None, ge=1, le=10)
    language: Optional[str] = Field(default=None)
    source_reliability: Optional[int] = Field(default=None, ge=1, le=10)
    status: Optional[str] = Field(default=None, description="状态: active/archived/pending_review")
    is_locked: Optional[int] = Field(default=None, ge=0, le=1, description="是否锁定")
    change_summary: Optional[str] = Field(default=None, description="本次变更说明")
    operator: Optional[str] = Field(default=None, description="操作者标识")


CHUNK_MAX_SIZE = 2000
CHUNK_OVERLAP = 200


def _split_content(text: str) -> list[str]:
    if len(text) <= CHUNK_MAX_SIZE:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_MAX_SIZE
        if end < len(text):
            nl = text.rfind("\n", start + CHUNK_MAX_SIZE // 2, end)
            if nl > start:
                end = nl
        chunks.append(text[start:end].strip())
        start = end - CHUNK_OVERLAP if end < len(text) else end
    return [c for c in chunks if c]


async def _find_existing_by_event(db: AsyncSession, event_name: Optional[str],
                                   source_url: Optional[str],
                                   chunk_index: int) -> Optional[KnowledgeEntry]:
    """Dedup by event_name + source_url + chunk_index. Returns the existing entry if any."""
    if not event_name or not event_name.strip():
        # event_name 为空或仅含空白字符, 无法作为去重主键, 直接返回 None
        return None
    stmt = select(KnowledgeEntry).where(
        KnowledgeEntry.event_name == event_name,
        KnowledgeEntry.chunk_index == chunk_index,
    )
    if source_url:
        stmt = stmt.where(KnowledgeEntry.source_url == source_url)
    else:
        stmt = stmt.where(KnowledgeEntry.source_url.is_(None))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _record_version(db: AsyncSession, entry: KnowledgeEntry,
                          change_summary: str, change_source: str,
                          operator: Optional[str] = None) -> KnowledgeVersion:
    snapshot_meta = {
        "event_name": entry.event_name,
        "region": entry.region,
        "category": entry.category,
        "year": entry.year,
        "year_end": entry.year_end,
        "importance": entry.importance,
        "tags": entry.tags,
        "figures": entry.figures,
        "keywords": entry.keywords,
        "source_type": entry.source_type,
        "source_url": entry.source_url,
        "file_name": entry.file_name,
        "file_type": entry.file_type,
        "language": entry.language,
        "source_reliability": entry.source_reliability,
        "status": entry.status,
        "is_locked": entry.is_locked,
    }
    version_row = KnowledgeVersion(
        entry_id=entry.id,
        version=entry.version,
        title=entry.title,
        content=entry.content,
        content_hash=entry.content_hash,
        change_summary=change_summary,
        change_source=change_source,
        operator=operator,
        snapshot_meta=snapshot_meta,
        created_at=datetime.utcnow(),
    )
    db.add(version_row)
    return version_row


async def _store_chunks(db: AsyncSession, title: str, content: str,
                         source_type: str, file_name: Optional[str] = None,
                         file_type: Optional[str] = None,
                         source_url: Optional[str] = None,
                         event_name: Optional[str] = None,
                         year: Optional[int] = None,
                         year_end: Optional[int] = None,
                         region: Optional[str] = None,
                         category: Optional[str] = None,
                         tags: Optional[list] = None,
                         figures: Optional[list] = None,
                         keywords: Optional[list] = None,
                         importance: Optional[int] = None,
                         language: Optional[str] = "zh-CN",
                         source_reliability: Optional[int] = 5,
                         parent_event_id: Optional[str] = None,
                         change_source: str = "file_import",
                         operator: Optional[str] = None) -> dict:
    # event_name 为空或仅含空白字符时, 直接过滤, 不进行分块也不写入 DB
    if not event_name or not event_name.strip():
        logger.warning(
            f"Skip import due to empty event_name: title={title!r}, "
            f"file_name={file_name!r}, source_url={source_url!r}"
        )
        return {
            "imported": 0,
            "skipped": 0,
            "updated": 0,
            "chunks": 0,
            "filtered_reason": "empty_event_name",
        }
    chunks = _split_content(content)
    now = datetime.utcnow()
    imported = 0
    skipped = 0
    updated = 0

    for idx, chunk in enumerate(chunks):
        content_hash = KnowledgeEntry.compute_hash(chunk)

        # 优先按 event_name + source_url + chunk_index 去重
        existing = await _find_existing_by_event(db, event_name, source_url, idx)
        if existing:
            if existing.content_hash == content_hash:
                skipped += 1
                continue
            # 内容变化 -> 升级版本
            if existing.is_locked:
                skipped += 1
                continue
            existing.content = chunk
            existing.content_hash = content_hash
            existing.version += 1
            existing.version_count = (existing.version_count or 1) + 1
            existing.title = title if idx == 0 else f"{title} (part {idx + 1})"
            existing.updated_at = now
            existing.last_indexed_at = now
            existing.year = year
            existing.year_end = year_end
            existing.region = region
            existing.category = category
            existing.tags = tags or existing.tags or []
            existing.figures = figures or existing.figures or []
            existing.keywords = keywords or existing.keywords or []
            existing.importance = importance
            existing.language = language or existing.language
            existing.source_reliability = source_reliability or existing.source_reliability
            await _record_version(
                db, existing,
                change_summary=f"Updated via {change_source} (chunk {idx + 1})",
                change_source=change_source,
                operator=operator,
            )
            updated += 1
            continue

        # 其次按 content_hash + chunk_index 去重
        hash_stmt = select(KnowledgeEntry).where(
            KnowledgeEntry.content_hash == content_hash,
            KnowledgeEntry.chunk_index == idx,
        )
        hash_existing = (await db.execute(hash_stmt)).scalar_one_or_none()
        if hash_existing:
            skipped += 1
            continue

        entry = KnowledgeEntry(
            title=title if idx == 0 else f"{title} (part {idx + 1})",
            content=chunk,
            content_hash=content_hash,
            source_type=source_type,
            source_url=source_url,
            file_name=file_name,
            file_type=file_type,
            event_name=event_name,
            year=year,
            year_end=year_end,
            region=region,
            importance=importance,
            category=category,
            tags=tags or [],
            figures=figures or [],
            keywords=keywords or [],
            language=language or "zh-CN",
            source_reliability=source_reliability or 5,
            chunk_index=idx,
            chunk_total=len(chunks),
            version=1,
            version_count=1,
            parent_event_id=parent_event_id,
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
        await _record_version(
            db, entry,
            change_summary=f"Initial import via {source_type} (chunk {idx + 1}/{len(chunks)})",
            change_source=change_source,
            operator=operator,
        )
        imported += 1

    return {"imported": imported, "skipped": skipped, "updated": updated, "chunks": len(chunks)}


def _entry_to_summary(e: KnowledgeEntry) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "content_preview": (e.content[:200] + ("..." if len(e.content) > 200 else "")) if e.content else "",
        "source_type": e.source_type,
        "source_url": e.source_url,
        "file_name": e.file_name,
        "file_type": e.file_type,
        "event_name": e.event_name,
        "year": e.year,
        "year_end": e.year_end,
        "region": e.region,
        "category": e.category,
        "tags": e.tags,
        "figures": e.figures,
        "keywords": e.keywords,
        "importance": e.importance,
        "language": e.language,
        "source_reliability": e.source_reliability,
        "chunk_index": e.chunk_index,
        "chunk_total": e.chunk_total,
        "version": e.version,
        "version_count": e.version_count,
        "parent_event_id": e.parent_event_id,
        "status": e.status,
        "is_locked": e.is_locked,
        "created_at": str(e.created_at) if e.created_at else None,
        "updated_at": str(e.updated_at) if e.updated_at else None,
        "last_indexed_at": str(e.last_indexed_at) if e.last_indexed_at else None,
    }


@router.post("/search", response_model=BaseResponse, summary="搜索相关历史事件(支持条件过滤)")
async def search_events(req: SearchRequest):
    results = await search_similar(
        req.query, top_k=req.top_k,
        region=req.region, category=req.category,
        year_min=req.year_min, year_max=req.year_max,
    )
    return BaseResponse(data=results)


@router.post("/search-hybrid", response_model=BaseResponse,
             summary="事件表 + RAG 知识库 混合搜索, 用于首页搜索框")
async def search_hybrid(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    """联合事件表 ILIKE 与 RAG 向量检索, 事件表结果 score 加权 ×1.5."""
    from ..models.event import HistoryEvent

    # 1) RAG 向量搜索
    rag_results = await search_similar(
        req.query, top_k=req.top_k,
        region=req.region, category=req.category,
        year_min=req.year_min, year_max=req.year_max,
    )

    # 2) 事件表精确匹配
    like = f"%{req.query}%"
    event_stmt = (
        select(HistoryEvent)
        .where(
            (HistoryEvent.name.ilike(like))
            | (HistoryEvent.description.ilike(like))
            | (HistoryEvent.tags.cast(__import__("sqlalchemy").String).ilike(like))
        )
        .limit(req.top_k)
    )
    events = (await db.execute(event_stmt)).scalars().all()

    # 3) 合并去重
    seen_ids: set = set()
    merged: list[dict] = []
    for ev in events:
        item = {
            "source": "event_table",
            "id": ev.id,
            "name": ev.name,
            "year": ev.year,
            "region": ev.region,
            "importance": ev.importance,
            "description": (ev.description or "")[:200],
            "tags": ev.tags or [],
            "score": 1.5,
        }
        merged.append(item)
        seen_ids.add(ev.id)

    for r in rag_results:
        rid = r.get("id")
        if rid in seen_ids:
            continue
        merged.append({**r, "source": r.get("source", "knowledge_base")})
        seen_ids.add(rid)

    # 4) 排序后截断
    merged.sort(key=lambda x: x.get("score", 0), reverse=True)
    return BaseResponse(data=merged[:req.top_k])


@router.post("/ask", response_model=BaseResponse, summary="RAG 智能问答(支持条件过滤)")
async def ask_question(req: AskRequest):
    result = await full_rag_query(
        req.question,
        region=req.region, category=req.category,
        year_min=req.year_min, year_max=req.year_max,
    )
    return BaseResponse(data=result)


@router.post("/conditional-search", response_model=BaseResponse, summary="通用条件检索 — 支持多维条件与分页, 供前端页面查询使用")
async def conditional_search(req: ConditionalSearchRequest, db: AsyncSession = Depends(get_db)):
    conditions = [KnowledgeEntry.status == "active"]

    if req.region:
        conditions.append(KnowledgeEntry.region == req.region)
    if req.category:
        conditions.append(KnowledgeEntry.category == req.category)
    if req.year_min is not None:
        conditions.append(KnowledgeEntry.year >= req.year_min)
    if req.year_max is not None:
        conditions.append(KnowledgeEntry.year <= req.year_max)
    if req.importance_min is not None:
        conditions.append(KnowledgeEntry.importance >= req.importance_min)
    if req.event_name:
        conditions.append(KnowledgeEntry.event_name == req.event_name)
    if req.event_name_like:
        conditions.append(KnowledgeEntry.event_name.ilike(f"%{req.event_name_like}%"))
    if req.tag:
        # JSON contains (works on both MySQL JSON and SQLite TEXT json)
        try:
            conditions.append(KnowledgeEntry.tags.like(f'%"{req.tag}"%'))
        except Exception:
            pass
    if req.source_type:
        conditions.append(KnowledgeEntry.source_type == req.source_type)
    if req.status:
        conditions.append(KnowledgeEntry.status == req.status)
    if req.language:
        conditions.append(KnowledgeEntry.language == req.language)
    if req.text:
        like = f"%{req.text}%"
        conditions.append(
            (KnowledgeEntry.title.ilike(like))
            | (KnowledgeEntry.event_name.ilike(like))
            | (KnowledgeEntry.content.ilike(like))
            | (KnowledgeEntry.keywords.cast(__import__("sqlalchemy").String).ilike(like))
        )

    where = and_(*conditions) if conditions else True

    order_clauses = {
        "importance": KnowledgeEntry.importance.desc(),
        "year": KnowledgeEntry.year.asc(),
        "updated_at": KnowledgeEntry.updated_at.desc(),
        "relevance": KnowledgeEntry.importance.desc(),
    }
    order = order_clauses.get(req.order_by or "relevance", KnowledgeEntry.importance.desc())

    count_stmt = select(func.count()).select_from(KnowledgeEntry).where(where)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(KnowledgeEntry)
        .where(where)
        .order_by(order, KnowledgeEntry.id.desc())
        .offset((req.page - 1) * req.page_size)
        .limit(req.page_size)
    )
    rows = (await db.execute(stmt)).scalars().all()

    items = [_entry_to_summary(e) for e in rows]
    return BaseResponse(data={
        "items": items,
        "total": total,
        "page": req.page,
        "page_size": req.page_size,
        "filters_applied": {
            "region": req.region, "category": req.category,
            "year_min": req.year_min, "year_max": req.year_max,
            "importance_min": req.importance_min,
            "event_name": req.event_name, "event_name_like": req.event_name_like,
            "tag": req.tag, "source_type": req.source_type,
            "status": req.status, "language": req.language,
            "text": req.text,
        },
    })


@router.post("/rebuild", response_model=BaseResponse, summary="重建 RAG 索引")
async def rebuild_index():
    info = await build_index()
    return BaseResponse(data=info)


@router.post("/import/file", response_model=BaseResponse, summary="导入文件到知识库")
async def import_file(
    file: UploadFile = File(...),
    event_name: Optional[str] = Form(default=None, description="事件名称(去重主键)"),
    year: Optional[int] = Form(default=None),
    year_end: Optional[int] = Form(default=None),
    region: Optional[str] = Form(default=None),
    category: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None, description="逗号分隔的标签"),
    figures: Optional[str] = Form(default=None, description="逗号分隔的人物"),
    importance: Optional[int] = Form(default=None),
    language: Optional[str] = Form(default="zh-CN"),
    source_reliability: Optional[int] = Form(default=5),
    operator: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else "txt"
    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_bytes.decode("gbk", errors="ignore")

    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()] or None
    figure_list = [f.strip() for f in (figures or "").split(",") if f.strip()] or None

    if ext == "json":
        try:
            data = json.loads(text)
            if isinstance(data, list):
                all_results = []
                for item in data:
                    content = item.get("content") or item.get("description") or json.dumps(item, ensure_ascii=False)
                    title = item.get("title") or item.get("name") or file.filename
                    result = await _store_chunks(
                        db, title=title, content=content, source_type="file_import",
                        file_name=file.filename, file_type=ext,
                        event_name=item.get("event_name") or event_name,
                        year=item.get("year") or year,
                        year_end=item.get("year_end") or year_end,
                        region=item.get("region") or region,
                        category=item.get("category") or category,
                        tags=item.get("tags") or tag_list,
                        figures=item.get("figures") or figure_list,
                        keywords=item.get("keywords"),
                        importance=item.get("importance") or importance,
                        language=item.get("language") or language,
                        source_reliability=item.get("source_reliability") or source_reliability,
                        parent_event_id=item.get("parent_event_id"),
                        change_source="file_import",
                        operator=operator,
                    )
                    all_results.append(result)
                total_imported = sum(r["imported"] for r in all_results)
                total_skipped = sum(r["skipped"] for r in all_results)
                total_updated = sum(r.get("updated", 0) for r in all_results)
                await db.commit()
                try:
                    await build_index()
                except Exception:
                    pass
                return BaseResponse(data={
                    "imported": total_imported, "skipped": total_skipped,
                    "updated": total_updated,
                    "format": "json_array", "count": len(data),
                })
            else:
                content = data.get("content") or data.get("description") or json.dumps(data, ensure_ascii=False)
                title = data.get("title") or data.get("name") or file.filename
        except json.JSONDecodeError:
            title = file.filename
            content = text
    elif ext == "csv":
        reader = csv.DictReader(io.StringIO(text))
        all_results = []
        for row in reader:
            content = row.get("content") or row.get("description") or str(row)
            title = row.get("title") or row.get("name") or file.filename
            result = await _store_chunks(
                db, title=title, content=content, source_type="file_import",
                file_name=file.filename, file_type=ext,
                event_name=row.get("event_name") or event_name,
                year=int(row["year"]) if row.get("year") and row["year"].lstrip("-").isdigit() else year,
                year_end=int(row["year_end"]) if row.get("year_end") and row["year_end"].lstrip("-").isdigit() else year_end,
                region=row.get("region") or region,
                category=row.get("category") or category,
                tags=(row.get("tags", "").split(",") if row.get("tags") else tag_list),
                figures=(row.get("figures", "").split(",") if row.get("figures") else figure_list),
                importance=int(row["importance"]) if row.get("importance") and row["importance"].isdigit() else importance,
                change_source="file_import",
                operator=operator,
            )
            all_results.append(result)
        total_imported = sum(r["imported"] for r in all_results)
        total_skipped = sum(r["skipped"] for r in all_results)
        total_updated = sum(r.get("updated", 0) for r in all_results)
        await db.commit()
        try:
            await build_index()
        except Exception:
            pass
        return BaseResponse(data={
            "imported": total_imported, "skipped": total_skipped,
            "updated": total_updated,
            "format": "csv", "count": len(all_results),
        })
    else:
        title = file.filename.rsplit(".", 1)[0] if file.filename else "untitled"
        content = text

    result = await _store_chunks(
        db, title=title, content=content, source_type="file_import",
        file_name=file.filename, file_type=ext,
        event_name=event_name, year=year, year_end=year_end,
        region=region, category=category,
        tags=tag_list, figures=figure_list,
        importance=importance, language=language,
        source_reliability=source_reliability,
        change_source="file_import", operator=operator,
    )
    await db.commit()
    try:
        await build_index()
    except Exception:
        pass
    return BaseResponse(data={**result, "format": ext, "file_name": file.filename})


@router.post("/import/manual", response_model=BaseResponse, summary="手动添加知识条目")
async def add_manual_entry(req: ManualEntryRequest, db: AsyncSession = Depends(get_db)):
    result = await _store_chunks(
        db, title=req.title, content=req.content, source_type="manual",
        event_name=req.event_name, year=req.year, year_end=req.year_end,
        region=req.region, category=req.category,
        tags=req.tags, figures=req.figures, keywords=req.keywords,
        importance=req.importance, language=req.language,
        source_reliability=req.source_reliability,
        parent_event_id=req.parent_event_id,
        change_source="manual",
    )
    await db.commit()
    try:
        await build_index()
    except Exception:
        pass
    return BaseResponse(data=result)


@router.post("/import/seed", response_model=BaseResponse, summary="从 events_data 批量导入种子知识库条目")
async def import_seed_events(db: AsyncSession = Depends(get_db)):
    """One-shot seed of all 50 events from events_data into the knowledge base.
    Used to give the homepage real content immediately instead of dummy data.
    """
    from ..data.events_data import events_data

    now = datetime.utcnow()
    imported = 0
    skipped = 0
    updated = 0

    for ev in events_data:
        ev_name = ev.get("name")
        ev_id = ev.get("id")
        if not ev_name:
            continue

        # Build a rich text representation
        causes = "；".join(ev.get("causes", []))
        consequences = "；".join(ev.get("consequences", []))
        related = "；".join(ev.get("related_concepts", []))
        figures = ev.get("figures", [])
        tags = ev.get("tags", [])

        text = (
            f"{ev_name}（{'公元前' + str(abs(ev['year'])) + '年' if ev['year'] < 0 else '公元' + str(ev['year']) + '年'}，"
            f"{'中国' if ev['region'] == 'china' else '外国'}，重要性{ev['importance']}/10）：{ev.get('description', '')}。"
            f"原因：{causes}。影响：{consequences}。相关概念：{related}。"
            f"相关人物：{'、'.join(figures)}。标签：{'、'.join(tags)}。"
        )

        result = await _store_chunks(
            db,
            title=ev_name,
            content=text,
            source_type="seed_data",
            file_name=None,
            file_type="seed",
            event_name=ev_name,
            year=ev.get("year"),
            region=ev.get("region"),
            importance=ev.get("importance"),
            category=ev.get("category") or "综合",
            tags=tags,
            figures=figures,
            keywords=tags + [ev_name, ev.get("region", "")],
            language="zh-CN",
            source_reliability=10,
            parent_event_id=ev_id,
            change_source="seed_data",
        )
        imported += result["imported"]
        skipped += result["skipped"]
        updated += result.get("updated", 0)

    await db.commit()
    try:
        await build_index()
    except Exception:
        pass

    return BaseResponse(data={
        "imported": imported, "skipped": skipped, "updated": updated,
        "total_events": len(events_data),
    })


@router.get("/entries", response_model=BaseResponse, summary="查询知识库条目列表")
async def list_entries(
    source_type: Optional[str] = Query(default=None),
    region: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    event_name: Optional[str] = Query(default=None),
    importance_min: Optional[int] = Query(default=None, ge=1, le=10),
    year_min: Optional[int] = Query(default=None),
    year_max: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if source_type:
        conditions.append(KnowledgeEntry.source_type == source_type)
    if region:
        conditions.append(KnowledgeEntry.region == region)
    if category:
        conditions.append(KnowledgeEntry.category == category)
    if status:
        conditions.append(KnowledgeEntry.status == status)
    if event_name:
        conditions.append(KnowledgeEntry.event_name.ilike(f"%{event_name}%"))
    if importance_min is not None:
        conditions.append(KnowledgeEntry.importance >= importance_min)
    if year_min is not None:
        conditions.append(KnowledgeEntry.year >= year_min)
    if year_max is not None:
        conditions.append(KnowledgeEntry.year <= year_max)
    if keyword:
        like_pattern = f"%{keyword}%"
        conditions.append(
            (KnowledgeEntry.title.ilike(like_pattern))
            | (KnowledgeEntry.event_name.ilike(like_pattern))
            | (KnowledgeEntry.content.ilike(like_pattern))
        )

    where = and_(*conditions) if conditions else True

    count_stmt = select(func.count()).select_from(KnowledgeEntry).where(where)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(KnowledgeEntry)
        .where(where)
        .order_by(KnowledgeEntry.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    entries = (await db.execute(stmt)).scalars().all()
    items = [_entry_to_summary(e) for e in entries]

    return BaseResponse(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/entries/{entry_id}", response_model=BaseResponse, summary="获取单条知识条目详情")
async def get_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    data = _entry_to_summary(entry)
    data["content"] = entry.content
    data["content_hash"] = entry.content_hash
    return BaseResponse(data=data)


@router.get("/entries/{entry_id}/versions", response_model=BaseResponse, summary="获取条目的版本历史")
async def get_entry_versions(entry_id: int, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    if not exists.scalar():
        raise HTTPException(status_code=404, detail="条目不存在")
    stmt = (
        select(KnowledgeVersion)
        .where(KnowledgeVersion.entry_id == entry_id)
        .order_by(KnowledgeVersion.version.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {
            "id": v.id, "version": v.version, "title": v.title,
            "content_hash": v.content_hash, "change_summary": v.change_summary,
            "change_source": v.change_source, "operator": v.operator,
            "snapshot_meta": v.snapshot_meta,
            "created_at": str(v.created_at) if v.created_at else None,
        }
        for v in rows
    ]
    return BaseResponse(data={"items": items, "total": len(items), "entry_id": entry_id})


@router.put("/entries/{entry_id}", response_model=BaseResponse, summary="更新知识条目")
async def update_entry(entry_id: int, req: KnowledgeEntryUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    if entry.is_locked:
        raise HTTPException(status_code=403, detail="条目已锁定, 不能修改")

    update_data = req.model_dump(exclude_unset=True)
    change_summary = update_data.pop("change_summary", None) or f"Manual edit v{entry.version + 1}"
    operator = update_data.pop("operator", None)

    content_changed = False
    if "content" in update_data:
        new_content = update_data.pop("content")
        if new_content != entry.content:
            content_changed = True
        entry.content = new_content
        entry.content_hash = KnowledgeEntry.compute_hash(new_content)
        entry.version += 1
        entry.version_count = (entry.version_count or 1) + 1
        entry.last_indexed_at = datetime.utcnow()

    for key, value in update_data.items():
        if hasattr(entry, key):
            setattr(entry, key, value)

    entry.updated_at = datetime.utcnow()

    if content_changed or update_data:
        await _record_version(
            db, entry,
            change_summary=change_summary,
            change_source="manual_edit",
            operator=operator,
        )

    await db.flush()
    try:
        await build_index()
    except Exception:
        pass
    return BaseResponse(message="更新成功", data={"version": entry.version})


@router.delete("/entries/{entry_id}", response_model=BaseResponse, summary="删除知识条目")
async def delete_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    if entry.is_locked:
        raise HTTPException(status_code=403, detail="条目已锁定, 不能删除")
    await db.delete(entry)
    await db.flush()
    try:
        await build_index()
    except Exception:
        pass
    return BaseResponse(message="删除成功")


@router.get("/stats", response_model=BaseResponse, summary="知识库统计")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(KnowledgeEntry))).scalar() or 0

    by_source = {}
    for st in ["file_import", "web_crawl", "manual", "seed_data"]:
        cnt = (await db.execute(
            select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.source_type == st)
        )).scalar() or 0
        by_source[st] = cnt

    active = (await db.execute(
        select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.status == "active")
    )).scalar() or 0

    by_region = {}
    for r in ["china", "foreign"]:
        cnt = (await db.execute(
            select(func.count()).select_from(KnowledgeEntry).where(KnowledgeEntry.region == r)
        )).scalar() or 0
        by_region[r] = cnt

    by_category = {}
    cat_rows = await db.execute(
        select(KnowledgeEntry.category, func.count())
        .where(KnowledgeEntry.category.isnot(None))
        .group_by(KnowledgeEntry.category)
    )
    for cat, cnt in cat_rows.all():
        if cat:
            by_category[cat] = cnt

    latest_row = (await db.execute(
        select(KnowledgeEntry.updated_at).order_by(KnowledgeEntry.updated_at.desc()).limit(1)
    )).first()
    latest_update = str(latest_row[0]) if latest_row else None

    version_total = (await db.execute(select(func.count()).select_from(KnowledgeVersion))).scalar() or 0

    crawl_source_count = (await db.execute(
        select(func.count()).select_from(CrawlSource).where(CrawlSource.enabled == 1)
    )).scalar() or 0

    recommended_count = (await db.execute(
        select(func.count()).select_from(CrawlSource).where(CrawlSource.recommended == 1)
    )).scalar() or 0

    return BaseResponse(data={
        "total": total,
        "active": active,
        "by_source": by_source,
        "by_region": by_region,
        "by_category": by_category,
        "versions": version_total,
        "crawl_sources": crawl_source_count,
        "recommended_sources": recommended_count,
        "latest_update": latest_update,
    })


@router.get("/crawl-sources", response_model=BaseResponse, summary="获取爬虫来源列表")
async def list_crawl_sources(
    recommended: Optional[int] = Query(default=None, ge=0, le=1),
    enabled: Optional[int] = Query(default=None, ge=0, le=1),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if recommended is not None:
        conditions.append(CrawlSource.recommended == recommended)
    if enabled is not None:
        conditions.append(CrawlSource.enabled == enabled)
    stmt = select(CrawlSource).where(and_(*conditions) if conditions else True).order_by(
        CrawlSource.recommended.desc(), CrawlSource.priority.desc(), CrawlSource.id
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        {
            "id": r.id, "name": r.name, "url": r.url, "category": r.category,
            "region": r.region, "tags": r.tags, "description": r.description,
            "recommended": r.recommended, "enabled": r.enabled, "priority": r.priority,
            "last_crawled_at": str(r.last_crawled_at) if r.last_crawled_at else None,
            "last_status": r.last_status, "last_imported": r.last_imported,
        }
        for r in rows
    ]
    return BaseResponse(data={"items": items, "total": len(items)})


@router.post("/crawl", response_model=BaseResponse, summary="手动触发网页爬取")
async def trigger_crawl(db: AsyncSession = Depends(get_db)):
    from ..crawler import crawl_and_store
    try:
        result = await crawl_and_store()
        # Re-aggregate the latest entry count after crawl
        try:
            total = (await db.execute(select(func.count()).select_from(KnowledgeEntry))).scalar() or 0
            result["total_entries"] = total
        except Exception:
            pass
        return BaseResponse(data=result)
    except Exception as e:
        logger.error(f"Manual crawl failed: {e}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")
