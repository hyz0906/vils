"""Authentication API endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_active_user
from ..auth.security import (
    create_token_response,
    get_password_hash,
    verify_password,
    verify_token,
)
from ..database.connection import get_database
from ..models.user import User
from .schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Router
router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_database),
) -> Dict[str, Any]:
    """Register a new user account.
    
    Args:
        request: FastAPI request object
        user_data: User registration data
        db: Database session
        
    Returns:
        User response data
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        )
        .first()
    )
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        is_active=True,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_database),
) -> TokenResponse:
    """Authenticate user and return JWT tokens.
    
    Args:
        request: FastAPI request object
        form_data: Login form data
        db: Database session
        
    Returns:
        Token response with access and refresh tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    # Find user by username or email
    user = (
        db.query(User)
        .filter(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
        .first()
    )
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create token response
    scopes = form_data.scopes or ["read", "write"]
    
    return create_token_response(
        user_id=str(user.id),
        username=user.username,
        scopes=scopes,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_database),
) -> TokenResponse:
    """Refresh access token using refresh token.
    
    Args:
        request: FastAPI request object
        refresh_data: Refresh token data
        db: Database session
        
    Returns:
        New token response
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Find user
    user = db.query(User).filter(User.username == token_data.username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new token response
    return create_token_response(
        user_id=str(user.id),
        username=user.username,
        scopes=token_data.scopes,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Logout user (invalidate token).
    
    Note: In a production system, you would typically maintain a blacklist
    of invalidated tokens or use a token store that can be cleared.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # In a real implementation, you would:
    # 1. Add token to blacklist
    # 2. Clear user session from cache/store
    # 3. Log the logout event
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user data
    """
    return current_user


@router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database),
) -> Dict[str, str]:
    """Change user password.
    
    Args:
        request: FastAPI request object
        current_password: Current user password
        new_password: New password
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Validate new password (basic validation, extend as needed)
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}