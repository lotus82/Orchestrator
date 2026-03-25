"""
Точка входа FastAPI: REST API + раздача статики и видео для прототипа.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from src.api.routers import game, streams, users
from src.core.config import get_settings
from src.infrastructure.database import AsyncSessionLocal, init_db
from src.infrastructure.models import Stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _seed_demo_stream_if_empty()
    yield


async def _seed_demo_stream_if_empty() -> None:
    """Одна демо-трансляция penalty.mp4, если таблица пуста."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Stream).limit(1))
            result = await session.execute(select(Stream).limit(1))
            stream = result.scalar_one_or_none()
            
            if stream is not None:
                if stream.filename == "penalty.mp4":
                    stream.filename = "penalty_ball.mp4"
                    stream.title = "Демо: футбольный матч (AI)"
                    stream.is_processed_by_ai = True
                    session.add(stream)
                    await session.commit()
                else:
                    return
            else:
                stream = Stream(
                    title="Демо: футбольный матч (AI)",
                    filename="penalty_ball.mp4",
                    is_processed_by_ai=True,
                )
                session.add(stream)
                await session.commit()
            
            # Проверяем, есть ли уже события для этого стрима
            from src.infrastructure.models import AIEvent
            from sqlalchemy import func
            events_count = await session.execute(select(func.count(AIEvent.id)).where(AIEvent.stream_id == stream.id))
            if events_count.scalar() > 0:
                return

            # Загружаем предрассчитанные таймкоды, если они есть
            import json
            from src.core.config import get_settings
            
            settings = get_settings()
            timecodes_path = Path(settings.video_storage_path) / "goal_timecodes.json"
            
            if timecodes_path.exists():
                with open(timecodes_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for ts in data.get("goal_timestamps", []):
                        session.add(
                            AIEvent(
                                stream_id=stream.id,
                                event_type="goal",
                                timestamp_sec=float(ts),
                            )
                        )
                await session.commit()
            else:
                # Если файла нет, запускаем обработку видео
                from src.workers.tasks import process_stream_video
                process_stream_video.delay(str(stream.id))
        except Exception:
            await session.rollback()
            raise


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Live Event Game API",
        description="Прототип: клик по событию, скоринг относительно AI Ground Truth",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(users.router, prefix="/api")
    application.include_router(streams.router, prefix="/api")
    application.include_router(game.router, prefix="/api")

    static_dir = Path(__file__).resolve().parent.parent.parent / "static"
    if static_dir.is_dir():
        application.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        @application.get("/")
        async def serve_index() -> FileResponse:
            return FileResponse(static_dir / "index.html")

    video_dir = Path(settings.video_storage_path)
    if video_dir.is_dir():
        application.mount("/videos", StaticFiles(directory=str(video_dir)), name="videos")

    return application


app = create_app()
