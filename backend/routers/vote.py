from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case

from ..database import get_db
from ..models.vote import Vote
from ..redis_client import cache
from ..schemas import BaseResponse, VoteCreate, VoteOut, VoteStats

router = APIRouter(prefix="/api/vote", tags=["投票"])


async def _current_vote_stats(db: AsyncSession, event_id: str, session_id: str) -> dict:
    """统计某事件当前会话的三态计数字段（spec rating-system-enhancement）"""
    cond = [Vote.event_id == event_id, Vote.is_deleted == False]
    stmt = select(
        func.sum(case((Vote.vote_type == 1, 1), else_=0)).label("agree"),
        func.sum(case((Vote.vote_type == -1, 1), else_=0)).label("disagree"),
    ).where(and_(*cond))
    row = (await db.execute(stmt)).one()
    agree = int(row.agree or 0)
    disagree = int(row.disagree or 0)
    # favorite 暂用赞成 + session 已投 1 标记映射，前端按 vote_type 渲染
    my_vote_stmt = select(Vote.vote_type).where(
        and_(Vote.event_id == event_id, Vote.session_id == session_id, Vote.is_deleted == False)
    )
    my_vote = (await db.execute(my_vote_stmt)).scalar() or 0
    return {
        "agree_count": agree,
        "disagree_count": disagree,
        "favorite_count": 0,
        "my_vote": int(my_vote),
    }


@router.post("", response_model=BaseResponse, summary="创建或切换投票")
async def create_or_toggle_vote(
    vote: VoteCreate,
    db: AsyncSession = Depends(get_db),
):
    check_stmt = select(Vote).where(
        and_(
            Vote.event_id == vote.event_id,
            Vote.session_id == vote.session_id,
            Vote.is_deleted == False,
        )
    )
    existing_result = await db.execute(check_stmt)
    existing = existing_result.scalar_one_or_none()

    if existing:
        if existing.vote_type == vote.vote_type:
            existing.is_deleted = True
            action = "取消投票"
        else:
            existing.vote_type = vote.vote_type
            action = "切换投票"
        await db.flush()
        await db.refresh(existing)
        await cache.delete(f"vote:stats:{vote.event_id}")
        stats = await _current_vote_stats(db, vote.event_id, vote.session_id)
        data = VoteOut.model_validate(existing).model_dump()
        data.update(stats)
        return BaseResponse(
            message=f"{action}成功",
            data=data,
        )

    new_vote = Vote(
        event_id=vote.event_id,
        event_name=vote.event_name,
        session_id=vote.session_id,
        vote_type=vote.vote_type,
    )
    db.add(new_vote)
    await db.flush()
    await db.refresh(new_vote)

    await cache.delete(f"vote:stats:{vote.event_id}")
    stats = await _current_vote_stats(db, vote.event_id, vote.session_id)
    data = VoteOut.model_validate(new_vote).model_dump()
    data.update(stats)
    return BaseResponse(
        message="投票成功",
        data=data,
    )


@router.get("/stats/{event_id}", response_model=BaseResponse, summary="获取事件投票统计")
async def get_vote_stats(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    cached = await cache.get(f"vote:stats:{event_id}")
    if cached:
        return BaseResponse(data=cached)

    conditions = [Vote.event_id == event_id, Vote.is_deleted == False]

    stmt = select(
        func.sum(case((Vote.vote_type == 1, 1), else_=0)).label("up_count"),
        func.sum(case((Vote.vote_type == -1, 1), else_=0)).label("down_count"),
        func.count(Vote.id).label("total"),
    ).where(and_(*conditions))

    result = await db.execute(stmt)
    row = result.one()

    event_name_stmt = select(Vote.event_name).where(and_(*conditions)).limit(1)
    name_result = await db.execute(event_name_stmt)
    event_name = name_result.scalar() or event_id

    up_count = int(row.up_count or 0)
    down_count = int(row.down_count or 0)
    total = int(row.total or 0)
    ratio = round(up_count / total, 4) if total > 0 else 0.0

    stats = {
        "event_id": event_id,
        "event_name": event_name,
        "up_count": up_count,
        "down_count": down_count,
        "total": total,
        "ratio": ratio,
    }

    await cache.set(f"vote:stats:{event_id}", stats)

    return BaseResponse(data=stats)


@router.get("/my", response_model=BaseResponse, summary="获取用户投票记录")
async def get_my_votes(
    session_id: str = Query(..., description="会话ID"),
    event_id: Optional[str] = Query(default=None, description="历史事件ID"),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Vote.session_id == session_id, Vote.is_deleted == False]
    if event_id:
        conditions.append(Vote.event_id == event_id)

    stmt = select(Vote).where(and_(*conditions)).order_by(Vote.created_at.desc())
    result = await db.execute(stmt)
    votes = result.scalars().all()

    return BaseResponse(
        data=[VoteOut.model_validate(v).model_dump() for v in votes],
    )


@router.get("/batch-stats", response_model=BaseResponse, summary="批量获取事件投票统计")
async def batch_get_vote_stats(
    event_ids: str = Query(..., description="事件ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db),
):
    ids = [eid.strip() for eid in event_ids.split(",") if eid.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="事件ID列表不能为空")
    if len(ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多查询50个事件")

    conditions = [Vote.event_id.in_(ids), Vote.is_deleted == False]

    stmt = (
        select(
            Vote.event_id,
            func.sum(case((Vote.vote_type == 1, 1), else_=0)).label("up_count"),
            func.sum(case((Vote.vote_type == -1, 1), else_=0)).label("down_count"),
            func.count(Vote.id).label("total"),
        )
        .where(and_(*conditions))
        .group_by(Vote.event_id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    stats_map = {}
    for row in rows:
        up = int(row.up_count or 0)
        down = int(row.down_count or 0)
        total = int(row.total or 0)
        stats_map[row.event_id] = {
            "event_id": row.event_id,
            "up_count": up,
            "down_count": down,
            "total": total,
            "ratio": round(up / total, 4) if total > 0 else 0.0,
        }

    for eid in ids:
        if eid not in stats_map:
            stats_map[eid] = {
                "event_id": eid,
                "up_count": 0,
                "down_count": 0,
                "total": 0,
                "ratio": 0.0,
            }

    return BaseResponse(data=stats_map)
