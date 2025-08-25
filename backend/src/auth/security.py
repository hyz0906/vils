"""Security utilities for authentication and authorization."""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from ..config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model."""
    
    username: Optional[str] = None
    user_id: Optional[str] = None
    scopes: list[str] = []


class Token(BaseModel):
    """Token response model."""
    
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password.
    
    Args:
        password: The plain text password
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create an access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a refresh token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify a JWT token.
    
    Args:
        token: The JWT token to verify
        token_type: The expected token type ('access' or 'refresh')
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            return None
            
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        scopes: list[str] = payload.get("scopes", [])
        
        if username is None:
            return None
            
        return TokenData(
            username=username, 
            user_id=user_id, 
            scopes=scopes
        )
        
    except JWTError:
        return None


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token.
    
    Args:
        length: The length of the token
        
    Returns:
        A secure random token
    """
    return secrets.token_urlsafe(length)


def create_token_response(
    user_id: str, username: str, scopes: Optional[list[str]] = None
) -> Token:
    """Create a complete token response.
    
    Args:
        user_id: The user ID
        username: The username
        scopes: Optional list of scopes
        
    Returns:
        Token response with access and refresh tokens
    """
    scopes = scopes or []
    
    # Token data
    token_data = {
        "sub": username,
        "user_id": user_id,
        "scopes": scopes,
    }
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)
    
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data=token_data, expires_delta=refresh_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=refresh_token,
    )