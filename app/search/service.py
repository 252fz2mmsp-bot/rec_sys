"""
搜索服务
提供基于 Elasticsearch 的商品搜索功能
"""
from elasticsearch import Elasticsearch
from app.core.es import get_es_client
from app.core.config import settings
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SearchService:
    """ES 搜索服务"""
    
    def __init__(self, es_client: Elasticsearch = None):
        """
        初始化搜索服务
        
        Args:
            es_client: ES 客户端，如果为 None 则使用全局客户端
        """
        self.es = es_client or get_es_client()
        self.index_name = settings.ELASTICSEARCH_INDEX_ITEMS
    
    def search_items(
        self,
        query: str,
        page: int = 1,
        size: int = 20,
        category: Optional[str] = None,
        sort_by: str = "relevance"
    ) -> Dict[str, Any]:
        """
        搜索商品
        
        参考 MakerWorld 风格：
        - 使用 multi_match 在多个字段中搜索
        - 支持模糊匹配（fuzziness）
        - 支持短语匹配（phrase match）
        - 字段权重：title^3 > tags^2 > description^1
        
        Args:
            query: 搜索关键词
            page: 页码（从 1 开始）
            size: 每页大小
            category: 类目筛选（可选）
            sort_by: 排序方式（relevance/popular/newest）
            
        Returns:
            搜索结果字典，包含 hits、total、page、size
        """
        try:
            # 计算分页
            from_index = (page - 1) * size
            
            # 构建查询
            must_clauses = []
            
            # 1. 主查询：multi_match + 模糊匹配
            if query and query.strip():
                must_clauses.append({
                    "bool": {
                        "should": [
                            # 多字段匹配（权重控制）
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "title^3",           # 标题权重最高
                                        "title.english^2.5", # 英文词干（略低于标题）
                                        "tags^2",            # 标签权重中等
                                        "tags.text^1.8",     # 标签文本分析
                                        "description^1",     # 描述权重最低
                                        "description.english^0.9"
                                    ],
                                    "type": "best_fields",  # 取最佳字段分数
                                    "fuzziness": "AUTO",    # 模糊匹配（容错）
                                    "prefix_length": 2,     # 前缀长度（避免过度模糊）
                                    "operator": "or"
                                }
                            },
                            # 短语匹配（精确度加分）
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": [
                                        "title^5",
                                        "title.english^4"
                                    ],
                                    "type": "phrase",
                                    "boost": 2  # 短语匹配额外加分
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                })
            
            # 2. 类目筛选
            if category:
                must_clauses.append({
                    "term": {
                        "first_level_category": category
                    }
                })
            
            # 构建完整查询体
            query_body = {
                "query": {
                    "bool": {
                        "must": must_clauses if must_clauses else [{"match_all": {}}]
                    }
                },
                "from": from_index,
                "size": size
            }
            
            # 3. 排序
            if sort_by == "popular":
                query_body["sort"] = [
                    {"download_count": {"order": "desc"}},
                    {"like_count": {"order": "desc"}},
                    "_score"
                ]
            elif sort_by == "newest":
                query_body["sort"] = [
                    {"created_at": {"order": "desc"}},
                    "_score"
                ]
            # 默认按相关性排序（_score）
            
            # 执行搜索
            response = self.es.search(
                index=self.index_name,
                body=query_body
            )
            
            # 解析结果
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            
            items = []
            for hit in hits:
                source = hit["_source"]
                source["_score"] = hit["_score"]  # 添加相关性分数
                items.append(source)
            
            return {
                "success": True,
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "success": False,
                "items": [],
                "total": 0,
                "page": page,
                "size": size,
                "query": query,
                "error": str(e)
            }
    
    def suggest(self, prefix: str, size: int = 10) -> List[str]:
        """
        搜索建议（自动补全）
        
        Args:
            prefix: 前缀
            size: 返回数量
            
        Returns:
            建议列表
        """
        try:
            query_body = {
                "suggest": {
                    "title_suggest": {
                        "prefix": prefix,
                        "completion": {
                            "field": "title.keyword",
                            "size": size,
                            "skip_duplicates": True
                        }
                    }
                }
            }
            
            response = self.es.search(
                index=self.index_name,
                body=query_body
            )
            
            suggestions = []
            for option in response["suggest"]["title_suggest"][0]["options"]:
                suggestions.append(option["text"])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggest failed: {e}")
            return []
    
    def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取商品
        
        Args:
            item_id: 商品 ID
            
        Returns:
            商品信息
        """
        try:
            response = self.es.get(index=self.index_name, id=str(item_id))
            return response["_source"]
        except Exception as e:
            logger.error(f"Get by ID failed: {e}")
            return None
