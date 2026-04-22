"""
Authentication API routes
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from ...db.session import get_db
from ...db.user_crud import user_crud
from ...core.security import (
    verify_password,
    create_token_pair,
    decode_token,
    create_access_token,
)
from ...schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    UserUpdate,
)
from ..deps_auth import get_current_user, get_current_active_user
from ...models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user

    - **email**: User email (must be unique)
    - **username**: Username (must be unique, 3-100 chars)
    - **password**: Password (min 8 chars)
    - **full_name**: Optional full name
    """
    # Check if email already exists
    if user_crud.get_by_email(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    if user_crud.get_by_username(db, username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = user_crud.create(db, obj_in=user_in)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password

    Returns access token and refresh token
    """
    # Find user by email
    user = user_crud.get_by_email(db, email=user_in.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    user_crud.update_last_login(db, user_id=user.id)

    # Create token pair
    tokens = create_token_pair(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )

    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    token_in: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Decode and validate refresh token
    token_data = decode_token(token_in.refresh_token, expected_type="refresh")

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = user_crud.get(db, user_id=UUID(token_data.user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new token pair
    tokens = create_token_pair(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )

    return tokens


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile

    - **email**: New email (optional)
    - **username**: New username (optional)
    - **password**: New password (optional, min 8 chars)
    - **full_name**: New full name (optional)
    - **avatar_url**: New avatar URL (optional)
    """
    # Check email uniqueness if changing
    if user_in.email and user_in.email != current_user.email:
        existing = user_crud.get_by_email(db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )

    # Check username uniqueness if changing
    if user_in.username and user_in.username != current_user.username:
        existing = user_crud.get_by_username(db, username=user_in.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    # Update user
    user = user_crud.update(db, user_id=current_user.id, obj_in=user_in)
    return user


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout (invalidate refresh tokens)

    Note: In a production system, you would add the refresh token to a blacklist
    """
    # For now, just return success
    # Client should delete tokens from local storage
    return {"message": "Logged out successfully"}
