from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.models import Stream


class StreamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, title: str, filename: str) -> Stream:
        stream = Stream(title=title, filename=filename, is_processed_by_ai=False)
        self._session.add(stream)
        await self._session.flush()
        await self._session.refresh(stream)
        return stream

    async def get_by_id(self, stream_id: UUID) -> Stream | None:
        return await self._session.get(Stream, stream_id)
