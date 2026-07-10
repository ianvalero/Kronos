from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config.settings import settings
from app.database import get_session
from app.schemas.user import UserSSO, UserLoginResponse
from app.services.user_service import UserService
import app.dependencies.services as dependencies_services
from app.security.automation import require_automation

router = APIRouter()

@router.post(
    "/token",
    include_in_schema=(settings.environment == "local"),
    response_model=UserLoginResponse,
    dependencies=[Depends(require_automation)],
    summary="User login"
)
async def login(
    body: UserSSO,
    session: Session = Depends(get_session),
    user_service: UserService = Depends(dependencies_services.get_user_service),
):
    return user_service.authenticate_sso_user(session=session, user=body)