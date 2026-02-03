# app/utils/image_loader.py
# ----------------------------------------------------------------------------------
# 图像加载与预处理 (Image Loader)
# 作用：专门用于 AI 模型的图像预处理，将图片转换为 PyTorch Tensor。
# 对接前端：
#   - 不直接对接。
#   - 接收前端上传并保存到服务器的图片路径，处理后送入 AI 模型。
# ----------------------------------------------------------------------------------

import torch
from PIL import Image
from torchvision import transforms

# ----------------------------------------------------------------------------------
# 函数：加载图像并转换为 Tensor (load_image_to_tensor)
# 作用：读取图像 -> 转灰度 -> 调整大小 -> 转 Tensor -> 增加 Batch 维度。
# 参数：file_path - 图像文件路径
# 返回：torch.Tensor (Shape: [1, 1, 224, 224], Range: [0.0, 1.0])
# ----------------------------------------------------------------------------------
def load_image_to_tensor(file_path: str) -> torch.Tensor:
    """
    加载图像并转换为 AI 模型所需的输入张量。
    
    流程:
    1. 打开图片并转为灰度 (L模式, 单通道) - 适应脑出血 CT 特性
    2. Resize 到 224x224 (ResNet/VGG 等标准网络输入尺寸)
    3. ToTensor (归一化到 0-1, 转换为 FloatTensor)
    4. Unsqueeze (增加 Batch 维度，适配模型输入)
    """
    image = Image.open(file_path).convert('L')  # 转灰度
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),  # 自动转为 [0,1]
        # ⚠️ 注意：此处未进行 Normalize (如 ImageNet 均值方差标准化)，
        # 需确保与模型训练时的预处理步骤完全一致。
    ])
    
    tensor = transform(image)
    return tensor.unsqueeze(0)  # 添加 batch 维度 (C, H, W) -> (B, C, H, W)
