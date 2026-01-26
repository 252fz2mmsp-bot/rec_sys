# app/api/endpoints/items.py
"""
商品相关的 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.crud import crud_item
from app.schemas.item import ItemInfoCreate, ItemInfoUpdate, ItemInfoResponse
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=ResponseModel[ItemInfoResponse], status_code=status.HTTP_201_CREATED)
def create_item(
    item_in: ItemInfoCreate,
    db: Session = Depends(get_db)
):
    """创建商品"""
    # 检查商品是否已存在
    item_id = item_in._id if hasattr(item_in, '_id') else getattr(item_in, 'id', None)
    existing_item = crud_item.get(db, item_id)
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item with id {item_id} already exists"
        )
    
    item = crud_item.create(db, item_in)
    return ResponseModel(
        code=201,
        message="Item created successfully",
        data=item
    )


@router.get("/", response_model=ResponseModel[PaginatedResponse[ItemInfoResponse]])
def get_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取商品列表（分页）"""
    items = crud_item.get_multi(db, skip=skip, limit=limit)
    total = crud_item.get_count(db)
    
    return ResponseModel(
        data=PaginatedResponse(
            total=total,
            items=items,
            skip=skip,
            limit=limit
        )
    )


@router.get("/{item_id}", response_model=ResponseModel[ItemInfoResponse])
def get_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """获取单个商品信息"""
    item = crud_item.get(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    return ResponseModel(data=item)


@router.put("/{item_id}", response_model=ResponseModel[ItemInfoResponse])
def update_item(
    item_id: str,
    item_in: ItemInfoUpdate,
    db: Session = Depends(get_db)
):
    """更新商品信息"""
    item = crud_item.update(db, item_id, item_in)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    return ResponseModel(
        message="Item updated successfully",
        data=item
    )


@router.delete("/{item_id}", response_model=ResponseModel[dict])
def delete_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    """删除商品"""
    success = crud_item.delete(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id {item_id} not found"
        )
    
    return ResponseModel(
        message="Item deleted successfully",
        data={"item_id": item_id}
    )
