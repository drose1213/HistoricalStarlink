from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database import get_db
from ..models.rating import Rating
from ..redis_client import cache
from ..schemas import (
    BaseResponse,
    PaginationResponse,
    RatingCreate,
    RatingUpdate,
    RatingOut,
    RatingStats,
)

router = APIRouter(prefix="/api/rating", tags=["评分"])


@router.post("", response_model=BaseResponse, summary="创建评分")
async def create_rating(
    rating: RatingCreate,
    db: AsyncSession = Depends(get_db),
):
    check_stmt = select(Rating).where(
        and_(
            Rating.event_id == rating.event_id,
            Rating.session_id == rating.session_id,
            Rating.is_deleted == False,
        )
    )
    existing = await db.execute(check_stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该会话已对此事件评分，请使用更新接口")

    new_rating = Rating(
        event_id=rating.event_id,
        event_name=rating.event_name,
        session_id=rating.session_id,
        score=rating.score,
        comment=rating.comment,
        dimension_importance=rating.dimension_importance,
        dimension_interest=rating.dimension_interest,
        dimension_impact=rating.dimension_impact,
    )
    db.add(new_rating)
    await db.flush()
    await db.refresh(new_rating)

    await cache.delete(f"rating:stats:{rating.event_id}")

    return BaseResponse(
        message="评分创建成功",
        data=RatingOut.model_validate(new_rating).model_dump(),
    )


@router.put("/{rating_id}", response_model=BaseResponse, summary="更新评分")
async def update_rating(
    rating_id: int,
    update: RatingUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Rating).where(and_(Rating.id == rating_id, Rating.is_deleted == False))
    result = await db.execute(stmt)
    rating = result.scalar_one_or_none()

    if not rating:
        raise HTTPException(status_code=404, detail="评分记录不存在")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rating, field, value)

    await db.flush()
    await db.refresh(rating)

    await cache.delete(f"rating:stats:{rating.event_id}")

    return BaseResponse(
        message="评分更新成功",
        data=RatingOut.model_validate(rating).model_dump(),
    )


@router.get("", response_model=PaginationResponse, summary="查询评分列表")
async def list_ratings(
    event_id: Optional[str] = Query(default=None, description="历史事件ID"),
    session_id: Optional[str] = Query(default=None, description="会话ID"),
    min_score: Optional[float] = Query(default=None, ge=1.0, le=10.0, description="最低评分"),
    max_score: Optional[float] = Query(default=None, ge=1.0, le=10.0, description="最高评分"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Rating.is_deleted == False]
    if event_id:
        conditions.append(Rating.event_id == event_id)
    if session_id:
        conditions.append(Rating.session_id == session_id)
    if min_score is not None:
        conditions.append(Rating.score >= min_score)
    if max_score is not None:
        conditions.append(Rating.score <= max_score)

    count_stmt = select(func.count()).select_from(Rating).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(Rating)
        .where(and_(*conditions))
        .order_by(Rating.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    ratings = result.scalars().all()

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[RatingOut.model_validate(r).model_dump() for r in ratings],
    )


@router.get("/stats/{event_id}", response_model=BaseResponse, summary="获取事件评分统计")
async def get_rating_stats(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    cached = await cache.get(f"rating:stats:{event_id}")
    if cached:
        return BaseResponse(data=cached)

    conditions = [Rating.event_id == event_id, Rating.is_deleted == False]

    avg_stmt = select(
        func.avg(Rating.score).label("avg_score"),
        func.count(Rating.id).label("count"),
        func.avg(Rating.dimension_importance).label("avg_importance"),
        func.avg(Rating.dimension_interest).label("avg_interest"),
        func.avg(Rating.dimension_impact).label("avg_impact"),
    ).where(and_(*conditions))

    result = await db.execute(avg_stmt)
    row = result.one()

    event_name_stmt = select(Rating.event_name).where(and_(*conditions)).limit(1)
    name_result = await db.execute(event_name_stmt)
    event_name = name_result.scalar() or event_id

    stats = {
        "event_id": event_id,
        "event_name": event_name,
        "avg_score": round(float(row.avg_score or 0), 2),
        "count": row.count or 0,
        "avg_importance": round(float(row.avg_importance or 0), 2) if row.avg_importance else None,
        "avg_interest": round(float(row.avg_interest or 0), 2) if row.avg_interest else None,
        "avg_impact": round(float(row.avg_impact or 0), 2) if row.avg_impact else None,
    }

    await cache.set(f"rating:stats:{event_id}", stats)

    return BaseResponse(data=stats)


@router.delete("/{rating_id}", response_model=BaseResponse, summary="删除评分")
async def delete_rating(
    rating_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Rating).where(and_(Rating.id == rating_id, Rating.is_deleted == False))
    result = await db.execute(stmt)
    rating = result.scalar_one_or_none()

    if not rating:
        raise HTTPException(status_code=404, detail="评分记录不存在")

    rating.is_deleted = True
    await db.flush()

    await cache.delete(f"rating:stats:{rating.event_id}")

    return BaseResponse(message="评分已删除")
