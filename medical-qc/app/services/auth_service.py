# app/services/auth_service.py
import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.user_role import UserRole  # ✅ 必须导入，解决外键问题
from passlib.context import CryptContext

# ✅ 全局唯一密码上下文（关键！）
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


async def register_user(
        db: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: str = None,
        hospital: str = None,
        department: str = None
):
    # 检查用户是否存在
    result = await db.execute(
        select(User).where((User.username == username) | (User.email == email))
    )
    if result.scalars().first():
        return False, "用户名或邮箱已存在"

    # 确保默认角色存在（role_id=2）
    role_result = await db.execute(select(UserRole).where(UserRole.id == 2))
    if not role_result.scalars().first():
        default_role = UserRole(id=2, name="doctor", description="医生")
        db.add(default_role)
        await db.commit()

    # 加密密码并创建用户
    hashed_pw = pwd_context.hash(password)  # ✅ 正确加密
    token = secrets.token_urlsafe(32)
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


# app/services/auth_service.py
async def login_user(db: AsyncSession, username: str, password: str):
    """
    登录用户
    返回: (token: str | None, error: str | None)
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user:
        return None, "用户名不存在"

    if not pwd_context.verify(password, user.password_hash):
        return None, "密码错误"

    # 登录成功
    print(f"✅ 登录成功，token: {user.access_token}")
    return user.access_token, None