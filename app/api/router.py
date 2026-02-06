# app/api/router.py
"""
API 路由汇总
"""
from fastapi import APIRouter
from app.api.endpoints import users, items, recommend, search

# 创建 API 路由器
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    items.router,
    prefix="/items",
    tags=["Items"]
)

api_router.include_router(
    recommend.router,
    prefix="/recommend",
    tags=["Recommendations"]
)

api_router.include_router(
    search.router,
    prefix="/search",
    tags=["Search"]
)
