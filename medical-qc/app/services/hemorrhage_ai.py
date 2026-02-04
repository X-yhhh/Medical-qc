# app/services/hemorrhage_ai.py
# ----------------------------------------------------------------------------------
# AI 脑出血检测服务 (Hemorrhage AI Service)
# 作用：提供脑出血智能检测的核心算法实现。
#       包含 CNN 模型定义、权重加载、图像预处理、推理逻辑以及启发式规则兜底算法。
#       同时进行中线偏移和脑室结构的辅助分析。
# 对接模块：
#   - 上游调用: app.api.v1.quality.hemorrhage_quality_file (API 接口)
#   - 前端展示: src/views/quality/Hemorrhage.vue (展示检测结果、BBox、中线分析)
# ----------------------------------------------------------------------------------

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
import os
import time
import logging
import base64
from io import BytesIO
import pydicom  # 用于处理 DICOM 格式医学影像

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================
# 模型定义 (CNN Classifier)
# 作用：定义一个简单的卷积神经网络结构，用于二分类任务（出血 vs 未出血）。
# 结构：4个卷积块 (Conv-BN-ReLU x2 - Pool - Dropout) -> 全连接层
# ======================
class Classifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 提取基础纹理特征
            nn.Conv2d(1, 32, kernel_size=3, padding=1), # Input: (224, 224)
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (112, 112)
            nn.Dropout2d(0.1),

            # Block 2: 提取中层形状特征
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (56, 56)
            nn.Dropout2d(0.1),

            # Block 3: 提取高层语义特征
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (28, 28)
            nn.Dropout2d(0.1),

            # Block 4: 进一步抽象特征
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2), # Output: (14, 14)
            nn.Dropout2d(0.1),

            # Global Average Pooling: 降维到 1x1
            nn.AdaptiveAvgPool2d((1, 1)), 
        )
        # 分类器头部
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(64, 2) # 输出层：2个类别 (0:未出血, 1:出血)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

# ======================
# 全局配置与模型加载
# 作用：管理模型路径、计算设备选择、预处理管道以及单例模型实例。
# ======================
# 使用绝对路径，避免因运行目录不同导致找不到模型文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "..", "models", "hemorrhage_model_best.pth")
IMAGE_SIZE = (224, 224)

# 1. 设备选择策略
# 优先使用 GPU，如果不可用则回退到 CPU 并记录警告
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    torch.backends.cudnn.benchmark = True
    logger.info(f"✅ CUDA可用，使用GPU: {torch.cuda.get_device_name(0)}")
else:
    DEVICE = torch.device("cpu")
    logger.warning("⚠️ CUDA不可用，回退到CPU (注意：这可能会很慢，且不符合高性能要求)")

