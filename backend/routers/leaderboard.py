import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.exploration_record import ExplorationRecord
from ..models.user import User
from ..models.event import HistoryEvent
from ..schemas import BaseResponse

logger = logging.getLogger("historical_starlink.leaderboard")

router = APIRouter(prefix="/api/leaderboard", tags=["探索排行榜"])


def _period_range(period: str) -> Optional[datetime]:
    now = datetime.utcnow()
    if period == "daily":
        return now - timedelta(days=1)
    if period == "weekly":
        return now - timedelta(days=7)
    if period == "monthly":
        return now - timedelta(days=30)
    if period == "yearly":
        return now - timedelta(days=365)
    return None


@router.get("", summary="获取探索排行榜")
async def get_leaderboard(
    period: str = Query(default="weekly", pattern="^(daily|weekly|monthly|yearly)$"),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    since = _period_range(period)

    conditions = [ExplorationRecord.is_deleted == False]
    if since:
        conditions.append(ExplorationRecord.created_at >= since)

    session_stats = (
        select(
            ExplorationRecord.session_id.label("session_id"),
            func.count(ExplorationRecord.id).label("explore_count"),
            func.coalesce(func.sum(ExplorationRecord.stay_duration), 0).label("total_duration"),
            func.max(ExplorationRecord.event_id).label("favorite_event_id"),
            func.max(ExplorationRecord.event_name).label("favorite_event_name"),
        )
        .where(and_(*conditions))
        .group_by(ExplorationRecord.session_id)
        .order_by(func.count(ExplorationRecord.id).desc())
        .limit(limit)
    )
    result = await db.execute(session_stats)
    rows = result.all()

    user_map: dict[str, User] = {}
    session_ids = [r.session_id for r in rows]
    if session_ids:
        try:
            numeric_ids = [int(s) for s in session_ids if s and s.isdigit()]
            if numeric_ids:
                user_stmt = select(User).where(User.id.in_(numeric_ids))
                user_result = await db.execute(user_stmt)
                for u in user_result.scalars().all():
                    user_map[str(u.id)] = u
        except Exception:
            user_map = {}

    ranking = []
    for idx, r in enumerate(rows):
        user = user_map.get(r.session_id)
        ranking.append({
            "id": idx + 1,
            "sessionId": r.session_id,
            "name": user.nickname or user.username if user else f"探索者 #{r.session_id[:6]}",
            "exploreCount": int(r.explore_count),
            "totalDuration": int(r.total_duration),
            "favoriteEvent": r.favorite_event_name or "",
        })

    event_stats = (
        select(
            ExplorationRecord.event_id.label("event_id"),
            func.max(ExplorationRecord.event_name).label("event_name"),
            func.count(ExplorationRecord.id).label("explore_count"),
        )
        .where(and_(*conditions))
        .group_by(ExplorationRecord.event_id)
        .order_by(func.count(ExplorationRecord.id).desc())
        .limit(5)
    )
    event_result = await db.execute(event_stats)
    event_rows = event_result.all()

    champion_events = [
        {
            "name": r.event_name or r.event_id,
            "exploreCount": int(r.explore_count),
        }
        for r in event_rows
    ]

    return BaseResponse(data={
        "period": period,
        "ranking": ranking,
        "championEvents": champion_events,
    })
