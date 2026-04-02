"""User domain model with Pydantic validation."""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class User(BaseModel):
    """User domain model with validation."""
    
    id: Optional[int] = None
    username: str = Field(min_length=3, max_length=50)
    password_hash: str
    full_name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    role: str = Field(default='user', pattern="^(admin|manager|user)$")
    is_active: bool = Field(default=True)
    failed_login_attempts: int = Field(default=0, ge=0)
    locked_until: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is None:
            return None
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is valid."""
        if v not in ('admin', 'manager', 'user'):
            raise ValueError('Role must be admin, manager, or user')
        return v.lower()


class UserCreate(BaseModel):
    """DTO for creating users."""
    
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=12)
    full_name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    role: str = Field(default='user', pattern="^(admin|manager|user)$")
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is None:
            return None
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is valid."""
        if v not in ('admin', 'manager', 'user'):
            raise ValueError('Role must be admin, manager, or user')
        return v.lower()


class UserUpdate(BaseModel):
    """DTO for updating users (all fields optional)."""
    
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=12)
    full_name: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, pattern="^(admin|manager|user)$")
    is_active: Optional[bool] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format."""
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower() if v else None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is None:
            return None
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate role is valid."""
        if v is not None and v not in ('admin', 'manager', 'user'):
            raise ValueError('Role must be admin, manager, or user')
        return v.lower() if v else None


class Session(BaseModel):
    """Session domain model."""
    
    id: Optional[int] = None
    user_id: int
    token_hash: str
    encrypted_data: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    created_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
