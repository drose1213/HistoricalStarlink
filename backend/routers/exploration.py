import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.exploration_record import ExplorationRecord
from ..redis_client import cache
from ..schemas import BaseResponse, ExplorationRecordOut, PaginationResponse

router = APIRouter(prefix="/api/exploration", tags=["exploration"])


class ExploreStartRequest(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=128, description="Historical event ID")
    session_id: Optional[str] = Field(default=None, max_length=64, description="Session ID")
    event_name: Optional[str] = Field(default=None, max_length=256, description="Historical event name")


class ExploreEndRequest(BaseModel):
    record_id: int = Field(..., gt=0, description="Exploration record ID")
    duration_seconds: float = Field(default=0.0, ge=0, description="Stay duration in seconds")
    path_depth: int = Field(default=0, ge=0, description="Exploration path depth")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Exploration notes")


@router.post("/start", response_model=BaseResponse, summary="Start exploration")
async def start_exploration(
    req: ExploreStartRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    event_id = req.event_id.strip()
    if not event_id:
        raise HTTPException(status_code=400, detail="event_id is required")

    session_id = (req.session_id or str(uuid.uuid4())[:16]).strip()
    event_name = (req.event_name or event_id).strip()
    new_record = ExplorationRecord(
        session_id=session_id,
        event_id=event_id,
        event_name=event_name,
        depth=0,
        explore_path={"events": [event_id]},
        stay_duration=0.0,
        from_direction="initial",
        user_agent=request.headers.get("user-agent", ""),
        ip_address=request.client.host if request.client else None,
    )
    db.add(new_record)
    await db.flush()
    await db.refresh(new_record)

    await cache.incr(f"exploration:event:{event_id}:count")
    await cache.incr("exploration:total_count")

    return BaseResponse(
        message="Exploration started",
        data=ExplorationRecordOut.model_validate(new_record).model_dump(),
    )


@router.post("/end", response_model=BaseResponse, summary="End exploration")
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
    if req.notes is not None:
        notes = req.notes.strip()
        record.notes = notes or None
        current_path = record.explore_path if isinstance(record.explore_path, dict) else {}
        record.explore_path = {**current_path, "notes": record.notes}
    await db.flush()

    return BaseResponse(
        message="Exploration ended",
        data=ExplorationRecordOut.model_validate(record).model_dump(),
    )


@router.get("/records", response_model=PaginationResponse, summary="List exploration records")
async def list_exploration_records(
    session_id: Optional[str] = Query(default=None, description="Session ID"),
    event_id: Optional[str] = Query(default=None, description="Historical event ID"),
    event_region: Optional[str] = Query(default=None, description="Event region"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
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
        data=[ExplorationRecordOut.model_validate(r).model_dump() for r in records],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/records/{record_id}", response_model=BaseResponse, summary="Get exploration record")
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
        raise HTTPException(status_code=404, detail="Exploration record not found")

    return BaseResponse(data=ExplorationRecordOut.model_validate(record).model_dump())


@router.get("/event/{event_id}", response_model=BaseResponse, summary="Get event exploration records")
async def get_exploration_by_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ExplorationRecord)
        .where(and_(ExplorationRecord.event_id == event_id, ExplorationRecord.is_deleted == False))
        .order_by(ExplorationRecord.created_at.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    return BaseResponse(data=[ExplorationRecordOut.model_validate(r).model_dump() for r in records])


@router.get("/stats", response_model=BaseResponse, summary="Exploration stats")
async def get_exploration_stats(
    session_id: Optional[str] = Query(default=None, description="Session ID"),
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
    total_duration = float(duration_result.scalar() or 0.0)

    return BaseResponse(
        data={
            "total_records": total,
            "unique_events": unique_events,
            "total_stay_duration": round(total_duration, 2),
        }
    )


@router.delete("/records/{record_id}", response_model=BaseResponse, summary="Delete exploration record")
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
        raise HTTPException(status_code=404, detail="Exploration record not found")

    record.is_deleted = True
    await db.flush()
    return BaseResponse(message="Exploration record deleted")