# 推荐系统后端 API

基于 FastAPI + SQLAlchemy 构建的推荐系统后端应用，提供用户和商品的完整 CRUD 操作。

## 项目结构

```
rec_sys/
├── app/                      # 应用主目录
│   ├── api/                  # API 路由层
│   │   ├── endpoints/        # 具体的端点实现
│   │   │   ├── users.py      # 用户相关 API
│   │   │   ├── items.py      # 商品相关 API
│   │   │   └── __init__.py
│   │   ├── router.py         # 路由汇总
│   │   └── __init__.py
│   ├── core/                 # 核心配置
│   │   ├── config.py         # 应用配置
│   │   └── __init__.py
│   ├── crud/                 # CRUD 操作层
│   │   ├── user.py           # 用户 CRUD
│   │   ├── item.py           # 商品 CRUD
│   │   └── __init__.py
│   ├── db/                   # 数据库相关
│   │   ├── session.py        # 数据库会话管理
│   │   └── __init__.py
│   ├── models/               # SQLAlchemy 模型
│   │   ├── user.py           # 用户模型
│   │   ├── item.py           # 商品模型
│   │   └── __init__.py
│   ├── schemas/              # Pydantic Schema
│   │   ├── user.py           # 用户 Schema
│   │   ├── item.py           # 商品 Schema
│   │   ├── common.py         # 通用 Schema
│   │   └── __init__.py
│   └── __init__.py
├── main.py                   # 应用入口
├── requirements.txt          # 项目依赖
├── .env.example              # 环境变量示例
└── .gitignore                # Git 忽略配置
```

## 技术栈

- **Python**: 3.10+
- **FastAPI**: Web 框架
- **SQLAlchemy**: ORM
- **Pydantic**: 数据验证
- **MySQL**: 数据库
- **Uvicorn**: ASGI 服务器

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

复制 `.env.example` 为 `.env` 并修改数据库连接信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DATABASE_URL=mysql+pymysql://your_user:your_password@localhost:3306/rec_sys_db
APP_NAME=Recommendation System API
APP_VERSION=1.0.0
DEBUG=True
```

### 3. 创建数据库

在 MySQL 中创建数据库：

```sql
CREATE DATABASE rec_sys_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 启动应用

```bash
# 方式 1: 使用 uvicorn 命令
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 直接运行 main.py
python main.py
```

### 5. 访问 API 文档

启动成功后，访问以下地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## API 接口说明

### 用户接口 (Users)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/users/` | 创建用户 |
| GET | `/api/v1/users/` | 获取用户列表（支持分页） |
| GET | `/api/v1/users/{uid}` | 获取单个用户 |
| PUT | `/api/v1/users/{uid}` | 更新用户信息 |
| DELETE | `/api/v1/users/{uid}` | 删除用户 |

### 商品接口 (Items)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/items/` | 创建商品 |
| GET | `/api/v1/items/` | 获取商品列表（支持分页） |
| GET | `/api/v1/items/{item_id}` | 获取单个商品 |
| PUT | `/api/v1/items/{item_id}` | 更新商品信息 |
| DELETE | `/api/v1/items/{item_id}` | 删除商品 |

## 使用示例

### 创建用户

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "user001",
    "member_level": 1,
    "sex": "male",
    "country": "China",
    "province": "Beijing",
    "city": "Beijing"
  }'
```

### 获取用户列表

```bash
curl "http://localhost:8000/api/v1/users/?skip=0&limit=10"
```

### 创建商品

```bash
curl -X POST "http://localhost:8000/api/v1/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "item001",
    "group_name": "3D模型套装",
    "first_level_category_name": "模型",
    "second_level_category_name": "建筑模型",
    "tags_name_list": "建筑,现代,高清",
    "group_desc": "高质量建筑模型"
  }'
```

### 获取商品列表

```bash
curl "http://localhost:8000/api/v1/items/?skip=0&limit=10"
```

## 后续扩展建议

### 1. 推荐算法模块结构

```
app/
├── recommendation/          # 推荐算法模块
│   ├── recall/             # 召回层
│   │   ├── i2i.py          # Item-to-Item 协同过滤
│   │   ├── u2i.py          # User-to-Item 协同过滤
│   │   └── popular.py      # 热门商品召回
│   ├── rank/               # 排序层
│   │   ├── features.py     # 特征工程
│   │   └── model.py        # 排序模型
│   └── __init__.py
```

### 2. 数据库迁移

建议使用 Alembic 进行数据库版本管理：

```bash
pip install alembic
alembic init alembic
```

### 3. 缓存层

引入 Redis 用于缓存热门数据和推荐结果：

```python
# app/core/cache.py
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

### 4. 异步任务

使用 Celery 处理耗时的推荐计算任务：

```bash
pip install celery redis
```

### 5. 日志和监控

添加结构化日志和性能监控：

```python
# app/core/logging.py
import logging
from pythonjsonlogger import jsonlogger
```

## 项目特点

✅ **清晰的分层架构**: API → CRUD → Model，职责明确  
✅ **类型安全**: 使用 Pydantic 进行数据验证  
✅ **易于扩展**: 预留推荐算法模块空间  
✅ **开箱即用**: 配置简单，可直接运行  
✅ **规范的 RESTful API**: 遵循最佳实践  
✅ **完整的错误处理**: 提供友好的错误信息  

## 开发建议

1. **环境隔离**: 使用虚拟环境（venv 或 conda）
2. **代码规范**: 使用 black、flake8 进行代码格式化
3. **类型检查**: 使用 mypy 进行静态类型检查
4. **单元测试**: 使用 pytest 编写测试用例
5. **API 文档**: 充分利用 FastAPI 自动生成的文档

## 常见问题

### 1. 数据库连接失败

检查 `.env` 文件中的数据库配置是否正确，确保 MySQL 服务已启动。

### 2. 端口被占用

修改启动命令中的端口号：

```bash
uvicorn main:app --reload --port 8001
```

### 3. 依赖安装失败

尝试升级 pip：

```bash
python -m pip install --upgrade pip
```

## 许可证

MIT License
