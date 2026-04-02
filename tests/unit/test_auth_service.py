"""Unit tests for authentication service."""

import pytest
from src.services.auth_service import PasswordPolicy, ValidationError


class TestPasswordPolicy:
    """Test password policy validation."""
    
    def test_valid_password(self):
        """Test that a valid password passes validation."""
        password = "MySecureP@ssw0rd"
        is_valid, error = PasswordPolicy.validate(password)
        assert is_valid is True
        assert error == ""
    
    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        password = "Short1!"
        is_valid, error = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "at least 12 characters" in error
    
    def test_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        password = "mysecurep@ssw0rd"
        is_valid, error = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "uppercase letter" in error
    
    def test_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        password = "MYSECUREP@SSW0RD"
        is_valid, error = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "lowercase letter" in error
    
    def test_password_no_digit(self):
        """Test that passwords without digits are rejected."""
        password = "MySecureP@ssword"
        is_valid, error = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "digit" in error
    
    def test_password_no_special_char(self):
        """Test that passwords without special characters are rejected."""
        password = "MySecurePassw0rd"
        is_valid, error = PasswordPolicy.validate(password)
        assert is_valid is False
        assert "special character" in error
    
    def test_password_with_all_requirements(self):
        """Test various valid passwords with all requirements."""
        valid_passwords = [
            "Abcdefgh123!",
            "P@ssw0rd1234",
            "MyStr0ng#Pass",
            "Secure123$Pass",
            "C0mpl3x!Passw0rd"
        ]
        
        for password in valid_passwords:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is True, f"Password '{password}' should be valid but got error: {error}"
            assert error == ""
