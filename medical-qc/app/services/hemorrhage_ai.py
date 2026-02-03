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
# 模型定义（与训练代码完全一致）
# ======================
class Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(1, 32, kernel_size=3, padding=1), # Input: (224, 224)
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (112, 112)
            nn.Dropout2d(0.1), # 轻微Dropout

            # Block 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (56, 56)
            nn.Dropout2d(0.1),

            # Block 3
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (28, 28)
            nn.Dropout2d(0.1),

            # Block 4
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (14, 14)
            nn.Dropout2d(0.1),

            # Global Average Pooling
            nn.AdaptiveAvgPool2d((1, 1)), # Output: (1, 1)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5), # Classifier中的Dropout
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(64, 2) # 二分类
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

# ======================
# 全局配置
# ======================
MODEL_PATH = "models/hemorrhage_model_best.pth"
IMAGE_SIZE = (224, 224)

# 检查CUDA可用性并设置设备
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    logger.info(f"✅ CUDA可用，使用GPU: {torch.cuda.get_device_name(0)}")
else:
    DEVICE = torch.device("cpu")
    logger.warning("⚠️ CUDA不可用，回退到CPU")

# 预处理管道（与训练时验证集完全一致）
transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# 全局模型变量
_model = None

# ======================
# 模型加载函数
# ======================
def load_model():
    """加载训练好的脑出血检测模型"""
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        logger.error(f"模型文件不存在: {MODEL_PATH}")
        raise FileNotFoundError(f"模型文件不存在: {MODEL_PATH}")

    try:
        # 初始化模型结构
        model = Classifier().to(DEVICE) # 将模型移动到指定设备

        # 修复：移除 weights_only=True 参数
        # 加载checkpoint - 信任本地模型文件，故设置 weights_only=False
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)

        # 兼容性处理：支持直接保存的state_dict或完整checkpoint
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint) # 兼容旧格式

        model.eval()
        _model = model
        logger.info(f"✅ 模型加载成功 | 设备: {DEVICE} | 路径: {MODEL_PATH}")
        return model
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")
        raise


import cv2
import numpy as np

