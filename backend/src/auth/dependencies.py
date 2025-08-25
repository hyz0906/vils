"""Authentication dependencies for FastAPI."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.orm import Session

from ..database.connection import get_database
from ..models.user import User
from .security import TokenData, verify_token


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/auth/login",
    scopes={
        "read": "Read access",
        "write": "Write access", 
        "admin": "Admin access",
    },
)


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_database),
) -> User:
    """Get the current authenticated user.
    
    Args:
        security_scopes: Required security scopes
        token: The JWT token
        db: Database session
        
    Returns:
        The authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Create credentials exception
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    # Verify token
    token_data = verify_token(token, token_type="access")
    if token_data is None:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Check scopes
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user.
    
    Args:
        current_user: The current user from authentication
        
    Returns:
        The active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_database),
) -> Optional[User]:
    """Get the current user if authenticated, otherwise None.
    
    Args:
        token: The optional JWT token
        db: Database session
        
    Returns:
        The authenticated user or None
    """
    if not token:
        return None
        
    try:
        token_data = verify_token(token, token_type="access")
        if token_data is None:
            return None

        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        return None


def require_scopes(*scopes: str):
    """Decorator to require specific scopes for an endpoint.
    
    Args:
        *scopes: Required scopes
        
    Returns:
        Dependency function
    """
    def dependency(
        current_user: User = Depends(
            lambda token=Depends(oauth2_scheme), db=Depends(get_database): 
            get_current_user(SecurityScopes(scopes=list(scopes)), token, db)
        )
    ) -> User:
        return current_user
    
    return dependency