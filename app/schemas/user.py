from pydantic import BaseModel
from typing import List

class User(BaseModel):
    sub: str
    username: str
    email: str
    name: str
    roles: List[str]

class UserLoginResponse(BaseModel):
    id: int
    username: str
    api_key: str