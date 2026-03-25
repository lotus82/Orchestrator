from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.models import User, UserAction


class UserActionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_action(
        self,
        user_id: UUID,
        stream_id: UUID,
        click_timestamp_sec: float,
        matched_ai_event_id: UUID | None,
        score_awarded: int,
    ) -> UserAction:
        row = UserAction(
            user_id=user_id,
            stream_id=stream_id,
            click_timestamp_sec=click_timestamp_sec,
            matched_ai_event_id=matched_ai_event_id,
            score_awarded=score_awarded,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_leaderboard(self, limit: int = 50) -> list[tuple[UUID, str, int]]:
        """
        Возвращает (user_id, username, total_score), отсортировано по убыванию очков.
        """
        total_expr = func.coalesce(func.sum(UserAction.score_awarded), 0).label("total")
        stmt = (
            select(
                UserAction.user_id,
                User.username,
                total_expr,
            )
            .join(User, User.id == UserAction.user_id)
            .group_by(UserAction.user_id, User.username)
            .order_by(total_expr.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [(r.user_id, r.username, int(r.total)) for r in rows]
