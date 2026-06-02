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

    if redis_client is not None:
        try:
            await redis_client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
    else:
        logger.warning("Redis not installed, caching disabled")

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
