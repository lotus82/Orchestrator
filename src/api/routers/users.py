from fastapi import APIRouter, HTTPException, status

from src.api.deps import SessionDep
from src.api.schemas import UserRegisterRequest, UserRegisterResponse
from src.infrastructure.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRegisterResponse)
async def register_user(body: UserRegisterRequest, session: SessionDep) -> UserRegisterResponse:
    repo = UserRepository(session)
    existing = await repo.get_by_username(body.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Имя пользователя уже занято",
        )
    user = await repo.create(body.username)
    return UserRegisterResponse(id=user.id, username=user.username)
