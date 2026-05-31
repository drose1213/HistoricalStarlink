import os
import uuid
import shutil
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..config import settings
from ..database import get_db
from ..models.signature import Signature
from ..schemas import BaseResponse, PaginationResponse, SignatureOut

router = APIRouter(prefix="/api/signature", tags=["签名"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _build_file_url(file_path: str) -> str:
    return f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/{file_path}"


def _validate_file(file: UploadFile) -> None:
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_SIGNATURE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，仅支持: {', '.join(settings.ALLOWED_SIGNATURE_EXTENSIONS)}",
        )


@router.post("/upload", response_model=BaseResponse, summary="上传签名图片")
async def upload_signature(
    file: UploadFile = File(..., description="签名图片文件"),
    session_id: str = Form(..., max_length=64, description="会话ID"),
    nickname: Optional[str] = Form(default=None, max_length=64, description="用户昵称"),
    event_id: Optional[str] = Form(default=None, max_length=128, description="关联事件ID"),
    context: Optional[str] = Form(default=None, max_length=500, description="附带文字"),
    db: AsyncSession = Depends(get_db),
):
    _validate_file(file)

    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超出限制: {file_size} > {settings.MAX_UPLOAD_SIZE}",
        )

    ext = file.filename.rsplit(".", 1)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    file_path = session_dir / unique_name

    with open(file_path, "wb") as f:
        f.write(content)

    relative_path = f"{settings.UPLOAD_DIR}/{session_id}/{unique_name}"
    file_url = _build_file_url(relative_path)

    new_signature = Signature(
        session_id=session_id,
        nickname=nickname,
        file_path=relative_path,
        file_name=file.filename,
        file_size=file_size,
        file_type=file.content_type or "image/unknown",
        file_url=file_url,
        event_id=event_id,
        context=context,
    )
    db.add(new_signature)
    await db.flush()
    await db.refresh(new_signature)

    return BaseResponse(
        message="签名上传成功",
        data=SignatureOut.model_validate(new_signature).model_dump(),
    )


@router.get("", response_model=PaginationResponse, summary="查询签名列表")
async def list_signatures(
    session_id: Optional[str] = Query(default=None, description="会话ID"),
    event_id: Optional[str] = Query(default=None, description="关联事件ID"),
    is_approved: Optional[bool] = Query(default=None, description="审核状态"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
):
    conditions = [Signature.is_deleted == False]
    if session_id:
        conditions.append(Signature.session_id == session_id)
    if event_id:
        conditions.append(Signature.event_id == event_id)
    if is_approved is not None:
        conditions.append(Signature.is_approved == is_approved)

    count_stmt = select(func.count()).select_from(Signature).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(Signature)
        .where(and_(*conditions))
        .order_by(Signature.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    signatures = result.scalars().all()

    return PaginationResponse(
        total=total,
        page=page,
        page_size=page_size,
        data=[SignatureOut.model_validate(s).model_dump() for s in signatures],
    )


@router.get("/{signature_id}", response_model=BaseResponse, summary="获取单条签名记录")
async def get_signature(
    signature_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Signature).where(
        and_(Signature.id == signature_id, Signature.is_deleted == False)
    )
    result = await db.execute(stmt)
    sig = result.scalar_one_or_none()

    if not sig:
        raise HTTPException(status_code=404, detail="签名记录不存在")

    return BaseResponse(data=SignatureOut.model_validate(sig).model_dump())


@router.delete("/{signature_id}", response_model=BaseResponse, summary="删除签名")
async def delete_signature(
    signature_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Signature).where(
        and_(Signature.id == signature_id, Signature.is_deleted == False)
    )
    result = await db.execute(stmt)
    sig = result.scalar_one_or_none()

    if not sig:
        raise HTTPException(status_code=404, detail="签名记录不存在")

    sig.is_deleted = True
    await db.flush()

    file_path = Path(sig.file_path)
    if file_path.exists():
        os.remove(file_path)

    return BaseResponse(message="签名已删除")
