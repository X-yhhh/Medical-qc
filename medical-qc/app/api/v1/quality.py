# app/api/v1/quality.py
# ----------------------------------------------------------------------------------
# 质控模块 API (Quality Control API)
# 作用：处理影像上传和 AI 质控检测请求，特别是脑出血检测功能。
#       作为前后端交互的桥梁，接收前端图片，调用 AI 服务，返回 JSON 结果。
# 对接模块：
#   - 后端服务: app.services.hemorrhage_ai.run_hemorrhage_detection
#   - 前端调用: src/api/quality.js (predictHemorrhage)
#   - 前端视图: src/views/quality/Hemorrhage.vue
# ----------------------------------------------------------------------------------

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.database import get_db
from app.models.user import User
from sqlalchemy import select
import tempfile
import os
import base64
from io import BytesIO
from PIL import Image
from pydantic import BaseModel
from typing import Optional
from app.services.hemorrhage_ai import run_hemorrhage_detection

# ----------------------------------------------------------------------------------
# OAuth2 认证方案定义
# 作用：指定获取 Token 的 URL 路径，用于 Swagger UI 和依赖注入
# ----------------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ----------------------------------------------------------------------------------
# 依赖函数：获取当前用户
# 作用：通过 Access Token 从数据库中验证并获取当前用户信息。
# ----------------------------------------------------------------------------------
async def get_current_user(token: str, db: AsyncSession = Depends(get_db)):
    """
    验证 access_token 是否存在于数据库中
    
    Args:
        token: OAuth2 access token
        db: 数据库会话
        
    Returns:
        str: 用户名 (如果验证通过)
        
    Raises:
        HTTPException(401): 如果 token 无效或用户不存在
    """
    result = await db.execute(select(User).where(User.access_token == token))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="无效凭证")
    return user.username

router = APIRouter()

# ----------------------------------------------------------------------------------
# 数据模型：Base64 图片上传请求体
# 作用：定义前端通过 Base64 字符串上传图片时的参数结构。
# 对接前端: src/views/quality/Hemorrhage.vue (startAnalysisProcess)
# ----------------------------------------------------------------------------------
class HemorrhageBase64Request(BaseModel):
    image_base64: str
    filename: Optional[str] = "unknown.png"

# ----------------------------------------------------------------------------------
# 接口：脑出血检测 (文件流)
# URL: POST /api/v1/quality/hemorrhage
# 作用：接收 multipart/form-data 格式的图片文件，保存为临时文件后调用 AI 模型检测。
# 对接前端: 
#   - src/api/quality.js (predictHemorrhage - 备用模式)
#   - src/views/quality/Hemorrhage.vue
# ----------------------------------------------------------------------------------
@router.post("/hemorrhage")
async def hemorrhage_quality_file(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    脑出血检测接口（文件上传方式）
    
    Process:
    1. 验证文件类型 (必须为 image/*)
    2. 保存上传文件到临时目录
    3. 验证用户身份
    4. 调用 run_hemorrhage_detection 执行 AI 检测
    5. 返回检测结果 (JSON)
    6. 清理临时文件
    """
    # 1. 验证文件类型
    # 允许 image/* (PNG/JPG) 和 application/dicom (DICOM) 以及部分浏览器默认的 octet-stream
    valid_types = ["image/", "application/dicom", "application/octet-stream"]
    if file.content_type:
        is_valid = any(file.content_type.startswith(t) for t in valid_types)
        if not is_valid:
             # 为了更好的兼容性，如果是未知类型但扩展名正确也允许 (虽不仅严谨但实用)
             filename_lower = file.filename.lower() if file.filename else ""
             if not (filename_lower.endswith(".dcm") or filename_lower.endswith(".dicom")):
                raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}，仅支持 PNG/JPG/DICOM")

    # 2. 保存到临时文件
    # 尽量保留原始扩展名以帮助库识别文件格式
    suffix = ".png"
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in ['.dcm', '.dicom', '.png', '.jpg', '.jpeg']:
            suffix = ext
            
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 3. 验证用户身份
        username = await get_current_user(token, db)
        
        # 4. 调用 AI 服务进行检测
        # 直接返回 run_hemorrhage_detection 的结果 (包含检测结果和 Base64 标注图)
        result = run_hemorrhage_detection(tmp_path)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI检测失败: {str(e)}")
    finally:
        # 5. 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ----------------------------------------------------------------------------------
# 接口：脑出血检测 (Base64)
# URL: POST /api/v1/quality/hemorrhage/base64
# 作用：接收 Base64 编码的图片数据，解码后保存为临时文件并调用 AI 模型检测。
# 对接前端: 
#   - src/api/quality.js (predictHemorrhage - 默认模式)
#   - src/views/quality/Hemorrhage.vue (startAnalysisProcess)
# ----------------------------------------------------------------------------------
@router.post("/hemorrhage/base64")
async def hemorrhage_quality_base64(
    request: HemorrhageBase64Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    脑出血检测接口（Base64 方式）
    
    Process:
    1. 解码 Base64 字符串为图像对象
    2. 保存图像到临时目录
    3. 验证用户身份
    4. 调用 run_hemorrhage_detection 执行 AI 检测
    5. 返回检测结果
    6. 清理临时文件
    """
    try:
        # 1. 解码 Base64 字符串为图像对象
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(BytesIO(image_data)).convert("L") # 转为灰度图处理
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图像解码失败: {str(e)}")

    # 2. 保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image.save(tmp.name)
        tmp_path = tmp.name

    try:
        # 3. 验证用户身份
        username = await get_current_user(token, db)
        
        # 4. 调用 AI 服务进行检测
        result = run_hemorrhage_detection(tmp_path)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI检测失败: {str(e)}")
    finally:
        # 5. 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
