# app/models/user.py
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, ForeignKey, func, DateTime
from sqlalchemy.orm import relationship
from app.utils.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # ✅ 字段名必须一致
    full_name = Column(String(100))
    hospital = Column(String(100))
    department = Column(String(50))
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=False, default=2)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    access_token = Column(String(255), unique=True)  # ← 必须存在！

    role = relationship("UserRole", back_populates="users")
    hemorrhage_records = relationship("HemorrhageRecord", back_populates="user", cascade="all, delete-orphan")