from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update

from ..database import get_db
from ..deps import get_optional_user
from ..models.card_auction import CardAuction
from ..models.card_bid import CardBid
from ..models.card_review import CardReview
from ..models.champion_card import ChampionCard
from ..models.user import User
from ..schemas import (
    BaseResponse,
    PaginationResponse,
    CardAuctionCreate,
    CardAuctionOut,
    CardBidCreate,
    CardBidOut,
    CardReviewCreate,
    CardReviewOut,
)

router = APIRouter(prefix="/api/auction", tags=["卡牌拍卖"])

PLATFORM_FEE_RATE = 0.05  # 平台抽佣 5%


async def _expire_auctions(db: AsyncSession) -> None:
    """把过期的 active 拍卖批量结算为 expired"""
    now = datetime.utcnow()
    expired_stmt = select(CardAuction).where(
        and_(CardAuction.status == "active", CardAuction.end_time <= now)
    )
    expired_list = (await db.execute(expired_stmt)).scalars().all()
    for auction in expired_list:
        # 选择 is_winning 的最高出价作为成交价
        winning_stmt = (
            select(CardBid)
            .where(CardBid.auction_id == auction.id)
            .order_by(CardBid.amount.desc(), CardBid.created_at.asc())
            .limit(1)
        )
        winner = (await db.execute(winning_stmt)).scalar_one_or_none()

        if winner:
            auction.status = "sold"
            auction.sold_price = winner.amount
            auction.platform_fee = round(winner.amount * PLATFORM_FEE_RATE, 2)
            auction.seller_revenue = round(winner.amount - auction.platform_fee, 2)
            auction.winner_session_id = winner.bidder_session_id
            winner.is_winning = True

            # 转移卡牌所有权给赢家, 下架 is_on_auction
            card = (
                await db.execute(select(ChampionCard).where(ChampionCard.id == auction.card_id))
            ).scalar_one_or_none()
            if card:
                card.owner_session_id = winner.bidder_session_id
                card.is_on_auction = False

            # 自动加入收藏
            from ..models.user_card_collection import UserCardCollection

            dup_stmt = select(UserCardCollection).where(
                and_(
                    UserCardCollection.user_session_id == winner.bidder_session_id,
                    UserCardCollection.card_id == auction.card_id,
                    UserCardCollection.is_deleted == False,
                )
            )
            if not (await db.execute(dup_stmt)).scalar_one_or_none():
                db.add(UserCardCollection(
                    user_session_id=winner.bidder_session_id,
                    card_id=auction.card_id,
                    event_id=auction.event_id,
                    event_name=auction.event_name,
                    source="auction",
                    is_high_rated=bool(card.is_high_rated) if card else False,
                    collected_at=now,
                ))
        else:
            auction.status = "expired"
            # 退还卡牌, 关闭拍卖状态
            card = (
                await db.execute(select(ChampionCard).where(ChampionCard.id == auction.card_id))
            ).scalar_one_or_none()
            if card:
                card.is_on_auction = False

        await db.flush()


@router.post("", response_model=BaseResponse, summary="上架拍卖")
async def create_auction(
    payload: CardAuctionCreate,
    db: AsyncSession = Depends(get_db),
):
    card_stmt = select(ChampionCard).where(
        and_(ChampionCard.id == payload.card_id, ChampionCard.is_deleted == False)
    )
    card = (await db.execute(card_stmt)).scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="卡牌不存在")

    if card.owner_session_id and card.owner_session_id != payload.seller_session_id:
        raise HTTPException(status_code=403, detail="卡牌当前持有人无法发起拍卖")
    if card.is_on_auction:
        raise HTTPException(status_code=409, detail="该卡牌已在拍卖中")

    end_time = datetime.utcnow() + timedelta(hours=payload.duration_hours)
    auction = CardAuction(
        card_id=payload.card_id,
        event_id=card.event_id,
        event_name=card.event_name,
        seller_session_id=payload.seller_session_id,
        start_price=payload.start_price,
        current_price=payload.start_price,
        min_increment=payload.min_increment,
        end_time=end_time,
        status="active",
        description=payload.description,
        bid_count=0,
    )
    db.add(auction)
    await db.flush()

    # 同步卡牌拍卖状态 / 持有人
    card.is_on_auction = True
    card.owner_session_id = payload.seller_session_id
    await db.refresh(auction)

    return BaseResponse(
        message="上架成功",
        data=CardAuctionOut.model_validate(auction).model_dump(),
    )


