# app/core/security.py
# ----------------------------------------------------------------------------------
# 安全模块 (Security)
# 作用：提供密码哈希、验证以及 JWT 令牌生成的核心功能。
# 对接：auth_service.py, api/v1/auth.py
# ----------------------------------------------------------------------------------

from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

# 配置密码哈希上下文 (使用 bcrypt 算法)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------------------------------------------------------------------------------
# 函数：获取密码哈希值
# 作用：将明文密码转换为哈希字符串，用于存储到数据库。
# ----------------------------------------------------------------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# ----------------------------------------------------------------------------------
# 函数：验证密码
# 作用：比对明文密码和数据库中的哈希值是否匹配。
# ----------------------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT 配置 (应与 config.py 保持一致，建议统一引用)
SECRET_KEY = "medical-qc-secret-key-change-in-prod"
ALGORITHM = "HS256"

# ----------------------------------------------------------------------------------
# 函数：生成 Access Token
# 作用：根据用户信息和过期时间生成 JWT 字符串。
# 参数：
#   - data: 包含用户标识的字典 (如 {"sub": "username"})
#   - expires_delta: 过期时间增量
# ----------------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    # 添加过期时间字段
    to_encode.update({"exp": expire})
    
    # 编码生成 Token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
