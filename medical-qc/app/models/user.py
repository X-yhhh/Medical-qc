# app/models/user.py
# ----------------------------------------------------------------------------------
# 数据库模型：用户 (User)
# 作用：定义 Users 表结构，存储系统用户信息。
# 对接前端：
#   - views/auth/Login.vue (登录验证)
#   - views/auth/Register.vue (注册存储)
#   - 所有需要显示用户信息的组件 (如顶部导航栏的用户头像和名称)
# ----------------------------------------------------------------------------------

from sqlalchemy import Column, BigInteger, String, Integer, Boolean, ForeignKey, func, DateTime
from sqlalchemy.orm import relationship
from app.utils.database import Base

class User(Base):
    """
    用户模型类
    映射表名: users
    
    作用：
        存储用户的基本信息、认证凭据和状态。
    """
    __tablename__ = "users"

    # 主键 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # 登录账号 (唯一)
    # 对接前端：Login.vue 的用户名输入框
    username = Column(String(50), unique=True, nullable=False)
    
    # 电子邮箱 (唯一)
    # 对接前端：Register.vue 的邮箱输入框
    email = Column(String(100), unique=True, nullable=False)
    
    # 密码哈希值 (加密存储，不可逆)
    password_hash = Column(String(255), nullable=False)
    
    # 用户详细信息
    # 对接前端：Register.vue 的详细信息表单
    full_name = Column(String(100))  # 真实姓名
    hospital = Column(String(100))   # 所属医院
    department = Column(String(50))  # 所属科室
    
    # 角色关联 ID (默认为 2-医生)
    # 关联 user_roles 表
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=False, default=2)
    
    # 账号状态 (True=启用, False=禁用)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 当前有效的 Access Token
    # 作用：用于实现简单的服务端 Token 状态管理（如单点登录，或强制登出）
    access_token = Column(String(255), unique=True)

    # -------------------
    # 关联关系
    # -------------------
    # 关联用户角色
    role = relationship("UserRole", back_populates="users")
    
    # 关联该用户的脑出血检测记录 (级联删除：用户被删时，其历史记录也一并删除)
    hemorrhage_records = relationship("HemorrhageRecord", back_populates="user", cascade="all, delete-orphan")
