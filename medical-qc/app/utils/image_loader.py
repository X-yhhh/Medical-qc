# app/utils/image_loader.py
# ----------------------------------------------------------------------------------
# 图像加载与预处理 (Image Loader)
# 作用：专门用于 AI 模型的图像预处理，将图片转换为 PyTorch Tensor。
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
    加载图像并转换为模型输入张量。
    流程:
    1. 打开图片并转为灰度 (L)
    2. Resize 到 224x224 (ResNet 标准输入)
    3. ToTensor (归一化到 0-1)
    """
    image = Image.open(file_path).convert('L')  # 转灰度
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),  # 自动转为 [0,1]
        # ⚠️ 注意：此处未进行 Normalize，需确保与训练时预处理一致
    ])
    
    tensor = transform(image)
    return tensor.unsqueeze(0)  # 添加 batch 维度 (C, H, W) -> (B, C, H, W)
