"""Property-based tests for validation service.

**Validates: Requirements 2.1, 2.2**

These tests verify that the ValidationService correctly sanitizes inputs
and validates Brazilian document formats (CPF) across all possible inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import re

from src.services.validation_service import ValidationService, ValidationError


# Hypothesis strategies for generating test data
@st.composite
def safe_string_strategy(draw):
    """Generate strings that should pass sanitization."""
    # Generate strings without SQL injection or XSS patterns
    # Exclude dangerous characters and patterns
    chars = st.characters(
        blacklist_categories=('Cs',),  # Exclude surrogates
        blacklist_characters='<>;\'"=-/*'  # Exclude dangerous chars including -, /, * for comments
    )
    text = draw(st.text(alphabet=chars, min_size=0, max_size=200))
    
    # Ensure the text doesn't contain SQL keywords or dangerous patterns
    # Filter out texts that would trigger SQL injection detection
    dangerous_words = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE', 'OR', 'AND']
    text_upper = text.upper()
    
    # If text contains dangerous words, replace them
    for word in dangerous_words:
        if word in text_upper:
            text = text.replace(word, 'SAFE')
            text = text.replace(word.lower(), 'safe')
    
    return text


@st.composite
def cpf_digits_strategy(draw):
    """Generate 11-digit strings for CPF testing."""
    # Generate 9 random digits, ensuring not all are the same
    digits = [draw(st.integers(min_value=0, max_value=9)) for _ in range(9)]
    
    # Ensure not all digits are the same (invalid CPF pattern)
    # If all are the same, change the last one
    if len(set(digits)) == 1:
        digits[-1] = (digits[-1] + 1) % 10
    
    # Calculate first check digit
    weights_first = list(range(10, 1, -1))
    total = sum(digits[i] * weights_first[i] for i in range(9))
    remainder = total % 11
    first_digit = 0 if remainder < 2 else 11 - remainder
    digits.append(first_digit)
    
    # Calculate second check digit
    weights_second = list(range(11, 1, -1))
    total = sum(digits[i] * weights_second[i] for i in range(10))
    remainder = total % 11
    second_digit = 0 if remainder < 2 else 11 - remainder
    digits.append(second_digit)
    
    cpf = ''.join(str(d) for d in digits)
    
    # Double-check: if somehow we still got all same digits, regenerate
    if cpf == cpf[0] * 11:
        # Force a different pattern
        cpf = '12345678909'  # Known valid CPF
    
    return cpf


@st.composite
def invalid_cpf_strategy(draw):
    """Generate invalid CPF strings."""
    choice = draw(st.integers(min_value=0, max_value=3))
    
    if choice == 0:
        # Wrong length
        length = draw(st.integers(min_value=0, max_value=20).filter(lambda x: x != 11))
        return ''.join(str(draw(st.integers(min_value=0, max_value=9))) for _ in range(length))
    elif choice == 1:
        # All same digits
        digit = draw(st.integers(min_value=0, max_value=9))
        return str(digit) * 11
    elif choice == 2:
        # Valid format but wrong check digits
        digits = ''.join(str(draw(st.integers(min_value=0, max_value=9))) for _ in range(9))
        # Add wrong check digits
        wrong_digit1 = draw(st.integers(min_value=0, max_value=9))
        wrong_digit2 = draw(st.integers(min_value=0, max_value=9))
        cpf = digits + str(wrong_digit1) + str(wrong_digit2)
        
        # Make sure it's actually invalid by checking it doesn't match valid calculation
        # Calculate correct digits
        weights_first = list(range(10, 1, -1))
        total = sum(int(digits[i]) * weights_first[i] for i in range(9))
        remainder = total % 11
        correct_first = 0 if remainder < 2 else 11 - remainder
        
        weights_second = list(range(11, 1, -1))
        total = sum(int((digits + str(correct_first))[i]) * weights_second[i] for i in range(10))
        remainder = total % 11
        correct_second = 0 if remainder < 2 else 11 - remainder
        
        # If by chance we generated correct digits, modify them
        if cpf[-2:] == f"{correct_first}{correct_second}":
            cpf = cpf[:-1] + str((int(cpf[-1]) + 1) % 10)
        
        return cpf
    else:
        # Non-numeric characters
        return draw(st.text(min_size=11, max_size=11).filter(lambda x: not x.isdigit()))


class TestSanitizationIdempotence:
    """Property-based tests for sanitization idempotence."""
    
    @given(text=safe_string_strategy())
    @settings(max_examples=200)
    def test_sanitization_idempotence_safe_strings(self, text: str):
        """
        Property 4: Sanitization idempotence.
        
        **Validates: Requirements 2.1**
        
        Test that sanitize_string(sanitize_string(x)) = sanitize_string(x).
        Applying sanitization twice should produce the same result as applying it once.
        """
        # First sanitization
        sanitized_once = ValidationService.sanitize_string(text)
        
        # Second sanitization
        sanitized_twice = ValidationService.sanitize_string(sanitized_once)
        
        # They should be equal (idempotent)
        assert sanitized_once == sanitized_twice, (
            f"Sanitization is not idempotent!\n"
            f"Original: {repr(text)}\n"
            f"First pass: {repr(sanitized_once)}\n"
            f"Second pass: {repr(sanitized_twice)}"
        )
    
    @given(text=st.text(min_size=0, max_size=200))
    @settings(max_examples=200)
    def test_sanitization_idempotence_all_strings(self, text: str):
        """
        Property 4: Sanitization idempotence (comprehensive).
        
        **Validates: Requirements 2.1**
        
        Test idempotence for all strings, including those that might be rejected.
        If a string passes sanitization once, it should pass again with same result.
        """
        try:
            # First sanitization
            sanitized_once = ValidationService.sanitize_string(text)
            
            # Second sanitization should not raise error
            sanitized_twice = ValidationService.sanitize_string(sanitized_once)
            
            # They should be equal (idempotent)
            assert sanitized_once == sanitized_twice, (
                f"Sanitization is not idempotent!\n"
                f"Original: {repr(text)}\n"
                f"First pass: {repr(sanitized_once)}\n"
                f"Second pass: {repr(sanitized_twice)}"
            )
        except ValidationError:
            # If first sanitization fails, that's okay - we're testing idempotence
            # of successful sanitizations, not whether all strings pass
            pass
    
    @given(
        text=st.text(min_size=0, max_size=100),
        iterations=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100)
    def test_sanitization_idempotence_multiple_iterations(self, text: str, iterations: int):
        """
        Property 4: Sanitization idempotence (multiple iterations).
        
        **Validates: Requirements 2.1**
        
        Test that applying sanitization N times produces the same result
        as applying it once (for N >= 1).
        """
        try:
            # First sanitization
            result = ValidationService.sanitize_string(text)
            
            # Apply sanitization multiple times
            for i in range(iterations - 1):
                new_result = ValidationService.sanitize_string(result)
                assert result == new_result, (
                    f"Sanitization is not idempotent at iteration {i+2}!\n"
                    f"Previous: {repr(result)}\n"
                    f"Current: {repr(new_result)}"
                )
                result = new_result
        except ValidationError:
            # If first sanitization fails, that's okay
            pass
    
    def test_sanitization_idempotence_edge_cases(self):
        """
        Test specific edge cases for sanitization idempotence.
        
        **Validates: Requirements 2.1**
        """
        test_cases = [
            "",  # Empty string
            " ",  # Single space
            "  ",  # Multiple spaces
            "hello",  # Simple text
            "Hello World",  # Text with space
            "  hello  ",  # Text with leading/trailing spaces
            "123",  # Numbers
            "test@example.com",  # Email-like
            "Product Name 123",  # Alphanumeric with spaces
        ]
        
        for text in test_cases:
            sanitized_once = ValidationService.sanitize_string(text)
            sanitized_twice = ValidationService.sanitize_string(sanitized_once)
            
            assert sanitized_once == sanitized_twice, (
                f"Sanitization not idempotent for: {repr(text)}\n"
                f"First: {repr(sanitized_once)}\n"
                f"Second: {repr(sanitized_twice)}"
            )


class TestCPFValidation:
    """Property-based tests for CPF validation."""
    
    @given(cpf_digits=cpf_digits_strategy())
    @settings(max_examples=200)
    def test_valid_cpf_accepted(self, cpf_digits: str):
        """
        Property 5: CPF validation correctness (valid CPFs).
        
        **Validates: Requirements 2.2**
        
        Test that all valid CPFs (with correct check digits) are accepted.
        """
        # Valid CPF should not raise error
        result = ValidationService.validate_cpf(cpf_digits)
        
        # Result should be formatted
        assert result is not None
        assert len(result) == 14  # XXX.XXX.XXX-XX format
        assert result[3] == '.'
        assert result[7] == '.'
        assert result[11] == '-'
        
        # Remove formatting and verify it matches original
        result_digits = re.sub(r'\D', '', result)
        assert result_digits == cpf_digits
    
    @given(cpf_digits=cpf_digits_strategy())
    @settings(max_examples=100)
    def test_valid_cpf_with_formatting_accepted(self, cpf_digits: str):
        """
        Property 5: CPF validation correctness (formatted input).
        
        **Validates: Requirements 2.2**
        
        Test that valid CPFs with formatting are accepted.
        """
        # Format the CPF
        formatted = f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"
        
        # Should be accepted
        result = ValidationService.validate_cpf(formatted)
        
        # Result should be formatted correctly
        assert result == formatted
    
    @given(invalid_cpf=invalid_cpf_strategy())
    @settings(max_examples=200)
    def test_invalid_cpf_rejected(self, invalid_cpf: str):
        """
        Property 5: CPF validation correctness (invalid CPFs).
        
        **Validates: Requirements 2.2**
        
        Test that invalid CPFs are rejected.
        """
        # Invalid CPF should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ValidationService.validate_cpf(invalid_cpf)
        
        # Error message should be descriptive
        error_msg = str(exc_info.value).lower()
        assert any(word in error_msg for word in ['cpf', 'invalid', 'digit']), (
            f"Error message not descriptive: {exc_info.value}"
        )
    
    def test_cpf_all_same_digits_rejected(self):
        """
        Property 5: CPF validation correctness (same digits).
        
        **Validates: Requirements 2.2**
        
        Test that CPFs with all same digits are rejected (known invalid pattern).
        """
        for digit in range(10):
            cpf = str(digit) * 11
            
            with pytest.raises(ValidationError) as exc_info:
                ValidationService.validate_cpf(cpf)
            
            assert "invalid" in str(exc_info.value).lower()
    
    def test_cpf_wrong_length_rejected(self):
        """
        Property 5: CPF validation correctness (wrong length).
        
        **Validates: Requirements 2.2**
        
        Test that CPFs with wrong length are rejected.
        """
        test_cases = [
            "",  # Empty
            "123",  # Too short
            "12345678901234567890",  # Too long
            "1234567890",  # 10 digits
            "123456789012",  # 12 digits
        ]
        
        for cpf in test_cases:
            with pytest.raises(ValidationError) as exc_info:
                ValidationService.validate_cpf(cpf)
            
            error_msg = str(exc_info.value).lower()
            assert "11" in error_msg or "digit" in error_msg
    
    def test_cpf_specific_valid_examples(self):
        """
        Test specific known valid CPF examples.
        
        **Validates: Requirements 2.2**
        """
        # These are known valid CPF numbers (not real people)
        valid_cpfs = [
            "11144477735",  # Valid CPF
            "12345678909",  # Valid CPF
        ]
        
        for cpf in valid_cpfs:
            # Should not raise error
            result = ValidationService.validate_cpf(cpf)
            assert result is not None
            
            # Verify formatting
            assert len(result) == 14
            assert result[3] == '.'
            assert result[7] == '.'
            assert result[11] == '-'
    
    def test_cpf_specific_invalid_examples(self):
        """
        Test specific known invalid CPF examples.
        
        **Validates: Requirements 2.2**
        """
        invalid_cpfs = [
            "12345678901",  # Wrong check digits
            "11111111111",  # All same digits
            "00000000000",  # All zeros
            "12345678900",  # Wrong check digits
        ]
        
        for cpf in invalid_cpfs:
            with pytest.raises(ValidationError):
                ValidationService.validate_cpf(cpf)
    
    @given(
        cpf_digits=cpf_digits_strategy(),
        extra_chars=st.text(alphabet=st.characters(whitelist_categories=('P',)), min_size=0, max_size=5)
    )
    @settings(max_examples=100)
    def test_cpf_with_extra_formatting_accepted(self, cpf_digits: str, extra_chars: str):
        """
        Property 5: CPF validation handles various formatting.
        
        **Validates: Requirements 2.2**
        
        Test that CPF validation strips non-numeric characters correctly.
        """
        # Add extra formatting characters
        formatted = cpf_digits[:3] + extra_chars + cpf_digits[3:6] + extra_chars + cpf_digits[6:]
        
        # Should still be accepted (non-numeric chars are stripped)
        result = ValidationService.validate_cpf(formatted)
        
        # Result should be properly formatted
        assert len(result) == 14
        result_digits = re.sub(r'\D', '', result)
        assert result_digits == cpf_digits


class TestSanitizationProperties:
    """Additional property tests for sanitization behavior."""
    
    @given(text=st.text(min_size=0, max_size=100))
    @settings(max_examples=100)
    def test_sanitization_preserves_or_rejects(self, text: str):
        """
        Property: Sanitization either preserves safe content or rejects unsafe content.
        
        **Validates: Requirements 2.1**
        
        Test that sanitization is deterministic and consistent.
        """
        try:
            result1 = ValidationService.sanitize_string(text)
            result2 = ValidationService.sanitize_string(text)
            
            # Same input should always produce same output
            assert result1 == result2
        except ValidationError as e1:
            # If it fails once, it should always fail
            with pytest.raises(ValidationError):
                ValidationService.sanitize_string(text)
    
    @given(
        text=safe_string_strategy(),
        max_length=st.integers(min_value=10, max_value=500)
    )
    @settings(max_examples=100)
    def test_sanitization_respects_max_length(self, text: str, max_length: int):
        """
        Property: Sanitization respects max_length parameter.
        
        **Validates: Requirements 2.1**
        
        Test that sanitized strings never exceed specified max_length.
        """
        try:
            result = ValidationService.sanitize_string(text, max_length=max_length)
            assert len(result) <= max_length
        except ValidationError as e:
            # If rejected, it should be due to length
            if len(text.strip()) > max_length:
                assert "length" in str(e).lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