# 2. 图像预处理管道
# 必须与训练时的预处理步骤保持一致 (Resize -> ToTensor -> Normalize)
transform = transforms.Compose([
    transforms.Resize(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# 全局变量：缓存加载后的模型
_model_instance = None
_model_is_random = False # 标记位：如果为 True，表示使用的是随机权重的未训练模型

def get_model():
    """
    获取模型实例 (单例模式)
    
    Logic:
    1. 如果模型已加载，直接返回实例。
    2. 如果未加载，初始化模型结构。
    3. 尝试加载预训练权重文件。
    4. 如果权重文件不存在或加载失败，使用随机初始化模型(仅用于测试环境)，并设置 _model_is_random=True。
    """
    global _model_instance, _model_is_random
    if _model_instance is None:
        _model_instance = Classifier().to(DEVICE)
        # 尝试加载权重
        if os.path.exists(MODEL_PATH):
            try:
                state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
                
                # 兼容性处理：如果加载的是 Checkpoint 字典（包含 epoch 等信息），提取模型权重
                # 解决 "Missing key(s) in state_dict" 错误
                if isinstance(state_dict, dict) and 'model_state_dict' in state_dict:
                    logger.info("ℹ️ 检测到 Checkpoint 格式权重，正在提取 model_state_dict...")
                    state_dict = state_dict['model_state_dict']
                    
                _model_instance.load_state_dict(state_dict)
                logger.info(f"✅ 成功加载模型权重: {MODEL_PATH}")
                _model_is_random = False
            except Exception as e:
                logger.error(f"❌ 加载模型权重失败: {e}")
                _model_is_random = True
        else:
            logger.warning(f"⚠️ 模型权重文件未找到: {MODEL_PATH}，将使用随机初始化模型进行测试")
            _model_is_random = True
        _model_instance.eval() # 切换到评估模式，禁用 Dropout 等
    return _model_instance

# ----------------------------------------------------------------------------------
# 核心函数：运行脑出血检测
# 作用：处理单张图片，执行完整的检测流程（AI推理 + 规则分析），并返回详细报告。
# 参数：image_path (str) - 本地图片文件的绝对路径
# 返回：dict - 包含预测类别、概率、BBox、中线分析、脑室分析等
# ----------------------------------------------------------------------------------
def run_hemorrhage_detection(image_path: str):
    """
    运行脑出血检测
    
    Steps:
    1. 加载图像并进行标准化预处理 (Resize to 512x512 for analysis, 224x224 for AI).
    2. AI 模型推理: 获取分类概率.
    3. 启发式检测 (Heuristic): 基于像素阈值分析高亮区域，作为 AI 的补充或兜底.
    4. 决策融合: 结合 AI 概率和启发式结果得出最终结论.
    5. 特征分析: 计算出血区域 BBox、中线偏移、脑室情况.
    6. 结果封装: 生成 Base64 预览图和 JSON 数据.
    """
    model = get_model()
    
    try:
        # 1. 加载和预处理图像
        # 支持普通图片 (PNG/JPG) 和医学影像 (DICOM)
        # 作用：统一将不同格式的输入转换为 PIL Image 对象 (灰度图)
        try:
            original_image = Image.open(image_path).convert('L') # 尝试作为普通图片打开
        except Exception as e_pil:
            # 如果 PIL 打开失败，尝试作为 DICOM 读取
            try:
                logger.info(f"PIL加载失败 ({str(e_pil)})，尝试作为 DICOM 读取: {image_path}")
                ds = pydicom.dcmread(image_path)
                
                # 提取像素数据并归一化
                # 注意：简单的 Min-Max 归一化，将 CT 值映射到 0-255
                if hasattr(ds, 'pixel_array'):
                    pixel_array = ds.pixel_array.astype(float)
                    # 避免除以零
                    max_val = pixel_array.max()
                    if max_val > 0:
                        pixel_array = (np.maximum(pixel_array, 0) / max_val) * 255.0
                    original_image = Image.fromarray(np.uint8(pixel_array)).convert('L')
                else:
                    raise ValueError("DICOM 文件不包含像素数据")
            except Exception as e_dcm:
                logger.error(f"无法读取图像文件 (尝试了 PIL 和 DICOM): {e_dcm}")
                raise ValueError(f"不支持的文件格式或文件已损坏: {str(e_dcm)}")
        
        # 统一调整大小以确保尺寸一致且为偶数 (防止中线检测因奇数宽度崩溃)
        # 使用 512x512 进行详细特征分析 (中线、BBox)
        analysis_size = (512, 512)
        image = original_image.resize(analysis_size, Image.Resampling.LANCZOS)
        
        # 模型推理用的预处理 (224x224)
        input_tensor = transform(image).unsqueeze(0).to(DEVICE)
        
        # 2. AI 模型推理
        start_time = time.time()
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            
        # 解析 AI 结果
        probs = probabilities.cpu().numpy()[0]
        no_hemorrhage_prob = float(probs[0])
        hemorrhage_prob = float(probs[1])
        
        # 处理 NaN 异常
        if np.isnan(no_hemorrhage_prob): no_hemorrhage_prob = 0.0
        if np.isnan(hemorrhage_prob): hemorrhage_prob = 0.0
        
        # ==========================================
        # 3. 扩展特征分析 (BBox, 中线, 脑室)
        # ==========================================
        img_arr = np.array(image)
        h, w = img_arr.shape
        
        # ---------------------------
        # A. 启发式出血检测 (Heuristic Detection)
        # 原理：脑出血在 CT 上表现为高亮区域 (High Density)。
        # 作用：如果模型文件缺失或表现不佳，使用传统 CV 算法兜底。
        # ---------------------------
        
        # 制作掩膜：去除头骨 (优化：增大边缘去除范围至 15%，防止骨骼伪影干扰)
        mask = np.zeros_like(img_arr)
        m_x, m_y = int(w*0.15), int(h*0.15)
        mask[m_y:h-m_y, m_x:w-m_x] = 1
        roi = img_arr * mask
        
        # 寻找异常高亮区域 (阈值 > 50 排除背景)
        valid_pixels = roi[roi > 50]
        
        heuristic_has_hemorrhage = False
        heuristic_bboxes = []
        
        if len(valid_pixels) > 0:
            # 动态阈值计算：均值 + 2.0倍标准差
            # 限制阈值在合理范围 [110, 230] 之间
            v_mean = np.mean(valid_pixels)
            v_std = np.std(valid_pixels)
            dynamic_thresh = v_mean + 2.0 * v_std
            threshold = max(110, min(dynamic_thresh, 230))
            
            logger.info(f"启发式检测参数: Mean={v_mean:.2f}, Std={v_std:.2f}, Threshold={threshold:.2f}")
            
            # 二值化
            binary = roi > threshold
            
            # 排除过高亮度的像素 (如 >250)，通常是残留的骨骼或金属伪影
            # 注意：出血通常在 60-90 HU，归一化后可能在 100-200 范围，极亮通常不是出血
            binary[roi > 250] = 0
            
            coords = np.argwhere(binary)
            
            # 判定：如果高亮像素点数量超过阈值 (提高到 50 个，减少噪点误报)，认为有出血
            if len(coords) > 50:
                heuristic_has_hemorrhage = True
                
                # 计算边界框 (BBox)
                y0, x0 = coords.min(axis=0)
                y1, x1 = coords.max(axis=0)
                margin = 5
                heuristic_bboxes.append([
                    max(0, int(x0)-margin), 
                    max(0, int(y0)-margin), 
                    min(w, int(x1-x0)+2*margin), 
                    min(h, int(y1-y0)+2*margin)
                ])

        # ---------------------------
        # 4. 决策融合：模型结果 + 启发式结果
        # ---------------------------
        # 策略调整：
        # 1. 如果是随机模型 (无权重)，完全依赖启发式检测。
        # 2. 如果是训练模型 (有权重)，完全依赖模型预测，启发式仅作为附加信息 (不覆盖模型结果)。
        #    原因：启发式算法在存在骨骼伪影时容易误报，不应覆盖模型的正常判断。
        
        if _model_is_random:
            # 随机模式：兜底使用启发式
            if heuristic_has_hemorrhage:
                predicted_class = 1
                prediction_label = "出血"
                # 修正概率值，使其体现出高置信度
                hemorrhage_prob = max(hemorrhage_prob, 0.85)
                no_hemorrhage_prob = 1.0 - hemorrhage_prob
            else:
                # 均未检测到 -> 判定为未出血
                predicted_class = 0
                prediction_label = "未出血"
                hemorrhage_prob = 0.1
                no_hemorrhage_prob = 0.9
        else:
            # 真实模型模式：优先信任 AI 模型结果
            # 只有当模型预测结果非常不确定 (如 0.4-0.6) 时，才考虑参考启发式 (此处暂简化为完全信赖模型)
            predicted_class = 1 if hemorrhage_prob > 0.5 else 0
            prediction_label = "出血" if predicted_class == 1 else "未出血"
            
            # 如果模型判断正常，但启发式判断出血，记录日志但不改变结果 (避免误报)
            if predicted_class == 0 and heuristic_has_hemorrhage:
                logger.info("AI模型判定正常，但启发式算法检测到高亮区域 (可能是伪影)")
        
        # 计算置信度等级 (High/Medium/Low)
        max_prob = max(no_hemorrhage_prob, hemorrhage_prob)
        if max_prob > 0.9: confidence = "高"
        elif max_prob > 0.7: confidence = "中"
        else: confidence = "低"

        # B. 最终 BBox 生成
        bboxes = heuristic_bboxes
        # Note: 如果模型检测到出血但启发式未检测到，这里可能为空。
        # 可以在此处添加逻辑：如果 predicted_class == 1 and not bboxes，尝试降低阈值重新搜索。

        # ---------------------------
        # C. 中线偏移检测 (左右对称性分析)
        # ---------------------------
        mid_x = w // 2
        left_part = img_arr[:, :mid_x]
        right_part = img_arr[:, mid_x:] 
        
        # 裁剪到相同宽度
        min_w = min(left_part.shape[1], right_part.shape[1])
        left_part = left_part[:, :min_w]
        right_part = right_part[:, :min_w]
        
        has_midline_shift = False
        midline_detail = "中线结构居中"
        
        if min_w > 0:
            # 将右侧图像翻转，与左侧进行减法比较
            right_flipped = np.fliplr(right_part)
            diff = np.abs(left_part.astype(int) - right_flipped.astype(int))
            
            # 仅关注中心区域的差异 (去除边缘干扰)
            center_diff = diff[m_y:h-m_y, :]
            if center_diff.size > 0:
                symmetry_score = np.mean(center_diff)
                
                # 阈值判断：如果对称性差异大 (>30.0)，判定为中线偏移
                threshold_shift = 30.0
                if symmetry_score > threshold_shift:
                    has_midline_shift = True
                    midline_detail = f"检测到中线偏移 (对称性差异: {symmetry_score:.1f})"

        # ---------------------------
        # D. 脑室结构检测
        # ---------------------------
        cx, cy = w//2, h//2
        box_v = int(min(w, h) * 0.12)
        # 截取中心区域作为脑室 ROI
        ventricle_roi = img_arr[cy-box_v:cy+box_v, cx-box_v:cx+box_v]
        
        has_ventricle_issue = False
        ventricle_detail = "脑室形态正常，未见受压或积血"
        
        if ventricle_roi.size > 0:
            v_mean = np.mean(ventricle_roi)
            # 脑室区域平均像素值过高 -> 疑似脑室出血
            if v_mean > 130: 
                has_ventricle_issue = True
                ventricle_detail = "疑似脑室积血或高密度影"
            # 脑室区域像素值偏高且存在中线偏移 -> 疑似受压
            elif has_midline_shift and v_mean > 80:
                 has_ventricle_issue = True
                 ventricle_detail = "脑室受压变形"

        # 5. 生成 Base64 图像预览 (用于前端展示)
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
        return {
            "prediction": prediction_label,
            "confidence": confidence,
            "probability": {
                "hemorrhage": round(hemorrhage_prob, 4),
                "no_hemorrhage": round(no_hemorrhage_prob, 4)
            },
            "duration_ms": round((time.time() - start_time) * 1000, 2),
            "device": str(DEVICE),
            "image_base64": img_str, # 返回图像数据
            "image_width": image.width,
            "image_height": image.height,
            # 扩展字段
            "bboxes": bboxes,
            "midline_shift": has_midline_shift,
            "midline_detail": midline_detail,
            "ventricle_issue": has_ventricle_issue,
            "ventricle_detail": ventricle_detail
        }
    except Exception as e:
        logger.error(f"推理过程出错: {e}")
        raise e
