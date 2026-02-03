# app/core/config.py
# ----------------------------------------------------------------------------------
# 核心配置 (Core Configuration)
# 作用：集中管理应用程序的全局配置参数，如密钥、算法类型、过期时间等。
# ----------------------------------------------------------------------------------

# JWT 签名密钥 (生产环境应从环境变量获取)
SECRET_KEY = "medical-qc-secret-change-in-prod"

# 加密算法 (HS256: HMAC with SHA-256)
ALGORITHM = "HS256"

# Access Token 过期时间 (分钟)
ACCESS_TOKEN_EXPIRE_MINUTES = 30
