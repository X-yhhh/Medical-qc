# app/api/deps.py
# ----------------------------------------------------------------------------------
# API 依赖模块 (Dependencies)
# 作用：定义 FastAPI 路由依赖，如获取数据库会话、获取当前登录用户等。
# ----------------------------------------------------------------------------------

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.utils.database import get_db
from app.models.user import User

# OAuth2 方案配置：指定 Token 获取的 URL 路径
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ----------------------------------------------------------------------------------
# 依赖函数：获取当前登录用户 (get_current_user)
# 作用：解析请求头中的 Token，验证其有效性，并从数据库查询对应的用户对象。
# 流程：
#   1. 提取 Token (OAuth2PasswordBearer)
#   2. 在数据库中查找该 Token (Stateful Auth 模式)
#   3. 如果找到且有效，返回用户对象；否则抛出 401 异常。
# ----------------------------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 使用数据库验证 token (Stateful Auth: Token 存储在 User 表中)
    result = await db.execute(select(User).where(User.access_token == token))
    user = result.scalars().first()
    
    if not user:
        raise credentials_exception
        
    return user
