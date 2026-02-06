-- 创建推荐系统数据库表结构

-- 用户行为表
CREATE TABLE IF NOT EXISTS user_behavior (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    item_id VARCHAR(100) NOT NULL,
    scene VARCHAR(100),
    app_type VARCHAR(100),
    app_version VARCHAR(100),
    position TEXT,
    event VARCHAR(100),
    event_time DATETIME,
    ip VARCHAR(100),
    country VARCHAR(100),
    province VARCHAR(100),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_event_time (event_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户行为数据表';

-- 用户信息表
CREATE TABLE IF NOT EXISTS user_info (
    uid VARCHAR(100) PRIMARY KEY,
    member_level TINYINT DEFAULT 0 COMMENT '是否会员 0-否 1-是',
    modeler_level TINYINT DEFAULT 0 COMMENT '是否建模师 0-否 1-是',
    reg_time DATETIME COMMENT '注册时间',
    sex VARCHAR(10) COMMENT '性别',
    country VARCHAR(100),
    province VARCHAR(100),
    city VARCHAR(100),
    login_time DATETIME COMMENT '上次登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_reg_time (reg_time),
    INDEX idx_country (country)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- 商品信息表
CREATE TABLE IF NOT EXISTS item_info (
    _id VARCHAR(100) PRIMARY KEY,
    group_name VARCHAR(500),
    first_level_category_name VARCHAR(200),
    second_level_category_name VARCHAR(200),
    tags_name_list TEXT,
    cover_first VARCHAR(500),
    group_desc TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_first_category (first_level_category_name),
    INDEX idx_second_category (second_level_category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品信息表';
