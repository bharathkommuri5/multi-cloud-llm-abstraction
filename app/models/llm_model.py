from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    provider_id = Column(Integer, ForeignKey("providers.id"))
    provider = relationship("Provider")

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
