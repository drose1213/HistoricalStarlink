from typing import Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import settings
from .database import get_db
from .models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    stmt = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    可选登录态: 有 Bearer token 且合法时返回 User, 否则返回 None.
    不抛 401 — 供登录/匿名混合的写入接口使用 (user_id 兜底归集).
    """
    if credentials is None or not credentials.credentials:
        # 兜底: 某些客户端可能把 token 放在 Authorization header 但不通过 HTTPBearer 自动解析
        # 这种情况极少, 这里仅依赖 HTTPBearer
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("user_id")
        if user_id is None:
            return None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

    stmt = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
