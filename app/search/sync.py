"""
数据同步脚本
将 MySQL 数据库中的商品数据同步到 Elasticsearch
"""
from sqlalchemy.orm import Session
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from app.db.session import SessionLocal
from app.models.item import ItemInfo
from app.core.es import get_es_client
from app.core.config import settings
from app.search.index import IndexManager
import logging

logger = logging.getLogger(__name__)


class DataSyncer:
    """数据同步器"""
    
    def __init__(self, db: Session = None, es_client: Elasticsearch = None):
        """
        初始化数据同步器
        
        Args:
            db: 数据库会话，如果为 None 则创建新会话
            es_client: ES 客户端，如果为 None 则使用全局客户端
        """
        self.db = db
        self.es = es_client or get_es_client()
        self.index_name = settings.ELASTICSEARCH_INDEX_ITEMS
        self.should_close_db = db is None
    
    def _get_db(self) -> Session:
        """获取数据库会话"""
        if self.db is None:
            self.db = SessionLocal()
        return self.db
    
    def _close_db(self):
        """关闭数据库会话"""
        if self.should_close_db and self.db is not None:
            self.db.close()
            self.db = None
    
    def _item_to_doc(self, item: ItemInfo) -> dict:
        """
        将 Item 模型转换为 ES 文档
        
        Args:
            item: 商品 ORM 对象
            
        Returns:
            ES 文档字典
        """
        # 处理 tags：如果是字符串，分割为列表
        tags = []
        if item.tags_name_list:
            if isinstance(item.tags_name_list, str):
                # 假设 tags 是逗号分隔的字符串
                tags = [tag.strip() for tag in item.tags_name_list.split(",") if tag.strip()]
            elif isinstance(item.tags, list):
                tags = item.tags_name_list
        
        return {
            "_index": self.index_name,
            "_id": str(item._id),  # 使用 item_id 作为 ES 文档 ID
            "_source": {
                "item_id": item._id,
                # "title": item.title or "",
                "group_name": item.group_name or "",
                "description": item.group_desc or "",
                "tags": tags,
                "first_level_category": item.first_level_category_name or "",
                "second_level_category": item.second_level_category_name or "",
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                # "view_count": item.view_count or 0,
                # "download_count": item.download_count or 0,
                # "like_count": item.like_count or 0
            }
        }
    
    def sync_all(self, batch_size: int = 1000, recreate_index: bool = False) -> dict:
        """
        同步所有商品数据到 ES
        
        Args:
            batch_size: 批量写入大小
            recreate_index: 是否重建索引
            
        Returns:
            同步结果统计
        """
        try:
            db = self._get_db()
            
            # 如果需要，重建索引
            if recreate_index:
                logger.info("Recreating index...")
                index_manager = IndexManager(self.es)
                index_manager.create_index(delete_if_exists=True)
            
            # 查询所有商品（建议在生产环境中添加分页）
            logger.info("Fetching items from database...")
            items = db.query(ItemInfo).all()
            total_items = len(items)
            logger.info(f"Found {total_items} items to sync")
            
            if total_items == 0:
                return {
                    "success": True,
                    "total": 0,
                    "synced": 0,
                    "failed": 0
                }
            
            # 转换为 ES 文档
            docs = [self._item_to_doc(item) for item in items]
            
            # 批量写入 ES
            logger.info(f"Syncing to Elasticsearch (batch_size={batch_size})...")
            success_count, failed_items = bulk(
                self.es,
                docs,
                chunk_size=batch_size,
                raise_on_error=False,
                stats_only=False
            )
            
            # 统计结果
            failed_count = len(failed_items) if failed_items else 0
            
            logger.info(f"✅ Sync completed: {success_count} success, {failed_count} failed")
            
            return {
                "success": True,
                "total": total_items,
                "synced": success_count,
                "failed": failed_count,
                "failed_items": failed_items if failed_count > 0 else []
            }
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self._close_db()
    
    def sync_single(self, item_id: str) -> bool:
        """
        同步单个商品
        
        Args:
            item_id: 商品 ID
            
        Returns:
            是否同步成功
        """
        try:
            db = self._get_db()
            item = db.query(ItemInfo).filter(ItemInfo._id == item_id).first()
            
            if not item:
                logger.warning(f"Item {item_id} not found in database")
                return False
            
            doc = self._item_to_doc(item)
            self.es.index(
                index=doc["_index"],
                id=doc["_id"],
                document=doc["_source"]
            )
            
            logger.info(f"✅ Synced item {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync item {item_id}: {e}")
            return False
        finally:
            self._close_db()
    
    def delete_single(self, item_id: str) -> bool:
        """
        从 ES 删除单个商品
        
        Args:
            item_id: 商品 ID
            
        Returns:
            是否删除成功
        """
        try:
            self.es.delete(index=self.index_name, id=str(item_id))
            logger.info(f"Deleted item {item_id} from ES")
            return True
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            return False


def run_sync(batch_size: int = 1000, recreate_index: bool = False):
    """
    执行数据同步（命令行入口）
    
    Args:
        batch_size: 批量写入大小
        recreate_index: 是否重建索引
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    syncer = DataSyncer()
    result = syncer.sync_all(batch_size=batch_size, recreate_index=recreate_index)
    
    if result["success"]:
        print(f"\n🎉 Sync completed successfully!")
        print(f"Total: {result['total']}")
        print(f"Synced: {result['synced']}")
        print(f"Failed: {result['failed']}")
    else:
        print(f"\n❌ Sync failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync MySQL data to Elasticsearch")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for bulk insert")
    parser.add_argument("--recreate-index", action="store_true", help="Recreate index before syncing")
    
    args = parser.parse_args()
    run_sync(batch_size=args.batch_size, recreate_index=args.recreate_index)
