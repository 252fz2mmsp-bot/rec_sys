# 数据导入工具使用说明

## 文件说明

1. **create_tables.sql** - 数据库表结构创建脚本
2. **write_to_db.py** - 数据导入主程序
3. **action_en_2025-11-30.txt** - 用户行为数据文件（无表头）
4. **ods_user_en.txt** - 用户信息数据文件（无表头）
5. **model_export(1).csv** - 商品信息数据文件（有表头）

## 数据表结构

### 1. user_behavior（用户行为表）
- user_id - 用户ID
- item_id - 商品ID
- scene - 场景
- app_type - 应用类型
- app_version - 应用版本
- position - 位置
- event - 事件类型
- event_time - 事件时间
- ip - IP地址
- country - 国家
- province - 省份
- city - 城市

### 2. user_info（用户信息表）
- uid - 用户ID（主键）
- member_level - 是否会员（0-否，1-是）
- modeler_level - 是否建模师（0-否，1-是）
- reg_time - 注册时间
- sex - 性别
- country - 国家
- province - 省份
- city - 城市
- login_time - 上次登录时间

### 3. item_info（商品信息表）
- _id - 商品ID（主键）
- group_name - 组名称
- first_level_category_name - 一级分类
- second_level_category_name - 二级分类
- tags_name_list - 标签列表
- cover_first - 封面图
- group_desc - 商品描述

## 使用前准备

### 1. 安装依赖
```bash
pip install pymysql
```

### 2. 确保MySQL数据库已创建
```sql
CREATE DATABASE IF NOT EXISTS rec_sys DEFAULT CHARACTER SET utf8mb4;
```

### 3. 确保数据文件存在
确保以下文件在同一目录下：
- action_en_2025-11-30.txt
- ods_user_en.txt
- model_export(1).csv

## 运行步骤

### 方式1：直接运行（推荐）
```bash
python write_to_db.py
```

程序会自动：
1. 连接数据库
2. 创建数据表
3. 导入用户行为数据
4. 导入用户信息数据
5. 导入商品信息数据

### 方式2：分步执行

#### 步骤1：手动创建表
```bash
mysql -h localhost -u root -p123456 rec_sys < create_tables.sql
```

#### 步骤2：运行导入程序
```bash
python write_to_db.py
```

## 数据文件格式说明

### 用户行为文件（action_en_2025-11-30.txt）
无表头，制表符或逗号分隔，字段顺序：
```
user_id, item_id, scene, app_type, app_version, position, event, event_time, ip, country, province, city
```

### 用户信息文件（ods_user_en.txt）
无表头，制表符或逗号分隔，字段顺序：
```
uid, member_level, modeler_level, reg_time, sex, country, province, city, login_time
```

### 商品信息文件（model_export(1).csv）
有表头，逗号分隔，字段：
```
_id, group_name, first_level_category_name, second_level_category_name, tags_name_list, cover_first, group_desc
```

## 配置修改

如需修改数据库连接信息，编辑 `write_to_db.py` 文件的 `main()` 函数：

```python
db_config = {
    'host': 'localhost',      # 数据库主机
    'port': 3306,             # 端口
    'user': 'root',           # 用户名
    'password': '123456',     # 密码
    'database': 'rec_sys'     # 数据库名
}
```

## 功能特点

1. **批量导入**：使用批量插入提高导入效率（默认1000条/批）
2. **错误处理**：记录导入过程中的错误，不会因个别数据错误而中断
3. **重复处理**：用户信息和商品信息支持更新（ON DUPLICATE KEY UPDATE）
4. **日志记录**：详细的导入日志，方便追踪导入进度和问题
5. **多种日期格式支持**：自动识别多种日期时间格式
6. **编码支持**：支持UTF-8编码的中文数据

## 注意事项

1. 确保MySQL服务已启动
2. 确保数据库用户有相应的权限（CREATE, INSERT, UPDATE）
3. 大文件导入可能需要较长时间，请耐心等待
4. 建议先用小样本数据测试后再导入完整数据
5. 导入前建议备份数据库

## 常见问题

### 1. 连接数据库失败
- 检查MySQL服务是否启动
- 检查用户名、密码是否正确
- 检查数据库是否已创建

### 2. 文件找不到
- 确保数据文件与程序在同一目录
- 检查文件名是否正确（包括扩展名）

### 3. 数据导入失败
- 查看日志中的错误信息
- 检查数据格式是否符合要求
- 确认数据文件编码为UTF-8

### 4. 中文乱码
- 确保数据库字符集为utf8mb4
- 确保数据文件保存为UTF-8编码

## 查看导入结果

```sql
-- 查看各表数据量
SELECT COUNT(*) as behavior_count FROM user_behavior;
SELECT COUNT(*) as user_count FROM user_info;
SELECT COUNT(*) as item_count FROM item_info;

-- 查看样例数据
SELECT * FROM user_behavior LIMIT 10;
SELECT * FROM user_info LIMIT 10;
SELECT * FROM item_info LIMIT 10;
```
