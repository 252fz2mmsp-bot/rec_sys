"""
数据加载器模块
负责从数据库或缓存中加载推荐所需的数据
实现 IO 密集型操作与计算密集型操作的分离
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """
    推荐系统数据加载器
    
    职责：
    1. 从数据库加载用户-物品交互数据
    2. 构建用户-物品交互矩阵
    3. 提供数据预处理和缓存机制
    """
    
    def __init__(self, db: Session):
        """
        初始化数据加载器
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self._cache: Dict[str, any] = {}
    
    def get_all_item_ids(self, limit: Optional[int] = None) -> List[str]:
        """
        获取所有商品ID列表
        
        Args:
            limit: 限制返回数量，None表示不限制
            
        Returns:
            商品ID列表
        """
        cache_key = f"all_items_{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            query = "SELECT _id FROM item_info"
            if limit:
                query += f" LIMIT {limit}"
            
            result = self.db.execute(text(query))
            item_ids = [row[0] for row in result.fetchall()]
            
            self._cache[cache_key] = item_ids
            logger.info(f"Loaded {len(item_ids)} items from database")
            return item_ids
        except Exception as e:
            logger.error(f"Error loading items: {e}")
            return []
    
    def get_user_interacted_items(self, user_id: str) -> Set[str]:
        """
        获取用户已交互的商品ID集合
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户已交互的商品ID集合
        """
        # TODO: 当 user_behavior 表存在时，从数据库加载
        # 当前返回空集合作为示例
        try:
            query = text("""
                SELECT DISTINCT item_id 
                FROM user_behavior 
                WHERE user_id = :user_id
            """)
            result = self.db.execute(query, {"user_id": user_id})
            return {row[0] for row in result.fetchall()}
        except Exception as e:
            # 如果表不存在或查询失败，返回空集合
            logger.warning(f"Could not load user interactions for {user_id}: {e}")
            return set()
    
    def get_interaction_matrix(
        self, 
        min_interactions: int = 1
    ) -> Tuple[pd.DataFrame, Dict[str, int], Dict[str, int]]:
        """
        构建用户-物品交互矩阵
        
        Args:
            min_interactions: 最小交互次数阈值（用于过滤）
            
        Returns:
            - interaction_df: 交互数据DataFrame (user_id, item_id, score)
            - user_id_map: 用户ID到索引的映射
            - item_id_map: 商品ID到索引的映射
        """
        cache_key = f"interaction_matrix_{min_interactions}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 尝试从 user_behavior 表加载
            query = text("""
                SELECT user_id, item_id, COUNT(*) as interaction_count
                FROM user_behavior
                GROUP BY user_id, item_id
                HAVING interaction_count >= :min_interactions
            """)
            result = self.db.execute(query, {"min_interactions": min_interactions})
            
            data = []
            for row in result.fetchall():
                data.append({
                    "user_id": row[0],
                    "item_id": row[1],
                    "score": float(row[2])  # 使用交互次数作为分数
                })
            
            if not data:
                logger.warning("No interaction data found, returning empty matrix")
                return pd.DataFrame(), {}, {}
            
            df = pd.DataFrame(data)
            
            # 创建ID映射
            unique_users = df["user_id"].unique()
            unique_items = df["item_id"].unique()
            
            user_id_map = {uid: idx for idx, uid in enumerate(unique_users)}
            item_id_map = {iid: idx for idx, iid in enumerate(unique_items)}
            
            result_data = (df, user_id_map, item_id_map)
            self._cache[cache_key] = result_data
            
            logger.info(f"Built interaction matrix: {len(unique_users)} users, "
                       f"{len(unique_items)} items, {len(df)} interactions")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error building interaction matrix: {e}")
            return pd.DataFrame(), {}, {}
    
    def get_item_popularity(self, top_k: Optional[int] = None) -> List[Tuple[str, int]]:
        """
        获取商品热度排行（按交互次数）
        
        Args:
            top_k: 返回Top K热门商品，None表示返回所有
            
        Returns:
            (item_id, interaction_count) 元组列表，按热度降序
        """
        cache_key = f"item_popularity_{top_k}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            query = """
                SELECT item_id, COUNT(*) as popularity
                FROM user_behavior
                GROUP BY item_id
                ORDER BY popularity DESC
            """
            if top_k:
                query += f" LIMIT {top_k}"
            
            result = self.db.execute(text(query))
            popularity_list = [(row[0], row[1]) for row in result.fetchall()]
            
            self._cache[cache_key] = popularity_list
            logger.info(f"Loaded popularity for {len(popularity_list)} items")
            return popularity_list
            
        except Exception as e:
            logger.warning(f"Could not load item popularity: {e}")
            # 降级方案：返回所有商品（热度为0）
            all_items = self.get_all_item_ids(limit=top_k)
            return [(item_id, 0) for item_id in all_items]
    
    def get_cooccurrence_matrix(self) -> pd.DataFrame:
        """
        构建商品共现矩阵（用于ItemCF）
        
        Returns:
            商品共现矩阵 DataFrame (item_i, item_j, cooccurrence_count)
        """
        cache_key = "cooccurrence_matrix"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 查询：统计每对商品在同一用户行为中出现的次数
            query = text("""
                SELECT 
                    b1.item_id as item_i,
                    b2.item_id as item_j,
                    COUNT(DISTINCT b1.user_id) as cooccurrence
                FROM user_behavior b1
                JOIN user_behavior b2 ON b1.user_id = b2.user_id
                WHERE b1.item_id < b2.item_id
                GROUP BY b1.item_id, b2.item_id
                HAVING cooccurrence >= 2
            """)
            
            result = self.db.execute(query)
            
            data = []
            for row in result.fetchall():
                data.append({
                    "item_i": row[0],
                    "item_j": row[1],
                    "cooccurrence": row[2]
                })
            
            df = pd.DataFrame(data)
            self._cache[cache_key] = df
            
            logger.info(f"Built cooccurrence matrix with {len(df)} pairs")
            return df
            
        except Exception as e:
            logger.error(f"Error building cooccurrence matrix: {e}")
            return pd.DataFrame()
    
    def clear_cache(self):
        """清除所有缓存数据"""
        self._cache.clear()
        logger.info("Cache cleared")