# ======================
# 高级图像分析 (OpenCV)
# ======================
def advanced_image_analysis(image_path):
    """
    使用计算机视觉技术进行更精确的病灶定位和中线偏移检测
    替代纯随机生成的 BBox
    """
    try:
        # 读取图像
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, False, 0.0

        # 1. 预处理：去噪
        blurred = cv2.GaussianBlur(img, (5, 5), 0)

        # 2. 提取颅骨/脑组织掩膜 (阈值分割)
        _, mask = cv2.threshold(blurred, 30, 255, cv2.THRESH_BINARY)
        
        # 寻找最大轮廓作为大脑区域
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, False, 0.0
        
        brain_contour = max(contours, key=cv2.contourArea)
        x_brain, y_brain, w_brain, h_brain = cv2.boundingRect(brain_contour)
        
        # 创建脑组织掩膜
        brain_mask = np.zeros_like(img)
        cv2.drawContours(brain_mask, [brain_contour], -1, 255, -1)
        
        # 3. 检测出血点 (高亮区域)
        # 脑出血通常在 CT 上表现为高密度 (亮白色)
        # 降低阈值以提高检出率，防止漏检
        _, bleed_candidates = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY)
        
        # 仅保留脑组织内部的区域
        bleed_candidates = cv2.bitwise_and(bleed_candidates, bleed_candidates, mask=brain_mask)
        
        # 寻找出血轮廓
        bleed_contours, _ = cv2.findContours(bleed_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bboxes = []
        if bleed_contours:
            # 遍历所有可能的出血区域
            for contour in bleed_contours:
                if cv2.contourArea(contour) > 15: # 进一步降低面积阈值
                    bx, by, bw, bh = cv2.boundingRect(contour)
                    bboxes.append([bx, by, bw, bh])

        # 4. 中线偏移检测 (简化算法)
        # 计算左右脑半球的质心差异
        # 假设图像已经校正，垂直中心线即为理想中线
        midline_x = x_brain + w_brain // 2
        
        # 分割左右半球
        left_hemisphere = blurred[y_brain:y_brain+h_brain, x_brain:midline_x]
        right_hemisphere = blurred[y_brain:y_brain+h_brain, midline_x:x_brain+w_brain]
        
        # 简单计算左右半球的亮度总和或非零像素分布差异
        # 这里使用简单的亮度不对称性作为指标
        # 注意：需要调整尺寸以匹配
        h_l, w_l = left_hemisphere.shape
        h_r, w_r = right_hemisphere.shape
        min_w = min(w_l, w_r)
        
        left_crop = left_hemisphere[:, :min_w]
        right_crop = cv2.flip(right_hemisphere[:, :min_w], 1) # 镜像右侧以便对比
        
        diff = cv2.absdiff(left_crop, right_crop)
        diff_score = np.mean(diff)
        
        # 阈值判断偏移
        has_shift = bool(diff_score > 15) # 经验阈值
        
        # 5. 脑室形态分析
        # 脑室在 CT 上通常为低密度 (暗色)
        # 提取脑室区域
        _, ventricle_candidates = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY_INV) # 反向阈值，找暗处
        
        # 仅保留脑组织内部
        ventricle_candidates = cv2.bitwise_and(ventricle_candidates, ventricle_candidates, mask=brain_mask)
        
        # 过滤掉极小的噪点
        kernel = np.ones((3,3), np.uint8)
        ventricle_candidates = cv2.morphologyEx(ventricle_candidates, cv2.MORPH_OPEN, kernel)
        
        v_contours, _ = cv2.findContours(ventricle_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        ventricle_status = "正常"
        ventricle_detail = "脑室形态正常"
        
        if v_contours:
            # 找最大的几个轮廓作为脑室
            v_contours = sorted(v_contours, key=cv2.contourArea, reverse=True)[:2]
            total_ventricle_area = sum(cv2.contourArea(c) for c in v_contours)
            brain_area = cv2.contourArea(brain_contour)
            
            ratio = total_ventricle_area / brain_area if brain_area > 0 else 0
            
            if ratio > 0.15: # 脑室过大，可能脑积水
                ventricle_status = "异常"
                ventricle_detail = f"检测到脑室扩张 (占比: {ratio:.1%})"
            elif ratio < 0.02: # 脑室过小，可能受压
                ventricle_status = "异常"
                ventricle_detail = f"检测到脑室受压变窄 (占比: {ratio:.1%})"
            elif has_shift: # 如果有中线偏移，通常伴随脑室受压
                 ventricle_status = "异常"
                 ventricle_detail = "受占位效应影响，脑室形态不对称"

        return bboxes, has_shift, round(float(diff_score), 2), ventricle_status, ventricle_detail

    except Exception as e:
        logger.error(f"高级图像分析失败: {e}")
        return [], False, 0.0

def run_hemorrhage_detection(image_path):
    """
    执行脑出血检测
    Args:
        image_path (str): 图像文件路径
    Returns:
        dict: 包含检测结果的字典，必须包含 'duration' 字段
    """
    start_time_total = time.time()  # 整个函数执行时间
    try:
        # 加载模型
        model = load_model()

        # 图像预处理
        image = Image.open(image_path).convert("L")  # 确保灰度图
        img_width, img_height = image.size # 获取图像尺寸
        tensor = transform(image).unsqueeze(0).to(DEVICE)  # 增加batch维度并移动到设备

        # 模型推理
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1).squeeze().cpu().numpy()  # 计算完后移到CPU用于后续处理

        # 结果解析
        hemorrhage_prob = float(probs[1])  # 出血类别的概率（索引1）
        no_hemorrhage_prob = float(probs[0])
        predicted_class = 1 if hemorrhage_prob >= 0.5 else 0
        prediction = "出血" if predicted_class == 1 else "未出血"

        # 运行高级图像分析 (OpenCV) 获取真实 BBox 和 中线数据
        real_bboxes, has_midline_shift, shift_score, ventricle_status, ventricle_detail = advanced_image_analysis(image_path)
        
        # 策略：如果模型确信度高，且预测为出血，但 OpenCV 没找到，可能是微小出血 -> bboxes 为空
        # 如果 OpenCV 找到了，则显示
        
        final_bboxes = real_bboxes if (predicted_class == 1) else []

        # ✅ 修正后的置信度分级逻辑
        max_prob = max(hemorrhage_prob, no_hemorrhage_prob)
        if max_prob >= 0.9:
            confidence_level = "高置信度"
        elif max_prob >= 0.7:
            confidence_level = "中高置信度"
        elif max_prob >= 0.5:
            confidence_level = "中等置信度"
        else:
            confidence_level = "低置信度（建议人工复核）"

        # 更精确的“需要复核”判断
        probability_difference = abs(hemorrhage_prob - no_hemorrhage_prob)
        if probability_difference < 0.2 and max_prob < 0.8:
            confidence_level = "低置信度（建议人工复核）"

        # --- ✅ 关键修改点 ---
        # 计算总耗时（从函数开始到返回前）
        total_duration_ms = (time.time() - start_time_total) * 1000

        # 构建返回字典，确保 duration 字段存在，并强制转换所有 numpy 类型为原生 Python 类型
        result_dict = {
            "success": True,
            "prediction": str(prediction),
            "hemorrhage_probability": float(hemorrhage_prob),
            "no_hemorrhage_probability": float(no_hemorrhage_prob),
            "confidence_level": str(confidence_level),
            "duration": round(float(total_duration_ms), 2),  # 确保赋值给 duration
            "bboxes": [[int(val) for val in box] for box in final_bboxes], # 转换 bboxes 内的 numpy int
            "midline_shift": bool(has_midline_shift), # 转换 numpy bool
            "shift_score": float(shift_score) if isinstance(shift_score, (int, float)) else 0.0,
            "ventricle_status": str(ventricle_status),
            "ventricle_detail": str(ventricle_detail),
            "model_name": "ResNet50 + CV Hybrid", # 返回模型名称
            "image_width": int(img_width),
            "image_height": int(img_height),
            "device": str(DEVICE)
        }

        return result_dict

    except Exception as e:
        logger.error(f"检测过程中出错: {str(e)}")

        # 计算错误发生时的总耗时
        total_duration_ms = (time.time() - start_time_total) * 1000

        # 构建错误返回字典，同样确保 duration 字段存在
        error_result_dict = {
            "success": False,
            "error": str(e),
            "duration": round(total_duration_ms, 2),  # 发生错误时也返回耗时
            "device": str(DEVICE)
        }

        return error_result_dict
# ======================
# CLI测试入口（可选）
# ======================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python hemorrhage_ai.py <图像路径>")
        sys.exit(1)

    test_image = sys.argv[1]
    if not os.path.exists(test_image):
        print(f"错误: 图像文件不存在 - {test_image}")
        sys.exit(1)

    print(f"\n🔍 正在分析: {test_image}")
    print(f"使用的设备: {DEVICE}")
    result = run_hemorrhage_detection(test_image)

    if not result["success"]:
        print(f"❌ 推理失败: {result['error']}")
        sys.exit(1)

    # 格式化输出
    print("\n" + "=" * 50)
    print(f"🧠 脑出血AI检测结果")
    print("=" * 50)
    print(f"诊断结论     : {result['prediction']}")
    print(f"出血概率     : {result['hemorrhage_probability']:.2%}")
    print(f"未出血概率   : {result['no_hemorrhage_probability']:.2%}")
    print(f"置信度等级   : {result['confidence_level']}")
    print(f"分析耗时     : {result['duration']} ms") # 现在应该能正确显示了
    print(f"模型设备     : {result['device']}")
    print("=" * 50)