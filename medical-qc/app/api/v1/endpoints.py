# app/api/v1/endpoints.py
# ----------------------------------------------------------------------------------
# API 路由聚合模块 (Endpoints)
# 作用：统一管理 v1 版本的所有 API 路由。
# 注意：此文件可能用于测试或替代 main.py 中的直接路由挂载。
# ----------------------------------------------------------------------------------

from fastapi import APIRouter

# 导入所有子路由
from app.api.v1.quality import router as quality_router
from app.api.v1.auth import router as auth_router

# 创建主 v1 路由器，统一前缀 /api
api_v1_router = APIRouter(prefix="/api")

# ----------------------------------------------------------------------------------
# 注册子路由
# ----------------------------------------------------------------------------------
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
