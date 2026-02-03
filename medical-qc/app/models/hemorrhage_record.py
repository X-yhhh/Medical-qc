from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.utils.database import Base

class HemorrhageRecord(Base):
    __tablename__ = "hemorrhage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    
    # Patient / Exam Info (Can be extracted or manually input)
    patient_name = Column(String(100), nullable=True)
    exam_id = Column(String(100), nullable=True)
    
    # Image Info
    image_path = Column(String(500), nullable=False) # Path to stored image
    
    # Analysis Results
    prediction = Column(String(50), nullable=False) # "出血" or "未出血"
    confidence_level = Column(String(50), nullable=True) # "高", "中", "低"
    hemorrhage_probability = Column(Float, nullable=False)
    no_hemorrhage_probability = Column(Float, nullable=False)
    analysis_duration = Column(Float, nullable=True) # in ms
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="hemorrhage_records")
