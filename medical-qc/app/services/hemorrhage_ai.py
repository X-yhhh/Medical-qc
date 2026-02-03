# app/services/hemorrhage_ai.py
# ----------------------------------------------------------------------------------
# AI 脑出血检测服务 (Hemorrhage AI Service)
# 作用：定义 PyTorch CNN 模型结构，加载预训练模型，并提供图像推理接口。
# 对接 API：app.api.v1.quality
# ----------------------------------------------------------------------------------

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
import os
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# 模型定义 (CNN)
# 作用：简单的卷积神经网络，用于二分类（出血/未出血）。
# 结构：4个卷积块 (Conv-BN-ReLU-Conv-BN-ReLU-Pool-Dropout) -> 全连接层
# ======================
class Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 提取基础特征
            nn.Conv2d(1, 32, kernel_size=3, padding=1), # Input: (224, 224)
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (112, 112)
            nn.Dropout2d(0.1),

            # Block 2: 提取中层特征
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (56, 56)
            nn.Dropout2d(0.1),

            # Block 3: 提取高层特征
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (28, 28)
            nn.Dropout2d(0.1),

            # Block 4: 进一步抽象
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (14, 14)
            nn.Dropout2d(0.1),

            # Global Average Pooling: 降维
            nn.AdaptiveAvgPool2d((1, 1)), # Output: (1, 1)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(64, 2) # 输出层：2个类别 (未出血, 出血)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

# ======================
# 全局配置与模型加载
# ======================
MODEL_PATH = "models/hemorrhage_model_best.pth"
IMAGE_SIZE = (224, 224)

# 设备选择
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    logger.info(f"✅ CUDA可用，使用GPU: {torch.cuda.get_device_name(0)}")
else:
    DEVICE = torch.device("cpu")
    logger.warning("⚠️ CUDA不可用，回退到CPU")

# 预处理管道 (必须与训练时一致)
transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# 全局模型实例
_model_instance = None

def get_model():
    """单例模式获取模型实例"""
    global _model_instance
    if _model_instance is None:
        _model_instance = Classifier().to(DEVICE)
        # 尝试加载权重，如果不存在则使用随机权重(仅供测试)
        if os.path.exists(MODEL_PATH):
            try:
                state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
                _model_instance.load_state_dict(state_dict)
                logger.info(f"✅ 成功加载模型权重: {MODEL_PATH}")
            except Exception as e:
                logger.error(f"❌ 加载模型权重失败: {e}")
        else:
            logger.warning(f"⚠️ 模型权重文件未找到: {MODEL_PATH}，将使用随机初始化模型进行测试")
        _model_instance.eval() # 切换到评估模式
    return _model_instance

# ----------------------------------------------------------------------------------
# 函数：执行检测
# 作用：接收图像路径，预处理，推理，返回概率和结论。
# ----------------------------------------------------------------------------------
def run_hemorrhage_detection(image_path: str):
    """
    运行脑出血检测
    返回: dict 包含预测结果、置信度和概率
    """
    model = get_model()
    
    try:
        # 1. 加载和预处理图像
        image = Image.open(image_path).convert('L') # 灰度图
        input_tensor = transform(image).unsqueeze(0).to(DEVICE)
        
        # 2. 推理
        start_time = time.time()
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            
        # 3. 解析结果
        probs = probabilities.cpu().numpy()[0]
        no_hemorrhage_prob = float(probs[0])
        hemorrhage_prob = float(probs[1])
        
        predicted_class = 1 if hemorrhage_prob > 0.5 else 0
        prediction_label = "出血" if predicted_class == 1 else "未出血"
        
        # 计算置信度等级
        max_prob = max(no_hemorrhage_prob, hemorrhage_prob)
        if max_prob > 0.9:
            confidence = "高"
        elif max_prob > 0.7:
            confidence = "中"
        else:
            confidence = "低"
            
        return {
            "prediction": prediction_label,
            "confidence": confidence,
            "probability": {
                "hemorrhage": round(hemorrhage_prob, 4),
                "no_hemorrhage": round(no_hemorrhage_prob, 4)
            },
            "duration_ms": round((time.time() - start_time) * 1000, 2)
        }
    except Exception as e:
        logger.error(f"推理过程出错: {e}")
        raise e
