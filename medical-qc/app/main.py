# app/main.py
# ----------------------------------------------------------------------------------
# 应用程序入口 (Main Entry)
# 作用：FastAPI 应用的启动入口，负责挂载路由、中间件、静态资源和事件处理。
#       作为后端服务的核心调度器，将请求分发至各个 API 模块。
# 对接模块：
#   - 路由模块: app.api.v1.* (auth, quality, summary)
#   - 数据库: app.utils.database (初始化连接)
#   - 前端入口: src/main.js (API Base URL 配置)
# ----------------------------------------------------------------------------------

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import traceback

# 导入路由模块
from app.api.v1.auth import router as auth_router
from app.api.v1.quality import router as quality_router
from app.api.v1.summary import router as summary_router

# 导入所有模型以确保 create_all 能找到它们 (SQLAlchemy)
from app.models.user import User
from app.models.user_role import UserRole
from app.models.hemorrhage_record import HemorrhageRecord
from app.utils.database import engine, Base

# ----------------------------------------------------------------------------------
# FastAPI 实例初始化
# ----------------------------------------------------------------------------------
app = FastAPI(
    title="Medical Quality Control System",
    description="医学影像质控平台 - 脑出血检测与用户管理",
    version="1.0.0",
)

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "hemorrhage_uploads"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMP_DIR = BASE_DIR / "temp"

# ----------------------------------------------------------------------------------
# 生命周期事件：启动时
# 作用：初始化数据库表结构，创建必要的目录。
# ----------------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    应用启动时的初始化操作
    1. 创建数据库表 (仅用于开发环境，生产环境应使用 Alembic)
    2. 创建必要的存储目录 (data, temp)
    """
    # 自动创建表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 确保目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------------
# 静态资源挂载
# ----------------------------------------------------------------------------------
# 挂载上传目录 (用于访问检测图片)
# URL: /static/hemorrhage/filename.png
app.mount("/static/hemorrhage", StaticFiles(directory=str(UPLOAD_DIR)), name="hemorrhage_images")

# 挂载通用静态资源 (如果存在)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ----------------------------------------------------------------------------------
# 中间件配置：CORS
# 作用：允许前端跨域访问 API。
# ----------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # 允许所有来源，解决开发环境下的 "Network Error" 问题
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------------------
# 路由注册
# ----------------------------------------------------------------------------------
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(quality_router, prefix="/api/v1/quality")
app.include_router(summary_router, prefix="/api/v1/summary")

# 挂载临时目录 (用于调试或临时文件访问)
app.mount("/api/v1/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")

# ----------------------------------------------------------------------------------
# 全局异常处理
# ----------------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常捕获
    作用：捕获所有未处理异常，返回 500 JSON 响应，防止应用崩溃。
    """
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )
