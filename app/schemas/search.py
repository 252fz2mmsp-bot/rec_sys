"""
搜索相关的 Schema 定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SearchRequest(BaseModel):
    """搜索请求"""
    q: str = Field(..., description="搜索关键词", min_length=1)
    page: int = Field(1, ge=1, description="页码（从 1 开始）")
    size: int = Field(20, ge=1, le=100, description="每页大小（最大 100）")
    category: Optional[str] = Field(None, description="类目筛选")
    sort_by: str = Field("relevance", description="排序方式：relevance/popular/newest")
    
    class Config:
        json_schema_extra = {
            "example": {
                "q": "3d printing",
                "page": 1,
                "size": 20,
                "sort_by": "relevance"
            }
        }


class SearchItemResponse(BaseModel):
    """搜索结果中的商品"""
    item_id: str
    title: Optional[str] = None
    group_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    first_level_category: Optional[str] = None
    second_level_category: Optional[str] = None
    view_count: int = 0
    download_count: int = 0
    like_count: int = 0
    score: float = Field(..., alias="_score", description="相关性分数")
    
    class Config:
        populate_by_name = True  # Pydantic v2 允许使用别名
        json_schema_extra = {
            "example": {
                "item_id": "item_001",
                "title": "3D Printer Stand",
                "tags": ["3d-printing", "organizer"],
                "score": 8.5
            }
        }


class SearchResponse(BaseModel):
    """搜索响应"""
    success: bool = True
    items: List[SearchItemResponse]
    total: int = Field(..., description="总结果数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    query: str = Field(..., description="搜索关键词")
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "items": [
                    {
                        "item_id": "item_001",
                        "title": "3D Printer Stand",
                        "tags": ["3d-printing"],
                        "score": 8.5
                    }
                ],
                "total": 100,
                "page": 1,
                "size": 20,
                "query": "3d printing"
            }
        }


class SuggestRequest(BaseModel):
    """搜索建议请求"""
    prefix: str = Field(..., min_length=1, description="搜索前缀")
    size: int = Field(10, ge=1, le=20, description="返回数量")


class SuggestResponse(BaseModel):
    """搜索建议响应"""
    suggestions: List[str]
