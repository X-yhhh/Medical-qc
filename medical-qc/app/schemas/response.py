# app/schemas/response.py
# ----------------------------------------------------------------------------------
# 响应数据模型 (Response Schemas)
# 作用：定义 API 接口的返回数据结构，确保返回格式的标准化。
# 对接前端：
#   - 前端接收到的 API 响应数据，前端需要根据此结构解析 response.data。
# ----------------------------------------------------------------------------------

from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# ----------------------------------------------------------------------------------
# 质控检测单项 (QualityItem)
# 作用：描述单个质控检测项的结果 (如：伪影检测、扫描范围等)
# 对接前端：Head.vue, CoronaryCTA.vue, ChestContrast.vue 等结果列表中的每一行
# ----------------------------------------------------------------------------------
class QualityItem(BaseModel):
    item: str          # 检测项名称 (如 "金属伪影")
    description: str   # 检测说明或建议 (如 "未检测到明显金属伪影")
    status: str        # 状态："合格" / "不合格" / "检出出血" (对应前端图标和颜色)
    confidence: Optional[float] = None  # AI 置信度 (仅 AI 任务需要)

# ----------------------------------------------------------------------------------
# 质控任务响应 (QualityResponse)
# 作用：描述整个质控分析任务的结果
# 对接前端：前端分析完成后接收到的完整 JSON 对象
# ----------------------------------------------------------------------------------
class QualityResponse(BaseModel):
    task: str          # 任务名称 (如 "Head CT Quality Check")
    status: str = "success" # 整体状态
    duration_ms: int   # 耗时 (毫秒)
    results: List[QualityItem] # 检测项列表 (渲染到前端结果卡片中)

# ----------------------------------------------------------------------------------
# 错误响应 (ErrorResponse)
# 作用：通用的错误信息返回结构
# 对接前端：Axios 拦截器或 try-catch 中的 error.response.data.detail
# ----------------------------------------------------------------------------------
class ErrorResponse(BaseModel):
    detail: str

# ----------------------------------------------------------------------------------
# 登录响应 (LoginResponse)
# 作用：登录成功后返回的 Token 信息
# 对接前端：Login.vue 接收到响应后，将 access_token 存入 localStorage
# ----------------------------------------------------------------------------------
class LoginResponse(BaseModel):
    access_token: str # JWT 令牌字符串
    token_type: str   # 令牌类型 (通常为 "bearer")
    user: Dict[str, Any] # 用户信息摘要 (用于前端显示用户昵称等)
