from pydantic import BaseModel
from typing import List

class User(BaseModel):
    username: str
    email: str
    name: str
    roles: List[str]
    is_admin: bool

class UserSSO(User):
    sso_id: str

class UserLoginResponse(BaseModel):
    id: int
    username: str
    api_key: str