import os
from pathlib import Path
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

from .config import settings, SQLITE_PATH

logger = logging.getLogger("historical_starlink")

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata


from . import models  # noqa: F401,E402  触发所有 Model 类的注册，使 Base.metadata.create_all 生效


_db_url = settings.DATABASE_URL
_is_sqlite = _db_url.startswith("sqlite")

if not _is_sqlite:
    try:
        import aiomysql
        import pymysql
    except ImportError:
        logger.warning("aiomysql/pymysql not installed, falling back to SQLite")
        _db_url = f"sqlite+aiosqlite:///{SQLITE_PATH}"
        _is_sqlite = True
        settings._db_config["db.driver"] = "sqlite"
        settings.DB_DRIVER = "sqlite"

_engine_kwargs = {
    "echo": settings.DEBUG,
}
if not _is_sqlite:
    _engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    })

engine = create_async_engine(_db_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    if _is_sqlite:
        db_path = _db_url.split("///")[-1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
