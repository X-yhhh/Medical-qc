# app/core/config.py
# ----------------------------------------------------------------------------------
# 核心配置 (Core Configuration)
# 作用：集中管理应用程序的全局配置参数，如密钥、算法类型、过期时间等。
# 对接前端：
#   - 间接影响前端认证流程 (如 Token 过期时间决定了用户多久需要重新登录)。
# ----------------------------------------------------------------------------------

from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    系统配置类
    读取环境变量或默认值
    """
    # API 基础路径
    API_V1_STR: str = "/api/v1"
    
    # 项目名称
    PROJECT_NAME: str = "Medical QC System"
    
    # JWT 签名密钥 (生产环境应从环境变量获取)
    SECRET_KEY: str = "medical-qc-secret-change-in-prod"
    
    # 加密算法 (HS256: HMAC with SHA-256)
    ALGORITHM: str = "HS256"
    
    # Access Token 过期时间 (分钟)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 跨域资源共享 (CORS) 配置
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:8080"]

    class Config:
        case_sensitive = True

# 单例配置对象
settings = Settings()
