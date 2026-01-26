# app/schemas/user.py
"""
用户相关的 Pydantic Schema
用于请求验证和响应序列化
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ========== 用户信息 Schema ==========

class UserInfoBase(BaseModel):
    """用户信息基础 Schema"""
    member_level: Optional[int] = Field(0, description="是否会员 0-否 1-是")
    modeler_level: Optional[int] = Field(0, description="是否建模师 0-否 1-是")
    reg_time: Optional[datetime] = Field(None, description="注册时间")
    sex: Optional[str] = Field(None, max_length=10, description="性别")
    country: Optional[str] = Field(None, max_length=100, description="国家")
    province: Optional[str] = Field(None, max_length=100, description="省份")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    login_time: Optional[datetime] = Field(None, description="上次登录时间")


class UserInfoCreate(UserInfoBase):
    """创建用户信息 Schema"""
    uid: str = Field(..., max_length=100, description="用户ID")


class UserInfoUpdate(UserInfoBase):
    """更新用户信息 Schema（所有字段可选）"""
    pass


class UserInfoResponse(UserInfoBase):
    """用户信息响应 Schema"""
    uid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 使用 from_attributes 替代 orm_mode


# ========== 用户行为 Schema ==========

class UserBehaviorBase(BaseModel):
    """用户行为基础 Schema"""
    user_id: str = Field(..., max_length=100, description="用户ID")
    item_id: str = Field(..., max_length=100, description="商品ID")
    scene: Optional[str] = Field(None, max_length=100, description="场景")
    app_type: Optional[str] = Field(None, max_length=100, description="应用类型")
    app_version: Optional[str] = Field(None, max_length=100, description="应用版本")
    position: Optional[str] = Field(None, description="位置信息")
    event: Optional[str] = Field(None, max_length=100, description="事件类型")
    event_time: Optional[datetime] = Field(None, description="事件时间")
    ip: Optional[str] = Field(None, max_length=100, description="IP地址")
    country: Optional[str] = Field(None, max_length=100, description="国家")
    province: Optional[str] = Field(None, max_length=100, description="省份")
    city: Optional[str] = Field(None, max_length=100, description="城市")


class UserBehaviorCreate(UserBehaviorBase):
    """创建用户行为 Schema"""
    pass


class UserBehaviorResponse(UserBehaviorBase):
    """用户行为响应 Schema"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
