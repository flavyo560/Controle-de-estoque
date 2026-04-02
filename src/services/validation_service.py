"""
Centralized input validation and sanitization service.

This module provides comprehensive validation for user inputs including:
- String sanitization with SQL injection and XSS detection
- Numeric validation with bounds checking
- Email, CPF, and phone validation for Brazilian formats
- File upload validation with extension and size checks
"""

import re
from typing import Any, List
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class ValidationService:
    """Centralized input validation and sanitization."""
    
    # SQL injection patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"('.*--)",
    ]
    
    # XSS patterns to detect
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int | None = None) -> str:
        """
        Sanitize string input by removing dangerous characters.
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If input contains dangerous patterns
        """
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError("Input contains potentially dangerous SQL patterns")
        
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError("Input contains potentially dangerous script patterns")
        
        # Trim whitespace
        value = value.strip()
        
        # Enforce max length
        if max_length and len(value) > max_length:
            raise ValidationError(f"Input exceeds maximum length of {max_length}")
        
        return value
    
    @classmethod
    def validate_numeric(
        cls,
        value: Any,
        min_value: float | None = None,
        max_value: float | None = None,
        allow_decimal: bool = True
    ) -> float | int | Decimal:
        """
        Validate and convert numeric input.
        
        Args:
            value: Input value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_decimal: Whether to allow decimal values
            
        Returns:
            Validated numeric value (int if allow_decimal=False, Decimal otherwise)
            
        Raises:
            ValidationError: If input is not valid numeric
        """
        try:
            if allow_decimal:
                num = Decimal(str(value))
            else:
                num = Decimal(str(value))
                # Check if it's a whole number
                if num % 1 != 0:
                    raise ValidationError(f"Value must be an integer: {value}")
        except (ValueError, InvalidOperation):
            raise ValidationError(f"Invalid numeric value: {value}")
        
        if min_value is not None and num < Decimal(str(min_value)):
            raise ValidationError(f"Value must be at least {min_value}")
        
        if max_value is not None and num > Decimal(str(max_value)):
            raise ValidationError(f"Value must be at most {max_value}")
        
        # Return appropriate type
        if allow_decimal:
            return num
        else:
            return int(num)
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Validated and normalized email (lowercase)
            
        Raises:
            ValidationError: If email format is invalid
        """
        email = cls.sanitize_string(email, max_length=255)
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")
        
        return email.lower()
    
    @classmethod
    def validate_cpf(cls, cpf: str) -> str:
        """
        Validate Brazilian CPF format with check digit validation.
        
        Args:
            cpf: CPF string (can include formatting)
            
        Returns:
            Formatted CPF (XXX.XXX.XXX-XX)
            
        Raises:
            ValidationError: If CPF is invalid
        """
        # Remove non-numeric characters
        cpf = re.sub(r'\D', '', cpf)
        
        if len(cpf) != 11:
            raise ValidationError("CPF must have 11 digits")
        
        # Check if all digits are the same
        if cpf == cpf[0] * 11:
            raise ValidationError("Invalid CPF")
        
        # Validate check digits
        def calculate_digit(cpf_partial: str, weights: List[int]) -> int:
            total = sum(int(cpf_partial[i]) * weights[i] for i in range(len(weights)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        weights_first = list(range(10, 1, -1))
        weights_second = list(range(11, 1, -1))
        
        first_digit = calculate_digit(cpf[:9], weights_first)
        second_digit = calculate_digit(cpf[:10], weights_second)
        
        if cpf[-2:] != f"{first_digit}{second_digit}":
            raise ValidationError("Invalid CPF check digits")
        
        # Format with mask
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @classmethod
    def validate_phone(cls, phone: str) -> str:
        """
        Validate and format Brazilian phone number.
        
        Args:
            phone: Phone number (can include formatting)
            
        Returns:
            Formatted phone number
            
        Raises:
            ValidationError: If phone number is invalid
        """
        # Remove non-numeric characters
        phone = re.sub(r'\D', '', phone)
        
        if len(phone) < 10 or len(phone) > 11:
            raise ValidationError("Phone must have 10 or 11 digits")
        
        # Format with mask
        if len(phone) == 10:
            return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
        else:
            return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    
    @classmethod
    def validate_file_upload(
        cls,
        filename: str,
        content: bytes,
        allowed_extensions: List[str],
        max_size_mb: int = 10
    ) -> None:
        """
        Validate file upload.
        
        Args:
            filename: Original filename
            content: File content bytes
            allowed_extensions: List of allowed file extensions
            max_size_mb: Maximum file size in megabytes
            
        Raises:
            ValidationError: If file is invalid
        """
        # Check extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in allowed_extensions:
            raise ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Check size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValidationError(f"File size exceeds maximum of {max_size_mb}MB")
        
        # Check for malicious content (basic check)
        # In production, use a proper antivirus scanner
        dangerous_patterns = [b'<?php', b'<script', b'eval(']
        for pattern in dangerous_patterns:
            if pattern in content:
                raise ValidationError("File contains potentially dangerous content")
