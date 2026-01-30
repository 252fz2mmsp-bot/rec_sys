# 推荐系统模块 (Recommender System)

## 📁 目录结构

```
app/recommender/
├── __init__.py              # 模块初始化
├── base.py                  # 抽象基类（BaseRecommender）
├── data_loader.py           # 数据加载器
├── service.py               # 推荐服务层（工厂模式）
├── cache/                   # 缓存目录（存放相似度矩阵等）
│   └── itemcf_similarity.pkl
└── strategies/              # 具体算法实现
    ├── __init__.py
    ├── random_rec.py        # 随机推荐
    ├── most_popular.py      # 热门推荐
    └── item_cf.py           # 协同过滤
```

## 🏗️ 架构设计

### 1. 分层架构

```
┌─────────────────────────────────────┐
│   API Layer (endpoints/recommend.py) │  ← FastAPI 路由
├─────────────────────────────────────┤
│   Service Layer (service.py)         │  ← 工厂模式 + 策略模式
├─────────────────────────────────────┤
│   Algorithm Layer (strategies/*)     │  ← 具体推荐算法
├─────────────────────────────────────┤
│   Data Layer (data_loader.py)        │  ← 数据加载与预处理
├─────────────────────────────────────┤
│   Storage Layer (Database/Cache)     │  ← MySQL + Pickle Cache
└─────────────────────────────────────┘
```

### 2. 核心设计模式

#### 工厂模式（Factory Pattern）
`RecommenderService` 根据算法名称自动实例化对应的推荐器：

```python
rec_service = RecommenderService(db)
recommender = rec_service.get_recommender("itemcf")
```

#### 策略模式（Strategy Pattern）
所有推荐算法继承自 `BaseRecommender`，实现统一的 `recommend()` 接口：

```python
class BaseRecommender(ABC):
    @abstractmethod
    def recommend(self, user_id: str, k: int = 10) -> List[str]:
        pass
```

#### 单例模式（Singleton Pattern）
`RecommenderService` 缓存推荐器实例，避免重复初始化。

## 🚀 使用方法

### 1. API 调用

#### 获取推荐列表
```bash
GET /api/v1/recommend/{user_id}?algorithm=popular&k=10
```

**参数：**
- `user_id`: 用户ID
- `algorithm`: 推荐算法 (`random` / `popular` / `itemcf`)
- `k`: 推荐数量 (1-100)
- `filter_interacted`: 是否过滤已交互商品 (默认 true)
- `with_details`: 是否返回商品详情 (默认 false)

**响应示例：**
```json
{
  "code": 200,
  "message": "Recommendations generated successfully",
  "data": {
    "user_id": "user_123",
    "algorithm": "popular",
    "recommendations": [
      {
        "item_id": "item_001",
        "score": 0.95,
        "rank": 1,
        "title": "3D打印机 Pro Max",
        "category": "打印设备"
      }
    ],
    "total_count": 10,
    "generated_at": "2026-01-29T10:30:00"
  }
}
```

#### 训练模型（ItemCF）
```bash
POST /api/v1/recommend/train/itemcf
```

#### 获取相似商品
```bash
GET /api/v1/recommend/similar/{item_id}?k=10
```

#### 查看可用算法
```bash
GET /api/v1/recommend/algorithms
```

### 2. Python 代码调用

```python
from app.recommender.service import RecommenderService
from app.db import get_db

# 创建服务实例
db = next(get_db())
rec_service = RecommenderService(db)

# 方式1：直接调用服务（推荐）
recommendations = rec_service.recommend(
    user_id="user_123",
    algorithm="itemcf",
    k=10
)

# 方式2：获取推荐器实例
recommender = rec_service.get_recommender("popular")
recommendations = recommender.recommend(user_id="user_123", k=10)

# 方式3：带分数的推荐
results = rec_service.recommend_with_scores(
    user_id="user_123",
    algorithm="itemcf",
    k=10
)
# 输出: [{"item_id": "...", "score": 0.95, "rank": 1}, ...]
```

## 📊 算法说明

### 1. Random（随机推荐）
- **适用场景**: A/B测试对照组、探索性推荐
- **特点**: 从商品池中随机选择，无需训练
- **性能**: 极快（毫秒级）

### 2. Popular（热门推荐）
- **适用场景**: 首页推荐、冷启动用户、新用户引导
- **特点**: 基于全局交互次数排序
- **性能**: 快速（毫秒级）
- **优化**: 支持缓存热度榜单

### 3. ItemCF（协同过滤）
- **适用场景**: 个性化推荐、"看了又看"、相似商品推荐
- **特点**: 基于用户行为计算商品相似度
- **性能**: 
  - 训练: 慢（分钟-小时级，取决于数据量）
  - 推荐: 快速（毫秒级，查表）
