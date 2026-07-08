from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database import get_db
from ..models.user_card_collection import UserCardCollection
from ..models.champion_card import ChampionCard
from ..redis_client import cache
from ..schemas import (
    BaseResponse,
    PaginationResponse,
    UserCardCollectionCreate,
    UserCardCollectionOut,
)

router = APIRouter(prefix="/api/collection", tags=["卡牌收藏"])

HIGH_RATED_THRESHOLD = 8.0  # 评分 1.0-10.0 体系下, >=8.0 视为高分


async def _refresh_card_high_rated_flag(db: AsyncSession, card_id: int) -> None:
    """根据该卡牌所属事件的所有评分刷新 is_high_rated 标志 (单次 JOIN 查询)"""
    from ..models.rating import Rating

    # 一次性 JOIN: 取出卡片及对应事件平均分, 避免 N+1
    stmt = (
        select(ChampionCard, func.coalesce(func.avg(Rating.score), 0).label("avg_score"))
        .outerjoin(Rating, and_(Rating.event_id == ChampionCard.event_id, Rating.is_deleted == False))
        .where(and_(ChampionCard.id == card_id, ChampionCard.is_deleted == False))
        .group_by(ChampionCard.id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        return
    card, avg_score = row[0], row[1]
    card.is_high_rated = bool(avg_score and avg_score >= HIGH_RATED_THRESHOLD)


@router.post("", response_model=BaseResponse, summary="新增卡牌收藏")
async def add_collection(
    payload: UserCardCollectionCreate,
    db: AsyncSession = Depends(get_db),
):
    card_stmt = select(ChampionCard).where(
        and_(ChampionCard.id == payload.card_id, ChampionCard.is_deleted == False)
    )
    card = (await db.execute(card_stmt)).scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="卡牌不存在")

    dup_stmt = select(UserCardCollection).where(
        and_(
            UserCardCollection.user_session_id == payload.user_session_id,
            UserCardCollection.card_id == payload.card_id,
            UserCardCollection.is_deleted == False,
        )
    )
    existing = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing:
        return BaseResponse(
            message="该卡牌已在收藏中",
            data=UserCardCollectionOut.model_validate(existing).model_dump(),
        )

    # 同步卡牌持有者与高分标记
    card.owner_session_id = payload.user_session_id
    await _refresh_card_high_rated_flag(db, payload.card_id)

    item = UserCardCollection(
        user_session_id=payload.user_session_id,
        card_id=payload.card_id,
        event_id=card.event_id,
        event_name=card.event_name,
        source=payload.source,
        is_high_rated=bool(card.is_high_rated),
        collected_at=datetime.utcnow(),
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)

    return BaseResponse(
        message="收藏成功",
        data=UserCardCollectionOut.model_validate(item).model_dump(),
    )


@router.get("", response_model=PaginationResponse, summary="查询我的收藏")
async def list_collections(
    user_session_id: Optional[str] = Query(default=None, description="用户会话ID"),
    is_high_rated: Optional[bool] = Query(default=None, description="仅看高分卡牌"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    conditions = [UserCardCollection.is_deleted == False]
    if user_session_id:
        conditions.append(UserCardCollection.user_session_id == user_session_id)
    if is_high_rated is not None:
        conditions.append(UserCardCollection.is_high_rated == is_high_rated)

    total = (
        await db.execute(select(func.count()).select_from(UserCardCollection).where(and_(*conditions)))
    ).scalar() or 0

    stmt = (
        select(UserCardCollection)
        .where(and_(*conditions))
        .order_by(UserCardCollection.collected_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(stmt)).scalars().all()

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[UserCardCollectionOut.model_validate(i).model_dump() for i in items],
    )


@router.delete("/{collection_id}", response_model=BaseResponse, summary="移除收藏")
async def remove_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(UserCardCollection).where(
        and_(UserCardCollection.id == collection_id, UserCardCollection.is_deleted == False)
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="收藏记录不存在")
    item.is_deleted = True
    await db.flush()
    return BaseResponse(message="已移除收藏")