@router.get("", response_model=PaginationResponse, summary="拍卖列表")
async def list_auctions(
    status: Optional[str] = Query(default=None, description="状态过滤"),
    event_id: Optional[str] = Query(default=None, description="事件ID"),
    seller_session_id: Optional[str] = Query(default=None, description="卖家"),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await _expire_auctions(db)

    conditions = [CardAuction.is_deleted == False]
    if status:
        conditions.append(CardAuction.status == status)
    if event_id:
        conditions.append(CardAuction.event_id == event_id)
    if seller_session_id:
        conditions.append(CardAuction.seller_session_id == seller_session_id)
    if min_price is not None:
        conditions.append(CardAuction.current_price >= min_price)
    if max_price is not None:
        conditions.append(CardAuction.current_price <= max_price)

    total = (
        await db.execute(select(func.count()).select_from(CardAuction).where(and_(*conditions)))
    ).scalar() or 0

    stmt = (
        select(CardAuction)
        .where(and_(*conditions))
        .order_by(CardAuction.end_time.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(stmt)).scalars().all()

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[CardAuctionOut.model_validate(i).model_dump() for i in items],
    )


@router.get("/{auction_id}", response_model=BaseResponse, summary="拍卖详情")
async def get_auction(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
):
    await _expire_auctions(db)
    stmt = select(CardAuction).where(
        and_(CardAuction.id == auction_id, CardAuction.is_deleted == False)
    )
    auction = (await db.execute(stmt)).scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="拍卖不存在")

    bid_stmt = (
        select(CardBid)
        .where(CardBid.auction_id == auction_id)
        .order_by(CardBid.amount.desc(), CardBid.created_at.asc())
    )
    bids = (await db.execute(bid_stmt)).scalars().all()

    review_stmt = (
        select(CardReview)
        .where(CardReview.auction_id == auction_id)
        .order_by(CardReview.created_at.desc())
    )
    reviews = (await db.execute(review_stmt)).scalars().all()

    # 批量取 reviewer 用户昵称 (登录用户)
    review_user_ids = {r.user_id for r in reviews if r.user_id is not None}
    review_user_map: dict[int, User] = {}
    if review_user_ids:
        user_stmt = select(User).where(User.id.in_(review_user_ids))
        users = (await db.execute(user_stmt)).scalars().all()
        review_user_map = {u.id: u for u in users}

    def _display_name(uid):
        if uid is None:
            return None
        u = review_user_map.get(uid)
        if not u:
            return None
        return (u.nickname or u.username or "").strip() or None

    reviews_payload = []
    for r in reviews:
        item = CardReviewOut.model_validate(r).model_dump()
        item["reviewer_name"] = _display_name(r.user_id)
        reviews_payload.append(item)

    return BaseResponse(data={
        "auction": CardAuctionOut.model_validate(auction).model_dump(),
        "bids": [CardBidOut.model_validate(b).model_dump() for b in bids],
        "reviews": reviews_payload,
    })


@router.post("/bid", response_model=BaseResponse, summary="出价")
async def place_bid(
    payload: CardBidCreate,
    db: AsyncSession = Depends(get_db),
):
    auction_stmt = select(CardAuction).where(
        and_(CardAuction.id == payload.auction_id, CardAuction.is_deleted == False)
    )
    auction = (await db.execute(auction_stmt)).scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="拍卖不存在")
    if auction.status != "active":
        raise HTTPException(status_code=400, detail="拍卖已结束")
    if auction.end_time <= datetime.utcnow():
        # 触发结算
        await _expire_auctions(db)
        raise HTTPException(status_code=400, detail="拍卖已到期")

    if payload.amount < auction.current_price + auction.min_increment:
        raise HTTPException(
            status_code=400,
            detail=f"出价必须 >= {auction.current_price + auction.min_increment}",
        )

    # 把之前的领先出价标记为非领先
    await db.execute(
        update(CardBid)
        .where(and_(CardBid.auction_id == auction.id, CardBid.is_winning == True))
        .values(is_winning=False)
    )

    new_bid = CardBid(
        auction_id=auction.id,
        bidder_session_id=payload.bidder_session_id,
        amount=payload.amount,
        is_winning=True,
    )
    db.add(new_bid)
    await db.flush()

    auction.current_price = payload.amount
    auction.bid_count = (auction.bid_count or 0) + 1
    await db.refresh(new_bid)

    return BaseResponse(
        message="出价成功",
        data=CardBidOut.model_validate(new_bid).model_dump(),
    )


@router.post("/{auction_id}/cancel", response_model=BaseResponse, summary="卖家撤回拍卖")
async def cancel_auction(
    auction_id: int,
    seller_session_id: str = Query(..., description="卖家会话ID"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CardAuction).where(
        and_(CardAuction.id == auction_id, CardAuction.is_deleted == False)
    )
    auction = (await db.execute(stmt)).scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="拍卖不存在")
    if auction.seller_session_id != seller_session_id:
        raise HTTPException(status_code=403, detail="仅卖家可撤回拍卖")
    if auction.status != "active":
        raise HTTPException(status_code=400, detail="拍卖已结束, 无法撤回")

    auction.status = "cancelled"
    card = (
        await db.execute(select(ChampionCard).where(ChampionCard.id == auction.card_id))
    ).scalar_one_or_none()
    if card:
        card.is_on_auction = False
    return BaseResponse(message="拍卖已撤回")


@router.post("/review", response_model=BaseResponse, summary="评价已成交拍卖")
async def create_review(
    payload: CardReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    auction_stmt = select(CardAuction).where(
        and_(CardAuction.id == payload.auction_id, CardAuction.is_deleted == False)
    )
    auction = (await db.execute(auction_stmt)).scalar_one_or_none()
    if not auction:
        raise HTTPException(status_code=404, detail="拍卖不存在")
    if auction.status != "sold":
        raise HTTPException(status_code=400, detail="仅成交拍卖可评价")
    if auction.winner_session_id != payload.reviewer_session_id:
        raise HTTPException(status_code=403, detail="仅获胜买家可评价")

    # 登录态归集: 以后端 token 解析值为准
    resolved_user_id: Optional[int] = current_user.id if current_user else None

    dup_stmt = select(CardReview).where(
        and_(
            CardReview.auction_id == payload.auction_id,
            CardReview.reviewer_session_id == payload.reviewer_session_id,
        )
    )
    existing = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing:
        existing.stars = payload.stars
        existing.comment = payload.comment
        if existing.user_id is None:
            existing.user_id = resolved_user_id
        await db.flush()
        await db.refresh(existing)
        return BaseResponse(
            message="评价已更新",
            data=CardReviewOut.model_validate(existing).model_dump(),
        )

    item = CardReview(
        auction_id=payload.auction_id,
        reviewer_session_id=payload.reviewer_session_id,
        user_id=resolved_user_id,
        stars=payload.stars,
        comment=payload.comment,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return BaseResponse(
        message="评价成功",
        data=CardReviewOut.model_validate(item).model_dump(),
    )
