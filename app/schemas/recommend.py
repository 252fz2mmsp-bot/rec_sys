"""
推荐系统相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RecommendRequest(BaseModel):
    """推荐请求 Schema"""
    user_id: str = Field(..., description="用户ID")
    algorithm: str = Field("popular", description="推荐算法: random/popular/itemcf")
    k: int = Field(10, ge=1, le=100, description="推荐数量")
    filter_interacted: bool = Field(True, description="是否过滤用户已交互的商品")


class RecommendItem(BaseModel):
    """推荐商品 Schema"""
    item_id: str = Field(..., description="商品ID")
    score: float = Field(..., description="推荐分数")
    rank: int = Field(..., description="排名")
    title: Optional[str] = Field(None, description="商品标题")
    category: Optional[str] = Field(None, description="商品类目")


class RecommendResponse(BaseModel):
    """推荐响应 Schema"""
    user_id: str = Field(..., description="用户ID")
    algorithm: str = Field(..., description="使用的推荐算法")
    recommendations: List[RecommendItem] = Field(..., description="推荐列表")
    total_count: int = Field(..., description="推荐数量")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")


class AlgorithmInfo(BaseModel):
    """算法信息 Schema"""
    algorithm: str = Field(..., description="算法名称")
    display_name: str = Field(..., description="显示名称")
    description: str = Field(..., description="算法描述")
    is_fitted: bool = Field(False, description="是否已训练")
    requires_training: bool = Field(False, description="是否需要训练")


class UserBehaviorCreate(BaseModel):
    """创建用户行为 Schema"""
    user_id: str = Field(..., max_length=100, description="用户ID")
    item_id: str = Field(..., max_length=100, description="商品ID")
    action_type: str = Field(..., max_length=20, description="行为类型")
    timestamp: Optional[datetime] = Field(None, description="行为时间")


class UserBehaviorResponse(BaseModel):
    """用户行为响应 Schema"""
    id: int
    user_id: str
    item_id: str
    action_type: str
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
