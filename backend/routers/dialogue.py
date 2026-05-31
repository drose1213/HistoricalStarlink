import re
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database import get_db
from ..models.dialogue import DialogueSession

SESSION_PATTERN = re.compile(r'^session_\d+_[a-zA-Z0-9]{8}$')


def validate_session_id(session_id: str) -> str:
    if not SESSION_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session format")
    return session_id


def parse_dialogue_id(raw: str) -> int:
    try:
        return int(raw)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid dialogue ID")
from ..dialogue_engine import (
    generate_opening,
    process_choice,
    process_free_text,
    process_post_ending,
    calculate_timeline_branches,
    get_available_events,
    get_script,
)
from ..schemas import BaseResponse, PaginationResponse

router = APIRouter(prefix="/api/dialogue", tags=["对话探索"])


class DialogueStartRequest(BaseModel):
    event_id: str = Field(..., description="历史事件ID")
    session_id: Optional[str] = Field(default=None, description="用户会话ID")


class DialogueChoiceRequest(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")
    choice_id: str = Field(..., description="选择ID")
    round: Optional[int] = Field(default=None, description="当前轮次")


class DialogueChatRequest(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")
    message: str = Field(..., min_length=1, max_length=500, description="用户消息")


@router.post("/start", response_model=BaseResponse, summary="启动对话探索")
async def start_dialogue(
    req: DialogueStartRequest,
    db: AsyncSession = Depends(get_db),
):
    event_id = req.event_id
    session_id = req.session_id or f"session_{int(__import__('time').time())}_{uuid.uuid4().hex[:8]}"
    if session_id:
        validate_session_id(session_id)

    opening = generate_opening(event_id)
    if not opening:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' has no dialogue script")

    script = get_script(event_id)

    history = [
        {
            "role": "narrative",
            "content": f"【{script['context']}】\n\n{opening['narrative']}",
            "choices": opening["choices"],
            "round": 1
        }
    ]

    dialogue = DialogueSession(
        session_id=session_id,
        event_id=event_id,
        event_name=script["npc_name"],
        npc_name=script["npc_name"],
        dialogue_history=history,
        choices_made=[],
        timeline_branches=[],
        current_round=1,
        path_depth=0,
    )
    db.add(dialogue)
    await db.flush()
    await db.refresh(dialogue)

    return BaseResponse(
        message="Dialogue started",
        data={
            "dialogue_id": dialogue.id,
            "session_id": session_id,
            "event_id": event_id,
            "npc_name": opening["npc_name"],
            "npc_role": opening["npc_role"],
            "npc_symbol": opening["npc_symbol"],
            "context": opening["context"],
            "narrative": opening["narrative"],
            "choices": opening["choices"],
            "round": 1,
            "history": history,
        }
    )


@router.post("/choice", response_model=BaseResponse, summary="发送选择")
async def send_choice(
    req: DialogueChoiceRequest,
    db: AsyncSession = Depends(get_db),
):
    dialogue_id = parse_dialogue_id(req.dialogue_id)
    stmt = select(DialogueSession).where(
        and_(DialogueSession.id == dialogue_id, DialogueSession.is_deleted == False)
    )
    result = await db.execute(stmt)
    dialogue = result.scalar_one_or_none()

    if not dialogue:
        raise HTTPException(status_code=404, detail="Dialogue not found")

    if dialogue.is_completed:
        raise HTTPException(status_code=400, detail="Dialogue already completed")

    current_round = dialogue.current_round
    choices_made = dialogue.choices_made or []

    response = process_choice(dialogue.event_id, req.choice_id, current_round, choices_made)
    if not response:
        raise HTTPException(status_code=400, detail="Invalid choice for current round")

    new_choices_made = choices_made + [{
        "round": current_round,
        "choice_id": req.choice_id,
    }]
    new_choices_made_full = []
    for cm in new_choices_made:
        entry = dict(cm)
        new_choices_made_full.append(entry)

    user_msg = {
        "role": "choice",
        "content": f"choice:{req.choice_id}",
        "choice_id": req.choice_id,
        "round": current_round,
    }
    npc_msg = {
        "role": "narrative",
        "content": response["narrative"],
        "choices": response.get("choices", []),
        "round": response.get("round", current_round + 1),
        "timeline_change": response.get("timeline_change", False),
        "mood": response.get("mood"),
    }

    history = (dialogue.dialogue_history or []) + [user_msg, npc_msg]

    dialogue.dialogue_history = history
    dialogue.choices_made = new_choices_made_full
    dialogue.current_round = response.get("round", current_round + 1)
    dialogue.path_depth = dialogue.path_depth + 1

    if response.get("is_ending"):
        dialogue.is_completed = True
        dialogue.outcome_summary = response.get("ending_type", "historical")
        dialogue.timeline_branches = calculate_timeline_branches(new_choices_made_full)

    await db.flush()

    return BaseResponse(
        data={
            "dialogue_id": dialogue.id,
            "narrative": response["narrative"],
            "choices": response.get("choices", []),
            "round": response.get("round", 0),
            "timeline_change": response.get("timeline_change", False),
            "mood": response.get("mood"),
            "is_ending": response.get("is_ending", False),
            "ending_type": response.get("ending_type"),
            "choices_summary": response.get("choices_summary"),
            "history": history,
        }
    )


@router.post("/chat", response_model=BaseResponse, summary="自由文字输入")
async def free_chat(
    req: DialogueChatRequest,
    db: AsyncSession = Depends(get_db),
):
    dialogue_id = int(req.dialogue_id)
    stmt = select(DialogueSession).where(
        and_(DialogueSession.id == dialogue_id, DialogueSession.is_deleted == False)
    )
    result = await db.execute(stmt)
    dialogue = result.scalar_one_or_none()

    if not dialogue:
        raise HTTPException(status_code=404, detail="Dialogue not found")

    if dialogue.is_completed:
        response = process_post_ending(dialogue.event_id, req.message)
        user_msg = {
            "role": "user",
            "content": req.message,
            "round": 0,
        }
        npc_msg = {
            "role": "narrative",
            "content": response["narrative"],
            "choices": [],
            "round": 0,
        }
        history = (dialogue.dialogue_history or []) + [user_msg, npc_msg]
        dialogue.dialogue_history = history
        await db.flush()

        return BaseResponse(
            data={
                "dialogue_id": dialogue.id,
                "narrative": response["narrative"],
                "choices": [],
                "round": 0,
                "timeline_change": False,
                "is_ending": True,
                "history": history,
            }
        )

    current_round = dialogue.current_round
    choices_made = dialogue.choices_made or []

    response = process_free_text(dialogue.event_id, req.message, current_round, choices_made)

    user_msg = {
        "role": "user",
        "content": req.message,
        "round": current_round,
    }
    npc_msg = {
        "role": "narrative",
        "content": response["narrative"],
        "choices": response.get("choices", []),
        "round": response.get("round", current_round),
    }

    history = (dialogue.dialogue_history or []) + [user_msg, npc_msg]
    dialogue.dialogue_history = history

    await db.flush()

    return BaseResponse(
        data={
            "dialogue_id": dialogue.id,
            "narrative": response["narrative"],
            "choices": response.get("choices", []),
            "round": response.get("round", current_round),
            "timeline_change": response.get("timeline_change", False),
            "is_ending": response.get("is_ending", False),
            "history": history,
        }
    )


@router.get("/records", response_model=PaginationResponse, summary="查询对话记录列表")
async def list_dialogues(
    session_id: Optional[str] = Query(default=None),
    event_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions = [DialogueSession.is_deleted == False]
    if session_id:
        conditions.append(DialogueSession.session_id == session_id)
    if event_id:
        conditions.append(DialogueSession.event_id == event_id)

    count_stmt = select(func.count()).select_from(DialogueSession).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(DialogueSession)
        .where(and_(*conditions))
        .order_by(DialogueSession.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    items = []
    for r in records:
        items.append({
            "id": r.id,
            "session_id": r.session_id,
            "event_id": r.event_id,
            "event_name": r.event_name,
            "npc_name": r.npc_name,
            "current_round": r.current_round,
            "is_completed": r.is_completed,
            "outcome_summary": r.outcome_summary,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=items,
    )


@router.get("/events", response_model=BaseResponse, summary="获取可用的对话事件列表")
async def list_events():
    return BaseResponse(data=get_available_events())


@router.get("/{dialogue_id}", response_model=BaseResponse, summary="获取对话详情")
async def get_dialogue(
    dialogue_id: str,
    db: AsyncSession = Depends(get_db),
):
    dialogue_id_int = int(dialogue_id)
    stmt = select(DialogueSession).where(
        and_(DialogueSession.id == dialogue_id_int, DialogueSession.is_deleted == False)
    )
    result = await db.execute(stmt)
    dialogue = result.scalar_one_or_none()

    if not dialogue:
        raise HTTPException(status_code=404, detail="Dialogue not found")

    return BaseResponse(data={
        "id": dialogue.id,
        "session_id": dialogue.session_id,
        "event_id": dialogue.event_id,
        "event_name": dialogue.event_name,
        "npc_name": dialogue.npc_name,
        "dialogue_history": dialogue.dialogue_history,
        "choices_made": dialogue.choices_made,
        "timeline_branches": dialogue.timeline_branches,
        "current_round": dialogue.current_round,
        "is_completed": dialogue.is_completed,
        "outcome_summary": dialogue.outcome_summary,
        "created_at": dialogue.created_at.isoformat() if dialogue.created_at else None,
    })


@router.delete("/{dialogue_id}", response_model=BaseResponse, summary="删除对话记录")
async def delete_dialogue(
    dialogue_id: str,
    db: AsyncSession = Depends(get_db),
):
    did = int(dialogue_id)
    stmt = select(DialogueSession).where(
        and_(DialogueSession.id == did, DialogueSession.is_deleted == False)
    )
    result = await db.execute(stmt)
    dialogue = result.scalar_one_or_none()

    if not dialogue:
        raise HTTPException(status_code=404, detail="Dialogue not found")

    dialogue.is_deleted = True
    await db.flush()

    return BaseResponse(message="Dialogue deleted")
