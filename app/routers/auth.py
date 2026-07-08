from fastapi import APIRouter, Depends
from sqlmodel import Session

import app.dependencies.services as dependencies
from app.database import get_session
from app.schemas.user import User, UserLoginResponse
from app.services.user_service import UserService

router = APIRouter()

@router.post(
    "/token",
    include_in_schema=False,
    response_model=UserLoginResponse,
    summary="User login"
)
async def login(
    body: User,
    session: Session = Depends(get_session),
    user_service: UserService = Depends(dependencies.get_user_service),
):
    return user_service.authenticate_sso_user(
        session=session,
        sso_id=body.sub,
        username=body.username,
        email=body.email,
        name=body.name,
        roles=body.roles,
    )