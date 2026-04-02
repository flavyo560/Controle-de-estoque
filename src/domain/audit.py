"""Audit domain model with Pydantic validation."""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, Dict, Any


class AuditLog(BaseModel):
    """Audit log domain model."""
    
    id: Optional[int] = None
    user_id: Optional[int] = None
    operation: str = Field(pattern="^(CREATE|UPDATE|DELETE|LOGIN|LOGOUT|FAILED_LOGIN)$")
    table_name: Optional[str] = Field(None, max_length=50)
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation is valid."""
        valid_operations = ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'FAILED_LOGIN')
        if v not in valid_operations:
            raise ValueError(f'Operation must be one of: {", ".join(valid_operations)}')
        return v.upper()


class AuditLogCreate(BaseModel):
    """DTO for creating audit log entries."""
    
    user_id: Optional[int] = None
    operation: str = Field(pattern="^(CREATE|UPDATE|DELETE|LOGIN|LOGOUT|FAILED_LOGIN)$")
    table_name: Optional[str] = Field(None, max_length=50)
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    @field_validator('operation')
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation is valid."""
        valid_operations = ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'FAILED_LOGIN')
        if v not in valid_operations:
            raise ValueError(f'Operation must be one of: {", ".join(valid_operations)}')
        return v.upper()
