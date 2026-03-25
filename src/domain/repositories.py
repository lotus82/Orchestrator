"""
Порты репозиториев для use cases (без зависимости от SQLModel / infrastructure).
"""

from typing import Any, Protocol
from uuid import UUID


class UserRepositoryPort(Protocol):
    async def create(self, username: str) -> Any: ...

    async def get_by_id(self, user_id: UUID) -> Any | None: ...


class StreamRepositoryPort(Protocol):
    async def get_by_id(self, stream_id: UUID) -> Any | None: ...


class AIEventRepositoryPort(Protocol):
    async def find_nearest_goal(
        self, stream_id: UUID, click_timestamp_sec: float
    ) -> Any | None: ...


class UserActionRepositoryPort(Protocol):
    async def create_action(
        self,
        user_id: UUID,
        stream_id: UUID,
        click_timestamp_sec: float,
        matched_ai_event_id: UUID | None,
        score_awarded: int,
    ) -> Any: ...
