import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.analytics import AnalyticsEvent

logger = logging.getLogger(__name__)

ALLOWED_EVENTS = {
    "app_enter",
    "dialogue_completed",
    "paywall_clicked",
    "feedback_submitted",
}

router = APIRouter(prefix="/api/analytics", tags=["埋点分析"])


class AnalyticsEventRequest(BaseModel):
    """埋点事件上报请求"""
    event_name: str = Field(..., min_length=1, max_length=50, description="事件名")
    user_agent: Optional[str] = Field(default=None, max_length=500, description="浏览器UA")
    topic: Optional[str] = Field(default=None, max_length=200, description="关联话题/事件")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="附加数据")

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, v: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("payload 必须是 dict 类型")
        return v


@router.post("/event", summary="上报埋点事件")
async def create_event(
    req: AnalyticsEventRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # event_name 白名单 -> 业务层校验, 显式返回 400
    if req.event_name not in ALLOWED_EVENTS:
        raise HTTPException(
            status_code=400,
            detail=f"event_name 必须是 {sorted(ALLOWED_EVENTS)} 之一",
        )

    user_agent = req.user_agent or request.headers.get("user-agent", "")

    try:
        event = AnalyticsEvent(
            event_name=req.event_name,
            user_agent=user_agent[:500] if user_agent else None,
            topic=req.topic,
            payload=req.payload or {},
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("create analytics event failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to record analytics event")

    return {"success": True, "event_id": event.id}


@router.get("/summary", summary="14 天埋点数据汇总 (PMF 基线报告)")
async def get_summary(
    db: AsyncSession = Depends(get_db),
):
    """聚合 AnalyticsEvent 表，输出 PMF 基线报告所需的指标。

    - total_events / unique_users / event_counts / top_topics
    - avg_dialogue_duration_seconds / avg_feedback_rating
    空表 / 无匹配数据时返回 0 / [] / 0.0，绝不抛 500。
    """
    try:
        # ---- 1) total_events ----
        total_events = (
            await db.execute(select(func.count(AnalyticsEvent.id)))
        ).scalar() or 0

        # ---- 2) unique_users (按 user_agent 去重) ----
        unique_users = (
            await db.execute(
                select(func.count(func.distinct(AnalyticsEvent.user_agent)))
            )
        ).scalar() or 0

        # ---- 3) event_counts (按 event_name 分组) ----
        event_counts_rows = (
            await db.execute(
                select(
                    AnalyticsEvent.event_name,
                    func.count(AnalyticsEvent.id),
                ).group_by(AnalyticsEvent.event_name)
            )
        ).all()
        event_counts: Dict[str, int] = {name: 0 for name in ALLOWED_EVENTS}
        for name, cnt in event_counts_rows:
            if name in event_counts:
                event_counts[name] = int(cnt)

        # ---- 4) top_topics (仅 dialogue_completed, 按 count 倒序 limit 10) ----
        topic_rows = (
            await db.execute(
                select(
                    AnalyticsEvent.topic,
                    func.count(AnalyticsEvent.id).label("cnt"),
                )
                .where(AnalyticsEvent.event_name == "dialogue_completed")
                .where(AnalyticsEvent.topic.isnot(None))
                .where(AnalyticsEvent.topic != "")
                .group_by(AnalyticsEvent.topic)
                .order_by(func.count(AnalyticsEvent.id).desc())
                .limit(10)
            )
        ).all()
        top_topics: List[Dict[str, Any]] = [
            {"topic": topic, "count": int(cnt)}
            for topic, cnt in topic_rows
            if topic
        ]

        # ---- 5) avg_dialogue_duration_seconds (JSON 字段取平均) ----
        # SQLite/JSON: 用 json_extract; MySQL: 用 JSON_EXTRACT — SQLAlchemy
        # 的 JSON 类型在 select 时已是 Python dict, 但跨 DB 通用做法是
        # 拉出 dialogue_completed 行的 payload 后在 Python 侧取平均。
        dialogue_rows = (
            await db.execute(
                select(AnalyticsEvent.payload).where(
                    AnalyticsEvent.event_name == "dialogue_completed"
                )
            )
        ).all()
        durations: List[float] = []
        for (payload,) in dialogue_rows:
            if not isinstance(payload, dict):
                continue
            val = payload.get("duration_seconds")
            if isinstance(val, (int, float)):
                durations.append(float(val))
        avg_dialogue_duration_seconds = (
            round(sum(durations) / len(durations), 2) if durations else 0.0
        )

        # ---- 6) avg_feedback_rating (JSON 字段取平均) ----
        feedback_rows = (
            await db.execute(
                select(AnalyticsEvent.payload).where(
                    AnalyticsEvent.event_name == "feedback_submitted"
                )
            )
        ).all()
        ratings: List[float] = []
        for (payload,) in feedback_rows:
            if not isinstance(payload, dict):
                continue
            val = payload.get("rating")
            if isinstance(val, (int, float)):
                ratings.append(float(val))
        avg_feedback_rating = (
            round(sum(ratings) / len(ratings), 2) if ratings else 0.0
        )

        return {
            "total_events": int(total_events),
            "unique_users": int(unique_users),
            "event_counts": event_counts,
            "top_topics": top_topics,
            "avg_dialogue_duration_seconds": avg_dialogue_duration_seconds,
            "avg_feedback_rating": avg_feedback_rating,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get analytics summary failed: %s", e)
        # 退化: 永远不抛 500, 返回全 0 让前端能渲染空态
        return {
            "total_events": 0,
            "unique_users": 0,
            "event_counts": {name: 0 for name in ALLOWED_EVENTS},
            "top_topics": [],
            "avg_dialogue_duration_seconds": 0.0,
            "avg_feedback_rating": 0.0,
        }
