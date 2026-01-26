# app/models/__init__.py
"""
数据模型模块初始化
"""
from app.models.user import UserInfo, UserBehavior
from app.models.item import ItemInfo

__all__ = ["UserInfo", "UserBehavior", "ItemInfo"]
