# app/main.py
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import traceback

from app.api.v1.auth import router as auth_router
from app.api.v1.quality import router as quality_router
from app.api.v1.summary import router as summary_router
# 导入所有模型以确保 create_all 能找到它们
from app.models.user import User
from app.models.user_role import UserRole
from app.models.hemorrhage_record import HemorrhageRecord
from app.utils.database import engine, Base

# 创建 FastAPI 应用实例
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

# 启动时创建表
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 确保目录存在
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态文件目录
app.mount("/static/hemorrhage", StaticFiles(directory=str(UPLOAD_DIR)), name="hemorrhage_images")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", # 前端端口 (禁止修改)
        "http://127.0.0.1:5173", # 前端端口 (禁止修改)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API v1 路由（前缀 /api/v1）
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(quality_router, prefix="/api/v1/quality")
app.include_router(summary_router, prefix="/api/v1/summary")
app.mount("/api/v1/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )