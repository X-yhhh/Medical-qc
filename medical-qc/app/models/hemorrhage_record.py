# app/models/hemorrhage_record.py
# ----------------------------------------------------------------------------------
# 数据库模型：脑出血检测记录 (HemorrhageRecord)
# 作用：定义 hemorrhage_records 表结构，存储 AI 脑出血检测的历史记录。
# 对接前端：
#   - views/quality/Hemorrhage.vue (用于展示检测结果和历史记录)
#   - 对应 API: /api/v1/quality/predict_hemorrhage (写入记录)
# ----------------------------------------------------------------------------------

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class HemorrhageRecord(Base):
    """
    脑出血检测记录模型类
    映射表名: hemorrhage_records
    
    作用：
        持久化存储每次脑出血 AI 检测的结果，包括患者信息、影像路径和 AI 预测概率。
    """
    __tablename__ = "hemorrhage_records"

    # 主键 ID
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联操作用户 ID (外键关联 users 表)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # 患者与检查信息 (可选，可从 DICOM 提取或手动输入)
    # 对接前端：上传时若解析出 DICOM Tag，则存入此处
    patient_name = Column(String(100), nullable=True) # 患者姓名
    exam_id = Column(String(100), nullable=True)      # 检查号/流水号
    
    # 影像文件路径 (存储在服务器上的相对路径)
    # 示例: uploads/2023/10/01/uuid.jpg
    image_path = Column(String(500), nullable=False)
    
    # -------------------
    # AI 分析结果
    # -------------------
    # 预测结论："出血" 或 "未出血"
    # 对接前端：Hemorrhage.vue 结果面板的主标题
    prediction = Column(String(50), nullable=False)
    
    # 置信度等级："高", "中", "低"
    # 对接前端：Hemorrhage.vue 结果面板的置信度标签颜色 (Success/Warning/Danger)
    confidence_level = Column(String(50), nullable=True)
    
    # 具体概率值 (0.0 - 1.0)
    # 对接前端：Hemorrhage.vue 结果详情中的概率进度条
    hemorrhage_probability = Column(Float, nullable=False)    # 出血概率
    no_hemorrhage_probability = Column(Float, nullable=False) # 未出血概率
    
    # 分析耗时 (毫秒)
    analysis_duration = Column(Float, nullable=True)
    
    # 创建时间 (自动记录)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # -------------------
    # 关联关系
    # -------------------
    # 关联执行该检测的用户
    user = relationship("User", back_populates="hemorrhage_records")
