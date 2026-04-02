"""Product domain model with Pydantic validation."""

from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional


class Product(BaseModel):
    """Product domain model with validation."""
    
    id: Optional[int] = None
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    gender: str = Field(pattern="^(M|F|U)$")  # M=Male, F=Female, U=Unisex
    brand: str = Field(min_length=1, max_length=100)
    reference: str = Field(min_length=1, max_length=50)
    size: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=0)
    price: Decimal = Field(gt=0)
    barcode: Optional[str] = Field(None, max_length=50)
    min_stock: int = Field(default=5, ge=0)
    version: int = Field(default=1, ge=1)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Price must have at most 2 decimal places')
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        """Validate gender is M, F, or U."""
        if v not in ('M', 'F', 'U'):
            raise ValueError('Gender must be M (Male), F (Female), or U (Unisex)')
        return v.upper()
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is non-negative."""
        if v < 0:
            raise ValueError('Quantity must be greater than or equal to 0')
        return v


class ProductCreate(BaseModel):
    """DTO for creating products."""
    
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    gender: str = Field(pattern="^(M|F|U)$")
    brand: str = Field(min_length=1, max_length=100)
    reference: str = Field(min_length=1, max_length=50)
    size: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=0)
    price: Decimal = Field(gt=0)
    barcode: Optional[str] = Field(None, max_length=50)
    min_stock: int = Field(default=5, ge=0)
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Price must have at most 2 decimal places')
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        """Validate gender is M, F, or U."""
        if v not in ('M', 'F', 'U'):
            raise ValueError('Gender must be M (Male), F (Female), or U (Unisex)')
        return v.upper()
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is non-negative."""
        if v < 0:
            raise ValueError('Quantity must be greater than or equal to 0')
        return v


class ProductUpdate(BaseModel):
    """DTO for updating products (all fields optional)."""
    
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    gender: Optional[str] = Field(None, pattern="^(M|F|U)$")
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    reference: Optional[str] = Field(None, min_length=1, max_length=50)
    size: Optional[str] = Field(None, min_length=1, max_length=20)
    quantity: Optional[int] = Field(None, ge=0)
    price: Optional[Decimal] = Field(None, gt=0)
    barcode: Optional[str] = Field(None, max_length=50)
    min_stock: Optional[int] = Field(None, ge=0)
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Validate price has at most 2 decimal places."""
        if v is not None and v.as_tuple().exponent < -2:
            raise ValueError('Price must have at most 2 decimal places')
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender is M, F, or U."""
        if v is not None and v not in ('M', 'F', 'U'):
            raise ValueError('Gender must be M (Male), F (Female), or U (Unisex)')
        return v.upper() if v else None
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: Optional[int]) -> Optional[int]:
        """Validate quantity is non-negative."""
        if v is not None and v < 0:
            raise ValueError('Quantity must be greater than or equal to 0')
        return v
