# app/models/user.py
"""
用户相关数据模型
"""
from sqlalchemy import Column, String, TIMESTAMP, DateTime, Integer
from sqlalchemy.sql import func
from app.db.session import Base


class UserInfo(Base):
    """用户信息表模型"""
    
    __tablename__ = "user_info"
    
    uid = Column(String(100), primary_key=True, comment="用户ID")
    member_level = Column(Integer, default=0, comment="是否会员 0-否 1-是")
    modeler_level = Column(Integer, default=0, comment="是否建模师 0-否 1-是")
    reg_time = Column(DateTime, comment="注册时间")
    sex = Column(String(10), comment="性别")
    country = Column(String(100), comment="国家")
    province = Column(String(100), comment="省份")
    city = Column(String(100), comment="城市")
    login_time = Column(DateTime, comment="上次登录时间")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )

    def __repr__(self):
        return f"<UserInfo(uid={self.uid}, country={self.country})>"


class UserBehavior(Base):
    """用户行为表模型"""
    
    __tablename__ = "user_behavior"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(String(100), nullable=False, index=True, comment="用户ID")
    item_id = Column(String(100), nullable=False, index=True, comment="商品ID")
    scene = Column(String(100), comment="场景")
    app_type = Column(String(100), comment="应用类型")
    app_version = Column(String(100), comment="应用版本")
    position = Column(String(1000), comment="位置信息")
    event = Column(String(100), comment="事件类型")
    event_time = Column(DateTime, index=True, comment="事件时间")
    ip = Column(String(100), comment="IP地址")
    country = Column(String(100), comment="国家")
    province = Column(String(100), comment="省份")
    city = Column(String(100), comment="城市")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")

    def __repr__(self):
        return f"<UserBehavior(id={self.id}, user_id={self.user_id}, item_id={self.item_id})>"
