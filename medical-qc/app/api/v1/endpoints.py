# app/api/v1/endpoints.py
# ----------------------------------------------------------------------------------
# API 路由聚合模块 (Endpoints)
# 作用：统一管理 v1 版本的所有 API 路由，将不同模块的 Router 聚合到主路由中。
# 注意：此文件通常被 app/main.py 引用，用于注册所有 API 接口。
# 对接前端：
#   - 无直接对接，但决定了所有 API 的基础路径结构 (如 /api/v1/quality/...)
# ----------------------------------------------------------------------------------

from fastapi import APIRouter

# 导入所有子路由
from app.api.v1.quality import router as quality_router
from app.api.v1.auth import router as auth_router
# 注意：summary.py 的路由也应在此处注册，但在当前代码中未包含，建议后续添加
# from app.api.v1.summary import router as summary_router

# 创建主 v1 路由器，统一前缀 /api
# 最终 URL 示例: http://localhost:8000/api/v1/quality/detect
api_v1_router = APIRouter(prefix="/api")

# ----------------------------------------------------------------------------------
# 注册子路由
# ----------------------------------------------------------------------------------

# 注册质控相关路由
# 包含: 头部检测, 冠脉CTA, 脑出血预测等
api_v1_router.include_router(
    quality_router,
    prefix="/quality",
    tags=["Quality Assessment"]
)

# 注册认证相关路由
# 包含: 登录, 注册
api_v1_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)
