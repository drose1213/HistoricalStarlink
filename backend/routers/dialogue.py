import logging
import re
import uuid
import time
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database import get_db
from ..models.dialogue import DialogueSession
from ..models.exploration_profile import UserExplorationProfile
from ..dialogue_engine import _DYNAMIC_CHOICES

logger = logging.getLogger(__name__)

SESSION_PATTERN = re.compile(r'^session_\d+_[a-zA-Z0-9]{8}$')


def validate_session_id(session_id: str) -> str:
    if not SESSION_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session format")
    return session_id


def generate_session_id() -> str:
    """生成符合白名单格式的 session_id: session_<unix_ts>_<8 hex>"""
    return f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"


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
    compute_path_signature,
    compute_dimension_scores,
    predict_endings,
    start_dynamic_dialogue,
    process_dynamic_choice,
    process_dynamic_free_text,
    _build_dynamic_ending,
    resolve_hero_for_topic,
    cache_hero_persona,
)
from ..schemas import BaseResponse, PaginationResponse

router = APIRouter(prefix="/api/dialogue", tags=["对话探索"])


async def _persist_exploration_profile(
    db: AsyncSession,
    dialogue: DialogueSession,
    ending_type: str,
    choices_made: list,
    free_texts: Optional[list] = None,
) -> None:
    """对话结束时写一条 UserExplorationProfile 记录 (一次对话最多 1 条)."""
    try:
        scores = compute_dimension_scores(choices_made or [], free_texts or [])
        path_sig = ending_type if ending_type and ending_type not in ("historical", "altered", "rag_fallback") else compute_path_signature(choices_made or [])
        profile = UserExplorationProfile(
            session_id=dialogue.session_id,
            event_id=dialogue.event_id,
            ending_type=ending_type or "historical",
            reform_score=scores.get("reform", 0),
            conservative_score=scores.get("conservative", 0),
            empathy_score=scores.get("empathy", 0),
            radicalism_score=scores.get("radicalism", 0),
            choices_signature=path_sig or None,
            choices_made=choices_made or [],
        )
        db.add(profile)
        await db.flush()
        logger.info(
            "Exploration profile persisted: session=%s event=%s ending=%s reform=%s",
            dialogue.session_id, dialogue.event_id, ending_type, scores.get("reform"),
        )
    except Exception as e:
        logger.exception("Failed to persist exploration profile: %s", e)
        # 不抛出, 避免影响主流程


def _extract_choice_text(event_id: str, current_round: int, choice_id: str) -> str:
    """从剧本中提取选择文本, 找不到返回空串."""
    script = get_script(event_id)
    if not script:
        return ""
    rounds = script.get("rounds", [])
    if current_round < 1 or current_round > len(rounds):
        return ""
    for c in rounds[current_round - 1].get("choices", []):
        if c.get("choice_id") == choice_id:
            return c.get("text", "")
    return ""


def _extract_consequence(event_id: str, current_round: int, choice_id: str) -> str:
    """从剧本中提取选择的 consequence 文本."""
    script = get_script(event_id)
    if not script:
        return ""
    rounds = script.get("rounds", [])
    if current_round < 1 or current_round > len(rounds):
        return ""
    for c in rounds[current_round - 1].get("choices", []):
        if c.get("choice_id") == choice_id:
            return c.get("consequence", "")
    return ""


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


# --- 英雄卡牌 ---
class HeroPersona(BaseModel):
    hero_id: str = Field(..., description="英雄唯一标识")
    name: str = Field(..., description="人物名")
    role: str = Field(default="", description="身份/职务")
    era: str = Field(default="", description="时代")
    greeting: str = Field(default="", description="见面招呼")
    style_hint: str = Field(default="古朴典雅", description="语言风格")
    speaking_pattern: str = Field(default="吾", description="自称")
    description: str = Field(default="", description="人物简介")


class ResolveHeroRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=120, description="用户话题")


class ResolveHeroResponseData(BaseModel):
    heroes: list[HeroPersona] = Field(default_factory=list)
    source: str = Field(..., description="llm | fallback | empty")


