# app/models/item.py
"""
商品相关数据模型
"""
from sqlalchemy import Column, String, TIMESTAMP, Text
from sqlalchemy.sql import func
from app.db.session import Base


class ItemInfo(Base):
    """商品信息表模型"""
    
    __tablename__ = "item_info"
    
    _id = Column(String(100), primary_key=True, comment="商品ID")
    group_name = Column(String(500), comment="商品组名称")
    first_level_category_name = Column(String(200), index=True, comment="一级分类名称")
    second_level_category_name = Column(String(200), index=True, comment="二级分类名称")
    tags_name_list = Column(Text, comment="标签列表")
    cover_first = Column(String(500), comment="封面图片")
    group_desc = Column(Text, comment="商品描述")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )

    def __repr__(self):
        return f"<ItemInfo(_id={self._id}, group_name={self.group_name})>"
