# app/services/auth_service.py
# ----------------------------------------------------------------------------------
# 认证服务层 (Auth Service)
# 作用：封装用户注册和登录的核心业务逻辑，包括密码加密、Token 生成和数据库操作。
#       使用 Passlib 进行密码哈希处理，确保安全性。
# 对接前端：
#   - views/auth/Login.vue (登录)
#   - views/auth/Register.vue (注册)
# 对接 API:
#   - app.api.v1.auth (调用本服务的路由)
# ----------------------------------------------------------------------------------

import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.user_role import UserRole
from passlib.context import CryptContext

# 全局密码加密上下文配置
# 使用 pbkdf2_sha256 算法，deprecated="auto" 允许自动升级旧哈希
# 注意：应确保与 app.core.security 中的配置一致 (当前可能存在差异)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ----------------------------------------------------------------------------------
# 函数：注册新用户 (register_user)
# 作用：检查用户名/邮箱重复，创建默认角色，保存用户到数据库。
# 参数：db (Session), user_info...
# 返回：(success: bool, message: str)
# 对接前端：Register.vue 表单提交
# ----------------------------------------------------------------------------------
async def register_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        hospital: str = None,
        department: str = None
):
    """
    注册用户核心逻辑
    
    Steps:
    1. 检查用户名或邮箱是否已被注册。
    2. 检查默认角色 (ID=2, Doctor) 是否存在，不存在则自动创建。
    3. 对密码进行哈希加密。
    4. 生成初始 Access Token。
    5. 创建 User 对象并写入数据库。
    """
    # 1. 检查用户名或邮箱是否已存在
    result = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if result.scalars().first():
        return False, "用户名或邮箱已存在"

    # 2. 确保默认角色 (Doctor, ID=2) 存在
    role_result = await db.execute(select(UserRole).where(UserRole.id == 2))
    if not role_result.scalars().first():
        default_role = UserRole(id=2, name="doctor", description="医生")
        db.add(default_role)
        await db.commit()

    # 3. 密码加密与用户创建
    hashed_pw = pwd_context.hash(password)  # 加密密码
    token = secrets.token_urlsafe(32)       # 生成初始 Access Token
    
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        full_name=full_name,
        hospital=hospital,
        department=department,
        access_token=token,
        role_id=2
    )
    db.add(new_user)
    await db.commit()
    
    return True, "注册成功"


# ----------------------------------------------------------------------------------
# 函数：用户登录 (login_user)
# 作用：验证用户名密码，成功则返回 Access Token。
# 参数：db (Session), username, password
# 返回：(token: str | None, error: str | None)
# 对接前端：Login.vue 登录表单
# ----------------------------------------------------------------------------------
async def login_user(db: AsyncSession, username: str, password: str):
    """
    用户登录验证逻辑
    
    Steps:
    1. 根据用户名查询用户。
    2. 如果用户不存在，返回错误。
    3. 使用 pwd_context 验证密码是否匹配。
    4. 验证通过则返回用户的 Access Token。
    """
    # 1. 查询用户
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    # 2. 用户不存在
    if not user:
        return None, "用户名不存在"

    # 3. 验证密码
    if not pwd_context.verify(password, user.password_hash):
        return None, "密码错误"

    # 4. 登录成功，返回 Token
    # 注意：实际生产环境建议在此处更新 Token 或记录登录时间
    print(f"✅ 登录成功，token: {user.access_token}")
    return user.access_token, None
