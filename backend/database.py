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

if _is_sqlite:
    logger.warning(f"Using SQLite (DB_DRIVER={settings.DB_DRIVER}). MySQL was not available or not configured.")
else:
    logger.info(f"MySQL mode: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")

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
    # Idempotent migration: add columns that may be missing on older deployments.
    await _run_lightweight_migrations()


async def _run_lightweight_migrations():
    """Add columns that are missing from the existing tables.
    Safe to run repeatedly — uses information_schema and skips columns that already exist.
    """
    from sqlalchemy import text

    async def _table_exists(conn, table: str) -> bool:
        if _is_sqlite:
            row = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=:t"
            ), {"t": table})
            return row.scalar() is not None
        row = await conn.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = :t"
        ), {"t": table})
        return (row.scalar() or 0) > 0

    if _is_sqlite:
        for table, column, col_def in _PENDING_MIGRATIONS:
            try:
                async with engine.connect() as conn:
                    if not await _table_exists(conn, table):
                        continue
                    rows = await conn.execute(text(f"PRAGMA table_info({table})"))
                    existing = {r[1] for r in rows.fetchall()}
                    if column not in existing:
                        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                        await conn.commit()
                        logger.info(f"Migration: added {table}.{column}")
            except Exception as e:
                logger.warning(f"Migration {table}.{column} skipped: {e}")
    else:
        for table, column, col_def in _PENDING_MIGRATIONS:
            try:
                async with engine.connect() as conn:
                    if not await _table_exists(conn, table):
                        continue
                    result = await conn.execute(text(
                        "SELECT COUNT(*) FROM information_schema.columns "
                        "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
                    ), {"t": table, "c": column})
                    exists = (result.scalar() or 0) > 0
                    if not exists:
                        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                        await conn.commit()
                        logger.info(f"Migration: added {table}.{column}")
            except Exception as e:
                logger.warning(f"Migration {table}.{column} skipped: {e}")


_PENDING_MIGRATIONS = [
    ("knowledge_entries", "year_end", "INT NULL"),
    ("knowledge_entries", "language", "VARCHAR(16) NULL DEFAULT 'zh-CN'"),
    ("knowledge_entries", "source_reliability", "INT NULL DEFAULT 5"),
    ("knowledge_entries", "latest_version_id", "INT NULL"),
    ("knowledge_entries", "version_count", "INT NOT NULL DEFAULT 1"),
    ("knowledge_entries", "parent_event_id", "VARCHAR(64) NULL"),
    ("knowledge_entries", "is_locked", "INT NOT NULL DEFAULT 0"),
    ("knowledge_entries", "last_indexed_at", "DATETIME NULL"),
    # crawl_sources: must align with the model
    ("crawl_sources", "url_hash", "VARCHAR(64) NULL"),
    ("crawl_sources", "last_status", "VARCHAR(16) NULL DEFAULT 'pending'"),
    ("crawl_sources", "last_imported", "INT NULL DEFAULT 0"),
    ("crawl_sources", "priority", "INT NOT NULL DEFAULT 5"),
    ("crawl_sources", "recommended", "INT NOT NULL DEFAULT 0"),
    ("crawl_sources", "enabled", "INT NOT NULL DEFAULT 1"),
]
