from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case

from ..database import get_db
from ..models.card_review import CardReview
from ..models.review_like import ReviewLike
from ..redis_client import cache
from ..schemas import (
    BaseResponse,
    PaginationResponse,
    CardReviewListItem,
    CardReviewToggleLikeOut,
    CardReviewCreate,
    CardReviewOut,
)

router = APIRouter(prefix="/api/review", tags=["卡牌评价"])


def _mask_session(session_id: str) -> str:
    """前端显示用的 session 脱敏，例如 abc12345 -> ab***45"""
    if not session_id or len(session_id) <= 4:
        return "****"
    return f"{session_id[:2]}***{session_id[-2:]}"


@router.get("/list", response_model=PaginationResponse, summary="评价列表")
async def list_reviews(
    card_id: int = Query(..., description="卡牌ID"),
    min_stars: Optional[int] = Query(default=None, ge=1, le=5),
    max_stars: Optional[int] = Query(default=None, ge=1, le=5),
    session_id: Optional[str] = Query(default=None, description="当前会话，用于标记 liked_by_me"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """返回卡牌的评价列表（顶级评价 + 树状回复）"""
    # 取顶级评价（parent_review_id is null）
    top_conditions = [CardReview.card_id == card_id, CardReview.parent_review_id.is_(None)]
    if min_stars is not None:
        top_conditions.append(CardReview.stars >= min_stars)
    if max_stars is not None:
        top_conditions.append(CardReview.stars <= max_stars)

    count_stmt = select(func.count()).select_from(CardReview).where(and_(*top_conditions))
    total = (await db.execute(count_stmt)).scalar() or 0

    top_stmt = (
        select(CardReview)
        .where(and_(*top_conditions))
        .order_by(CardReview.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    top_reviews = (await db.execute(top_stmt)).scalars().all()

    # 获取所有回复
    top_ids = [r.id for r in top_reviews]
    replies_map: dict[int, list[CardReview]] = {}
    if top_ids:
        reply_stmt = (
            select(CardReview)
            .where(CardReview.parent_review_id.in_(top_ids))
            .order_by(CardReview.created_at.asc())
        )
        replies = (await db.execute(reply_stmt)).scalars().all()
        for reply in replies:
            replies_map.setdefault(reply.parent_review_id, []).append(reply)

    # liked_by_me
    liked_ids: set[int] = set()
    if session_id and top_ids:
        like_stmt = select(ReviewLike.review_id).where(
            and_(
                ReviewLike.review_id.in_(top_ids + [r.id for rs in replies_map.values() for r in rs]),
                ReviewLike.user_session_id == session_id,
                ReviewLike.is_deleted == False,
            )
        )
        liked_ids = set((await db.execute(like_stmt)).scalars().all())

    items: list[dict] = []
    for r in top_reviews:
        item = CardReviewListItem(
            id=r.id,
            card_id=r.card_id,
            auction_id=r.auction_id,
            reviewer_session_id=_mask_session(r.reviewer_session_id),
            stars=r.stars,
            comment=r.comment,
            parent_review_id=r.parent_review_id,
            likes_count=r.likes_count or 0,
            liked_by_me=r.id in liked_ids,
            reply_count=len(replies_map.get(r.id, [])),
            created_at=r.created_at,
            updated_at=r.updated_at,
        ).model_dump()
        # 嵌入回复（脱敏）
        item["replies"] = [
            CardReviewListItem(
                id=rp.id,
                card_id=rp.card_id,
                auction_id=rp.auction_id,
                reviewer_session_id=_mask_session(rp.reviewer_session_id),
                stars=rp.stars,
                comment=rp.comment,
                parent_review_id=rp.parent_review_id,
                likes_count=rp.likes_count or 0,
                liked_by_me=rp.id in liked_ids,
                reply_count=0,
                created_at=rp.created_at,
                updated_at=rp.updated_at,
            ).model_dump()
            for rp in replies_map.get(r.id, [])
        ]
        items.append(item)

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=items,
    )


@router.post("", response_model=BaseResponse, summary="创建评价（卡牌或回复）")
async def create_review(
    payload: CardReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    if not payload.auction_id and not payload.card_id:
        raise HTTPException(status_code=400, detail="auction_id 和 card_id 至少需要一个")

    # 如果是回复，校验父评价存在
    if payload.parent_review_id is not None:
        parent_stmt = select(CardReview).where(CardReview.id == payload.parent_review_id)
        parent = (await db.execute(parent_stmt)).scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="父评价不存在")

    # 卡牌维度去重：同一 session 对同一卡牌只能有一条顶级评价
    if payload.card_id and payload.parent_review_id is None:
        dup_stmt = select(CardReview).where(
            and_(
                CardReview.card_id == payload.card_id,
                CardReview.reviewer_session_id == payload.reviewer_session_id,
                CardReview.parent_review_id.is_(None),
            )
        )
        existing = (await db.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            existing.stars = payload.stars
            existing.comment = payload.comment
            await db.flush()
            await db.refresh(existing)
            return BaseResponse(
                message="评价已更新",
                data=CardReviewOut.model_validate(existing).model_dump(),
            )

    item = CardReview(
        card_id=payload.card_id,
        auction_id=payload.auction_id,
        reviewer_session_id=payload.reviewer_session_id,
        stars=payload.stars,
        comment=payload.comment,
        parent_review_id=payload.parent_review_id,
        likes_count=0,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)

    return BaseResponse(
        message="评价成功",
        data=CardReviewOut.model_validate(item).model_dump(),
    )


@router.post("/{review_id}/like", response_model=BaseResponse, summary="评价点赞 toggle")
async def toggle_review_like(
    review_id: int,
    user_session_id: str = Query(..., description="点赞者会话ID"),
    db: AsyncSession = Depends(get_db),
):
    review_stmt = select(CardReview).where(CardReview.id == review_id)
    review = (await db.execute(review_stmt)).scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")

    like_stmt = select(ReviewLike).where(
        and_(
            ReviewLike.review_id == review_id,
            ReviewLike.user_session_id == user_session_id,
        )
    )
    existing = (await db.execute(like_stmt)).scalar_one_or_none()

    if existing and not existing.is_deleted:
        # 取消点赞
        existing.is_deleted = True
        review.likes_count = max(0, (review.likes_count or 0) - 1)
        liked = False
    else:
        if existing:
            existing.is_deleted = False
        else:
            db.add(ReviewLike(review_id=review_id, user_session_id=user_session_id))
        review.likes_count = (review.likes_count or 0) + 1
        liked = True

    await db.flush()
    await db.refresh(review)

    return BaseResponse(
        data=CardReviewToggleLikeOut(
            review_id=review_id,
            liked=liked,
            likes_count=review.likes_count or 0,
        ).model_dump(),
    )


@router.delete("/{review_id}", response_model=BaseResponse, summary="删除评价（仅作者）")
async def delete_review(
    review_id: int,
    user_session_id: str = Query(..., description="操作者会话ID"),
    db: AsyncSession = Depends(get_db),
):
    review_stmt = select(CardReview).where(CardReview.id == review_id)
    review = (await db.execute(review_stmt)).scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")
    if review.reviewer_session_id != user_session_id:
        raise HTTPException(status_code=403, detail="只能删除自己的评价")
    await db.delete(review)
    await db.flush()
    return BaseResponse(message="评价已删除")
