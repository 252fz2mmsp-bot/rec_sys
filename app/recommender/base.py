"""
推荐算法抽象基类
定义统一的推荐接口，所有具体算法必须继承此基类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session


class BaseRecommender(ABC):
    """
    推荐算法抽象基类
    
    所有推荐算法都必须实现 recommend 方法
    可选实现 fit 方法用于模型训练（离线计算）
    """
    
    def __init__(self, db: Session, **kwargs):
        """
        初始化推荐器
        
        Args:
            db: 数据库会话
            **kwargs: 其他配置参数（如 top_k, cache_path 等）
        """
        self.db = db
        self.config = kwargs
        self._is_fitted = False
    
    @abstractmethod
    def recommend(
        self, 
        user_id: str, 
        k: int = 10,
        filter_interacted: bool = True,
        **kwargs
    ) -> List[str]:
        """
        为指定用户生成推荐列表
        
        Args:
            user_id: 目标用户ID
            k: 返回推荐结果的数量
            filter_interacted: 是否过滤用户已交互的商品
            **kwargs: 其他算法特定参数
            
        Returns:
            推荐的商品ID列表，按推荐分数降序排列
        """
        pass
    
    def fit(self, **kwargs) -> None:
        """
        训练/预计算模型（可选实现）
        
        对于需要离线计算的算法（如协同过滤），在此方法中实现：
        - 计算相似度矩阵
        - 训练机器学习模型
        - 生成缓存数据
        
        Args:
            **kwargs: 训练参数
        """
        self._is_fitted = True
    
    def is_fitted(self) -> bool:
        """检查模型是否已训练"""
        return self._is_fitted
    
    def get_algorithm_name(self) -> str:
        """返回算法名称"""
        return self.__class__.__name__
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        返回算法元数据信息
        
        Returns:
            包含算法名称、版本、配置等信息的字典
        """
        return {
            "algorithm": self.get_algorithm_name(),
            "is_fitted": self.is_fitted(),
            "config": self.config
        }
