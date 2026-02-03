# app/models/hemorrhage_record.py
# ----------------------------------------------------------------------------------
# 数据库模型：脑出血检测记录 (HemorrhageRecord)
# 作用：定义 hemorrhage_records 表结构，存储 AI 脑出血检测的历史记录。
# 关联表：User
# ----------------------------------------------------------------------------------

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class HemorrhageRecord(Base):
    """
    脑出血检测记录模型类
    映射表名: hemorrhage_records
    """
    __tablename__ = "hemorrhage_records"

    # 主键 ID
    id = Column(Integer, primary_key=True, index=True)
    
    # 关联操作用户 ID
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # 患者与检查信息 (可选，可从 DICOM 提取或手动输入)
    patient_name = Column(String(100), nullable=True) # 患者姓名
    exam_id = Column(String(100), nullable=True)      # 检查号/流水号
    
    # 影像文件路径 (存储在服务器上的相对路径)
    image_path = Column(String(500), nullable=False)
    
    # -------------------
    # AI 分析结果
    # -------------------
    prediction = Column(String(50), nullable=False)       # 预测结论："出血" 或 "未出血"
    confidence_level = Column(String(50), nullable=True)  # 置信度等级："高", "中", "低"
    
    # 具体概率值 (0.0 - 1.0)
    hemorrhage_probability = Column(Float, nullable=False)    # 出血概率
    no_hemorrhage_probability = Column(Float, nullable=False) # 未出血概率
    
    analysis_duration = Column(Float, nullable=True) # 分析耗时 (毫秒)
    
    # 创建时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # -------------------
    # 关联关系
    # -------------------
    # 关联执行该检测的用户
    user = relationship("User", back_populates="hemorrhage_records")
