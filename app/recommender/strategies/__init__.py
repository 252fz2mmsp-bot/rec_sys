"""
推荐策略模块
包含所有具体的推荐算法实现
"""
from app.recommender.strategies.random_rec import RandomRecommender
from app.recommender.strategies.most_popular import MostPopularRecommender
from app.recommender.strategies.item_cf import ItemCFRecommender

__all__ = [
    "RandomRecommender",
    "MostPopularRecommender", 
    "ItemCFRecommender"
]
