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
    PROJECT_NAME: str = "历史星链探索"
    PROJECT_VERSION: str = "1.0.0"
    DESCRIPTION: str = "赛博朋克风格的历史探索游戏后端 API"

    SERVER_HOST: str = "111.231.50.67"
    SERVER_PORT: int = 8000
    DEBUG: bool = True

    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "historical_starlink")
    MYSQL_CHARSET: str = "utf8mb4"

    DB_DRIVER: str = os.getenv("DB_DRIVER", "auto")

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
                (self.MYSQL_HOST, self.MYSQL_PORT), timeout=2
            )
            s.close()
            return True
        except (ConnectionRefusedError, OSError, TimeoutError):
            return False

    @property
    def DB_TYPE(self) -> str:
        return "MySQL" if self._should_use_mysql() else "SQLite"

    REDIS_HOST: str = os.getenv("REDIS_HOST", "111.231.50.67")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_EXPIRE_SECONDS: int = 3600

    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024
    ALLOWED_SIGNATURE_EXTENSIONS: set = {"png", "jpg", "jpeg", "gif", "webp"}

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.qq.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "")
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"

    EMAIL_CODE_EXPIRE_SECONDS: int = 300
    EMAIL_CODE_COOLDOWN_SECONDS: int = 60
    EMAIL_CODE_MAX_PER_HOUR: int = 10

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7


settings = Settings()

if not settings.JWT_SECRET_KEY:
    if settings.DEBUG:
        settings.JWT_SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"
        logger.warning("JWT_SECRET_KEY not set. Using dev key. Do NOT use in production!")
    else:
        settings.JWT_SECRET_KEY = secrets.token_hex(32)
        logger.warning("JWT_SECRET_KEY not set in production! Generated random key. Set JWT_SECRET_KEY env var for persistence.")
