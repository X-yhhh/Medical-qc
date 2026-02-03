# app/api/deps.py
# ----------------------------------------------------------------------------------
# 依赖注入模块 (Dependencies Module)
# 作用：定义 FastAPI 路由依赖项，如数据库会话获取、当前用户验证等。
# 对接前端：
#   - 所有需要鉴权的组件 (如 Head.vue, Hemorrhage.vue, CoronaryCTA.vue 等)
#   - 登录/注册页面 (Login.vue, Register.vue) - 间接相关
# ----------------------------------------------------------------------------------

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.utils.database import AsyncSessionLocal
from app.models.user import User

# OAuth2 方案定义
# 对接前端：前端请求头中的 Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话 (Database Session Dependency)
    
    作用：
        创建一个新的异步数据库会话，并在请求处理完成后自动关闭。
        作为 FastAPI 的依赖项注入到路由处理函数中。
    
    对接前端：
        不直接对接前端，但支持所有涉及数据库操作的 API。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前登录用户 (Get Current User Dependency)
    
    作用：
        验证请求中的 Token 有效性。
        从数据库中查询并返回对应的用户对象。
        如果验证失败，抛出 401 未授权异常。
    
    参数：
        db: 数据库会话
        token: 访问令牌 (从请求头 Authorization 中提取)
    
    对接前端：
        所有受保护的 API 调用。
        前端在发送请求时需在 Header 中携带 Token。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 直接通过 Token 查询用户 (匹配 auth_service 中的实现)
    result = await db.execute(select(User).where(User.access_token == token))
    user = result.scalars().first()
    
    if not user:
        raise credentials_exception
        
    return user
