from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.models import AIEvent


class AIEventRepository:
    """CRUD и поиск ближайшего goal-события для скоринга."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_nearest_goal(
        self, stream_id: UUID, click_timestamp_sec: float
    ) -> AIEvent | None:
        stmt = (
            select(AIEvent)
            .where(
                AIEvent.stream_id == stream_id,
                AIEvent.event_type == "goal",
            )
            .order_by(func.abs(AIEvent.timestamp_sec - click_timestamp_sec))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
