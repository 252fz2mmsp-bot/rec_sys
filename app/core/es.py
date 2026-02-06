"""
Elasticsearch 客户端配置
提供全局单例 ES 客户端
"""
from elasticsearch import Elasticsearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 全局 Elasticsearch 客户端实例
_es_client: Elasticsearch = None


def get_es_client() -> Elasticsearch:
    """
    获取 Elasticsearch 客户端单例
    
    Returns:
        Elasticsearch 客户端实例
    """
    global _es_client
    
    if _es_client is None:
        try:
            _es_client = Elasticsearch(
                [settings.ELASTICSEARCH_URL],
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # 测试连接
            if _es_client.ping():
                logger.info(f"✅ Successfully connected to Elasticsearch at {settings.ELASTICSEARCH_URL}")
            else:
                logger.warning("⚠️ Elasticsearch client created but ping failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to create Elasticsearch client: {e}")
            raise
    
    return _es_client


def close_es_client():
    """关闭 Elasticsearch 客户端连接"""
    global _es_client
    if _es_client is not None:
        _es_client.close()
        _es_client = None
        logger.info("Elasticsearch client closed")
