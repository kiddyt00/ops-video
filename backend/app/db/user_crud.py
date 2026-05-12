"""
User CRUD operations
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash


class UserCRUD:
    """User CRUD operations"""

    def get(self, db: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Get all users with pagination"""
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user"""
        user = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(
        self,
        db: Session,
        *,
        user_id: UUID,
        obj_in: UserUpdate
    ) -> Optional[User]:
        """Update user"""
        user = self.get(db, user_id=user_id)
        if not user:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)

        # Hash password if provided
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def delete(self, db: Session, user_id: UUID) -> bool:
        """Delete user"""
        user = self.get(db, user_id=user_id)
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    def update_last_login(self, db: Session, user_id: UUID) -> Optional[User]:
        """Update user's last login timestamp"""
        from datetime import datetime, timezone
        user = self.get(db, user_id=user_id)
        if not user:
            return None

        user.last_login_at = datetime.now(timezone.utc)
        user.login_count = str(int(user.login_count) + 1)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def is_admin(self, db: Session, user_id: UUID) -> bool:
        """Check if user is admin"""
        user = self.get(db, user_id=user_id)
        return user is not None and user.role == UserRole.ADMIN


user_crud = UserCRUD()
