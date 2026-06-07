# BUG: comment just repeats the filename
# the file path already tells us this
# delete comments that say nothing new
# models/base_response.py
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    success: bool = True
    content: T
