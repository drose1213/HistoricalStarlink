import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import time

from .config import settings
from .database import init_db
from .redis_client import redis_client
from .routers import exploration, rating, vote, signature, champion, dialogue, auth, rag, events, config
from .routers.leaderboard import router as leaderboard_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("historical_starlink")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Historical Starlink backend starting...")
    try:
        await init_db()
        logger.info(f"Database tables initialized ({settings.DB_TYPE})")
    except Exception as e:
        logger.error(f"Database init failed: {e}")

    await _seed_configs()

    await load_db_config_safe()

    await _seed_events()

    await _seed_knowledge_base()

    if redis_client is not None:
        try:
            await redis_client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
    else:
        logger.warning("Redis not installed, caching disabled")

    try:
        from .crawler import start_crawl_scheduler
        asyncio.create_task(start_crawl_scheduler())
    except Exception as e:
        logger.warning(f"Failed to start crawl scheduler: {e}")

    # 异步预热 RAG 索引, 从 DB 加载已持久化的向量
    async def _warmup_rag() -> None:
        try:
            from .rag_engine import _load_index_from_db
            loaded = await _load_index_from_db()
            if loaded:
                logger.info("RAG index warmed from DB cache (no API call)")
            else:
                logger.info("No persisted embeddings yet, will compute on first query")
        except Exception as e:
            logger.warning(f"RAG warmup failed (non-fatal): {e}")

    asyncio.create_task(_warmup_rag())

    yield

    logger.info("Historical Starlink backend shutting down...")
    if redis_client is not None:
        try:
            await redis_client.close()
        except Exception:
            pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def cors_and_log_middleware(request: Request, call_next):
    start_time = time.time()

    origin = request.headers.get("origin")
    is_cors = origin and origin in settings.CORS_ORIGINS

    if is_cors and request.method == "OPTIONS":
        from fastapi.responses import Response
        resp = Response()
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Methods"] = ",".join(settings.CORS_ALLOW_METHODS)
        resp.headers["Access-Control-Allow-Headers"] = ",".join(settings.CORS_ALLOW_HEADERS)
        resp.headers["Access-Control-Max-Age"] = "600"
        return resp

    response = await call_next(request)

    if is_cors:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s"
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


app.include_router(exploration.router)
app.include_router(rating.router)
app.include_router(vote.router)
app.include_router(signature.router)
app.include_router(champion.router)
app.include_router(dialogue.router)
app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(events.router)
app.include_router(config.router)
app.include_router(leaderboard_router)


async def load_db_config_safe():
    try:
        from .config import load_db_config
        await load_db_config()
    except Exception as e:
        logger.warning(f"Failed to load DB config: {e}")


async def _seed_configs():
    from sqlalchemy import select, func
    from .database import AsyncSessionLocal
    from .models.system_config import SystemConfig
    from .data.config_data import DEFAULT_CONFIGS

    try:
        async with AsyncSessionLocal() as db:
            count_result = await db.execute(select(func.count()).select_from(SystemConfig))
            count = count_result.scalar()
            if count and count > 0:
                logger.info(f"SystemConfig table already has {count} records, skipping seed")
                return

            for cfg in DEFAULT_CONFIGS:
                db.add(SystemConfig(
                    key=cfg["key"],
                    value=cfg["value"],
                    group=cfg["group"],
                    label=cfg["label"],
                    value_type=cfg["value_type"],
                ))
            await db.commit()
            logger.info(f"Seeded {len(DEFAULT_CONFIGS)} default config items")
    except Exception as e:
        logger.error(f"Failed to seed configs: {e}")


