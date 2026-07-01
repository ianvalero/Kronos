from sqlmodel import SQLModel, Field

class UserDB(SQLModel, table=True):
    __tablename__ = "users"
    id: str | None = Field(default=None, primary_key=True)
    role: str
    exp: int