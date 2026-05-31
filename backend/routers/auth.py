import asyncio
import hashlib
import hmac
import logging
import random
import secrets
import smtplib
import string
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models.user import User
from ..redis_client import cache
from ..schemas import BaseResponse

logger = logging.getLogger("historical_starlink.auth")

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200000)
    return f"{salt}${h.hex()}"


def _verify_password(password: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split("$", 1)
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200000)
        return hmac.compare_digest(check.hex(), h)
    except (ValueError, AttributeError):
        return False


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _user_out(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


# ==================== 邮件验证码 ====================

_CODE_TPL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#0a0f1e;">
<div style="max-width:480px;margin:40px auto;padding:32px;
  background:linear-gradient(135deg,#0d1424,#141e33);
  border:1px solid #31f7ff33;border-radius:12px;
  font-family:'Microsoft YaHei','PingFang SC',sans-serif;color:#e0e6f0;">
  <h2 style="text-align:center;color:#31f7ff;margin:0 0 24px;
    text-shadow:0 0 12px #31f7ff55;font-size:20px;">
    ◇ 文明星链 · 验证码
  </h2>
  <p style="font-size:14px;line-height:1.8;">
    你好，你正在进行 <b>文明星链：遗迹探索</b> 的邮箱验证。
  </p>
  <div style="text-align:center;margin:24px 0;">
    <span style="display:inline-block;padding:12px 36px;
      background:linear-gradient(135deg,#31f7ff1a,#ff35f30d);
      border:1px solid #31f7ff;border-radius:8px;
      font-size:28px;font-weight:700;letter-spacing:6px;
      color:#31f7ff;text-shadow:0 0 8px #31f7ff55;">
      {code}
    </span>
  </div>
  <p style="font-size:13px;color:#8892a8;line-height:1.6;">
    验证码 <b style="color:#31f7ff;">{expire} 分钟</b> 内有效。
    如果这不是你的操作，请忽略此邮件。
  </p>
  <hr style="border:none;border-top:1px solid #31f7ff1a;margin:20px 0;">
  <p style="font-size:11px;color:#5a6478;text-align:center;">
    — 文明星链：遗迹探索 —
  </p>
</div>
</body></html>"""


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


def _email_code_key(email: str) -> str:
    return f"email_code:{email}"


def _email_code_cooldown_key(email: str) -> str:
    return f"email_code_cd:{email}"


def _email_code_rate_key(email: str) -> str:
    t = int(time.time()) // 3600
    return f"email_code_rate:{email}:{t}"


async def _send_email(to_email: str, code: str) -> None:
    expire_min = settings.EMAIL_CODE_EXPIRE_SECONDS // 60
    html = _CODE_TPL.format(code=code, expire=expire_min)
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = f"【文明星链】验证码：{code}"
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email

    loop = asyncio.get_running_loop()
    if settings.SMTP_USE_SSL:
        def _do_send():
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as s:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.sendmail(msg["From"], [to_email], msg.as_string())
        await loop.run_in_executor(None, _do_send)
    else:
        def _do_send():
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
                s.starttls()
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                s.sendmail(msg["From"], [to_email], msg.as_string())
        await loop.run_in_executor(None, _do_send)


# ==================== 请求模型 ====================

class SendCodeRequest(BaseModel):
    email: str = Field(..., max_length=100, description="邮箱")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("邮箱格式不正确")
        return v.lower()


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., max_length=100, description="邮箱")
    email_code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    nickname: Optional[str] = Field(default=None, max_length=50, description="昵称")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum() and not all(c.isalnum() or c in ("_", "-") for c in v):
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("邮箱格式不正确")
        return v.lower()


class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, max_length=50, description="昵称")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="头像URL")


# ==================== 路由 ====================


@router.post("/send-code", response_model=BaseResponse, summary="发送邮箱验证码")
async def send_email_code(
    req: SendCodeRequest,
    db: AsyncSession = Depends(get_db),
):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise HTTPException(status_code=500, detail="邮件服务未配置，请联系管理员")

    existing = await db.execute(select(User).where(User.email == req.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    cd_key = _email_code_cooldown_key(req.email)
    if await cache.exists(cd_key):
        raise HTTPException(status_code=429, detail="操作过于频繁，请60秒后重试")

    rate_key = _email_code_rate_key(req.email)
    rate_val = await cache.get(rate_key)
    if rate_val is not None and int(rate_val) >= settings.EMAIL_CODE_MAX_PER_HOUR:
        raise HTTPException(status_code=429, detail="该邮箱验证码发送次数已达上限，请稍后再试")

    code = _generate_code()

    await cache.set(_email_code_key(req.email), code, settings.EMAIL_CODE_EXPIRE_SECONDS)
    await cache.set(cd_key, "1", settings.EMAIL_CODE_COOLDOWN_SECONDS)

    if rate_val is None:
        await cache.set(rate_key, "1", 3600)
    else:
        try:
            await cache.set(rate_key, str(int(rate_val) + 1), 3600)
        except (ValueError, TypeError):
            await cache.set(rate_key, "1", 3600)

    try:
        await _send_email(req.email, code)
    except Exception as e:
        logger.error(f"发送验证码失败: {e}")
        await cache.delete(_email_code_key(req.email))
        raise HTTPException(status_code=500, detail="验证码发送失败，请稍后重试")

    return BaseResponse(message="验证码已发送，请查收邮箱")


@router.post("/register", response_model=BaseResponse, summary="用户注册")
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(
        or_(User.username == req.username, User.email == req.email)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        if existing.username == req.username:
            raise HTTPException(status_code=400, detail="用户名已存在")
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    code_key = _email_code_key(req.email)
    stored_code = await cache.get(code_key)
    if stored_code is None:
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if str(stored_code) != req.email_code:
        raise HTTPException(status_code=400, detail="验证码错误")

    await cache.delete(code_key)
    await cache.delete(_email_code_cooldown_key(req.email))

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=_hash_password(req.password),
        nickname=req.nickname or req.username,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_token(user.id)
    return BaseResponse(
        message="注册成功",
        data={"token": token, "user": _user_out(user)},
    )


@router.post("/login", response_model=BaseResponse, summary="用户登录")
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(
        or_(User.username == req.username, User.email == req.username)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="该账号未注册，请先注册")

    if not _verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = create_token(user.id)
    return BaseResponse(
        message="登录成功",
        data={"token": token, "user": _user_out(user)},
    )


@router.get("/me", response_model=BaseResponse, summary="获取当前用户信息")
async def get_me(
    user: User = Depends(get_current_user),
):
    return BaseResponse(data=_user_out(user))


@router.put("/profile", response_model=BaseResponse, summary="更新用户资料")
async def update_profile(
    req: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url

    await db.flush()
    await db.refresh(user)

    return BaseResponse(
        message="资料更新成功",
        data=_user_out(user),
    )
