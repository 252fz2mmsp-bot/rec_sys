"""
协同过滤推荐算法（Item-based Collaborative Filtering）
基于物品相似度进行推荐
适用场景：个性化推荐、"看了又看"、"买了又买"
"""
import os
import pickle
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
import logging

from app.recommender.base import BaseRecommender
from app.recommender.data_loader import DataLoader

logger = logging.getLogger(__name__)


class ItemCFRecommender(BaseRecommender):
    """
    基于物品的协同过滤推荐算法（Item-based CF）
    
    核心思想：
    1. 离线计算商品之间的相似度矩阵
    2. 在线推荐时，根据用户历史交互的商品，找到相似商品进行推荐
    
    相似度计算方法：
    - 余弦相似度（基于用户-物品交互矩阵）
    - 可选：Jaccard相似度、Pearson相关系数
    """
    
    def __init__(self, db: Session, **kwargs):
        """
        初始化ItemCF推荐器
        
        Args:
            db: 数据库会话
            **kwargs: 配置参数
                - cache_path: 相似度矩阵缓存路径
                - similarity_method: 相似度计算方法 ['cosine', 'jaccard']
                - min_similarity: 最小相似度阈值
                - top_n_similar: 每个商品保留的最相似商品数量
        """
        super().__init__(db, **kwargs)
        self.data_loader = DataLoader(db)
        
        # 配置参数
        self.cache_path = kwargs.get("cache_path", "app/recommender/cache/itemcf_similarity.pkl")
        self.similarity_method = kwargs.get("similarity_method", "cosine")
        self.min_similarity = kwargs.get("min_similarity", 0.1)
        self.top_n_similar = kwargs.get("top_n_similar", 50)
        
        # 相似度矩阵（延迟加载）
        self.similarity_matrix: Optional[Dict[str, List[Tuple[str, float]]]] = None
        self.item_id_to_idx: Optional[Dict[str, int]] = None
        self.idx_to_item_id: Optional[Dict[int, str]] = None
        
        # 尝试加载缓存
        self._load_similarity_cache()
    
    def fit(self, **kwargs) -> None:
        """
        训练模型：计算商品相似度矩阵
        
        这是一个离线计算过程，应该定期执行（如每天/每周）
        
        Args:
            **kwargs: 训练参数
                - min_interactions: 最小交互次数阈值
                - save_cache: 是否保存缓存
        """
        logger.info("Starting ItemCF model training...")
        
        min_interactions = kwargs.get("min_interactions", 1)
        save_cache = kwargs.get("save_cache", True)
        
        # 1. 加载交互矩阵
        interaction_df, user_id_map, item_id_map = self.data_loader.get_interaction_matrix(
            min_interactions=min_interactions
        )
        
        if interaction_df.empty:
            logger.warning("No interaction data available for training")
            self._is_fitted = False
            return
        
        # 2. 构建用户-物品评分矩阵
        n_users = len(user_id_map)
        n_items = len(item_id_map)
        
        # 创建稀疏矩阵（使用字典存储）
        rating_matrix = np.zeros((n_users, n_items))
        
        for _, row in interaction_df.iterrows():
            user_idx = user_id_map[row["user_id"]]
            item_idx = item_id_map[row["item_id"]]
            rating_matrix[user_idx, item_idx] = row["score"]
        
        logger.info(f"Built rating matrix: {n_users} users × {n_items} items")
        
        # 3. 计算商品相似度矩阵
        if self.similarity_method == "cosine":
            # 余弦相似度（基于用户维度）
            item_similarity = cosine_similarity(rating_matrix.T)
        else:
            # 默认使用余弦相似度
            item_similarity = cosine_similarity(rating_matrix.T)
        
        logger.info(f"Computed similarity matrix: {item_similarity.shape}")
        
        # 4. 为每个商品保留Top N最相似的商品
        self.item_id_to_idx = item_id_map
        self.idx_to_item_id = {idx: item_id for item_id, idx in item_id_map.items()}
        self.similarity_matrix = {}
        
        for item_id, item_idx in item_id_map.items():
            # 获取该商品与所有商品的相似度
            similarities = item_similarity[item_idx]
            
            # 过滤并排序
            similar_items = []
            for other_idx, sim_score in enumerate(similarities):
                if other_idx != item_idx and sim_score >= self.min_similarity:
                    other_item_id = self.idx_to_item_id[other_idx]
                    similar_items.append((other_item_id, float(sim_score)))
            
            # 按相似度降序排序，保留Top N
            similar_items.sort(key=lambda x: x[1], reverse=True)
            self.similarity_matrix[item_id] = similar_items[:self.top_n_similar]
        
        logger.info(f"Built similarity index for {len(self.similarity_matrix)} items")
        
        # 5. 保存缓存
        if save_cache:
            self._save_similarity_cache()
        
        self._is_fitted = True
        logger.info("ItemCF model training completed")
    
    def recommend(
        self, 
        user_id: str, 
        k: int = 10,
        filter_interacted: bool = True,
        **kwargs
    ) -> List[str]:
        """
        生成协同过滤推荐列表
        
        Args:
            user_id: 目标用户ID
            k: 推荐商品数量
            filter_interacted: 是否过滤用户已交互的商品
            **kwargs: 其他参数
                - diversity_factor: 多样性因子（未来扩展）
            
        Returns:
            推荐的商品ID列表，按预测分数降序
        """
        if not self.is_fitted() or self.similarity_matrix is None:
            logger.warning("Model not fitted, falling back to random recommendations")
            # 降级方案：返回随机推荐
            from app.recommender.strategies.random_rec import RandomRecommender
            fallback = RandomRecommender(self.db)
            return fallback.recommend(user_id, k, filter_interacted)
        
        # 1. 获取用户历史交互商品
        interacted_items = self.data_loader.get_user_interacted_items(user_id)
        
        if not interacted_items:
            logger.info(f"User {user_id} has no interaction history")
            # 降级方案：返回热门推荐
            from app.recommender.strategies.most_popular import MostPopularRecommender
            fallback = MostPopularRecommender(self.db)
            return fallback.recommend(user_id, k, filter_interacted=False)
        
        # 2. 基于用户历史商品，找到相似商品并聚合分数
        candidate_scores = defaultdict(float)
        
        for item_id in interacted_items:
            if item_id not in self.similarity_matrix:
                continue
            
            # 获取该商品的相似商品列表
            similar_items = self.similarity_matrix[item_id]
            
            for similar_item_id, similarity_score in similar_items:
                # 聚合分数（可以使用加权求和）
                candidate_scores[similar_item_id] += similarity_score
        
        # 3. 过滤已交互商品
        if filter_interacted:
            candidate_scores = {
                item_id: score for item_id, score in candidate_scores.items()
                if item_id not in interacted_items
            }
        
        # 4. 排序并返回Top K
        sorted_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        recommendations = [item_id for item_id, _ in sorted_candidates[:k]]
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        return recommendations
    
    def get_similar_items(self, item_id: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        获取与指定商品最相似的商品列表
        
        Args:
            item_id: 目标商品ID
            k: 返回数量
            
        Returns:
            (item_id, similarity_score) 元组列表
        """
        if not self.is_fitted() or self.similarity_matrix is None:
            logger.warning("Model not fitted")
            return []
        
        if item_id not in self.similarity_matrix:
            logger.warning(f"Item {item_id} not in similarity matrix")
            return []
        
        similar_items = self.similarity_matrix[item_id][:k]
        return similar_items
    
    def _save_similarity_cache(self):
        """保存相似度矩阵到缓存文件"""
        try:
            cache_dir = os.path.dirname(self.cache_path)
            os.makedirs(cache_dir, exist_ok=True)
            
            cache_data = {
                "similarity_matrix": self.similarity_matrix,
                "item_id_to_idx": self.item_id_to_idx,
                "idx_to_item_id": self.idx_to_item_id,
                "config": self.config
            }
            
            with open(self.cache_path, "wb") as f:
                pickle.dump(cache_data, f)
            
            logger.info(f"Similarity cache saved to {self.cache_path}")
        except Exception as e:
            logger.error(f"Failed to save similarity cache: {e}")
    
    def _load_similarity_cache(self):
        """从缓存文件加载相似度矩阵"""
        if not os.path.exists(self.cache_path):
            logger.info(f"No cache file found at {self.cache_path}")
            return
        
        try:
            with open(self.cache_path, "rb") as f:
                cache_data = pickle.load(f)
            
            self.similarity_matrix = cache_data.get("similarity_matrix")
            self.item_id_to_idx = cache_data.get("item_id_to_idx")
            self.idx_to_item_id = cache_data.get("idx_to_item_id")
            
            if self.similarity_matrix:
                self._is_fitted = True
                logger.info(f"Similarity cache loaded from {self.cache_path}")
                logger.info(f"Loaded {len(self.similarity_matrix)} items")
        except Exception as e:
            logger.error(f"Failed to load similarity cache: {e}")
            self.similarity_matrix = None
    
    def get_algorithm_name(self) -> str:
        """返回算法名称"""
        return "ItemCF"
