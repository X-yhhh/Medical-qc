# F:\Medical\medical-qc\app\models\response.py
from pydantic import BaseModel
from typing import List, Optional

class QualityItem(BaseModel):
    item: str
    description: str
    status: str  # "合格" / "不合格" / "检出出血"
    confidence: Optional[float] = None  # 仅AI任务需要

class QualityResponse(BaseModel):
    task: str
    status: str = "success"
    duration_ms: int
    results: List[QualityItem]

class ErrorResponse(BaseModel):
    detail: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict