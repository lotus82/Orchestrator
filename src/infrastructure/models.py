"""
SQLModel-сущности: PostgreSQL, UUID, индексы.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=128)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Stream(SQLModel, table=True):
    __tablename__ = "streams"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=256)
    filename: str = Field(max_length=512, description="Имя файла или относительный путь в VIDEO_STORAGE_PATH")
    is_processed_by_ai: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AIEvent(SQLModel, table=True):
    __tablename__ = "ai_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    stream_id: UUID = Field(foreign_key="streams.id", index=True)
    event_type: str = Field(max_length=64, index=True)
    timestamp_sec: float = Field(description="Секунды от начала видео")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserAction(SQLModel, table=True):
    __tablename__ = "user_actions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    stream_id: UUID = Field(foreign_key="streams.id", index=True)
    click_timestamp_sec: float = Field()
    matched_ai_event_id: UUID | None = Field(default=None, foreign_key="ai_events.id")
    score_awarded: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
