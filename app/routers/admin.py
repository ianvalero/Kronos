from fastapi import APIRouter, HTTPException, Depends, Request
from sqlmodel import Session, select

from app.models.user import User
from app.database import get_session

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", tags=["admin"], response_model=dict, summary="Get all users")
async def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return [
        {
            "id": user.id,
            "role": user.role,
            "expiration": user.exp
        }
        for user in users
    ]

@router.get("/users/{user_id}", tags=["admin"], response_model=dict, summary="Get a user")
async def get_user(user_id: str, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "role": user.role,
        "expiration": user.exp
    }

