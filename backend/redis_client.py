import json
import time
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
        # 关键: 防止 Redis 不可用时永久 hang
        socket_connect_timeout=1.0,
        socket_timeout=1.0,
    )
    redis_client = aioredis.Redis(connection_pool=redis_pool)
    _REDIS_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"Redis unavailable, falling back to in-memory cache: {e}")
    redis_client = None
    _REDIS_AVAILABLE = False

_mem_store: dict[str, tuple[Any, float]] = {}


def _mem_cleanup():
    now = time.time()
    expired = [k for k, (_, exp) in _mem_store.items() if exp <= now]
    for k in expired:
        del _mem_store[k]


def _mem_get(key: str) -> Optional[Any]:
    _mem_cleanup()
    entry = _mem_store.get(key)
    if entry is None:
        return None

    value, exp = entry
    if exp > time.time():
        return value

    del _mem_store[key]
    return None


def _mem_set(key: str, value: Any, expire: int) -> None:
    _mem_store[key] = (value, time.time() + expire)


class RedisCache:
    def __init__(self, default_expire: int = settings.REDIS_EXPIRE_SECONDS):
        self.default_expire = default_expire

    async def get(self, key: str) -> Optional[Any]:
        if not _REDIS_AVAILABLE:
            return _mem_get(key)
        try:
            value = await redis_client.get(key)
            if value is not None:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
        except Exception:
            return _mem_get(key)
        return None

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> None:
        expire = expire or self.default_expire
        if not _REDIS_AVAILABLE:
            _mem_set(key, value, expire)
            return
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            await redis_client.set(key, value, ex=expire)
        except Exception:
            _mem_set(key, value, expire)

    async def delete(self, key: str) -> None:
        if not _REDIS_AVAILABLE:
            _mem_store.pop(key, None)
            return
        try:
            await redis_client.delete(key)
        except Exception:
            _mem_store.pop(key, None)

    async def exists(self, key: str) -> bool:
        if not _REDIS_AVAILABLE:
            return _mem_get(key) is not None
        try:
            return bool(await redis_client.exists(key))
        except Exception:
            return _mem_get(key) is not None

    async def incr(self, key: str, amount: int = 1) -> int:
        if not _REDIS_AVAILABLE:
            entry = _mem_store.get(key)
            if entry is not None:
                val, exp = entry
                if exp > time.time():
                    try:
                        new_val = int(val) + amount
                    except (ValueError, TypeError):
                        new_val = amount
                    _mem_store[key] = (new_val, exp)
                    return new_val
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
            _mem_store.clear()
            return
        try:
            await redis_client.flushdb()
            _mem_store.clear()
        except Exception:
            _mem_store.clear()


cache = RedisCache()
