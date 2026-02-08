"""
Централизованная конфигурация приложения через Pydantic Settings.
"""
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Главная конфигурация приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== TELEGRAM BOT ====================
    BOT_TOKEN: str = Field(..., description="Telegram Bot API Token")
    ADMIN_CHAT_ID: int = Field(..., description="Admin Telegram Chat ID")

    # ==================== DATABASE ====================
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./instagram_bot.db",
        description="Database URL (asyncpg or aiosqlite)",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string",
    )

    # ==================== EXTERNAL APIs ====================
    OPENROUTER_API_KEY: str = Field(..., description="OpenRouter API Key")
    OPENROUTER_MODEL: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="AI model for rewriting",
    )
    OPENROUTER_TEMPERATURE: float = Field(
        default=0.7,
        description="Temperature for AI (0.7 — баланс креативности и стабильности)",
    )
    OPENROUTER_MAX_TOKENS: int = Field(
        default=4000,
        description="Max tokens в ответе OpenRouter",
    )

    ORSHOT_API_KEY: str = Field(
        ..., description="Orshot API Key for image generation"
    )
    ORSOT_TEMPLATE_ID: int = Field(
        default=2685,
        description="Orshot template ID (backward compatibility)",
    )
    YANDEX_DISK_TOKEN: str = Field(
        default="",
        description="Yandex.Disk OAuth Token",
    )
    APIFY_API_KEY: str = Field(
        default="",
        description="Apify API Key for Instagram parsing",
    )

    # ==================== INSTAGRAM PUBLISHING ====================
    INSTAGRAM_USERNAME: str = Field(
        default="",
        description="Instagram username for publishing",
    )
    INSTAGRAM_PASSWORD: str = Field(
        default="",
        description="Instagram password for publishing",
    )
    INSTAGRAM_PROXY: Optional[str] = Field(
        default=None,
        description="Proxy URL for Instagram (e.g. http://user:pass@host:port)",
    )

    # ==================== INSTAGRAM PARSING ====================
    INSTAGRAM_AUTHORS: str = Field(
        default="sanyaagainst,theivansergeev,ivan.loginov_ai,provotorov_pro,generalov_ai",
        description="Comma-separated list of Instagram usernames to parse",
    )
    MIN_LIKES: int = Field(default=5000, description="Minimum likes for viral posts")
    MAX_POST_AGE_DAYS: int = Field(default=3, description="Maximum post age in days")
    MIN_TEXT_LENGTH: int = Field(default=100, description="Minimum text length")

    # ==================== CELERY WORKERS ====================
    CELERY_BROKER_URL: Optional[str] = Field(default=None)
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None)

    # ==================== SCHEDULER ====================
    PARSE_CRON: str = Field(
        default="0 */6 * * *",
        description="Cron expression for parsing (every 6 hours)",
    )
    PROCESS_CRON: str = Field(
        default="0 * * * *",
        description="Cron expression for processing (every hour)",
    )

    # ==================== LOGGING ====================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="logs/bot.log", description="Log file path")

    # ==================== VALIDATORS ====================

    @field_validator("INSTAGRAM_AUTHORS")
    @classmethod
    def validate_instagram_authors(cls, v: str) -> str:
        """Валидация списка авторов Instagram."""
        authors = [a.strip() for a in v.split(",") if a.strip()]
        if not authors:
            raise ValueError("INSTAGRAM_AUTHORS must contain at least one username")
        if len(authors) > 20:
            raise ValueError("Too many authors (max 20)")
        return v

    @field_validator("MIN_LIKES")
    @classmethod
    def validate_min_likes(cls, v: int) -> int:
        """Валидация минимального количества лайков."""
        if v < 100:
            raise ValueError("MIN_LIKES must be at least 100")
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Валидация уровня логирования."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v

    # ==================== COMPUTED PROPERTIES ====================

    @property
    def instagram_authors_list(self) -> List[str]:
        """Возвращает список авторов Instagram как list."""
        return [a.strip() for a in self.INSTAGRAM_AUTHORS.split(",") if a.strip()]

    @property
    def celery_broker(self) -> str:
        """Возвращает Celery broker URL (по умолчанию Redis)."""
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        """Возвращает Celery result backend URL."""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @property
    def logs_dir(self) -> Path:
        """Возвращает путь к директории логов."""
        log_path = Path(self.LOG_FILE)
        return log_path.parent

    # Обратная совместимость с прежними именами настроек
    @property
    def MIN_LIKES_THRESHOLD(self) -> int:
        return self.MIN_LIKES

    @property
    def POSTS_AGE_DAYS(self) -> int:
        return self.MAX_POST_AGE_DAYS

    @property
    def PARSING_INTERVAL_HOURS(self) -> int:
        """Из PARSE_CRON '0 */6 * * *' -> 6."""
        if "*/6" in self.PARSE_CRON:
            return 6
        return 6

    @property
    def ORSOT_API_KEY(self) -> str:
        return self.ORSHOT_API_KEY

    # ==================== METHODS ====================

    @classmethod
    def from_env(cls) -> "Config":
        """Загружает конфигурацию из .env файла."""
        return cls()

    def ensure_logs_dir(self) -> None:
        """Создает директорию для логов если не существует."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def get_database_url(self, sync: bool = False) -> str:
        """
        Возвращает Database URL.

        Args:
            sync: Если True, возвращает синхронный URL (psycopg2)
        """
        if sync:
            return self.DATABASE_URL.replace("asyncpg", "psycopg2")
        return self.DATABASE_URL

    def __repr__(self) -> str:
        """Безопасное представление конфигурации (без секретов)."""
        return (
            f"Config("
            f"bot_token=***{self.BOT_TOKEN[-4:]}, "
            f"admin_chat_id={self.ADMIN_CHAT_ID}, "
            f"authors={len(self.instagram_authors_list)}, "
            f"log_level={self.LOG_LEVEL}"
            f")"
        )


# ==================== SINGLETON INSTANCE ====================

_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Возвращает singleton instance конфигурации."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.from_env()
        _config_instance.ensure_logs_dir()
    return _config_instance


# Backward compatibility: from app.config import settings
settings = get_config()


# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    # Для тестирования
    config = get_config()
    print(config)
    print(f"Instagram authors: {config.instagram_authors_list}")
    print(f"Database URL: {config.get_database_url(sync=False)}")
    print(f"Celery broker: {config.celery_broker}")
