# app/schemas/common.py
"""
通用响应 Schema
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[T] = None


class PaginationParams(BaseModel):
    """分页参数"""
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    total: int
    items: List[T]
    skip: int
    limit: int
