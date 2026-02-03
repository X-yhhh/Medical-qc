# app/api/v1/auth.py
# ----------------------------------------------------------------------------------
# 认证模块 API (Authentication API)
# 作用：处理用户注册和登录请求，提供基于 OAuth2 的身份验证服务。
#       作为系统的入口门禁，验证用户凭证并发放 Access Token。
# 对接模块：
#   - 后端服务: app.services.auth_service
#   - 前端调用: src/api/auth.js (login, register)
#   - 前端视图: src/views/Login.vue, src/views/Register.vue
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
# 对接前端: src/views/Register.vue (handleSubmit)
# ----------------------------------------------------------------------------------
@router.post("/register")
async def register(req: RegisterReq, db: AsyncSession = Depends(get_db)):
    """
    用户注册接口
    
    Process:
    1. 接收注册请求参数 (用户名, 密码, 邮箱, 医院信息等)
    2. 调用 auth_service.register_user 执行业务逻辑
    3. 如果注册失败(如用户已存在)，抛出 400 异常
    4. 返回成功消息
    """
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
# 对接前端: src/views/Login.vue (handleLogin)
# ----------------------------------------------------------------------------------
@router.post("/login", response_model=LoginResponse)
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    """
    用户登录接口
    
    Process:
    1. 接收登录请求 (用户名, 密码)
    2. 调用 auth_service.login_user 验证凭证
    3. 如果验证通过，返回 Access Token 和用户信息
    4. 如果验证失败，抛出 400 异常 (模糊错误信息以提高安全性)
    """
    # 调用 auth_service 中的 login_user 进行验证并生成 Token
    token, error = await login_user(db, req.username, req.password)

    if error is None and token:
        # 登录成功，构造返回数据
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": req.username,  # 直接用登录名
                "full_name": req.username, # 暂用用户名代替全名
                "role": "doctor" # 默认角色，后续可从数据库读取 dynamic role
            }
        }

    # 统一返回 400，不暴露具体是用户名不存在还是密码错误
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="用户名或密码错误"
    )
