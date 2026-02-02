# app/core/config.py
"""
应用配置模块
使用 pydantic-settings 管理配置项
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本信息
    APP_NAME: str = "Recommendation System API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    # DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/rec_sys_db"
    DATABASE_URL: str = "mysql+pymysql://root:123456@172.17.144.1:3306/rec_sys"  # wsl 连接宿主机数据库
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
