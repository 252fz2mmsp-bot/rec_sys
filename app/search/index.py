"""
Elasticsearch 索引管理器
负责创建、更新、删除索引
"""
from elasticsearch import Elasticsearch
from app.core.es import get_es_client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class IndexManager:
    """ES 索引管理器"""
    
    def __init__(self, es_client: Elasticsearch = None):
        """
        初始化索引管理器
        
        Args:
            es_client: Elasticsearch 客户端，如果为 None 则使用全局客户端
        """
        self.es = es_client or get_es_client()
        self.index_name = settings.ELASTICSEARCH_INDEX_ITEMS
    
    def create_index(self, delete_if_exists: bool = False) -> bool:
        """
        创建商品索引
        
        采用 "MakerWorld" 风格的多语言支持：
        - 使用 standard analyzer 作为默认分析器（支持中英文混合）
        - 使用 english analyzer 处理英文词干提取
        - multi-fields 策略：同一字段多种分析方式
        
        Args:
            delete_if_exists: 如果索引已存在，是否删除后重建
            
        Returns:
            是否创建成功
        """
        try:
            # 检查索引是否存在
            if self.es.indices.exists(index=self.index_name):
                if delete_if_exists:
                    logger.warning(f"Index {self.index_name} exists, deleting...")
                    self.es.indices.delete(index=self.index_name)
                else:
                    logger.info(f"Index {self.index_name} already exists")
                    return True
            
            # 定义索引 Mapping
            index_body = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            # 自定义分析器（可选，如果需要同义词）
                            "custom_synonym_analyzer": {
                                "type": "custom",  # 自定义分析器
                                "tokenizer": "standard",  # 切词
                                "filter": ["lowercase", "stop"]  # 基础过滤器
                                # 未来可以添加同义词过滤器：
                                # "filter": ["lowercase", "stop", "synonym_filter"]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        # 商品 ID
                        "item_id": {
                            "type": "keyword"
                        },
                        
                        # 商品标题（核心字段）
                        "title": {
                            "type": "text",
                            "analyzer": "standard",  # 默认：标准分析器（支持中英文）
                            "fields": {
                                # 子字段：英文词干提取
                                "english": {
                                    "type": "text",
                                    "analyzer": "english"  # 处理 printing -> print
                                },
                                # 子字段：精确匹配（用于排序和聚合）
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        
                        # 商品组名称（通常与标题相同或相似）
                        "group_name": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "english": {
                                    "type": "text",
                                    "analyzer": "english"
                                }
                            }
                        },
                        
                        # 商品描述
                        "description": {
                            "type": "text",
                            "analyzer": "standard",
                            "fields": {
                                "english": {
                                    "type": "text",
                                    "analyzer": "english"
                                }
                            }
                        },
                        
                        # 标签（重要：同时支持精确匹配和全文搜索）
                        "tags": {
                            "type": "keyword",  # 精确匹配
                            "fields": {
                                "text": {
                                    "type": "text",
                                    "analyzer": "standard"
                                }
                            }
                        },
                        
                        # 类目信息
                        "first_level_category": {
                            "type": "keyword"
                        },
                        "second_level_category": {
                            "type": "keyword"
                        },
                        
                        # 时间字段
                        "created_at": {
                            "type": "date"
                        },
                        "updated_at": {
                            "type": "date"
                        },
                        
                        # 统计字段（用于排序和打分）
                        "view_count": {
                            "type": "integer"
                        },
                        "download_count": {
                            "type": "integer"
                        },
                        "like_count": {
                            "type": "integer"
                        }
                    }
                }
            }
            
            # 创建索引
            response = self.es.indices.create(
                index=self.index_name,
                body=index_body
            )
            
            logger.info(f"✅ Successfully created index: {self.index_name}")
            return response.get("acknowledged", False)
            
        except Exception as e:
            logger.error(f"❌ Failed to create index: {e}")
            return False
    
    def delete_index(self) -> bool:
        """
        删除索引
        
        Returns:
            是否删除成功
        """
        try:
            if self.es.indices.exists(index=self.index_name):
                response = self.es.indices.delete(index=self.index_name)
                logger.info(f"Deleted index: {self.index_name}")
                return response.get("acknowledged", False)
            else:
                logger.warning(f"Index {self.index_name} does not exist")
                return False
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            return False
    
    def index_exists(self) -> bool:
        """
        检查索引是否存在
        
        Returns:
            索引是否存在
        """
        return self.es.indices.exists(index=self.index_name)
    
    def get_index_stats(self) -> dict:
        """
        获取索引统计信息
        
        Returns:
            索引统计数据
        """
        try:
            if not self.index_exists():
                return {"error": "Index does not exist"}
            
            stats = self.es.indices.stats(index=self.index_name)
            count = self.es.count(index=self.index_name)
            
            return {
                "index_name": self.index_name,
                "doc_count": count.get("count", 0),
                "size_in_bytes": stats["indices"][self.index_name]["total"]["store"]["size_in_bytes"],
                "exists": True
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}
