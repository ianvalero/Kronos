from pydantic import BaseModel
from typing import Generic, TypeVar


class Pagination(BaseModel):
    offset: int
    limit: int
    total: int
    has_next: bool
    has_prev: bool

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    pagination: Pagination