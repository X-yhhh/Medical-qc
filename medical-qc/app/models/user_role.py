# app/models/user_role.py
# ----------------------------------------------------------------------------------
# 数据库模型：用户角色 (UserRole)
# 作用：定义 user_roles 表结构，存储系统中的角色定义（如医生、管理员）。
# 对接前端：
#   - 暂时无直接前端管理界面，通常由数据库预置数据。
#   - 影响前端权限控制 (如某些按钮仅管理员可见)。
# ----------------------------------------------------------------------------------

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime

class UserRole(Base):
    """
    用户角色模型类
    映射表名: user_roles
    
    作用：
        定义系统权限角色，如 'admin' (管理员), 'doctor' (医生) 等。
    """
    __tablename__ = "user_roles"

    # 主键 ID
    id = Column(Integer, primary_key=True)
    
    # 角色名称 (如 "doctor", "admin")
    name = Column(String(20), nullable=False)
    
    # 角色描述 (如 "普通医生，拥有查看和上传权限")
    description = Column(String(100))
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # -------------------
    # 关联关系
    # -------------------
    # 关联拥有该角色的用户列表
    users = relationship("User", back_populates="role")
