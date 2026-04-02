"""Customer domain model with Pydantic validation."""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class Customer(BaseModel):
    """Customer domain model with validation."""
    
    id: Optional[int] = None
    name: str = Field(min_length=1, max_length=200)
    cpf: Optional[str] = Field(None, max_length=14)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        """Validate Brazilian CPF with check digit validation."""
        if v is None or v == '':
            return None
        
        # Remove non-numeric characters
        cpf = re.sub(r'\D', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF must have 11 digits')
        
        # Check if all digits are the same (invalid CPF)
        if cpf == cpf[0] * 11:
            raise ValueError('Invalid CPF: all digits are the same')
        
        # Validate check digits
        def calculate_digit(cpf_partial: str, weights: list) -> int:
            total = sum(int(cpf_partial[i]) * weights[i] for i in range(len(weights)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        weights_first = list(range(10, 1, -1))
        weights_second = list(range(11, 1, -1))
        
        first_digit = calculate_digit(cpf[:9], weights_first)
        second_digit = calculate_digit(cpf[:10], weights_second)
        
        if cpf[-2:] != f"{first_digit}{second_digit}":
            raise ValueError('Invalid CPF: check digits do not match')
        
        # Format with mask: 123.456.789-01
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is None or v == '':
            return None
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate and format Brazilian phone number."""
        if v is None or v == '':
            return None
        
        # Remove non-numeric characters
        phone = re.sub(r'\D', '', v)
        
        if len(phone) < 10 or len(phone) > 11:
            raise ValueError('Phone must have 10 or 11 digits')
        
        # Format with mask
        if len(phone) == 10:
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        else:
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"


class CustomerCreate(BaseModel):
    """DTO for creating customers."""
    
    name: str = Field(min_length=1, max_length=200)
    cpf: Optional[str] = Field(None, max_length=14)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        """Validate Brazilian CPF with check digit validation."""
        if v is None or v == '':
            return None
        
        # Remove non-numeric characters
        cpf = re.sub(r'\D', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF must have 11 digits')
        
        # Check if all digits are the same (invalid CPF)
        if cpf == cpf[0] * 11:
            raise ValueError('Invalid CPF: all digits are the same')
        
        # Validate check digits
        def calculate_digit(cpf_partial: str, weights: list) -> int:
            total = sum(int(cpf_partial[i]) * weights[i] for i in range(len(weights)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        weights_first = list(range(10, 1, -1))
        weights_second = list(range(11, 1, -1))
        
        first_digit = calculate_digit(cpf[:9], weights_first)
        second_digit = calculate_digit(cpf[:10], weights_second)
        
        if cpf[-2:] != f"{first_digit}{second_digit}":
            raise ValueError('Invalid CPF: check digits do not match')
        
        # Format with mask: 123.456.789-01
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is None or v == '':
            return None
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate and format Brazilian phone number."""
        if v is None or v == '':
            return None
        
        # Remove non-numeric characters
        phone = re.sub(r'\D', '', v)
        
        if len(phone) < 10 or len(phone) > 11:
            raise ValueError('Phone must have 10 or 11 digits')
        
        # Format with mask
        if len(phone) == 10:
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        else:
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"


class CustomerUpdate(BaseModel):
    """DTO for updating customers (all fields optional)."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    cpf: Optional[str] = Field(None, max_length=14)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        """Validate Brazilian CPF with check digit validation."""
        if v is None or v == '':
            return None
        
        # Remove non-numeric characters
        cpf = re.sub(r'\D', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF must have 11 digits')
        
        # Check if all digits are the same (invalid CPF)
        if cpf == cpf[0] * 11:
            raise ValueError('Invalid CPF: all digits are the same')
        
        # Validate check digits
        def calculate_digit(cpf_partial: str, weights: list) -> int:
            total = sum(int(cpf_partial[i]) * weights[i] for i in range(len(weights)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        weights_first = list(range(10, 1, -1))
        weights_second = list(range(11, 1, -1))
        
        first_digit = calculate_digit(cpf[:9], weights_first)
        second_digit = calculate_digit(cpf[:10], weights_second)
        
        if cpf[-2:] != f"{first_digit}{second_digit}":
            raise ValueError('Invalid CPF: check digits do not match')
        
        # Format with mask: 123.456.789-01
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format."""
        if v is None or v == '':
            return None
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate and format Brazilian phone number."""
        if v is None or v == '':
            return None
        
        # Remove non-numeric characters
        phone = re.sub(r'\D', '', v)
        
        if len(phone) < 10 or len(phone) > 11:
            raise ValueError('Phone must have 10 or 11 digits')
        
        # Format with mask
        if len(phone) == 10:
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        else:
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
