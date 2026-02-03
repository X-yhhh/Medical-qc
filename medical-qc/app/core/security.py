# app/core/security.py
# ----------------------------------------------------------------------------------
# 安全模块 (Security)
# 作用：提供密码哈希、验证以及 JWT 令牌生成的核心功能。
# 对接前端：
#   - Login.vue (登录): 验证密码
#   - Register.vue (注册): 哈希密码存储
# ----------------------------------------------------------------------------------

from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from app.core.config import settings

# 配置密码哈希上下文 (使用 bcrypt 算法)
# 作用：自动处理加盐和哈希迭代，保证密码存储安全
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ----------------------------------------------------------------------------------
# 函数：获取密码哈希值
# 作用：将明文密码转换为哈希字符串，用于存储到数据库。
# 参数：password - 明文密码
# ----------------------------------------------------------------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# ----------------------------------------------------------------------------------
# 函数：验证密码
# 作用：比对明文密码和数据库中的哈希值是否匹配。
# 参数：plain_password - 用户输入的明文密码
#       hashed_password - 数据库中存储的哈希值
# ----------------------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT 配置 (引用 config.py)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# ----------------------------------------------------------------------------------
# 函数：生成 Access Token
# 作用：根据用户信息和过期时间生成 JWT 字符串。
# 参数：
#   - data: 包含用户标识的字典 (如 {"sub": "username"})
#   - expires_delta: 过期时间增量
# 对接前端：登录成功后返回此 Token
# ----------------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 添加过期时间字段
    to_encode.update({"exp": expire})
    
    # 编码生成 Token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
