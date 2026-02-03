# app/services/quality_service.py
# ----------------------------------------------------------------------------------
# 质控服务模块 (Quality Service - Legacy/Fallback)
# 作用：提供一个基础的 AI 模型加载和检测服务。
# 注意：目前主要使用的是 hemorrhage_ai.py，本文件可能作为备用或旧版本实现保留。
# 对接模块：
#   - 潜在调用方: 其他旧版 API 或测试脚本
# ----------------------------------------------------------------------------------

import torch
import os
from typing import Optional

# 全局变量：用于缓存加载后的模型实例
_model: Optional[torch.nn.Module] = None
_model_loaded = False
_model_error: Optional[str] = None


# ----------------------------------------------------------------------------------
# 函数：获取/加载模型 (get_model)
# 作用：单例模式加载 PyTorch 模型。首次调用时加载文件，后续直接返回缓存实例。
# 异常处理：加载失败时记录错误信息，确保服务不崩溃。
# ----------------------------------------------------------------------------------
def get_model():
    """
    懒加载模型：首次调用时加载，之后复用
    如果加载失败，记录错误但不抛出（由调用方处理）
    """
    global _model, _model_loaded, _model_error

    # 如果已尝试加载过，直接返回结果（无论成功失败）
    if _model_loaded:
        return _model, _model_error

    try:
        # 构建模型文件绝对路径
        model_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "models", "hemorrhage_model.pth"
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")

        print("正在加载脑出血检测模型...")
        # 自动选择计算设备：优先使用 GPU (CUDA)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载模型权重
        model = torch.load(model_path, map_location=device)
        model.eval()      # 设置为评估模式
        model.to(device)  # 移动到指定设备

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


# ----------------------------------------------------------------------------------
# 函数：执行脑出血检测 (detect_hemorrhage)
# 作用：调用加载的模型对输入图像进行推理。
# 参数：image_path - 待检测图像的路径
# 返回：包含检测结果（是否出血、置信度、BBox）的字典
# ----------------------------------------------------------------------------------
def detect_hemorrhage(image_path: str):
    """
    脑出血检测主函数 (简单版)
    即使模型加载失败，也返回明确错误信息，不中断服务
    """
    # 1. 获取模型实例
    model, error = get_model()

    # 2. 检查模型状态
    if error:
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

    # 3. 执行推理
    try:
        # TODO: 这里应该添加真实的图像预处理 (Transforms) 和 model(input) 调用
        # 目前为模拟返回，用于测试流程
        
        # 模拟返回结果
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
