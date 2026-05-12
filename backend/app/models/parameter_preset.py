"""
Parameter preset model
"""
import uuid
from sqlalchemy import Column, String, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class ParameterPreset(BaseModel):
    """Saved generation parameter template"""

    __tablename__ = "parameter_presets"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    generator_type = Column(String(50), nullable=False, index=True)  # script, storyboard, image, tts, bgm, video_composer
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    is_system = Column(Boolean, nullable=False, default=False)

    # Relationships
    user = relationship("User", backref="parameter_presets")

    def __repr__(self):
        return f"<ParameterPreset(id={self.id}, name='{self.name}', type='{self.generator_type}')>"
