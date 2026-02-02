"""
推荐系统 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.schemas.common import ResponseModel
from app.schemas.recommend import (
    RecommendResponse,
    RecommendItem,
    AlgorithmInfo
)
from app.recommender.service import RecommenderService
from app.crud import crud_item
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/algorithms", response_model=ResponseModel[List[AlgorithmInfo]])
def list_algorithms():
    """
    获取所有可用的推荐算法列表
    """
    algorithms_info = [
        AlgorithmInfo(
            algorithm="random",
            display_name="随机推荐",
            description="从商品池中随机选择商品进行推荐，适用于A/B测试对照组",
            is_fitted=True,
            requires_training=False
        ),
        AlgorithmInfo(
            algorithm="popular",
            display_name="热门推荐",
            description="基于全局热度推荐最受欢迎的商品，适用于首页推荐和冷启动",
            is_fitted=True,
            requires_training=False
        ),
        AlgorithmInfo(
            algorithm="itemcf",
            display_name="协同过滤",
            description="基于物品相似度的协同过滤算法，提供个性化推荐",
            is_fitted=False,
            requires_training=True
        )
    ]
    
    return ResponseModel(
        code=200,
        message="Success",
        data=algorithms_info
    )


@router.get("/{user_id}", response_model=ResponseModel[RecommendResponse])
def get_recommendations(
    user_id: str,
    algorithm: str = Query("popular", description="推荐算法: random/popular/itemcf"),
    k: int = Query(10, ge=1, le=100, description="推荐数量"),
    filter_interacted: bool = Query(True, description="是否过滤已交互商品"),
    with_details: bool = Query(True, description="是否返回商品详细信息"),
    db: Session = Depends(get_db)
):
    """
    为指定用户生成推荐列表
    
    - **user_id**: 用户ID
    - **algorithm**: 推荐算法 (random, popular, itemcf)
    - **k**: 推荐商品数量 (1-100)
    - **filter_interacted**: 是否过滤用户已交互的商品
    - **with_details**: 是否返回商品详细信息（标题、类目等）
    """
    try:
        # 创建推荐服务
        rec_service = RecommenderService(db)
        
        # 生成推荐
        recommendations_with_scores = rec_service.recommend_with_scores(
            user_id=user_id,
            algorithm=algorithm,
            k=k,
            filter_interacted=filter_interacted
        )
        
        # 构建响应
        recommend_items = []
        for rec in recommendations_with_scores:
            item_data = {
                "item_id": rec["item_id"],
                "score": rec["score"],
                "rank": rec["rank"]
            }
            
            # 如果需要商品详情，从数据库查询
            if with_details:
                try:
                    item = crud_item.get(db, rec["item_id"])
                    if item:
                        item_data["title"] = item.group_name
                        item_data["category"] = item.first_level_category_name
                except Exception as e:
                    logger.warning(f"Failed to fetch item details for {rec['item_id']}: {e}")
            
            recommend_items.append(RecommendItem(**item_data))
        
        response = RecommendResponse(
            user_id=user_id,
            algorithm=algorithm,
            recommendations=recommend_items,
            total_count=len(recommend_items)
        )
        
        return ResponseModel(
            code=200,
            message="Recommendations generated successfully",
            data=response
        )
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post("/train/{algorithm}", response_model=ResponseModel[dict])
def train_algorithm(
    algorithm: str,
    db: Session = Depends(get_db)
):
    """
    训练指定的推荐算法（用于需要离线训练的算法，如ItemCF）
    
    - **algorithm**: 算法名称 (itemcf)
    
    注意：此操作可能耗时较长，建议使用后台任务
    """
    try:
        rec_service = RecommenderService(db)
        
        # 检查算法是否存在
        if algorithm.lower() not in rec_service.list_available_algorithms():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown algorithm: {algorithm}"
            )
        
        # 开始训练
        success = rec_service.train_model(algorithm)
        
        if success:
            return ResponseModel(
                code=200,
                message=f"Algorithm {algorithm} trained successfully",
                data={"algorithm": algorithm, "status": "trained"}
            )
        else:
            return ResponseModel(
                code=200,
                message=f"Algorithm {algorithm} does not require training",
                data={"algorithm": algorithm, "status": "no_training_required"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training algorithm: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to train algorithm: {str(e)}"
        )


@router.get("/similar/{item_id}", response_model=ResponseModel[List[dict]])
def get_similar_items(
    item_id: str,
    k: int = Query(10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取与指定商品最相似的商品列表（基于ItemCF）
    
    - **item_id**: 目标商品ID
    - **k**: 返回数量
    """
    try:
        rec_service = RecommenderService(db)
        recommender = rec_service.get_recommender("itemcf")
        
        if not recommender.is_fitted():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ItemCF model not trained yet. Please train the model first."
            )
        
        # 获取相似商品
        from app.recommender.strategies.item_cf import ItemCFRecommender
        if isinstance(recommender, ItemCFRecommender):
            similar_items = recommender.get_similar_items(item_id, k)
            
            results = [
                {
                    "item_id": similar_id,
                    "similarity_score": round(score, 4)
                }
                for similar_id, score in similar_items
            ]
            
            return ResponseModel(
                code=200,
                message="Success",
                data=results
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint only supports ItemCF algorithm"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting similar items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get similar items: {str(e)}"
        )
