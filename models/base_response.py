from typing import Generic, TypeVar
from pydantic import BaseModel
from typing import List

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    status_code: int
    success: bool = True
    content: T

    
    