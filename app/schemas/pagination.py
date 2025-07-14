from math import ceil
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int


def create_paginated_response(
    data: List[T], total: int, page: int, per_page: int
) -> PaginatedResponse[T]:
    return PaginatedResponse(
        data=data,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=ceil(total / per_page) if per_page > 0 else 0,
    )
