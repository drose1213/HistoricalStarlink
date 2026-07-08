import logging
from typing import Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.event import HistoryEvent
from ..models.exploration_record import ExplorationRecord
from ..schemas import BaseResponse
from ..utils import iso_utc

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


@router.get("/home", summary="首页聚合 feed: 系统推荐 + 用户已探索")
async def get_home_feed(
    user_id: Optional[int] = Query(default=None, description="用户ID(已登录必传)"),
    session_id: Optional[str] = Query(default=None, description="匿名会话ID(前端localStorage)"),
    recommended_limit: int = Query(default=50, ge=1, le=100, description="系统推荐数量"),
    explored_limit: int = Query(default=50, ge=1, le=100, description="已探索数量"),
    db: AsyncSession = Depends(get_db),
):
    """首页初始化加载, 一次返回系统推荐与用户已探索两类事件.

    - 推荐: 按 importance DESC, id ASC 排序
    - 已探索: 按 exploration_records 中 event_id 访问次数 DESC, 最近访问 DESC 排序
    """
    # 1) 系统推荐
    rec_stmt = (
        select(HistoryEvent)
        .order_by(HistoryEvent.importance.desc(), HistoryEvent.id.asc())
        .limit(recommended_limit)
    )
    recommended = (await db.execute(rec_stmt)).scalars().all()

    # 2) 用户已探索: 优先按 user_id 聚合, 匿名时回退 session_id
    explored: list[dict] = []
    if user_id or session_id:
        exp_conditions = [ExplorationRecord.is_deleted == False]  # noqa: E712
        if user_id:
            exp_conditions.append(ExplorationRecord.user_id == user_id)
        elif session_id:
            exp_conditions.append(ExplorationRecord.session_id == session_id)
        exp_stmt = (
            select(
                ExplorationRecord.event_id.label("event_id"),
                func.count().label("visit_count"),
                func.max(ExplorationRecord.created_at).label("last_visit"),
            )
            .where(and_(*exp_conditions))
            .group_by(ExplorationRecord.event_id)
            .order_by(func.count().desc(), func.max(ExplorationRecord.created_at).desc())
            .limit(explored_limit)
        )
        rows = (await db.execute(exp_stmt)).all()
        if rows:
            ids = [r.event_id for r in rows]
            ev_map = {
                e.id: e for e in
                (await db.execute(select(HistoryEvent).where(HistoryEvent.id.in_(ids)))).scalars()
            }
            explored = [
                {**_event_dict(ev_map[r.event_id]), "visit_count": r.visit_count, "last_visit": iso_utc(r.last_visit)}
                for r in rows
                if r.event_id in ev_map
            ]

    return BaseResponse(data={
        "recommended": [_event_dict(e) for e in recommended],
        "explored": explored,
        "recommended_total": len(recommended),
        "explored_total": len(explored),
    })


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
    limit: int = Query(default=50, ge=1, le=100, description="返回数量上限"),
    db: AsyncSession = Depends(get_db),
):
    # SQL 侧 LIKE 过滤, 避免全表加载到 Python 内存
    keyword = q.strip()
    if not keyword:
        return BaseResponse(data=[])

    pattern = f"%{keyword}%"
    stmt = (
        select(HistoryEvent)
        .where(
            (HistoryEvent.name.like(pattern))
            | (HistoryEvent.description.like(pattern))
            | (HistoryEvent.tags.like(pattern))
            | (HistoryEvent.figures.like(pattern))
            | (HistoryEvent.related_concepts.like(pattern))
        )
        .order_by(HistoryEvent.importance.desc(), HistoryEvent.id.asc())
        .limit(limit)
    )
    events = (await db.execute(stmt)).scalars().all()

    # 结果二次过滤: keyword 可能在 JSON 数组或 description 大小写不敏感
    kw_lower = keyword.lower()
    matched = []
    for e in events:
        if (
            kw_lower in (e.name or "").lower()
            or kw_lower in (e.description or "").lower()
            or any(kw_lower in t.lower() for t in (e.tags or []))
            or any(kw_lower in f.lower() for f in (e.figures or []))
            or any(kw_lower in c.lower() for c in (e.related_concepts or []))
        ):
            matched.append(e)

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
