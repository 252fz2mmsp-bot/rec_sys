# app/api/endpoints/users.py
"""
用户相关的 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.crud import crud_user
from app.schemas.user import UserInfoCreate, UserInfoUpdate, UserInfoResponse
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=ResponseModel[UserInfoResponse], status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserInfoCreate,
    db: Session = Depends(get_db)
):
    """创建用户"""
    # 检查用户是否已存在
    existing_user = crud_user.get(db, user_in.uid)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with uid {user_in.uid} already exists"
        )
    
    user = crud_user.create(db, user_in)
    return ResponseModel(
        code=201,
        message="User created successfully",
        data=user
    )


@router.get("/", response_model=ResponseModel[PaginatedResponse[UserInfoResponse]])
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取用户列表（分页）"""
    users = crud_user.get_multi(db, skip=skip, limit=limit)
    total = crud_user.get_count(db)
    
    return ResponseModel(
        data=PaginatedResponse(
            total=total,
            items=users,
            skip=skip,
            limit=limit
        )
    )


@router.get("/{uid}", response_model=ResponseModel[UserInfoResponse])
def get_user(
    uid: str,
    db: Session = Depends(get_db)
):
    """获取单个用户信息"""
    user = crud_user.get(db, uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with uid {uid} not found"
        )
    
    return ResponseModel(data=user)


@router.put("/{uid}", response_model=ResponseModel[UserInfoResponse])
def update_user(
    uid: str,
    user_in: UserInfoUpdate,
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = crud_user.update(db, uid, user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with uid {uid} not found"
        )
    
    return ResponseModel(
        message="User updated successfully",
        data=user
    )


@router.delete("/{uid}", response_model=ResponseModel[dict])
def delete_user(
    uid: str,
    db: Session = Depends(get_db)
):
    """删除用户"""
    success = crud_user.delete(db, uid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with uid {uid} not found"
        )
    
    return ResponseModel(
        message="User deleted successfully",
        data={"uid": uid}
    )
