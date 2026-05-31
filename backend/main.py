from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import time

from .config import settings
from .database import init_db
from .redis_client import redis_client
from .routers import exploration, rating, vote, signature, champion, dialogue, auth

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
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
