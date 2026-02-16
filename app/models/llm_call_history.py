from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class LLMCallHistory(Base):
    __tablename__ = "llm_call_history"

    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=False)
    
    # Request details
    prompt = Column(String, nullable=False)
    response = Column(String, nullable=False)
    
    # Parameters used for this call
    parameters_used = Column(JSON, nullable=True)  # temperature, max_tokens, etc.
    
    # Performance metrics
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Cost tracking
    cost = Column(Float, nullable=True)
    
    # Status
    status = Column(String, default="success")  # success, error, timeout
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete timestamp
    
    # Relationships
    user = relationship("User", back_populates="call_history")
    provider = relationship("Provider")
    model = relationship("LLMModel")
