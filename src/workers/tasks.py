"""
Celery-задачи: офлайн-анализ видео и запись AIEvent в PostgreSQL.
"""

import logging
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete

from src.core.celery_app import celery_app
from src.core.config import get_settings
from src.infrastructure.database_sync import get_sync_session
from src.infrastructure.models import AIEvent, Stream
from src.infrastructure.repositories_sync import insert_goal_events, mark_stream_processed
from src.workers.video_pipeline import (
    resolve_debug_mode,
    resolve_debug_path,
    run_goal_detection_pipeline,
)

logger = logging.getLogger(__name__)


@celery_app.task(name="process_stream_video")
def process_stream_video(stream_id: str) -> dict:
    """
    Полный проход по mp4: детекция голов, перезапись событий для данного stream_id.
    """
    settings = get_settings()
    sid = UUID(stream_id)
    video_dir = Path(settings.video_storage_path)

    try:
        with get_sync_session() as session:
            stream = session.get(Stream, sid)
            if stream is None:
                return {"ok": False, "error": "stream_not_found", "stream_id": stream_id}

            video_path = video_dir / stream.filename
            if not video_path.is_file():
                logger.error("Файл видео отсутствует: %s", video_path)
                return {"ok": False, "error": "video_file_missing", "path": str(video_path)}

            session.execute(delete(AIEvent).where(AIEvent.stream_id == sid))

        debug = resolve_debug_mode()
        debug_path = resolve_debug_path() if debug else None

        timestamps = run_goal_detection_pipeline(
            video_path,
            target_process_fps=30.0,
            debug_mode=debug,
            debug_output_path=debug_path,
        )

        with get_sync_session() as session:
            insert_goal_events(session, sid, timestamps)
            mark_stream_processed(session, sid, processed=True)

        logger.info("Stream %s: записано %d событий goal", stream_id, len(timestamps))
        return {
            "ok": True,
            "stream_id": stream_id,
            "goals_detected": len(timestamps),
            "timestamps": timestamps,
            "debug_video": str(debug_path) if debug and debug_path else None,
        }
    except Exception as exc:  # noqa: BLE001 — прототип: логируем и отдаём текст в результат
        logger.exception("Ошибка обработки видео stream=%s", stream_id)
        return {"ok": False, "error": str(exc), "stream_id": stream_id}
