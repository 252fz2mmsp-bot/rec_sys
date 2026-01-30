"""
随机推荐算法
简单地从候选商品池中随机选择商品进行推荐
适用场景：冷启动、A/B测试对照组、探索性推荐
"""
import random
from typing import List
from sqlalchemy.orm import Session

from app.recommender.base import BaseRecommender
from app.recommender.data_loader import DataLoader


class RandomRecommender(BaseRecommender):
    """
    随机推荐算法
    
    从所有商品中随机选择 k 个商品推荐给用户
    可选择是否过滤用户已交互的商品
    """
    
    def __init__(self, db: Session, **kwargs):
        """
        初始化随机推荐器
        
        Args:
            db: 数据库会话
            **kwargs: 配置参数
                - seed: 随机种子（可选）
        """
        super().__init__(db, **kwargs)
        self.data_loader = DataLoader(db)
        
        # 设置随机种子（如果提供）
        if "seed" in kwargs:
            random.seed(kwargs["seed"])
    
    def recommend(
        self, 
        user_id: str, 
        k: int = 10,
        filter_interacted: bool = True,
        **kwargs
    ) -> List[str]:
        """
        生成随机推荐列表
        
        Args:
            user_id: 目标用户ID
            k: 推荐商品数量
            filter_interacted: 是否过滤用户已交互的商品
            **kwargs: 其他参数（本算法暂不使用）
            
        Returns:
            随机选择的商品ID列表
        """
        # 获取所有候选商品
        all_items = self.data_loader.get_all_item_ids()
        
        if not all_items:
            return []
        
        # 如果需要过滤已交互商品
        if filter_interacted:
            interacted_items = self.data_loader.get_user_interacted_items(user_id)
            candidate_items = [item for item in all_items if item not in interacted_items]
        else:
            candidate_items = all_items
        
        # 随机采样
        sample_size = min(k, len(candidate_items))
        recommendations = random.sample(candidate_items, sample_size)
        
        return recommendations
    
    def get_algorithm_name(self) -> str:
        """返回算法名称"""
        return "Random"
