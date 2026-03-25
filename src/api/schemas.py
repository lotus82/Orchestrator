from uuid import UUID

from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)


class UserRegisterResponse(BaseModel):
    id: UUID
    username: str


class PredictClickRequest(BaseModel):
    user_id: UUID
    stream_id: UUID
    click_timestamp_sec: float = Field(..., ge=0.0)


class PredictClickResponse(BaseModel):
    score_awarded: int
    delta_t: float | None
    matched_ai_event_id: UUID | None
    t_true: float | None


class LeaderboardEntry(BaseModel):
    user_id: UUID
    username: str
    total_score: int


class StreamCreateRequest(BaseModel):
    title: str = Field(..., max_length=256)
    filename: str = Field(..., max_length=512)


class StreamResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    is_processed_by_ai: bool
