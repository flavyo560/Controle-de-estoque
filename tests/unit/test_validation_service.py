"""
Unit tests for ValidationService.

Tests cover:
- String sanitization with SQL injection and XSS detection
- Numeric validation with bounds
- Email validation
- CPF validation with check digits
- Phone validation for Brazilian formats
- File upload validation
"""

import pytest
from decimal import Decimal
from src.services.validation_service import ValidationService, ValidationError


class TestSanitizeString:
    """Tests for sanitize_string method."""
    
    def test_sanitize_valid_string(self):
        """Test sanitizing a valid string."""
        result = ValidationService.sanitize_string("Hello World")
        assert result == "Hello World"
    
    def test_sanitize_trims_whitespace(self):
        """Test that whitespace is trimmed."""
        result = ValidationService.sanitize_string("  Hello World  ")
        assert result == "Hello World"
    
    def test_sanitize_enforces_max_length(self):
        """Test max length enforcement."""
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            ValidationService.sanitize_string("Hello World", max_length=5)
    
    def test_sanitize_rejects_sql_injection_select(self):
        """Test SQL injection detection - SELECT."""
        with pytest.raises(ValidationError, match="dangerous SQL patterns"):
            ValidationService.sanitize_string("'; SELECT * FROM users--")
    
    def test_sanitize_rejects_sql_injection_drop(self):
        """Test SQL injection detection - DROP."""
        with pytest.raises(ValidationError, match="dangerous SQL patterns"):
            ValidationService.sanitize_string("'; DROP TABLE users;--")
    
    def test_sanitize_rejects_sql_injection_comment(self):
        """Test SQL injection detection - SQL comments."""
        with pytest.raises(ValidationError, match="dangerous SQL patterns"):
            ValidationService.sanitize_string("admin'--")
    
    def test_sanitize_rejects_sql_injection_or(self):
        """Test SQL injection detection - OR clause."""
        with pytest.raises(ValidationError, match="dangerous SQL patterns"):
            ValidationService.sanitize_string("' OR '1'='1")
    
    def test_sanitize_rejects_xss_script_tag(self):
        """Test XSS detection - script tag."""
        with pytest.raises(ValidationError, match="dangerous script patterns"):
            ValidationService.sanitize_string("<script>alert('XSS')</script>")
    
    def test_sanitize_rejects_xss_javascript_protocol(self):
        """Test XSS detection - javascript protocol."""
        with pytest.raises(ValidationError, match="dangerous script patterns"):
            ValidationService.sanitize_string("javascript:alert('XSS')")
    
    def test_sanitize_rejects_xss_event_handler(self):
        """Test XSS detection - event handler."""
        with pytest.raises(ValidationError, match="dangerous script patterns"):
            ValidationService.sanitize_string("<img src=x onerror=alert('XSS')>")
    
    def test_sanitize_rejects_xss_iframe(self):
        """Test XSS detection - iframe."""
        with pytest.raises(ValidationError, match="dangerous script patterns"):
            ValidationService.sanitize_string("<iframe src='evil.com'>")
    
    def test_sanitize_rejects_non_string(self):
        """Test that non-string input is rejected."""
        with pytest.raises(ValidationError, match="must be a string"):
            ValidationService.sanitize_string(123)


class TestValidateNumeric:
    """Tests for validate_numeric method."""
    
    def test_validate_integer(self):
        """Test validating an integer."""
        result = ValidationService.validate_numeric(42, allow_decimal=False)
        assert result == 42
        assert isinstance(result, int)
    
    def test_validate_decimal(self):
        """Test validating a decimal."""
        result = ValidationService.validate_numeric("3.14", allow_decimal=True)
        assert result == Decimal("3.14")
    
    def test_validate_numeric_string(self):
        """Test validating numeric string."""
        result = ValidationService.validate_numeric("100", allow_decimal=False)
        assert result == 100
    
    def test_validate_enforces_min_value(self):
        """Test minimum value enforcement."""
        with pytest.raises(ValidationError, match="must be at least"):
            ValidationService.validate_numeric(5, min_value=10)
    
    def test_validate_enforces_max_value(self):
        """Test maximum value enforcement."""
        with pytest.raises(ValidationError, match="must be at most"):
            ValidationService.validate_numeric(100, max_value=50)
    
    def test_validate_within_bounds(self):
        """Test value within bounds."""
        result = ValidationService.validate_numeric(50, min_value=0, max_value=100)
        assert result == Decimal("50")
    
    def test_validate_rejects_invalid_numeric(self):
        """Test rejection of invalid numeric input."""
        with pytest.raises(ValidationError, match="Invalid numeric value"):
            ValidationService.validate_numeric("not a number")
    
    def test_validate_negative_numbers(self):
        """Test validating negative numbers."""
        result = ValidationService.validate_numeric(-10, min_value=-100)
        assert result == Decimal("-10")


