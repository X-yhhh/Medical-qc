# app/services/quality_service.py
import torch
import os
from typing import Optional

# 全局变量，初始为 None
_model: Optional[torch.nn.Module] = None
_model_loaded = False
_model_error: Optional[str] = None


def get_model():
    """
    懒加载模型：首次调用时加载，之后复用
    如果加载失败，记录错误但不抛出（由调用方处理）
    """
    global _model, _model_loaded, _model_error

    if _model_loaded:
        return _model, _model_error

    try:
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "models", "hemorrhage_model.pth"
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        print("正在加载脑出血检测模型...")
        # 自动选择设备：有 CUDA 用 GPU，否则用 CPU
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = torch.load(model_path, map_location=device)
        model.eval()
        model.to(device)  # 确保模型在正确设备上

        _model = model
        _model_error = None
        print(f"✅ 模型加载成功！运行设备: {device}")

    except Exception as e:
        error_msg = f"模型加载失败: {str(e)}"
        print(f"❌ {error_msg}")
        _model_error = error_msg
        _model = None

    _model_loaded = True
    return _model, _model_error


def detect_hemorrhage(image_path: str):
    """
    脑出血检测主函数
    即使模型加载失败，也返回明确错误信息，不中断服务
    """
    model, error = get_model()

    if error:
        # 返回结构化错误，前端可识别
        return {
            "success": False,
            "error": error,
            "message": "模型未就绪，请联系管理员"
        }

    if model is None:
        return {
            "success": False,
            "error": "模型加载异常",
            "message": "模型未初始化"
        }

    # TODO: 实际推理逻辑（这里模拟）
    try:
        # 假设你有图像预处理和推理代码
        result = {
            "success": True,
            "has_hemorrhage": False,
            "confidence": 0.95,
            "bbox": [100, 100, 200, 200],
            "device": str(next(model.parameters()).device)  # 显示实际运行设备
        }
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"推理出错: {str(e)}",
            "message": "检测过程中发生错误"
        }