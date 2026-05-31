import json
import logging
from typing import Any, Optional

from .config import settings

logger = logging.getLogger("historical_starlink.redis")

try:
    import redis.asyncio as aioredis

    redis_pool = aioredis.ConnectionPool(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True,
        max_connections=20,
    )
    redis_client = aioredis.Redis(connection_pool=redis_pool)
    _REDIS_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"Redis unavailable, caching disabled: {e}")
    redis_client = None
    _REDIS_AVAILABLE = False


class RedisCache:
    def __init__(self, default_expire: int = settings.REDIS_EXPIRE_SECONDS):
        self.default_expire = default_expire

    async def get(self, key: str) -> Optional[Any]:
        if not _REDIS_AVAILABLE:
            return None
        try:
            value = await redis_client.get(key)
            if value is not None:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
        except Exception:
            pass
        return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        if not _REDIS_AVAILABLE:
            return
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            expire = expire or self.default_expire
            await redis_client.set(key, value, ex=expire)
        except Exception:
            pass

    async def delete(self, key: str) -> None:
        if not _REDIS_AVAILABLE:
            return
        try:
            await redis_client.delete(key)
        except Exception:
            pass

    async def exists(self, key: str) -> bool:
        if not _REDIS_AVAILABLE:
            return False
        try:
            return bool(await redis_client.exists(key))
        except Exception:
            return False

    async def incr(self, key: str, amount: int = 1) -> int:
        if not _REDIS_AVAILABLE:
            return 0
        try:
            return await redis_client.incr(key, amount)
        except Exception:
            return 0

    async def hash_set(self, name: str, key: str, value: Any) -> None:
        if not _REDIS_AVAILABLE:
            return
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            await redis_client.hset(name, key, value)
        except Exception:
            pass

    async def hash_get(self, name: str, key: str) -> Optional[Any]:
        if not _REDIS_AVAILABLE:
            return None
        try:
            value = await redis_client.hget(name, key)
            if value is not None:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
        except Exception:
            pass
        return None

    async def hash_get_all(self, name: str) -> dict:
        if not _REDIS_AVAILABLE:
            return {}
        try:
            data = await redis_client.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            return result
        except Exception:
            return {}

    async def set_add(self, key: str, *values) -> int:
        if not _REDIS_AVAILABLE:
            return 0
        try:
            return await redis_client.sadd(key, *values)
        except Exception:
            return 0

    async def set_members(self, key: str) -> set:
        if not _REDIS_AVAILABLE:
            return set()
        try:
            return await redis_client.smembers(key)
        except Exception:
            return set()

    async def flush_db(self) -> None:
        if not _REDIS_AVAILABLE:
            return
        try:
            await redis_client.flushdb()
        except Exception:
            pass


cache = RedisCache()
