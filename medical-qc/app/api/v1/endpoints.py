# F:\Medical\medical-qc\app\api\v1\endpoints.py

from fastapi import APIRouter

# 导入所有子路由
from app.api.v1.quality import router as quality_router
from app.api.v1.auth import router as auth_router  # ← 必须加这一行！

# 创建主 v1 路由器，统一前缀 /api
api_v1_router = APIRouter(prefix="/api")

# 注册子路由（只注册一次！）
api_v1_router.include_router(
    quality_router,
    prefix="/quality",
    tags=["Quality Assessment"]
)

api_v1_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# 注意：不要重复 include_router 同一个 router！