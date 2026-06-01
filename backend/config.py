import os
import secrets
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

logger = logging.getLogger("historical_starlink")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

if _ENV_FILE.exists():
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


SQLITE_PATH = str(_PROJECT_ROOT / "data" / "local.db")


class Settings:
    _db_config: dict[str, str] = {}

    def __init__(self):
        env_map = {
            "app.name": os.getenv("PROJECT_NAME", "历史星链探索"),
            "app.host": os.getenv("SERVER_HOST", "111.231.50.67"),
            "app.port": os.getenv("SERVER_PORT", "8000"),
            "app.debug": os.getenv("DEBUG", "true"),
            "mysql.host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "mysql.port": os.getenv("MYSQL_PORT", "3306"),
            "mysql.user": os.getenv("MYSQL_USER", "root"),
            "mysql.password": os.getenv("MYSQL_PASSWORD", ""),
            "mysql.database": os.getenv("MYSQL_DATABASE", "historical_starlink"),
            "mysql.charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
            "db.driver": os.getenv("DB_DRIVER", "auto"),
            "redis.host": os.getenv("REDIS_HOST", "127.0.0.1"),
            "redis.port": os.getenv("REDIS_PORT", "6379"),
            "redis.db": os.getenv("REDIS_DB", "0"),
            "redis.password": os.getenv("REDIS_PASSWORD", ""),
            "redis.expire_seconds": os.getenv("REDIS_EXPIRE_SECONDS", "3600"),
            "cors.origins": os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"),
            "jwt.secret_key": os.getenv("JWT_SECRET_KEY", ""),
            "smtp.host": os.getenv("SMTP_HOST", "smtp.qq.com"),
            "smtp.port": os.getenv("SMTP_PORT", "465"),
            "smtp.user": os.getenv("SMTP_USER", ""),
            "smtp.password": os.getenv("SMTP_PASSWORD", ""),
            "smtp.from": os.getenv("SMTP_FROM", ""),
            "smtp.use_ssl": os.getenv("SMTP_USE_SSL", "true"),
            "upload.dir": os.getenv("UPLOAD_DIR", "uploads"),
            "minimax.api_key": os.getenv("MINIMAX_API_KEY", ""),
        }
        self._db_config = {k: v for k, v in env_map.items() if v}
        self.load_from_db(self._db_config)

    PROJECT_NAME: str = "历史星链探索"
    PROJECT_VERSION: str = "1.0.0"
    DESCRIPTION: str = "赛博朋克风格的历史探索游戏后端 API"

    SERVER_HOST: str = "111.231.50.67"
    SERVER_PORT: int = 8000
    DEBUG: bool = True

    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "historical_starlink"
    MYSQL_CHARSET: str = "utf8mb4"
    DB_DRIVER: str = "auto"

    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_EXPIRE_SECONDS: int = 3600

    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    ALLOWED_SIGNATURE_EXTENSIONS: set = {"png", "jpg", "jpeg", "gif", "webp"}

    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_SSL: bool = True

    EMAIL_CODE_EXPIRE_SECONDS: int = 300
    EMAIL_CODE_COOLDOWN_SECONDS: int = 60
    EMAIL_CODE_MAX_PER_HOUR: int = 10

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    MINIMAX_API_KEY: str = ""

    def _str(self, key: str, default: str = "") -> str:
        val = self._db_config.get(key)
        if val is not None and val != "":
            return val
        return default

    def _int(self, key: str, default: int = 0) -> int:
        val = self._db_config.get(key)
        if val is not None and val != "":
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
        return default

    def _bool(self, key: str, default: bool = False) -> bool:
        val = self._db_config.get(key)
        if val is not None and val != "":
            return val.lower() in ("true", "1", "yes")
        return default

    def _list(self, key: str, default: Optional[list] = None) -> list:
        val = self._db_config.get(key)
        if val is not None and val != "":
            return [v.strip() for v in val.split(",") if v.strip()]
        return default or []

    def load_from_db(self, configs: dict[str, str]):
        self._db_config = configs
        logger.info(f"Loaded {len(configs)} config items from database")

        self.PROJECT_NAME = self._str("app.name", self.PROJECT_NAME)
        self.PROJECT_VERSION = self._str("app.version", self.PROJECT_VERSION)
        self.DESCRIPTION = self._str("app.description", self.DESCRIPTION)
        self.SERVER_HOST = self._str("app.host", self.SERVER_HOST)
        self.SERVER_PORT = self._int("app.port", self.SERVER_PORT)
        self.DEBUG = self._bool("app.debug", self.DEBUG)

        self.MYSQL_HOST = self._str("mysql.host", self.MYSQL_HOST)
        self.MYSQL_PORT = self._int("mysql.port", self.MYSQL_PORT)
        self.MYSQL_USER = self._str("mysql.user", self.MYSQL_USER)
        self.MYSQL_PASSWORD = self._str("mysql.password", self.MYSQL_PASSWORD)
        self.MYSQL_DATABASE = self._str("mysql.database", self.MYSQL_DATABASE)
        self.MYSQL_CHARSET = self._str("mysql.charset", self.MYSQL_CHARSET)
        self.DB_DRIVER = self._str("db.driver", self.DB_DRIVER)

        self.REDIS_HOST = self._str("redis.host", self.REDIS_HOST)
        self.REDIS_PORT = self._int("redis.port", self.REDIS_PORT)
        self.REDIS_DB = self._int("redis.db", self.REDIS_DB)
        self.REDIS_PASSWORD = self._str("redis.password") or None
        self.REDIS_EXPIRE_SECONDS = self._int("redis.expire_seconds", self.REDIS_EXPIRE_SECONDS)

        self.CORS_ORIGINS = self._list("cors.origins", self.CORS_ORIGINS)
        self.CORS_ALLOW_CREDENTIALS = self._bool("cors.allow_credentials", self.CORS_ALLOW_CREDENTIALS)

        self.JWT_SECRET_KEY = self._str("jwt.secret_key", self.JWT_SECRET_KEY)
        self.JWT_ALGORITHM = self._str("jwt.algorithm", self.JWT_ALGORITHM)
        self.JWT_EXPIRE_DAYS = self._int("jwt.expire_days", self.JWT_EXPIRE_DAYS)

        self.SMTP_HOST = self._str("smtp.host", self.SMTP_HOST)
        self.SMTP_PORT = self._int("smtp.port", self.SMTP_PORT)
        self.SMTP_USER = self._str("smtp.user", self.SMTP_USER)
        self.SMTP_PASSWORD = self._str("smtp.password", self.SMTP_PASSWORD)
        self.SMTP_FROM = self._str("smtp.from", self.SMTP_FROM)
        self.SMTP_USE_SSL = self._bool("smtp.use_ssl", self.SMTP_USE_SSL)

        self.EMAIL_CODE_EXPIRE_SECONDS = self._int("email.code_expire_seconds", self.EMAIL_CODE_EXPIRE_SECONDS)
        self.EMAIL_CODE_COOLDOWN_SECONDS = self._int("email.code_cooldown_seconds", self.EMAIL_CODE_COOLDOWN_SECONDS)
        self.EMAIL_CODE_MAX_PER_HOUR = self._int("email.code_max_per_hour", self.EMAIL_CODE_MAX_PER_HOUR)

        self.UPLOAD_DIR = self._str("upload.dir", self.UPLOAD_DIR)
        self.MAX_UPLOAD_SIZE = self._int("upload.max_size", self.MAX_UPLOAD_SIZE)

        self.MINIMAX_API_KEY = self._str("minimax.api_key", self.MINIMAX_API_KEY)

    @property
    def DATABASE_URL(self) -> str:
        if self._should_use_mysql():
            user = quote_plus(self.MYSQL_USER)
            pwd = quote_plus(self.MYSQL_PASSWORD)
            return (
                f"mysql+aiomysql://{user}:{pwd}"
                f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
                f"?charset={self.MYSQL_CHARSET}"
            )
        return f"sqlite+aiosqlite:///{SQLITE_PATH}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self._should_use_mysql():
            user = quote_plus(self.MYSQL_USER)
            pwd = quote_plus(self.MYSQL_PASSWORD)
            return (
                f"mysql+pymysql://{user}:{pwd}"
                f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
                f"?charset={self.MYSQL_CHARSET}"
            )
        return f"sqlite:///{SQLITE_PATH}"

    def _should_use_mysql(self) -> bool:
        if self.DB_DRIVER == "mysql":
            return True
        if self.DB_DRIVER == "sqlite":
            return False
        return self._check_mysql_available()

    def _check_mysql_available(self) -> bool:
        import socket
        try:
            s = socket.create_connection(
                (self.MYSQL_HOST, self.MYSQL_PORT), timeout=5
            )
            s.close()
            return True
        except (ConnectionRefusedError, OSError, TimeoutError) as e:
            logger.warning(f"MySQL TCP probe failed: {e}")
            return False

    @property
    def DB_TYPE(self) -> str:
        return "MySQL" if self._should_use_mysql() else "SQLite"


