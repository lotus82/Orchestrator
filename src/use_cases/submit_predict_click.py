"""
Сценарий: приём клика пользователя, сопоставление с ближайшим AI-событием и начисление очков.
"""

from dataclasses import dataclass
from uuid import UUID

from src.domain.repositories import (
    AIEventRepositoryPort,
    StreamRepositoryPort,
    UserActionRepositoryPort,
    UserRepositoryPort,
)
from src.use_cases.scoring import calculate_score


@dataclass
class SubmitClickResult:
    score_awarded: int
    delta_t: float | None
    matched_ai_event_id: UUID | None
    t_true: float | None


class SubmitPredictClickUseCase:
    def __init__(
        self,
        users: UserRepositoryPort,
        streams: StreamRepositoryPort,
        ai_events: AIEventRepositoryPort,
        actions: UserActionRepositoryPort,
        *,
        p_max: int = 1000,
        window: float = 3.0,
    ) -> None:
        self._users = users
        self._streams = streams
        self._ai_events = ai_events
        self._actions = actions
        self._p_max = p_max
        self._window = window

    async def execute(
        self,
        user_id: UUID,
        stream_id: UUID,
        click_timestamp_sec: float,
    ) -> SubmitClickResult:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ValueError("Пользователь не найден")

        stream = await self._streams.get_by_id(stream_id)
        if stream is None:
            raise ValueError("Трансляция не найдена")

        nearest = await self._ai_events.find_nearest_goal(stream_id, click_timestamp_sec)

        if nearest is None:
            await self._actions.create_action(
                user_id=user_id,
                stream_id=stream_id,
                click_timestamp_sec=click_timestamp_sec,
                matched_ai_event_id=None,
                score_awarded=0,
            )
            return SubmitClickResult(
                score_awarded=0,
                delta_t=None,
                matched_ai_event_id=None,
                t_true=None,
            )

        t_true = float(nearest.timestamp_sec)
        score, delta_t = calculate_score(
            t_true, click_timestamp_sec, p_max=self._p_max, window=self._window
        )

        await self._actions.create_action(
            user_id=user_id,
            stream_id=stream_id,
            click_timestamp_sec=click_timestamp_sec,
            matched_ai_event_id=nearest.id,
            score_awarded=score,
        )

        return SubmitClickResult(
            score_awarded=score,
            delta_t=delta_t,
            matched_ai_event_id=nearest.id,
            t_true=t_true,
        )
