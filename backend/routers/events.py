import logging
from typing import Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.event import HistoryEvent
from ..schemas import BaseResponse

logger = logging.getLogger("historical_starlink.events")

router = APIRouter(prefix="/api/events", tags=["历史事件"])


def _event_dict(e: HistoryEvent) -> dict:
    return {
        "id": e.id,
        "name": e.name,
        "year": e.year,
        "region": e.region,
        "importance": e.importance,
        "description": e.description,
        "causes": e.causes or [],
        "consequences": e.consequences or [],
        "related_concepts": e.related_concepts or [],
        "figures": e.figures or [],
        "tags": e.tags or [],
    }


@router.get("", summary="获取所有事件列表")
async def get_events(
    region: Optional[str] = Query(default=None, description="区域筛选: china 或 foreign"),
    min_importance: Optional[int] = Query(default=None, ge=1, le=10, description="最低重要性"),
    tag: Optional[str] = Query(default=None, description="标签筛选"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    query = select(HistoryEvent)
    if region:
        query = query.where(HistoryEvent.region == region)
    if min_importance:
        query = query.where(HistoryEvent.importance >= min_importance)

    result = await db.execute(query)
    events = result.scalars().all()

    if tag:
        events = [e for e in events if tag in (e.tags or [])]

    total = len(events)
    start = (page - 1) * page_size
    end = start + page_size
    page_events = events[start:end]

    return BaseResponse(
        data={
            "list": [_event_dict(e) for e in page_events],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/search", summary="搜索事件")
async def search_events(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(HistoryEvent))
    events = result.scalars().all()

    keyword = q.lower()
    matched = [
        e
        for e in events
        if keyword in e.name.lower()
        or keyword in (e.description or "").lower()
        or any(keyword in t.lower() for t in (e.tags or []))
        or any(keyword in f.lower() for f in (e.figures or []))
        or any(keyword in c.lower() for c in (e.related_concepts or []))
    ]

    return BaseResponse(data=[_event_dict(e) for e in matched])


@router.get("/{event_id}", summary="获取单个事件")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HistoryEvent).where(HistoryEvent.id == event_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        return BaseResponse(code=404, message="事件不存在", data=None)

    return BaseResponse(data=_event_dict(event))