async def _seed_events():
    from sqlalchemy import select, func
    from .database import AsyncSessionLocal
    from .models.event import HistoryEvent
    from .data.events_data import events_data

    try:
        async with AsyncSessionLocal() as db:
            count_result = await db.execute(select(func.count()).select_from(HistoryEvent))
            count = count_result.scalar()
            if count and count > 0:
                logger.info(f"Events table already has {count} records, skipping seed")
                return

            for ev in events_data:
                db.add(HistoryEvent(
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
            await db.commit()
            logger.info(f"Seeded {len(events_data)} historical events into database")
    except Exception as e:
        logger.error(f"Failed to seed events: {e}")


async def _seed_knowledge_base():
    """Seed the RAG knowledge base from events_data on first run.
    This gives the homepage real knowledge base content instead of dummy data.
    Idempotent — uses event_name + source_url dedup so re-runs are safe.
    """
    from datetime import datetime
    from sqlalchemy import select, func
    from .database import AsyncSessionLocal
    from .models.knowledge_base import KnowledgeEntry, KnowledgeVersion
    from .data.events_data import events_data

    try:
        async with AsyncSessionLocal() as db:
            count_result = await db.execute(
                select(func.count()).select_from(KnowledgeEntry).where(
                    KnowledgeEntry.source_type == "seed_data"
                )
            )
            existing = count_result.scalar() or 0
            if existing >= len(events_data):
                logger.info(
                    f"Knowledge base already has {existing} seed entries, skipping seed"
                )
                return

            now = datetime.utcnow()
            imported = 0
            skipped = 0
            for ev in events_data:
                ev_name = ev.get("name")
                if not ev_name:
                    continue

                # Dedup by event_name + source_url=None + chunk_index=0
                existing_entry = await db.execute(
                    select(KnowledgeEntry).where(
                        KnowledgeEntry.event_name == ev_name,
                        KnowledgeEntry.chunk_index == 0,
                        KnowledgeEntry.source_url.is_(None),
                    )
                )
                if existing_entry.scalar_one_or_none():
                    skipped += 1
                    continue

                causes = "；".join(ev.get("causes", []))
                consequences = "；".join(ev.get("consequences", []))
                related = "；".join(ev.get("related_concepts", []))
                figures = ev.get("figures", [])
                tags = ev.get("tags", [])

                year_str = (
                    f"公元前{abs(ev['year'])}年" if ev["year"] < 0
                    else f"公元{ev['year']}年"
                )
                region_str = "中国" if ev["region"] == "china" else "外国"

                text = (
                    f"{ev_name}（{year_str}，{region_str}，重要性{ev['importance']}/10）："
                    f"{ev.get('description', '')}。"
                    f"原因：{causes}。影响：{consequences}。相关概念：{related}。"
                    f"相关人物：{'、'.join(figures)}。标签：{'、'.join(tags)}。"
                )
                content_hash = KnowledgeEntry.compute_hash(text)

                entry = KnowledgeEntry(
                    title=ev_name,
                    content=text,
                    content_hash=content_hash,
                    source_type="seed_data",
                    source_url=None,
                    file_name=None,
                    file_type="seed",
                    event_name=ev_name,
                    year=ev.get("year"),
                    region=ev.get("region"),
                    importance=ev.get("importance"),
                    category=ev.get("category") or "综合",
                    tags=tags,
                    figures=figures,
                    keywords=tags + [ev_name, ev.get("region", "")],
                    language="zh-CN",
                    source_reliability=10,
                    chunk_index=0,
                    chunk_total=1,
                    version=1,
                    version_count=1,
                    parent_event_id=ev.get("id"),
                    status="active",
                    is_locked=0,
                    created_at=now,
                    updated_at=now,
                    last_indexed_at=now,
                )
                db.add(entry)
                try:
                    await db.flush()
                except Exception:
                    pass

                snapshot_meta = {
                    "event_name": ev_name,
                    "region": ev.get("region"),
                    "category": ev.get("category") or "综合",
                    "year": ev.get("year"),
                    "importance": ev.get("importance"),
                    "tags": tags,
                    "figures": figures,
                    "source_type": "seed_data",
                }
                db.add(KnowledgeVersion(
                    entry_id=entry.id,
                    version=1,
                    title=ev_name,
                    content=text,
                    content_hash=content_hash,
                    change_summary="Seeded from events_data on first run",
                    change_source="seed_data",
                    operator="system",
                    snapshot_meta=snapshot_meta,
                    created_at=now,
                ))
                imported += 1

            await db.commit()
            try:
                from .rag_engine import build_index
                await build_index()
            except Exception:
                pass
            logger.info(
                f"Seeded knowledge base with {imported} entries, skipped {skipped}"
            )
    except Exception as e:
        logger.error(f"Failed to seed knowledge base: {e}")


@app.get("/", tags=["健康检查"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "running",
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    db_status = "unknown"
    redis_status = "unknown"

    try:
        from .database import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_status = "connected"
        except Exception as e:
            redis_status = f"error: {str(e)}"
    else:
        redis_status = "not installed"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "server": settings.SERVER_HOST,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
