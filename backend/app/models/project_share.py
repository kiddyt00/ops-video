"""
Project sharing model
"""
import uuid
from enum import Enum
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .guid_type import GUID
from .base import BaseModel


class SharePermission(str, Enum):
    """Permission levels for shared projects"""
    VIEW = "view"
    EDIT = "edit"


class ProjectShare(BaseModel):
    """Represents a project shared from one user to another"""

    __tablename__ = "project_shares"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shared_with_user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission = Column(
        SQLEnum(SharePermission),
        default=SharePermission.VIEW,
        nullable=False,
    )

    # Relationships
    project = relationship("Project")
    owner = relationship("User", foreign_keys=[owner_id])
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])

    def __repr__(self):
        return f"<ProjectShare(id={self.id}, project={self.project_id}, shared_to={self.shared_with_user_id})>"
