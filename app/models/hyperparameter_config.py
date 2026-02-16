from sqlalchemy import Column, Integer, String, ForeignKey, Integer as IntegerType, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class HyperparameterConfig(Base):
    __tablename__ = "hyperparameter_configs"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Store hyperparameters as JSON for flexibility
    # Example: {"temperature": 0.7, "top_p": 0.9, "frequency_penalty": 0.5}
    parameters = Column(JSON, nullable=False, default={})
    
    description = Column(String, nullable=True)
    is_default = Column(IntegerType, default=False)  # Flag for default config
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete timestamp
    
    # Relationships
    user = relationship("User", back_populates="hyperparameter_configs")
    model = relationship("LLMModel")
