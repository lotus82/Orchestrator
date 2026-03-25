"""
Синхронные репозитории для Celery (общая сессия Session).
"""

from uuid import UUID

from sqlalchemy.orm import Session

from src.infrastructure.models import AIEvent, Stream


def insert_goal_events(session: Session, stream_id: UUID, timestamps_sec: list[float]) -> None:
    for ts in timestamps_sec:
        session.add(
            AIEvent(
                stream_id=stream_id,
                event_type="goal",
                timestamp_sec=float(ts),
            )
        )


def mark_stream_processed(session: Session, stream_id: UUID, processed: bool = True) -> None:
    stream = session.get(Stream, stream_id)
    if stream is not None:
        stream.is_processed_by_ai = processed
        session.add(stream)
