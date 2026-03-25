"""
Синхронная сессия для Celery (psycopg2), без asyncpg.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import SQLModel, create_engine

from src.core.config import get_settings

settings = get_settings()

sync_engine = create_engine(
    settings.database_url_sync,
    echo=False,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db_sync() -> None:
    SQLModel.metadata.create_all(sync_engine)
