"""
训练 ItemCF 推荐模型脚本
用于离线计算商品相似度矩阵

使用方法:
    python scripts/train_itemcf.py

建议定期执行（如每天/每周），更新推荐模型
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.recommender.service import RecommenderService
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_itemcf_model():
    """训练 ItemCF 推荐模型"""
    logger.info("=" * 60)
    logger.info("Starting ItemCF Model Training")
    logger.info("=" * 60)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建推荐服务
        rec_service = RecommenderService(db)
        
        # 训练 ItemCF 模型
        logger.info("Training ItemCF model...")
        success = rec_service.train_model(
            algorithm="itemcf",
            min_interactions=2,      # 最小交互次数阈值
            save_cache=True          # 保存相似度矩阵到缓存
        )
        
        if success:
            logger.info("✅ ItemCF model training completed successfully!")
            
            # 获取模型信息
            algo_info = rec_service.get_algorithm_info("itemcf")
            logger.info(f"Model Info: {algo_info}")
            
            # 测试推荐
            logger.info("\nTesting recommendations...")
            try:
                test_recommendations = rec_service.recommend(
                    user_id="test_user",
                    algorithm="itemcf",
                    k=5
                )
                logger.info(f"Test recommendations: {test_recommendations}")
            except Exception as e:
                logger.warning(f"Test recommendation failed: {e}")
        else:
            logger.warning("⚠️  Model training returned False (may not require training)")
        
    except Exception as e:
        logger.error(f"❌ Error during training: {e}", exc_info=True)
        raise
    
    finally:
        db.close()
        logger.info("Database connection closed")
    
    logger.info("=" * 60)
    logger.info("Training process completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    train_itemcf_model()