settings = Settings()


async def load_db_config():
    from .database import AsyncSessionLocal
    from .models.system_config import SystemConfig
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(SystemConfig))
            rows = result.scalars().all()
            configs = {row.key: row.value for row in rows if row.value is not None}
            settings.load_from_db(configs)
    except Exception as e:
        logger.warning(f"Failed to load config from database, using defaults: {e}")

    _apply_env_override()


def _apply_env_override():
    env_map = {
        "app.name": "PROJECT_NAME",
        "app.host": "SERVER_HOST",
        "app.port": "SERVER_PORT",
        "app.debug": "DEBUG",
        "mysql.host": "MYSQL_HOST",
        "mysql.port": "MYSQL_PORT",
        "mysql.user": "MYSQL_USER",
        "mysql.password": "MYSQL_PASSWORD",
        "mysql.database": "MYSQL_DATABASE",
        "mysql.charset": "MYSQL_CHARSET",
        "db.driver": "DB_DRIVER",
        "redis.host": "REDIS_HOST",
        "redis.port": "REDIS_PORT",
        "redis.db": "REDIS_DB",
        "redis.password": "REDIS_PASSWORD",
        "redis.expire_seconds": "REDIS_EXPIRE_SECONDS",
        "cors.origins": "CORS_ORIGINS",
        "jwt.secret_key": "JWT_SECRET_KEY",
        "smtp.host": "SMTP_HOST",
        "smtp.port": "SMTP_PORT",
        "smtp.user": "SMTP_USER",
        "smtp.password": "SMTP_PASSWORD",
        "smtp.from": "SMTP_FROM",
        "smtp.use_ssl": "SMTP_USE_SSL",
        "upload.dir": "UPLOAD_DIR",
        "upload.max_size": "MAX_UPLOAD_SIZE",
        "minimax.api_key": "MINIMAX_API_KEY",
        "jwt.algorithm": "JWT_ALGORITHM",
        "jwt.expire_days": "JWT_EXPIRE_DAYS",
    }
    for cfg_key, env_name in env_map.items():
        env_val = os.getenv(env_name)
        if env_val is not None and env_val != "":
            settings._db_config[cfg_key] = env_val

    settings.load_from_db(settings._db_config)


if not settings.JWT_SECRET_KEY:
    if settings.DEBUG:
        settings.JWT_SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
        logger.warning("JWT_SECRET_KEY not set. Using dev key. Do NOT use in production!")
    else:
        settings.JWT_SECRET_KEY = secrets.token_hex(32)
        logger.warning("JWT_SECRET_KEY not set in production! Generated random key.")