# --- 任意话题 dynamic 对话 ---
class DynamicDialogueStartRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=120, description="任意话题")
    session_id: Optional[str] = Field(default=None, description="用户会话ID")
    hero_id: Optional[str] = Field(default=None, description="英雄卡牌 ID (可选)")


class DynamicDialogueChoiceRequest(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")
    choice_id: str = Field(..., description="选择ID")


class DynamicDialogueChatRequest(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")
    message: str = Field(..., min_length=1, max_length=500, description="用户消息")


class DynamicDialogueEndRequest(BaseModel):
    dialogue_id: str = Field(..., description="对话ID")


@router.post("/start", response_model=BaseResponse, summary="启动对话探索")
async def start_dialogue(
    req: DialogueStartRequest,
    db: AsyncSession = Depends(get_db),
):
    event_id = req.event_id
    session_id = req.session_id or generate_session_id()
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

    try:
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
        await db.commit()
        await db.refresh(dialogue)
    except Exception as e:
        await db.rollback()
        logger.exception("start_dialogue failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start dialogue")

    return BaseResponse(
        message="Dialogue started",
        data={
            "dialogue_id": str(dialogue.id),
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
            "path_signature": "",
            "cumulative_impact": compute_dimension_scores([]),
            "predicted_endings": predict_endings(script, "", top_n=2),
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

    try:
        response = process_choice(dialogue.event_id, req.choice_id, current_round, choices_made)
        if not response:
            raise HTTPException(status_code=400, detail="Invalid choice for current round")

        new_choices_made = choices_made + [{
            "round": current_round,
            "choice_id": req.choice_id,
            "mood": response.get("mood", ""),
            "timeline_change": response.get("timeline_change", False),
            "choice_text": _extract_choice_text(dialogue.event_id, current_round, req.choice_id),
            "consequence": _extract_consequence(dialogue.event_id, current_round, req.choice_id),
        }]

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
        dialogue.choices_made = new_choices_made
        dialogue.current_round = response.get("round", current_round + 1)
        dialogue.path_depth = dialogue.path_depth + 1

        if response.get("is_ending"):
            dialogue.is_completed = True
            dialogue.outcome_summary = response.get("ending_type", "historical")
            dialogue.timeline_branches = calculate_timeline_branches(new_choices_made)

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("send_choice failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process choice")

    # 写画像 (is_completed 时) - 不阻塞主流程
    if response.get("is_ending"):
        await _persist_exploration_profile(
            db, dialogue,
            ending_type=response.get("ending_type", "historical"),
            choices_made=new_choices_made,
        )

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
            "path_signature": response.get("path_signature", ""),
            "partial_match": response.get("partial_match", False),
            "cumulative_impact": response.get("cumulative_impact", {}),
            "predicted_endings": response.get("predicted_endings", []),
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
        try:
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
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.exception("free_chat (post-ending) failed: %s", e)
            raise HTTPException(status_code=500, detail="Failed to process chat")

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

    try:
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
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("free_chat failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process chat")

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


@router.get("/profile", response_model=BaseResponse, summary="查询用户探索画像")
async def get_exploration_profile(
    session_id: str = Query(..., description="会话ID"),
    db: AsyncSession = Depends(get_db),
):
    """返回该 session 累计画像: 探索记录 + 4 维 max + 探索过的事件 + 已解锁结局数."""
    if not SESSION_PATTERN.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session format")

    stmt = (
        select(UserExplorationProfile)
        .where(and_(UserExplorationProfile.session_id == session_id, UserExplorationProfile.is_deleted == False))
        .order_by(UserExplorationProfile.created_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    if not records:
        return BaseResponse(
            data={
                "records": [],
                "aggregate": {"reform": 0, "conservative": 0, "empathy": 0, "radicalism": 0},
                "events_explored": [],
                "endings_unlocked": 0,
            }
        )

    aggregate = {
        "reform": max((r.reform_score or 0) for r in records),
        "conservative": max((r.conservative_score or 0) for r in records),
        "empathy": max((r.empathy_score or 0) for r in records),
        "radicalism": max((r.radicalism_score or 0) for r in records),
    }
    events_explored = list({r.event_id for r in records})
    endings_unlocked = len({r.ending_type for r in records if r.ending_type})

    return BaseResponse(
        data={
            "records": [r.to_dict() for r in records],
            "aggregate": aggregate,
            "events_explored": events_explored,
            "endings_unlocked": endings_unlocked,
        }
    )


@router.get("/branches/{event_id}", response_model=BaseResponse, summary="查询事件结局分支")
async def get_branches(
    event_id: str,
    session_id: Optional[str] = Query(default=None, description="会话ID, 用于显示已解锁结局"),
    db: AsyncSession = Depends(get_db),
):
    """返回该事件所有可达结局列表 + 当前 session 已解锁的结局 key."""
    script = get_script(event_id)
    if not script:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' has no dialogue script")

    endings = script.get("endings") or {}
    available = [
        {"key": k, "label": _ending_label(k), "hint": _ending_hint(k, v)}
        for k, v in endings.items()
    ]

    unlocked: list = []
    if session_id and SESSION_PATTERN.match(session_id):
        stmt = select(UserExplorationProfile.ending_type).where(
            and_(
                UserExplorationProfile.session_id == session_id,
                UserExplorationProfile.event_id == event_id,
                UserExplorationProfile.is_deleted == False,
            )
        )
        result = await db.execute(stmt)
        unlocked = list({row[0] for row in result.all() if row[0]})

    return BaseResponse(
        data={
            "event_id": event_id,
            "npc_name": script.get("npc_name", ""),
            "available_endings": available,
            "unlocked_endings": unlocked,
        }
    )


def _ending_label(key: str) -> str:
    """从 ending key 派生展示标签."""
    if key == "historical":
        return "历史定论"
    if key == "altered":
        return "平行时间线"
    if key == "rag_fallback":
        return "AI 推演结局"
    if key.startswith("A"):
        return "温和路线"
    if key.startswith("D"):
        return "激进路线"
    if key.startswith("T"):
        return "深思路线"
    return f"路径 {key}"


def _ending_hint(key: str, text: str) -> str:
    """截取 ending 正文前 40 字作为 hint."""
    if not text:
        return ""
    flat = text.replace("\n", " ").strip()
    return flat[:40] + ("…" if len(flat) > 40 else "")


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
            "created_at": iso_utc(r.created_at),
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
        "created_at": iso_utc(dialogue.created_at),
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

    try:
        dialogue.is_deleted = True
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("delete_dialogue failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete dialogue")

    return BaseResponse(message="Dialogue deleted")


# === 英雄卡牌推荐 ===
@router.post("/dynamic/resolve-hero", response_model=BaseResponse, summary="为话题推荐英雄卡牌")
async def dynamic_resolve_hero(req: ResolveHeroRequest):
    """根据用户 topic 推荐 1-3 个历史人物供用户选择.

    - LLM 智能推荐 (需要 MINIMAX_API_KEY)
    - 失败时回退到 events_data 关键词匹配
    - 推荐结果中的 hero_id 传给 /dynamic/start 即可激活角色扮演
    """
    try:
        result = await resolve_hero_for_topic(req.topic.strip(), max_count=3)
        # 缓存 hero personas 以便后续 start 时使用
        for hero in result.get("heroes", []):
            cache_hero_persona(hero)
        return BaseResponse(data=result)
    except Exception as e:
        logger.exception("dynamic_resolve_hero failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve hero")


# === 任意话题 dynamic 对话 endpoints ===
@router.post("/dynamic/start", response_model=BaseResponse, summary="为任意话题开启时空对话")
async def dynamic_start(
    req: DynamicDialogueStartRequest,
    db: AsyncSession = Depends(get_db),
):
    session_id = req.session_id or generate_session_id()
    validate_session_id(session_id)

    try:
        opening = await start_dynamic_dialogue(req.topic, session_id=session_id, hero_id=req.hero_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("dynamic_start failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to start dynamic dialogue")

    try:
        dialogue = DialogueSession(
            session_id=session_id,
            event_id=opening["event_id"],
            event_name=f"自由探索: {req.topic[:80]}",
            topic=req.topic[:256],
            npc_name=opening["npc_name"],
            dialogue_history=[{
                "round": 1,
                "role": "npc",
                "content": opening["narrative"],
            }],
            choices_made=[],
            timeline_branches=[],
            current_round=1,
            path_depth=0,
            is_completed=False,
            outcome_summary=None,
            is_dynamic=True,
        )
        db.add(dialogue)
        await db.commit()
        await db.refresh(dialogue)
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to persist dynamic dialogue: %s", e)
        raise HTTPException(status_code=500, detail="Failed to persist dynamic dialogue")

    return BaseResponse(data={
        "dialogue_id": str(dialogue.id),
        "event_id": opening["event_id"],
        "event_name": dialogue.event_name,
        "npc_name": opening["npc_name"],
        "npc_role": opening["npc_role"],
        "npc_symbol": opening["npc_symbol"],
        "context": opening["context"],
        "narrative": opening["narrative"],
        "choices": opening["choices"],
        "round": 1,
        "is_dynamic": True,
        "hero": opening.get("hero"),  # 如果有 hero persona 则返回
        "hero_id": opening.get("hero_id"),
        "topic": req.topic,
    })


@router.post("/dynamic/choice", response_model=BaseResponse, summary="dynamic 对话提交选择")
async def dynamic_choice(
    req: DynamicDialogueChoiceRequest,
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
    if not dialogue.is_dynamic:
        raise HTTPException(status_code=400, detail="该对话非 dynamic 模式, 请用普通 choice 接口")
    if dialogue.is_completed:
        raise HTTPException(status_code=410, detail="Dialogue already ended")

    # 提取 topic: 优先使用持久化字段, 兼容历史数据回退到 event_name 前缀剥离
    topic = dialogue.topic
    if not topic and dialogue.event_name:
        topic = dialogue.event_name.replace("自由探索: ", "", 1)
    choices_made = dialogue.choices_made or []
    free_texts = [m.get("content") for m in (dialogue.dialogue_history or [])
                  if m.get("role") == "user" and m.get("content")]

    try:
        result_dict = await process_dynamic_choice(
            topic=topic, choice_id=req.choice_id,
            choices_made=choices_made, free_texts=free_texts,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("process_dynamic_choice failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process choice")

    try:
        # 复用 dialogue_engine._DYNAMIC_CHOICES 作为单一选项来源 (DRY)
        choice_text = next(
            (c["text"] for c in _DYNAMIC_CHOICES if c["choice_id"] == req.choice_id),
            "",
        )
        new_choices = choices_made + [{
            "round": result_dict["round"],
            "choice_id": req.choice_id,
            "choice_text": choice_text,
            "mood": result_dict.get("mood", "default"),
        }]
        dialogue.choices_made = new_choices
        dialogue.current_round = result_dict["round"]
        history = dialogue.dialogue_history or []
        history.append({"round": result_dict["round"], "role": "npc", "content": result_dict["narrative"]})
        dialogue.dialogue_history = history
        if result_dict.get("is_ending"):
            # dynamic 模式也直接调结束逻辑生成结局
            ending = await _build_dynamic_ending(topic, new_choices, free_texts)
            history.append({"round": 0, "role": "npc", "content": ending["narrative"]})
            dialogue.dialogue_history = history
            dialogue.is_completed = True
            dialogue.outcome_summary = ending["narrative"][:500]
            await _persist_exploration_profile(
                db, dialogue,
                ending_type=ending.get("ending_type", "rag_dynamic"),
                choices_made=new_choices,
                free_texts=free_texts,
            )
        await db.commit()
        await db.refresh(dialogue)
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to persist dynamic choice: %s", e)
        raise HTTPException(status_code=500, detail="Failed to persist choice")

    return BaseResponse(data={
        "dialogue_id": str(dialogue.id),
        "narrative": result_dict["narrative"],
        "choices": result_dict.get("choices", []),
        "round": result_dict["round"],
        "is_ending": result_dict.get("is_ending", False),
        "is_dynamic": True,
        "path_signature": result_dict.get("path_signature", ""),
        "cumulative_impact": result_dict.get("cumulative_impact", {}),
    })


@router.post("/dynamic/chat", response_model=BaseResponse, summary="dynamic 对话自由聊天")
async def dynamic_chat(
    req: DynamicDialogueChatRequest,
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
    if not dialogue.is_dynamic:
        raise HTTPException(status_code=400, detail="该对话非 dynamic 模式, 请用普通 chat 接口")
    if dialogue.is_completed:
        raise HTTPException(status_code=410, detail="Dialogue already ended")

    topic = dialogue.topic
    if not topic and dialogue.event_name:
        topic = dialogue.event_name.replace("自由探索: ", "", 1)
    choices_made = dialogue.choices_made or []
    free_texts = [m.get("content") for m in (dialogue.dialogue_history or [])
                  if m.get("role") == "user" and m.get("content")]

    try:
        result_dict = await process_dynamic_free_text(
            topic=topic, message=req.message,
            choices_made=choices_made, free_texts=free_texts,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("process_dynamic_free_text failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to process chat")

    try:
        new_free_texts = free_texts + [req.message]
        history = dialogue.dialogue_history or []
        history.append({"round": result_dict["round"], "role": "user", "content": req.message})
        history.append({"round": result_dict["round"], "role": "npc", "content": result_dict["narrative"]})
        dialogue.dialogue_history = history
        dialogue.current_round = result_dict["round"]
        await db.commit()
        await db.refresh(dialogue)
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to persist dynamic chat: %s", e)
        raise HTTPException(status_code=500, detail="Failed to persist chat")

    return BaseResponse(data={
        "dialogue_id": str(dialogue.id),
        "narrative": result_dict["narrative"],
        "choices": result_dict.get("choices", []),
        "round": result_dict["round"],
        "is_ending": False,
        "is_dynamic": True,
        "path_signature": result_dict.get("path_signature", ""),
        "cumulative_impact": result_dict.get("cumulative_impact", {}),
    })


@router.post("/dynamic/end", response_model=BaseResponse, summary="dynamic 对话主动结束")
async def dynamic_end(
    req: DynamicDialogueEndRequest,
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
    if not dialogue.is_dynamic:
        raise HTTPException(status_code=400, detail="该对话非 dynamic 模式")
    if dialogue.is_completed:
        return BaseResponse(data={"dialogue_id": str(dialogue.id), "already_completed": True})

    topic = dialogue.topic
    if not topic and dialogue.event_name:
        topic = dialogue.event_name.replace("自由探索: ", "", 1)
    choices_made = dialogue.choices_made or []
    free_texts = [m.get("content") for m in (dialogue.dialogue_history or [])
                  if m.get("role") == "user" and m.get("content")]

    try:
        ending = await _build_dynamic_ending(topic, choices_made, free_texts)
    except Exception as e:
        logger.exception("_build_dynamic_ending failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to build ending")

    try:
        history = dialogue.dialogue_history or []
        history.append({"round": 0, "role": "npc", "content": ending["narrative"]})
        dialogue.dialogue_history = history
        dialogue.is_completed = True
        dialogue.outcome_summary = ending["narrative"][:500]
        await _persist_exploration_profile(
            db, dialogue,
            ending_type=ending.get("ending_type", "rag_dynamic"),
            choices_made=choices_made,
            free_texts=free_texts,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to persist dynamic end: %s", e)
        raise HTTPException(status_code=500, detail="Failed to persist ending")

    return BaseResponse(data={
        "dialogue_id": str(dialogue.id),
        "narrative": ending["narrative"],
        "ending_type": ending.get("ending_type", "rag_dynamic"),
        "is_dynamic": True,
        "is_ending": True,
        "path_signature": ending.get("path_signature", ""),
        "cumulative_impact": ending.get("cumulative_impact", {}),
    })
