from pydantic import BaseModel
from datetime import datetime
from typing import List

class User(BaseModel):
    username: str
    email: str
    name: str
    roles: List[str]
    is_admin: bool
    is_automation: bool

class UserSSO(BaseModel):
    sso_id: str
    username: str
    email: str
    name: str
    roles: List[str]

class UserLoginResponse(BaseModel):
    id: int
    username: str
    api_key: str
    api_key_expires_at: datetime