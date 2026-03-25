"""
Глобальные настройки приложения (pydantic-settings).
Поддерживаются переменные окружения и .env в корне проекта.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL: async для FastAPI, sync для Celery
    database_url: str = "postgresql+asyncpg://game:game@localhost:5432/game_db"
    database_url_sync: str = "postgresql://game:game@localhost:5432/game_db"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Каталог с mp4 (в Docker: /app/videos)
    video_storage_path: str = "./videos"

    # Отладочная визуализация YOLO (путь к выходному mp4)
    yolo_debug_mode: bool = False
    yolo_debug_output: str = "./debug_output.mp4"

    # CORS для локальной разработки фронта
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000", "null"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
