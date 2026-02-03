# app/api/v1/auth.py
# ----------------------------------------------------------------------------------
# 认证模块 API (Authentication API)
# 作用：处理用户注册和登录请求，提供身份验证服务。
# 对接服务：app.services.auth_service
# ----------------------------------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.request import RegisterReq, LoginReq
from app.schemas.response import LoginResponse
from app.services.auth_service import register_user, login_user
from app.utils.database import get_db

router = APIRouter()

# ----------------------------------------------------------------------------------
# 接口：用户注册
# URL: POST /api/v1/auth/register
# 作用：接收用户提交的注册信息，并在数据库中创建新用户。
# 参数：RegisterReq (username, password, email, full_name, etc.)
# 返回：注册成功或失败的消息
# ----------------------------------------------------------------------------------
@router.post("/register")
async def register(req: RegisterReq, db: AsyncSession = Depends(get_db)):
    # 调用 auth_service 中的 register_user 逻辑
    success, msg = await register_user(
        db,
        req.username,
        req.email,
        req.password,
        req.full_name,
        req.hospital,
        req.department
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


# ----------------------------------------------------------------------------------
# 接口：用户登录
# URL: POST /api/v1/auth/login
# 作用：验证用户凭证，成功后生成并返回 JWT 访问令牌 (Access Token)。
# 参数：LoginReq (username, password)
# 返回：LoginResponse (包含 token 和用户信息)
# ----------------------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    # 调用 auth_service 中的 login_user 进行验证并生成 Token
    token, error = await login_user(db, req.username, req.password)

    if error is None and token:
        # 登录成功，构造返回数据
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": req.username,  # 直接用登录名（安全且简单）
                "full_name": req.username,
                "role": "doctor" # 默认角色，可根据数据库实际角色扩展
            }
        }

    # ✅ 统一返回 400，不暴露具体原因（安全考虑）
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="用户名或密码错误"
    )
