"""
热门推荐算法
基于全局热度（交互次数）推荐最受欢迎的商品
适用场景：首页推荐、冷启动用户、新用户引导
"""
from typing import List
from sqlalchemy.orm import Session

from app.recommender.base import BaseRecommender
from app.recommender.data_loader import DataLoader


class MostPopularRecommender(BaseRecommender):
    """
    热门推荐算法（Most Popular）
    
    根据商品的全局热度（交互次数）进行推荐
    优先推荐交互次数最多的商品
    """
    
    def __init__(self, db: Session, **kwargs):
        """
        初始化热门推荐器
        
        Args:
            db: 数据库会话
            **kwargs: 配置参数
                - time_decay: 是否使用时间衰减（未来扩展）
                - popularity_threshold: 最低热度阈值
        """
        super().__init__(db, **kwargs)
        self.data_loader = DataLoader(db)
        self.popularity_threshold = kwargs.get("popularity_threshold", 0)
    
    def recommend(
        self, 
        user_id: str, 
        k: int = 10,
        filter_interacted: bool = True,
        **kwargs
    ) -> List[str]:
        """
        生成热门推荐列表
        
        Args:
            user_id: 目标用户ID
            k: 推荐商品数量
            filter_interacted: 是否过滤用户已交互的商品
            **kwargs: 其他参数
                - category: 指定类目（未来扩展）
            
        Returns:
            按热度排序的商品ID列表
        """
        # 获取商品热度排行（多取一些以应对过滤需求）
        fetch_size = k * 3 if filter_interacted else k
        popularity_list = self.data_loader.get_item_popularity(top_k=fetch_size)
        
        if not popularity_list:
            return []
        
        # 过滤低于阈值的商品
        popularity_list = [
            (item_id, count) for item_id, count in popularity_list
            if count >= self.popularity_threshold
        ]
        
        # 如果需要过滤用户已交互的商品
        if filter_interacted:
            interacted_items = self.data_loader.get_user_interacted_items(user_id)
            popularity_list = [
                (item_id, count) for item_id, count in popularity_list
                if item_id not in interacted_items
            ]
        
        # 提取商品ID（已按热度排序）
        recommendations = [item_id for item_id, _ in popularity_list[:k]]
        
        return recommendations
    
    def get_algorithm_name(self) -> str:
        """返回算法名称"""
        return "MostPopular"
    
    def get_popularity_scores(self, item_ids: List[str]) -> dict:
        """
        获取指定商品的热度分数
        
        Args:
            item_ids: 商品ID列表
            
        Returns:
            商品ID到热度分数的映射
        """
        all_popularity = self.data_loader.get_item_popularity()
        popularity_dict = {item_id: count for item_id, count in all_popularity}
        
        return {
            item_id: popularity_dict.get(item_id, 0)
            for item_id in item_ids
        }
