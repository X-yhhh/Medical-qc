from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.utils.database import Base
from datetime import datetime

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)  # 改为 20，匹配数据库
    description = Column(String(100))         # 新增
    created_at = Column(DateTime, default=datetime.utcnow)  # 新增，自动填充

    users = relationship("User", back_populates="role")