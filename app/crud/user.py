# app/crud/user.py
"""
用户相关的 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.user import UserInfo
from app.schemas.user import UserInfoCreate, UserInfoUpdate


class CRUDUser:
    """用户信息 CRUD 操作类"""
    
    def get(self, db: Session, uid: str) -> Optional[UserInfo]:
        """根据 UID 获取单个用户"""
        return db.query(UserInfo).filter(UserInfo.uid == uid).first()
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserInfo]:
        """获取用户列表"""
        return db.query(UserInfo).offset(skip).limit(limit).all()
    
    def get_count(self, db: Session) -> int:
        """获取用户总数"""
        return db.query(UserInfo).count()
    
    def create(self, db: Session, obj_in: UserInfoCreate) -> UserInfo:
        """创建用户"""
        db_obj = UserInfo(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        uid: str, 
        obj_in: UserInfoUpdate
    ) -> Optional[UserInfo]:
        """更新用户信息"""
        db_obj = self.get(db, uid)
        if not db_obj:
            return None
        
        # 只更新非 None 的字段
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, uid: str) -> bool:
        """删除用户"""
        db_obj = self.get(db, uid)
        if not db_obj:
            return False
        
        db.delete(db_obj)
        db.commit()
        return True
    
    def get_by_country(
        self, 
        db: Session, 
        country: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserInfo]:
        """根据国家查询用户"""
        return db.query(UserInfo).filter(
            UserInfo.country == country
        ).offset(skip).limit(limit).all()


# 创建全局实例
crud_user = CRUDUser()
