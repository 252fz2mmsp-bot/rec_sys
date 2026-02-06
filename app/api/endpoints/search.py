"""
搜索 API 端点
提供商品搜索和建议接口
"""
from fastapi import APIRouter, Query, HTTPException
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchItemResponse,
    SuggestRequest,
    SuggestResponse
)
from app.search.service import SearchService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
search_service = SearchService()


@router.get("/search", response_model=SearchResponse)
def search_items(
    q: str = Query(..., description="搜索关键词", min_length=1),
    page: int = Query(1, ge=1, description="页码（从 1 开始）"),
    size: int = Query(20, ge=1, le=100, description="每页大小（最大 100）"),
    category: Optional[str] = Query(None, description="类目筛选"),
    sort_by: str = Query("relevance", description="排序方式：relevance/popular/newest")
):
    """
    搜索商品
    
    支持功能：
    - 多字段搜索（标题、标签、描述）
    - 模糊匹配（容错拼写）
    - 短语匹配
    - 中英文混合搜索
    - 权重控制（title > tags > description）
    - 多种排序方式
    
    示例：
    - `/search?q=3d printing` - 基础搜索
    - `/search?q=printer&sort_by=popular` - 按热度排序
    - `/search?q=stand&category=Tools` - 类目筛选
    """
    try:
        result = search_service.search_items(
            query=q,
            page=page,
            size=size,
            category=category,
            sort_by=sort_by
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))
        
        # 转换为 Pydantic 模型
        items = [SearchItemResponse(**item) for item in result["items"]]
        
        return SearchResponse(
            success=True,
            items=items,
            total=result["total"],
            page=result["page"],
            size=result["size"],
            query=result["query"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest", response_model=SuggestResponse)
def search_suggest(
    prefix: str = Query(..., description="搜索前缀", min_length=1),
    size: int = Query(10, ge=1, le=20, description="返回数量")
):
    """
    搜索建议（自动补全）
    
    根据输入前缀返回建议列表
    
    示例：
    - `/suggest?prefix=3d` - 返回以 "3d" 开头的建议
    """
    try:
        suggestions = search_service.suggest(prefix=prefix, size=size)
        return SuggestResponse(suggestions=suggestions)
        
    except Exception as e:
        logger.error(f"Suggest API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/item/{item_id}")
def get_item_by_id(item_id: str):
    """
    根据 ID 获取商品详情
    
    示例：
    - `/item/item_001`
    """
    try:
        item = search_service.get_by_id(item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return {"success": True, "item": item}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get item API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
