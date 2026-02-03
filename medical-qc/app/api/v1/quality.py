# app/api/v1/quality.py
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
from app.services.hemorrhage_ai import run_hemorrhage_detection # 确保导入了正确的函数

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str, db: AsyncSession = Depends(get_db)):
    """验证 access_token 是否存在于数据库中"""
    result = await db.execute(select(User).where(User.access_token == token))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="无效凭证")
    return user.username

router = APIRouter()

# 新增：Base64 请求体模型
class HemorrhageBase64Request(BaseModel):
    image_base64: str
    filename: Optional[str] = "unknown.png"

# ======================
# 方式1：原始文件上传（保持兼容）
# ======================
@router.post("/hemorrhage")
async def hemorrhage_quality_file(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """脑出血检测接口（文件上传方式，兼容旧前端）"""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图像文件 (PNG/JPG)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        username = await get_current_user(token, db)
        # 直接返回 run_hemorrhage_detection 的结果
        result = run_hemorrhage_detection(tmp_path)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI检测失败: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ======================
# 方式2：Base64 上传（新前端使用）
# ======================
@router.post("/hemorrhage/base64")
async def hemorrhage_quality_base64(
    request: HemorrhageBase64Request,
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """脑出血检测接口（Base64 方式，新前端使用）"""
    try:
        # 解码 Base64
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(BytesIO(image_data)).convert("L")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图像解码失败: {str(e)}")

    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image.save(tmp.name)
        tmp_path = tmp.name

    try:
        username = await get_current_user(token, db)
        # 直接返回 run_hemorrhage_detection 的结果
        result = run_hemorrhage_detection(tmp_path)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI检测失败: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ======================
# 备用接口（保持原样）
# ======================
@router.post("/detect-hemorrhage")
async def detect_hemorrhage_api(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """备用接口（逻辑同上）"""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图像文件 (PNG/JPG)")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        username = await get_current_user(token, db)
        result = run_hemorrhage_detection(tmp_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI检测失败: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ======================
# 新增接口：匹配前端调用路径
# ======================
import shutil
import uuid
from app.models.hemorrhage_record import HemorrhageRecord

# ======================
# 新增接口：匹配前端调用路径
# ======================
@router.post("/hemorrhage/predict") # 这是您前端需要的路径
async def predict_hemorrhage_new(
    file: UploadFile = File(...),
    patient_name: Optional[str] = Form(None),
    exam_id: Optional[str] = Form(None),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    新的脑出血检测接口，匹配前端调用路径 /api/v1/quality/hemorrhage/predict
    """
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图像文件 (PNG/JPG)")

    # 生成永久文件名
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else "png"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    save_dir = "data/hemorrhage_uploads"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, unique_filename)

    try:
        # 获取当前用户
        result_user = await db.execute(select(User).where(User.access_token == token))
        user = result_user.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="无效凭证")

        # 保存文件
        # 确保文件指针在开头
        await file.seek(0)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 运行检测
        result = run_hemorrhage_detection(save_path)
        if not result["success"]:
             # 如果失败，删除文件
             if os.path.exists(save_path):
                 os.remove(save_path)
             raise HTTPException(status_code=500, detail=f"AI检测失败: {result.get('error', '未知错误')}")
        
        # 保存记录到数据库
        new_record = HemorrhageRecord(
            user_id=user.id,
            image_path=save_path,
            prediction=result["prediction"],
            confidence_level=result["confidence_level"],
            hemorrhage_probability=result["hemorrhage_probability"],
            no_hemorrhage_probability=result["no_hemorrhage_probability"],
            analysis_duration=result["duration"],
            patient_name=patient_name or "Unknown",
            exam_id=exam_id or "Unknown"
        )
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)

        # 返回前端期望的格式
        return {
            "id": new_record.id,
            "prediction": result["prediction"],
            "hemorrhage_probability": result["hemorrhage_probability"],
            "no_hemorrhage_probability": result["no_hemorrhage_probability"],
            "confidence_level": result["confidence_level"],
            "duration": result["duration"],
            "bbox": result.get("bbox"),
            "midline_shift": result.get("midline_shift"),
            "shift_score": result.get("shift_score"),
            "model_name": result.get("model_name"),
            "device": result.get("device", "CPU"),
            "image_width": result.get("image_width"),
            "image_height": result.get("image_height"),
            "image_url": f"/static/hemorrhage/{unique_filename}" # 需要在main.py挂载静态目录
        }
    except HTTPException:
        # 重新抛出 FastAPI 的 HTTPException
        if os.path.exists(save_path): # 发生异常时尝试清理
             try: os.remove(save_path) 
             except: pass
        raise
    except Exception as e:
        if os.path.exists(save_path):
             try: os.remove(save_path) 
             except: pass
        raise HTTPException(status_code=500, detail=f"AI检测失败: {str(e)}")

@router.get("/hemorrhage/history")
async def get_hemorrhage_history(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    limit: int = 20
):
    """获取用户的脑出血检测历史记录"""
    result_user = await db.execute(select(User).where(User.access_token == token))
    user = result_user.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="无效凭证")
    
    query = select(HemorrhageRecord).where(HemorrhageRecord.user_id == user.id).order_by(HemorrhageRecord.created_at.desc()).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()
    
    return records