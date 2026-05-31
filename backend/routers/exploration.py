import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.future import select

from ..database import get_db
from ..models.exploration_record import ExplorationRecord
from ..redis_client import cache
from ..schemas import (
    BaseResponse,
    PaginationResponse,
    ExplorationRecordCreate,
    ExplorationRecordOut,
)

router = APIRouter(prefix="/api/exploration", tags=["探索记录"])


class ExploreStartRequest(BaseModel):
    event_id: str = Field(..., description="历史事件ID")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    event_name: Optional[str] = Field(default=None, description="事件名称")


class ExploreEndRequest(BaseModel):
    record_id: int = Field(..., description="记录ID")
    duration_seconds: float = Field(default=0.0, description="停留时长秒")
    path_depth: int = Field(default=0, description="路径深度")
    notes: Optional[str] = Field(default=None, description="备注")


@router.post("/start", response_model=BaseResponse, summary="开始探索")
async def start_exploration(
    req: ExploreStartRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    session_id = req.session_id or str(uuid.uuid4())[:16]

    new_record = ExplorationRecord(
        session_id=session_id,
        event_id=req.event_id,
        event_name=req.event_name or req.event_id,
        depth=0,
        explore_path={"events": [req.event_id]},
        stay_duration=0.0,
        from_direction="initial",
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_record)
    await db.flush()
    await db.refresh(new_record)

    await cache.incr(f"exploration:event:{req.event_id}:count")
    await cache.incr("exploration:total_count")

    out = ExplorationRecordOut.model_validate(new_record).model_dump()
    return BaseResponse(
        message="Exploration started",
        data=out,
    )


@router.post("/end", response_model=BaseResponse, summary="结束探索")
async def end_exploration(
    req: ExploreEndRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExplorationRecord).where(
        and_(ExplorationRecord.id == req.record_id, ExplorationRecord.is_deleted == False)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    record.stay_duration = req.duration_seconds
    record.depth = req.path_depth
    await db.flush()

    out = ExplorationRecordOut.model_validate(record).model_dump()
    return BaseResponse(
        message="Exploration ended",
        data=out,
    )


@router.get("/records", response_model=PaginationResponse, summary="查询探索记录列表")
async def list_exploration_records(
    session_id: Optional[str] = Query(default=None, description="会话ID"),
    event_id: Optional[str] = Query(default=None, description="历史事件ID"),
    event_region: Optional[str] = Query(default=None, description="事件区域"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    conditions = [ExplorationRecord.is_deleted == False]
    if session_id:
        conditions.append(ExplorationRecord.session_id == session_id)
    if event_id:
        conditions.append(ExplorationRecord.event_id == event_id)
    if event_region:
        conditions.append(ExplorationRecord.event_region == event_region)

    count_stmt = select(func.count()).select_from(ExplorationRecord).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(ExplorationRecord)
        .where(and_(*conditions))
        .order_by(ExplorationRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[ExplorationRecordOut.model_validate(r).model_dump() for r in records],
    )


@router.get("/records/{record_id}", response_model=BaseResponse, summary="获取单条探索记录")
async def get_exploration_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExplorationRecord).where(
        and_(ExplorationRecord.id == record_id, ExplorationRecord.is_deleted == False)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="探索记录不存在")

    return BaseResponse(data=ExplorationRecordOut.model_validate(record).model_dump())


@router.get("/event/{event_id}", response_model=BaseResponse, summary="获取某事件的探索记录")
async def get_exploration_by_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ExplorationRecord)
        .where(and_(ExplorationRecord.event_id == event_id, ExplorationRecord.is_deleted == False))
        .order_by(ExplorationRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return BaseResponse(
        data=[ExplorationRecordOut.model_validate(r).model_dump() for r in records],
    )


@router.get("/stats", response_model=BaseResponse, summary="探索统计信息")
async def get_exploration_stats(
    session_id: Optional[str] = Query(default=None, description="会话ID"),
    db: AsyncSession = Depends(get_db),
):
    conditions = [ExplorationRecord.is_deleted == False]
    if session_id:
        conditions.append(ExplorationRecord.session_id == session_id)

    total_stmt = select(func.count()).select_from(ExplorationRecord).where(and_(*conditions))
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    unique_stmt = (
        select(func.count(func.distinct(ExplorationRecord.event_id)))
        .select_from(ExplorationRecord)
        .where(and_(*conditions))
    )
    unique_result = await db.execute(unique_stmt)
    unique_events = unique_result.scalar() or 0

    duration_stmt = select(func.sum(ExplorationRecord.stay_duration)).where(and_(*conditions))
    duration_result = await db.execute(duration_stmt)
    total_duration = duration_result.scalar() or 0.0

    return BaseResponse(
        data={
            "total_records": total,
            "unique_events": unique_events,
            "total_stay_duration": round(total_duration, 2),
        }
    )


@router.delete("/records/{record_id}", response_model=BaseResponse, summary="删除探索记录")
async def delete_exploration_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExplorationRecord).where(
        and_(ExplorationRecord.id == record_id, ExplorationRecord.is_deleted == False)
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="探索记录不存在")

    record.is_deleted = True
    await db.flush()

    return BaseResponse(message="探索记录已删除")
