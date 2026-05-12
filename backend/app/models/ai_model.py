"""
AI Model configuration model
"""
import uuid
from sqlalchemy import Column, String, Boolean, JSON, Text
from .guid_type import GUID
from .base import BaseModel


class AIModel(BaseModel):
    """Configurable AI model for generation pipeline"""

    __tablename__ = "ai_models"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # llm, wanx, tts, bgm, video
    provider = Column(String(50), nullable=False)  # dashscope, siliconflow, edge_tts, scipy, ffmpeg
    model_name = Column(String(100), nullable=False)
    api_key = Column(Text, nullable=True)
    api_base_url = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    is_builtin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, server_default="false")
    config = Column(JSON, nullable=False, default=dict)

    def __repr__(self):
        return f"<AIModel(id={self.id}, name='{self.name}', category={self.category})>"