- **优化**: 
  - 相似度矩阵预计算并缓存
  - 每个商品仅保留 Top-N 相似商品
  - 支持增量更新

## 🔧 配置与优化

### 1. ItemCF 配置参数

```python
recommender = ItemCFRecommender(
    db=db,
    cache_path="app/recommender/cache/itemcf_similarity.pkl",
    similarity_method="cosine",      # 相似度方法
    min_similarity=0.1,              # 最小相似度阈值
    top_n_similar=50                 # 每个商品保留的相似商品数
)
```

### 2. 定期训练任务

ItemCF 需要定期重新训练以更新相似度矩阵：

```python
# scripts/train_itemcf.py
from app.db import SessionLocal
from app.recommender.service import RecommenderService

db = SessionLocal()
rec_service = RecommenderService(db)

# 训练模型
rec_service.train_model(
    algorithm="itemcf",
    min_interactions=2,    # 最小交互次数阈值
    save_cache=True        # 保存缓存
)
```

**建议：**
- 小规模数据（< 10万条交互）: 每天训练一次
- 中等规模（10万-100万）: 每周训练一次
- 大规模（> 100万）: 每月训练或使用增量更新

### 3. 缓存策略

- **相似度矩阵**: 使用 Pickle 序列化存储到文件
- **热度榜单**: 在 DataLoader 中使用内存缓存
- **推荐器实例**: 在 RecommenderService 中缓存

## 🔄 扩展新算法

### 步骤1: 创建算法类

```python
# app/recommender/strategies/my_algorithm.py
from app.recommender.base import BaseRecommender

class MyRecommender(BaseRecommender):
    def recommend(self, user_id: str, k: int = 10, **kwargs) -> List[str]:
        # 实现推荐逻辑
        return []
```

### 步骤2: 注册到工厂

```python
# app/recommender/service.py
from app.recommender.strategies.my_algorithm import MyRecommender

RecommenderService.register_algorithm("myalgo", MyRecommender)
```

### 步骤3: 调用

```python
rec_service.recommend(user_id="user_123", algorithm="myalgo", k=10)
```

## 📈 性能优化建议

1. **数据库索引**
   ```sql
   CREATE INDEX idx_user_behavior_user ON user_behavior(user_id);
   CREATE INDEX idx_user_behavior_item ON user_behavior(item_id);
   CREATE INDEX idx_user_behavior_time ON user_behavior(timestamp);
   ```

2. **批量推荐**
   ```python
   # 使用批量接口提升效率
   results = rec_service.batch_recommend(
       user_ids=["user_1", "user_2", "user_3"],
       algorithm="itemcf",
       k=10
   )
   ```

3. **异步任务**
   - 使用 Celery 或 APScheduler 进行定期训练
   - 将耗时操作放入后台任务队列

4. **分布式缓存**
   - 将相似度矩阵存储到 Redis
   - 使用 Redis 缓存推荐结果（设置过期时间）

## 🧪 测试

```python
# tests/test_recommender.py
from app.recommender.service import RecommenderService

def test_random_recommender(db):
    rec_service = RecommenderService(db)
    recommendations = rec_service.recommend(
        user_id="test_user",
        algorithm="random",
        k=10
    )
    assert len(recommendations) == 10

def test_itemcf_training(db):
    rec_service = RecommenderService(db)
    success = rec_service.train_model("itemcf")
    assert success == True
```

## 📝 注意事项

1. **冷启动问题**: 
   - 新用户: 使用 Popular 算法
   - 新商品: 无法通过 ItemCF 推荐，需要内容推荐

2. **数据稀疏性**: 
   - 如果用户行为数据不足，ItemCF 效果可能不佳
   - 建议设置 `min_interactions` 阈值过滤噪声

3. **降级策略**: 
   - ItemCF 未训练时自动降级到 Popular
   - 用户无历史行为时降级到 Popular
   - 任何异常时最终降级到 Random

4. **内存管理**: 
   - ItemCF 相似度矩阵可能占用大量内存
   - 可以调整 `top_n_similar` 参数控制大小

## 🔮 未来扩展方向

1. **深度学习模型**: 
   - Wide & Deep
   - DeepFM
   - Neural Collaborative Filtering

2. **实时推荐**: 
   - 接入 Kafka 实时计算
   - 在线学习更新模型

3. **多目标优化**: 
   - 点击率 + 转化率 + 多样性
   - Multi-armed Bandit

4. **个性化融合**: 
   - 集成多个算法（Ensemble）
   - 根据用户特征动态选择算法
