"""
User model for authentication and authorization
"""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, DateTime, Boolean, JSON
from .guid_type import GUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """User model for authentication"""

    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)

    # Metadata
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(String(50), default="0")
    metainfo = Column(JSON, nullable=False, default=dict)

    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class RefreshToken(BaseModel):
    """Refresh token model for token rotation"""

    __tablename__ = "refresh_tokens"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", backref="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
