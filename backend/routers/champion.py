from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database import get_db
from ..models.champion_card import ChampionCard
from ..redis_client import cache
from ..schemas import (
    BaseResponse,
    PaginationResponse,
    ChampionCardCreate,
    ChampionCardUpdate,
    ChampionCardOut,
    ChampionCardStats,
)

router = APIRouter(prefix="/api/champion", tags=["冠军卡片"])


def _calculate_card_level(explore_count: int, stay_duration: float) -> int:
    score = explore_count * 10 + stay_duration
    if score >= 200:
        return 4
    if score >= 100:
        return 3
    if score >= 50:
        return 2
    return 1


LEVEL_NAMES = {1: "普通", 2: "稀有", 3: "史诗", 4: "传说"}


@router.post("", response_model=BaseResponse, summary="创建或更新冠军卡片")
async def create_champion_card(
    card: ChampionCardCreate,
    db: AsyncSession = Depends(get_db),
):
    check_stmt = select(ChampionCard).where(
        and_(
            ChampionCard.event_id == card.event_id,
            ChampionCard.session_id == card.session_id,
            ChampionCard.is_deleted == False,
        )
    )
    existing_result = await db.execute(check_stmt)
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.explore_count += 1
        existing.card_level = _calculate_card_level(existing.explore_count, existing.total_stay_duration)
        if card.nickname:
            existing.nickname = card.nickname
        if card.related_events:
            existing.related_events = card.related_events
        if card.achievements:
            if existing.achievements:
                combined = set(existing.achievements) | set(card.achievements)
                existing.achievements = list(combined)
            else:
                existing.achievements = card.achievements

        await db.flush()
        await db.refresh(existing)

        return BaseResponse(
            message=f"冠军卡片已更新（等级: {LEVEL_NAMES[existing.card_level]}）",
            data=ChampionCardOut.model_validate(existing).model_dump(),
        )

    new_card = ChampionCard(
        session_id=card.session_id,
        nickname=card.nickname,
        event_id=card.event_id,
        event_name=card.event_name,
        event_year=card.event_year,
        event_region=card.event_region,
        event_description=card.event_description,
        card_level=1,
        explore_count=1,
        related_events=card.related_events,
        achievements=card.achievements,
        owner_session_id=card.session_id,
    )
    db.add(new_card)
    await db.flush()
    await db.refresh(new_card)

    return BaseResponse(
        message="冠军卡片创建成功",
        data=ChampionCardOut.model_validate(new_card).model_dump(),
    )


@router.get("", response_model=PaginationResponse, summary="查询冠军卡片列表")
async def list_champion_cards(
    session_id: Optional[str] = Query(default=None, description="会话ID"),
    owner_session_id: Optional[str] = Query(default=None, description="当前持有人"),
    event_id: Optional[str] = Query(default=None, description="历史事件ID"),
    event_region: Optional[str] = Query(default=None, description="事件区域"),
    card_level: Optional[int] = Query(default=None, ge=1, le=4, description="卡片等级"),
    is_favorite: Optional[bool] = Query(default=None, description="是否收藏"),
    is_high_rated: Optional[bool] = Query(default=None, description="是否高分卡牌"),
    is_on_auction: Optional[bool] = Query(default=None, description="是否拍卖中"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    conditions = [ChampionCard.is_deleted == False]
    if session_id:
        conditions.append(ChampionCard.session_id == session_id)
    if owner_session_id:
        conditions.append(ChampionCard.owner_session_id == owner_session_id)
    if event_id:
        conditions.append(ChampionCard.event_id == event_id)
    if event_region:
        conditions.append(ChampionCard.event_region == event_region)
    if card_level is not None:
        conditions.append(ChampionCard.card_level == card_level)
    if is_favorite is not None:
        conditions.append(ChampionCard.is_favorite == is_favorite)
    if is_high_rated is not None:
        conditions.append(ChampionCard.is_high_rated == is_high_rated)
    if is_on_auction is not None:
        conditions.append(ChampionCard.is_on_auction == is_on_auction)

    count_stmt = select(func.count()).select_from(ChampionCard).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(ChampionCard)
        .where(and_(*conditions))
        .order_by(ChampionCard.card_level.desc(), ChampionCard.explore_count.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    cards = result.scalars().all()

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[ChampionCardOut.model_validate(c).model_dump() for c in cards],
    )


@router.get("/stats/{session_id}", response_model=BaseResponse, summary="获取用户冠军卡片统计")
async def get_champion_stats(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    conditions = [ChampionCard.session_id == session_id, ChampionCard.is_deleted == False]

    total_stmt = select(func.count()).select_from(ChampionCard).where(and_(*conditions))
    total_result = await db.execute(total_stmt)
    total_cards = total_result.scalar() or 0

    explore_stmt = select(func.sum(ChampionCard.explore_count)).where(and_(*conditions))
    explore_result = await db.execute(explore_stmt)
    total_explores = explore_result.scalar() or 0

    fav_stmt = select(func.count()).select_from(ChampionCard).where(
        and_(*conditions, ChampionCard.is_favorite == True)
    )
    fav_result = await db.execute(fav_stmt)
    favorite_count = fav_result.scalar() or 0

    level_stmt = (
        select(ChampionCard.card_level, func.count(ChampionCard.id))
        .where(and_(*conditions))
        .group_by(ChampionCard.card_level)
    )
    level_result = await db.execute(level_stmt)
    level_distribution = {LEVEL_NAMES.get(row[0], str(row[0])): row[1] for row in level_result.all()}

    return BaseResponse(
        data={
            "session_id": session_id,
            "total_cards": total_cards,
            "total_explores": total_explores,
            "favorite_count": favorite_count,
            "level_distribution": level_distribution,
        }
    )


@router.put("/{card_id}", response_model=BaseResponse, summary="更新冠军卡片")
async def update_champion_card(
    card_id: int,
    update: ChampionCardUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChampionCard).where(
        and_(ChampionCard.id == card_id, ChampionCard.is_deleted == False)
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=404, detail="冠军卡片不存在")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(card, field, value)

    await db.flush()
    await db.refresh(card)

    return BaseResponse(
        message="冠军卡片更新成功",
        data=ChampionCardOut.model_validate(card).model_dump(),
    )


@router.delete("/{card_id}", response_model=BaseResponse, summary="删除冠军卡片")
async def delete_champion_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ChampionCard).where(
        and_(ChampionCard.id == card_id, ChampionCard.is_deleted == False)
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(status_code=404, detail="冠军卡片不存在")

    card.is_deleted = True
    await db.flush()

    return BaseResponse(message="冠军卡片已删除")
