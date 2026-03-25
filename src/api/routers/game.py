from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import SessionDep
from src.api.schemas import LeaderboardEntry, PredictClickRequest, PredictClickResponse
from src.infrastructure.repositories.ai_event_repository import AIEventRepository
from src.infrastructure.repositories.stream_repository import StreamRepository
from src.infrastructure.repositories.user_action_repository import UserActionRepository
from src.infrastructure.repositories.user_repository import UserRepository
from src.use_cases.submit_predict_click import SubmitPredictClickUseCase

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/click", response_model=PredictClickResponse)
async def predict_click(body: PredictClickRequest, session: SessionDep) -> PredictClickResponse:
    use_case = SubmitPredictClickUseCase(
        users=UserRepository(session),
        streams=StreamRepository(session),
        ai_events=AIEventRepository(session),
        actions=UserActionRepository(session),
    )
    try:
        result = await use_case.execute(
            user_id=body.user_id,
            stream_id=body.stream_id,
            click_timestamp_sec=body.click_timestamp_sec,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return PredictClickResponse(
        score_awarded=result.score_awarded,
        delta_t=result.delta_t,
        matched_ai_event_id=result.matched_ai_event_id,
        t_true=result.t_true,
    )


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def leaderboard(
    session: SessionDep,
    limit: int = Query(50, ge=1, le=200),
) -> list[LeaderboardEntry]:
    repo = UserActionRepository(session)
    rows = await repo.get_leaderboard(limit=limit)
    return [
        LeaderboardEntry(user_id=uid, username=uname, total_score=score)
        for uid, uname, score in rows
    ]
