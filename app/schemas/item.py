# app/schemas/item.py
"""
商品相关的 Pydantic Schema
用于请求验证和响应序列化
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ItemInfoBase(BaseModel):
    """商品信息基础 Schema"""
    group_name: Optional[str] = Field(None, max_length=500, description="商品组名称")
    first_level_category_name: Optional[str] = Field(None, max_length=200, description="一级分类名称")
    second_level_category_name: Optional[str] = Field(None, max_length=200, description="二级分类名称")
    tags_name_list: Optional[str] = Field(None, description="标签列表，多个标签用逗号分隔")
    cover_first: Optional[str] = Field(None, max_length=500, description="封面图片URL")
    group_desc: Optional[str] = Field(None, description="商品描述")


class ItemInfoCreate(ItemInfoBase):
    """创建商品信息 Schema"""
    id: str = Field(..., max_length=100, description="商品ID", alias="_id")
    
    class Config:
        populate_by_name = True  # 允许使用字段名或别名


class ItemInfoUpdate(ItemInfoBase):
    """更新商品信息 Schema（所有字段可选）"""
    pass


class ItemInfoResponse(ItemInfoBase):
    """商品信息响应 Schema"""
    id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
