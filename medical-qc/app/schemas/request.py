# app/schemas/request.py
# ----------------------------------------------------------------------------------
# 请求参数模型 (Request Schemas)
# 作用：定义前端 API 请求的 Body 参数结构，用于 FastAPI 的自动验证和文档生成。
# ----------------------------------------------------------------------------------

from pydantic import BaseModel
from typing import Optional

# ----------------------------------------------------------------------------------
# 注册请求参数 (RegisterReq)
# 作用：用户注册接口的请求体
# ----------------------------------------------------------------------------------
class RegisterReq(BaseModel):
    username: str             # 必填：用户名
    email: str                # 必填：邮箱
    password: str             # 必填：密码
    full_name: Optional[str] = None # 选填：真实姓名
    hospital: Optional[str] = None  # 选填：所属医院
    department: Optional[str] = None # 选填：所属科室

# ----------------------------------------------------------------------------------
# 登录请求参数 (LoginReq)
# 作用：用户登录接口的请求体
# ----------------------------------------------------------------------------------
class LoginReq(BaseModel):
    username: str # 用户名
    password: str # 密码
