# app/utils/jwt_utils.py
# ----------------------------------------------------------------------------------
# JWT 工具模块 (JWT Utilities)
# 作用：提供独立的 JWT 编码和解码验证功能。
# 注意：部分功能与 app.core.security 重叠，建议后续合并。
# 对接前端：
#   - 生成的 Token 会被前端存储在 localStorage 中。
#   - 验证失败时返回 401，前端拦截器会据此跳转回登录页。
# ----------------------------------------------------------------------------------

import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

# 密钥配置 (应统一从 core.config 获取)
SECRET_KEY = "your-secret-key-here"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ----------------------------------------------------------------------------------
# 函数：创建 Access Token
# 作用：生成包含过期时间的 JWT 字符串。
# 参数：data (Payload 数据), expires_delta (过期时间增量)
# ----------------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ----------------------------------------------------------------------------------
# 函数：验证 Token
# 作用：解码并验证 Token 的有效性（签名和过期时间）。
# 异常：过期抛出 401，无效抛出 401。
# ----------------------------------------------------------------------------------
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
