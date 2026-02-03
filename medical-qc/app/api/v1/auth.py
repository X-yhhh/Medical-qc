# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.request import RegisterReq, LoginReq
from app.schemas.response import LoginResponse
from app.services.auth_service import register_user, login_user
from app.utils.database import get_db



router = APIRouter()


@router.post("/register")
async def register(req: RegisterReq, db: AsyncSession = Depends(get_db)):
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


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    token, error = await login_user(db, req.username, req.password)

    if error is None and token:
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "username": req.username,  # 直接用登录名（安全且简单）
                "full_name": req.username,
                "role": "doctor"
            }
        }

    # ✅ 统一返回 400，不暴露具体原因（安全）
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="用户名或密码错误"
    )