class TestValidateEmail:
    """Tests for validate_email method."""
    
    def test_validate_valid_email(self):
        """Test validating a valid email."""
        result = ValidationService.validate_email("user@example.com")
        assert result == "user@example.com"
    
    def test_validate_email_lowercase(self):
        """Test email is converted to lowercase."""
        result = ValidationService.validate_email("User@Example.COM")
        assert result == "user@example.com"
    
    def test_validate_email_with_plus(self):
        """Test email with plus sign."""
        result = ValidationService.validate_email("user+tag@example.com")
        assert result == "user+tag@example.com"
    
    def test_validate_email_with_dots(self):
        """Test email with dots."""
        result = ValidationService.validate_email("first.last@example.com")
        assert result == "first.last@example.com"
    
    def test_validate_rejects_invalid_email_no_at(self):
        """Test rejection of email without @."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            ValidationService.validate_email("userexample.com")
    
    def test_validate_rejects_invalid_email_no_domain(self):
        """Test rejection of email without domain."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            ValidationService.validate_email("user@")
    
    def test_validate_rejects_invalid_email_no_tld(self):
        """Test rejection of email without TLD."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            ValidationService.validate_email("user@example")


class TestValidateCPF:
    """Tests for validate_cpf method."""
    
    def test_validate_valid_cpf(self):
        """Test validating a valid CPF."""
        # Valid CPF: 123.456.789-09
        result = ValidationService.validate_cpf("12345678909")
        assert result == "123.456.789-09"
    
    def test_validate_cpf_with_formatting(self):
        """Test validating CPF with formatting."""
        result = ValidationService.validate_cpf("123.456.789-09")
        assert result == "123.456.789-09"
    
    def test_validate_cpf_another_valid(self):
        """Test another valid CPF."""
        # Valid CPF: 111.444.777-35
        result = ValidationService.validate_cpf("11144477735")
        assert result == "111.444.777-35"
    
    def test_validate_rejects_cpf_wrong_length(self):
        """Test rejection of CPF with wrong length."""
        with pytest.raises(ValidationError, match="must have 11 digits"):
            ValidationService.validate_cpf("123456789")
    
    def test_validate_rejects_cpf_all_same_digits(self):
        """Test rejection of CPF with all same digits."""
        with pytest.raises(ValidationError, match="Invalid CPF"):
            ValidationService.validate_cpf("11111111111")
    
    def test_validate_rejects_cpf_invalid_check_digits(self):
        """Test rejection of CPF with invalid check digits."""
        with pytest.raises(ValidationError, match="Invalid CPF check digits"):
            ValidationService.validate_cpf("12345678900")


class TestValidatePhone:
    """Tests for validate_phone method."""
    
    def test_validate_phone_10_digits(self):
        """Test validating 10-digit phone."""
        result = ValidationService.validate_phone("1234567890")
        assert result == "(12) 3456-7890"
    
    def test_validate_phone_11_digits(self):
        """Test validating 11-digit phone (with 9)."""
        result = ValidationService.validate_phone("12345678901")
        assert result == "(12) 34567-8901"
    
    def test_validate_phone_with_formatting(self):
        """Test validating phone with formatting."""
        result = ValidationService.validate_phone("(12) 3456-7890")
        assert result == "(12) 3456-7890"
    
    def test_validate_rejects_phone_too_short(self):
        """Test rejection of phone too short."""
        with pytest.raises(ValidationError, match="must have 10 or 11 digits"):
            ValidationService.validate_phone("123456789")
    
    def test_validate_rejects_phone_too_long(self):
        """Test rejection of phone too long."""
        with pytest.raises(ValidationError, match="must have 10 or 11 digits"):
            ValidationService.validate_phone("123456789012")


class TestValidateFileUpload:
    """Tests for validate_file_upload method."""
    
    def test_validate_valid_file(self):
        """Test validating a valid file."""
        content = b"This is a test file content"
        ValidationService.validate_file_upload(
            "test.txt",
            content,
            allowed_extensions=["txt", "pdf"],
            max_size_mb=10
        )
        # Should not raise
    
    def test_validate_rejects_invalid_extension(self):
        """Test rejection of invalid file extension."""
        content = b"Test content"
        with pytest.raises(ValidationError, match="File type not allowed"):
            ValidationService.validate_file_upload(
                "test.exe",
                content,
                allowed_extensions=["txt", "pdf"]
            )
    
    def test_validate_rejects_file_too_large(self):
        """Test rejection of file too large."""
        # Create 2MB content
        content = b"x" * (2 * 1024 * 1024)
        with pytest.raises(ValidationError, match="exceeds maximum"):
            ValidationService.validate_file_upload(
                "test.txt",
                content,
                allowed_extensions=["txt"],
                max_size_mb=1
            )
    
    def test_validate_rejects_php_content(self):
        """Test rejection of PHP content."""
        content = b"<?php echo 'malicious'; ?>"
        with pytest.raises(ValidationError, match="dangerous content"):
            ValidationService.validate_file_upload(
                "test.txt",
                content,
                allowed_extensions=["txt"]
            )
    
    def test_validate_rejects_script_content(self):
        """Test rejection of script content."""
        content = b"<script>alert('xss')</script>"
        with pytest.raises(ValidationError, match="dangerous content"):
            ValidationService.validate_file_upload(
                "test.html",
                content,
                allowed_extensions=["html"]
            )
    
    def test_validate_rejects_eval_content(self):
        """Test rejection of eval content."""
        content = b"eval('malicious code')"
        with pytest.raises(ValidationError, match="dangerous content"):
            ValidationService.validate_file_upload(
                "test.js",
                content,
                allowed_extensions=["js"]
            )
    
    def test_validate_file_no_extension(self):
        """Test rejection of file without extension."""
        content = b"Test content"
        with pytest.raises(ValidationError, match="File type not allowed"):
            ValidationService.validate_file_upload(
                "testfile",
                content,
                allowed_extensions=["txt"]
            )
