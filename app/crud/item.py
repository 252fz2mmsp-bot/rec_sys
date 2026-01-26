# app/crud/item.py
"""
商品相关的 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.item import ItemInfo
from app.schemas.item import ItemInfoCreate, ItemInfoUpdate


class CRUDItem:
    """商品信息 CRUD 操作类"""
    
    def get(self, db: Session, item_id: str) -> Optional[ItemInfo]:
        """根据 ID 获取单个商品"""
        return db.query(ItemInfo).filter(ItemInfo._id == item_id).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ItemInfo]:
        """获取商品列表"""
        return db.query(ItemInfo).offset(skip).limit(limit).all()
    
    def get_count(self, db: Session) -> int:
        """获取商品总数"""
        return db.query(ItemInfo).count()
    
    def create(self, db: Session, obj_in: ItemInfoCreate) -> ItemInfo:
        """创建商品"""
        # 使用 _id 字段名而不是别名
        obj_data = obj_in.model_dump(by_alias=False)
        if 'id' in obj_data:
            obj_data['_id'] = obj_data.pop('id')
        
        db_obj = ItemInfo(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        item_id: str, 
        obj_in: ItemInfoUpdate
    ) -> Optional[ItemInfo]:
        """更新商品信息"""
        db_obj = self.get(db, item_id)
        if not db_obj:
            return None
        
        # 只更新非 None 的字段
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, item_id: str) -> bool:
        """删除商品"""
        db_obj = self.get(db, item_id)
        if not db_obj:
            return False
        
        db.delete(db_obj)
        db.commit()
        return True
    
    def get_by_category(
        self, 
        db: Session, 
        category: str, 
        level: int = 1,
        skip: int = 0, 
        limit: int = 100
    ) -> List[ItemInfo]:
        """根据分类查询商品"""
        if level == 1:
            return db.query(ItemInfo).filter(
                ItemInfo.first_level_category_name == category
            ).offset(skip).limit(limit).all()
        else:
            return db.query(ItemInfo).filter(
                ItemInfo.second_level_category_name == category
            ).offset(skip).limit(limit).all()


# 创建全局实例
crud_item = CRUDItem()
