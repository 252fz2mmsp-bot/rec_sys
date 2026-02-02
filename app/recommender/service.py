"""
推荐服务层
提供统一的推荐服务接口，实现工厂模式和策略模式
负责算法选择、实例化和调用
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.recommender.base import BaseRecommender
from app.recommender.strategies import (
    RandomRecommender,
    MostPopularRecommender,
    ItemCFRecommender
)

logger = logging.getLogger(__name__)


class RecommenderService:
    """
    推荐服务类
    
    职责：
    1. 根据算法名称自动实例化对应的推荐器
    2. 提供统一的推荐接口
    3. 管理推荐器实例的生命周期
    4. 处理降级策略和异常情况
    """
    
    # 算法注册表（工厂模式）
    _ALGORITHM_REGISTRY: Dict[str, type] = {
        "random": RandomRecommender,
        "popular": MostPopularRecommender,
        "mostpopular": MostPopularRecommender,
        "itemcf": ItemCFRecommender,
        "item_cf": ItemCFRecommender,
    }
    
    # 默认算法
    _DEFAULT_ALGORITHM = "popular"
    
    def __init__(self, db: Session):
        """
        初始化推荐服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self._recommender_cache: Dict[str, BaseRecommender] = {}
    
    @classmethod
    def register_algorithm(cls, name: str, recommender_class: type):
        """
        注册新的推荐算法
        
        Args:
            name: 算法名称（小写）
            recommender_class: 推荐器类（必须继承BaseRecommender）
        """
        if not issubclass(recommender_class, BaseRecommender):
            raise ValueError(f"{recommender_class} must inherit from BaseRecommender")
        
        cls._ALGORITHM_REGISTRY[name.lower()] = recommender_class
        logger.info(f"Registered algorithm: {name} -> {recommender_class.__name__}")
    
    @classmethod
    def list_available_algorithms(cls) -> List[str]:
        """
        列出所有可用的推荐算法
        
        Returns:
            算法名称列表
        """
        return list(set(cls._ALGORITHM_REGISTRY.keys()))
    
    def get_recommender(
        self, 
        algorithm: str = "popular",
        use_cache: bool = True,
        **kwargs
    ) -> BaseRecommender:
        """
        获取推荐器实例
        
        Args:
            algorithm: 算法名称
            use_cache: 是否使用缓存的实例
            **kwargs: 传递给推荐器的配置参数
            
        Returns:
            推荐器实例
            
        Raises:
            ValueError: 如果算法名称不存在
        """
        algorithm_key = algorithm.lower()
        
        # 检查算法是否存在
        if algorithm_key not in self._ALGORITHM_REGISTRY:
            logger.warning(f"Unknown algorithm: {algorithm}, falling back to {self._DEFAULT_ALGORITHM}")
            algorithm_key = self._DEFAULT_ALGORITHM
        
        # 使用缓存
        cache_key = f"{algorithm_key}_{hash(frozenset(kwargs.items()))}"
        if use_cache and cache_key in self._recommender_cache:
            return self._recommender_cache[cache_key]
        
        # 实例化推荐器
        recommender_class = self._ALGORITHM_REGISTRY[algorithm_key]
        recommender = recommender_class(self.db, **kwargs)
        
        # 缓存实例
        if use_cache:
            self._recommender_cache[cache_key] = recommender
        
        logger.info(f"Created recommender: {recommender.get_algorithm_name()}")
        return recommender
    
    def recommend(
        self,
        user_id: str,
        algorithm: str = "popular",
        k: int = 10,
        filter_interacted: bool = True,
        **kwargs
    ) -> List[str]:
        """
        为用户生成推荐列表（统一接口）
        
        Args:
            user_id: 目标用户ID
            algorithm: 推荐算法名称
            k: 推荐数量
            filter_interacted: 是否过滤用户已交互的商品
            **kwargs: 其他参数
            
        Returns:
            推荐的商品ID列表
        """
        try:
            recommender = self.get_recommender(algorithm, **kwargs)
            recommendations = recommender.recommend(
                user_id=user_id,
                k=k,
                filter_interacted=filter_interacted,
                **kwargs
            )
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {user_id} "
                       f"using {recommender.get_algorithm_name()}")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            # 降级策略：使用随机推荐
            logger.warning("Falling back to random recommendations")
            try:
                fallback = self.get_recommender("random")
                return fallback.recommend(user_id, k, filter_interacted)
            except:
                return []
    
    def recommend_with_scores(
        self,
        user_id: str,
        algorithm: str = "popular",
        k: int = 10,
        filter_interacted: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        生成带分数的推荐列表
        
        Args:
            user_id: 目标用户ID
            algorithm: 推荐算法名称
            k: 推荐数量
            filter_interacted: 是否过滤用户已交互的商品
            **kwargs: 其他参数
            
        Returns:
            推荐结果列表，每个元素包含 item_id 和 score（真实的算法分数）
        """
        try:
            recommender = self.get_recommender(algorithm, **kwargs)
            
            # 调用算法的 recommend_with_scores 方法获取真实分数
            recommendations_with_scores = recommender.recommend_with_scores(
                user_id=user_id,
                k=k,
                filter_interacted=filter_interacted,
                **kwargs
            )
            
            # 构建返回结果
            results = []
            for idx, (item_id, score) in enumerate(recommendations_with_scores):
                results.append({
                    "item_id": item_id,
                    "score": round(float(score), 4),
                    "rank": idx + 1
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating recommendations with scores: {e}")
            # 降级策略：使用默认分数
            recommendations = self.recommend(
                user_id=user_id,
                algorithm=algorithm,
                k=k,
                filter_interacted=filter_interacted,
                **kwargs
            )
            
            results = []
            for idx, item_id in enumerate(recommendations):
                score = 1.0 - (idx / max(len(recommendations), 1))
                results.append({
                    "item_id": item_id,
                    "score": round(score, 4),
                    "rank": idx + 1
                })
            
            return results
    
    def batch_recommend(
        self,
        user_ids: List[str],
        algorithm: str = "popular",
        k: int = 10,
        **kwargs
    ) -> Dict[str, List[str]]:
        """
        批量生成推荐
        
        Args:
            user_ids: 用户ID列表
            algorithm: 推荐算法
            k: 每个用户的推荐数量
            **kwargs: 其他参数
            
        Returns:
            用户ID到推荐列表的映射
        """
        results = {}
        recommender = self.get_recommender(algorithm, **kwargs)
        
        for user_id in user_ids:
            try:
                recommendations = recommender.recommend(user_id, k, **kwargs)
                results[user_id] = recommendations
            except Exception as e:
                logger.error(f"Error recommending for user {user_id}: {e}")
                results[user_id] = []
        
        return results
    
    def train_model(self, algorithm: str, **kwargs) -> bool:
        """
        训练推荐模型（用于需要离线训练的算法）
        
        Args:
            algorithm: 算法名称
            **kwargs: 训练参数
            
        Returns:
            训练是否成功
        """
        try:
            recommender = self.get_recommender(algorithm, use_cache=False)
            
            if hasattr(recommender, 'fit'):
                logger.info(f"Training {recommender.get_algorithm_name()} model...")
                recommender.fit(**kwargs)
                logger.info(f"Model training completed: {recommender.get_algorithm_name()}")
                return True
            else:
                logger.warning(f"{recommender.get_algorithm_name()} does not require training")
                return False
                
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False
    
    def get_algorithm_info(self, algorithm: str) -> Dict[str, Any]:
        """
        获取算法信息
        
        Args:
            algorithm: 算法名称
            
        Returns:
            算法元数据信息
        """
        try:
            recommender = self.get_recommender(algorithm)
            return recommender.get_metadata()
        except Exception as e:
            logger.error(f"Error getting algorithm info: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """清除推荐器缓存"""
        self._recommender_cache.clear()
        logger.info("Recommender cache cleared")
