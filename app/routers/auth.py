from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.database import get_session
from app.models.user import UserDB

router = APIRouter()

@router.post("/token", include_in_schema=False)
async def login_para_swagger(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: Session = Depends(get_session),
):

    statement = (
        select(UserDB)
        .where(UserDB.name == form_data.username)
    )
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario incorrecto para pruebas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": str(user.id), "token_type": "bearer"}