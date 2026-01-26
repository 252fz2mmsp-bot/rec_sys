# app/schemas/__init__.py
"""
Schema 模块初始化
"""
from app.schemas.user import (
    UserInfoCreate,
    UserInfoUpdate,
    UserInfoResponse,
    UserBehaviorCreate,
    UserBehaviorResponse
)
from app.schemas.item import (
    ItemInfoCreate,
    ItemInfoUpdate,
    ItemInfoResponse
)
from app.schemas.common import ResponseModel, PaginationParams, PaginatedResponse

__all__ = [
    "UserInfoCreate",
    "UserInfoUpdate",
    "UserInfoResponse",
    "UserBehaviorCreate",
    "UserBehaviorResponse",
    "ItemInfoCreate",
    "ItemInfoUpdate",
    "ItemInfoResponse",
    "ResponseModel",
    "PaginationParams",
    "PaginatedResponse",
]
