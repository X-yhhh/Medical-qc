# app/utils/image_loader.py
import torch
from PIL import Image
from torchvision import transforms

def load_image_to_tensor(file_path: str) -> torch.Tensor:
    """
    加载图像并转换为模型输入张量。
    输出形状: [1, 1, 224, 224]
    像素值范围: [0.0, 1.0]
    """
    image = Image.open(file_path).convert('L')  # 转灰度
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),  # 自动转为 [0,1]
        # ⚠️ 删除 Normalize！除非训练时也用了
    ])
    tensor = transform(image)
    return tensor.unsqueeze(0)  # 添加 batch 维度