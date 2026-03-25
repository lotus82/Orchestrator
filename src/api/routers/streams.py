from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.api.deps import SessionDep
from src.api.schemas import StreamCreateRequest, StreamResponse
from src.infrastructure.models import Stream
from src.infrastructure.repositories.stream_repository import StreamRepository

router = APIRouter(prefix="/streams", tags=["streams"])


@router.get("", response_model=list[StreamResponse])
async def list_streams(session: SessionDep) -> list[StreamResponse]:
    result = await session.execute(select(Stream).order_by(Stream.created_at))
    rows = result.scalars().all()
    return [
        StreamResponse(
            id=s.id,
            title=s.title,
            filename=s.filename,
            is_processed_by_ai=s.is_processed_by_ai,
        )
        for s in rows
    ]


@router.post("", response_model=StreamResponse, status_code=status.HTTP_201_CREATED)
async def create_stream(body: StreamCreateRequest, session: SessionDep) -> StreamResponse:
    repo = StreamRepository(session)
    s = await repo.create(body.title, body.filename)
    return StreamResponse(
        id=s.id,
        title=s.title,
        filename=s.filename,
        is_processed_by_ai=s.is_processed_by_ai,
    )


@router.post("/{stream_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_ai_processing(stream_id: UUID, session: SessionDep) -> dict:
    """Ставит в очередь Celery задачу разбора видео (YOLO + сохранение AIEvent)."""
    stream = await session.get(Stream, stream_id)
    if stream is None:
        raise HTTPException(status_code=404, detail="Трансляция не найдена")

    from src.workers.tasks import process_stream_video

    process_stream_video.delay(str(stream_id))
    return {"enqueued": True, "stream_id": str(stream_id)}
