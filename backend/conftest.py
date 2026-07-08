import os
import sys
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
from httpx import AsyncClient, ASGITransport

# 设置测试环境变量
os.environ.setdefault("DB_DRIVER", "sqlite")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-pytest")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("MINIMAX_API_KEY", "")  # 关键词回退模式

# 把项目根目录加入 sys.path
BACKEND_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT))


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """使用 SQLite 内存数据库，函数级别隔离"""
    from backend.database import engine, AsyncSessionLocal, Base
    from backend.redis_client import cache

    # 重建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await cache.flush_db()

    # 注入种子数据
    from backend.data.events_data import events_data
    from backend.models.event import HistoryEvent
    from backend.models.system_config import SystemConfig
    from backend.data.config_data import DEFAULT_CONFIGS
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # 插入事件
        target_ids = {"qin_unification", "han_empire", "great_wall_construction", "invention_of_paper", "invention_of_gunpowder"}
        for ev in events_data:
            if ev["id"] in target_ids:
                session.add(HistoryEvent(
                    id=ev["id"],
                    name=ev["name"],
                    year=ev["year"],
                    region=ev["region"],
                    importance=ev["importance"],
                    description=ev.get("description", ""),
                    causes=ev.get("causes", []),
                    consequences=ev.get("consequences", []),
                    related_concepts=ev.get("related_concepts", []),
                    figures=ev.get("figures", []),
                    tags=ev.get("tags", []),
                ))
        # 插入配置
        for cfg in DEFAULT_CONFIGS:
            session.add(SystemConfig(
                key=cfg["key"],
                value=cfg["value"],
                group=cfg["group"],
                label=cfg["label"],
                value_type=cfg["value_type"],
            ))
        await session.commit()

    yield engine

    # 清理
    await cache.flush_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    """创建 FastAPI 异步测试客户端"""
    from backend.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def auth_token(client, test_db):
    """创建并登录一个测试用户，返回 token"""
    import hashlib
    import secrets
    from backend.database import AsyncSessionLocal
    from backend.models.user import User
    from backend.routers.auth import create_token

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.username == "testuser"))
        user = result.scalar_one_or_none()
        if not user:
            salt = secrets.token_hex(16)
            h = hashlib.pbkdf2_hmac("sha256", "Test123456".encode(), salt.encode(), 200000)
            hashed = f"{salt}${h.hex()}"
            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=hashed,
                nickname="测试用户",
                is_active=True,
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
        user_id = user.id
        await session.commit()

    return create_token(user_id)


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """带认证头的请求头"""
    return {"Authorization": f"Bearer {auth_token}"} if auth_token else {}


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db):
    """直接获取数据库会话"""
    from backend.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
