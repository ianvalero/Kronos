from fastapi import APIRouter, Depends
from sqlmodel import Session

import app.dependencies.services as dependencies
from app.database import get_session
from app.schemas.user import UserSSO, UserLoginResponse
from app.services.user_service import UserService

router = APIRouter()

@router.post(
    "/token",
    include_in_schema=False,
    response_model=UserLoginResponse,
    summary="User login"
)
async def login(
    body: UserSSO,
    session: Session = Depends(get_session),
    user_service: UserService = Depends(dependencies.get_user_service),
):
    return user_service.authenticate_sso_user(session=session, user=body)