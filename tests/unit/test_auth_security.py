"""Unit tests for authentication security features.

This module tests password policy enforcement, account lockout mechanisms,
and password hash uniqueness to ensure secure authentication.
"""

import pytest
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.auth_service import PasswordPolicy, AuthService
from src.domain.user import User, UserCreate
from src.exceptions import ValidationError, DuplicateError


class TestPasswordPolicy:
    """Test password policy validation for security requirements."""
    
    def test_minimum_length_requirement(self):
        """Test that passwords must be at least 12 characters."""
        # Test passwords below minimum length
        short_passwords = [
            "Short1!",      # 7 chars
            "Pass1!",       # 6 chars
            "Abcd123!",     # 8 chars
            "MyPass123!",   # 11 chars
        ]
        
        for password in short_passwords:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is False, f"Password '{password}' should be rejected for being too short"
            assert "at least 12 characters" in error
    
    def test_minimum_length_boundary(self):
        """Test password length boundary at exactly 12 characters."""
        # Exactly 12 characters with all requirements
        password = "Abcdefgh123!"
        is_valid, error = PasswordPolicy.validate(password)
        assert is_valid is True
        assert error == ""
    
    def test_uppercase_requirement(self):
        """Test that passwords must contain at least one uppercase letter."""
        passwords_without_uppercase = [
            "mysecurep@ssw0rd",
            "alllowercase123!",
            "no_uppercase_123!",
        ]
        
        for password in passwords_without_uppercase:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is False
            assert "uppercase letter" in error.lower()
    
    def test_lowercase_requirement(self):
        """Test that passwords must contain at least one lowercase letter."""
        passwords_without_lowercase = [
            "MYSECUREP@SSW0RD",
            "ALLUPPERCASE123!",
            "NO_LOWERCASE_123!",
        ]
        
        for password in passwords_without_lowercase:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is False
            assert "lowercase letter" in error.lower()
    
    def test_digit_requirement(self):
        """Test that passwords must contain at least one digit."""
        passwords_without_digit = [
            "MySecureP@ssword",
            "NoDigitsHere!@#",
            "OnlyLetters!@#$",
        ]
        
        for password in passwords_without_digit:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is False
            assert "digit" in error.lower()
    
    def test_special_character_requirement(self):
        """Test that passwords must contain at least one special character."""
        passwords_without_special = [
            "MySecurePassw0rd",
            "NoSpecialChars123",
            "OnlyAlphanumeric123",
        ]
        
        for password in passwords_without_special:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is False
            assert "special character" in error.lower()
    
    def test_all_special_characters_accepted(self):
        """Test that all defined special characters are accepted."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        for char in special_chars:
            password = f"MyPassword123{char}"
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is True, f"Password with special char '{char}' should be valid"
            assert error == ""
    
    def test_valid_passwords_with_all_requirements(self):
        """Test various valid passwords that meet all requirements."""
        valid_passwords = [
            "Abcdefgh123!",           # Minimum length
            "P@ssw0rd1234",           # Common pattern
            "MyStr0ng#Pass",          # Mixed case
            "Secure123$Password",     # Longer password
            "C0mpl3x!Passw0rd",       # Complex password
            "Test_User_123!",         # With underscores
            "Admin@2024Pass",         # With year
            "Super^Secure#99",        # Multiple special chars
        ]
        
        for password in valid_passwords:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid is True, f"Password '{password}' should be valid but got error: {error}"
            assert error == ""
    
    def test_password_complexity_combinations(self):
        """Test various combinations of password complexity requirements."""
        # Missing one requirement each
        test_cases = [
            ("abcdefgh123!", False, "uppercase"),  # No uppercase
            ("ABCDEFGH123!", False, "lowercase"),  # No lowercase
            ("Abcdefghijk!", False, "digit"),      # No digit (12 chars)
            ("Abcdefgh1234", False, "special"),    # No special char
            ("Short1!", False, "12 characters"),   # Too short
        ]
        
        for password, should_be_valid, missing_requirement in test_cases:
            is_valid, error = PasswordPolicy.validate(password)
            assert is_valid == should_be_valid
            if not should_be_valid:
                assert missing_requirement.lower() in error.lower()
    
    def test_password_policy_constants(self):
        """Test that password policy constants are correctly defined."""
        assert PasswordPolicy.MIN_LENGTH == 12
        assert PasswordPolicy.REQUIRE_UPPERCASE is True
        assert PasswordPolicy.REQUIRE_LOWERCASE is True
        assert PasswordPolicy.REQUIRE_DIGIT is True
        assert PasswordPolicy.REQUIRE_SPECIAL is True
        assert len(PasswordPolicy.SPECIAL_CHARS) > 0


class TestAccountLockout:
    """Test account lockout mechanism after failed login attempts."""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Create mock user repository."""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_audit_repo(self):
        """Create mock audit repository."""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Create mock rate limiter."""
        limiter = AsyncMock()
        limiter.check_login_attempt = AsyncMock(return_value=True)
        return limiter
    
    @pytest.fixture
    def mock_encryption(self):
        """Create mock encryption service."""
        encryption = MagicMock()
        encryption.encrypt = MagicMock(return_value="encrypted_data")
        return encryption
    
    @pytest.fixture
    def auth_service(self, mock_user_repo, mock_audit_repo, mock_rate_limiter, mock_encryption):
        """Create auth service with mocked dependencies."""
        return AuthService(
            user_repo=mock_user_repo,
            audit_repo=mock_audit_repo,
            rate_limiter=mock_rate_limiter,
            encryption=mock_encryption
        )
    
    @pytest.mark.asyncio
    async def test_account_locks_after_max_failed_attempts(
        self, auth_service, mock_user_repo, mock_audit_repo
    ):
        """Test that account locks after reaching maximum failed attempts."""
        # Create user with 4 failed attempts (one away from lockout)
        user = User(
            id=1,
            username="testuser",
            password_hash=bcrypt.hashpw(b"correct_password", bcrypt.gensalt()).decode(),
            failed_login_attempts=4,
            locked_until=None,
            is_active=True
        )
        
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_user_repo.increment_failed_attempts = AsyncMock()
        mock_user_repo.lock_account = AsyncMock()
        
        # Attempt login with wrong password (5th failed attempt)
        success, message, token = await auth_service.authenticate(
            username="testuser",
            password="wrong_password",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify account was locked
        assert success is False
        assert "locked" in message.lower()
        assert "30 minutes" in message
        assert token is None
        
        # Verify lock_account was called
        mock_user_repo.lock_account.assert_called_once()
        call_args = mock_user_repo.lock_account.call_args
        assert call_args[0][0] == 1  # user_id
        
        # Verify lockout time is approximately 30 minutes from now
        lockout_time = call_args[0][1]
        expected_lockout = datetime.now() + timedelta(minutes=30)
        time_diff = abs((lockout_time - expected_lockout).total_seconds())
        assert time_diff < 5, "Lockout time should be approximately 30 minutes from now"
        
        # Verify audit log was called
        mock_audit_repo.log_failed_login.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_locked_account_rejects_login(
        self, auth_service, mock_user_repo, mock_audit_repo
    ):
        """Test that locked accounts cannot log in even with correct password."""
        # Create locked user
        lockout_time = datetime.now() + timedelta(minutes=15)
        user = User(
            id=1,
            username="testuser",
            password_hash=bcrypt.hashpw(b"correct_password", bcrypt.gensalt()).decode(),
            failed_login_attempts=5,
            locked_until=lockout_time,
            is_active=True
        )
        
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        
        # Attempt login with correct password
        success, message, token = await auth_service.authenticate(
            username="testuser",
            password="correct_password",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify login was rejected
        assert success is False
        assert "locked" in message.lower()
        assert "15 minutes" in message or "14 minutes" in message  # Allow for timing variance
        assert token is None
    
    @pytest.mark.asyncio
    async def test_account_unlocks_after_timeout(
        self, auth_service, mock_user_repo, mock_audit_repo
    ):
        """Test that account can log in after lockout period expires."""
        # Create user with expired lockout
        lockout_time = datetime.now() - timedelta(minutes=1)  # Expired 1 minute ago
        correct_password = "TestPassword123!"
        password_hash = bcrypt.hashpw(correct_password.encode(), bcrypt.gensalt()).decode()
        
        user = User(
            id=1,
            username="testuser",
            password_hash=password_hash,
            failed_login_attempts=5,
            locked_until=lockout_time,
            is_active=True
        )
        
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_user_repo.reset_failed_attempts = AsyncMock()
        mock_user_repo.create_session = AsyncMock()
        mock_user_repo.update_last_login = AsyncMock()
        
        # Attempt login with correct password
        success, message, token = await auth_service.authenticate(
            username="testuser",
            password=correct_password,
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify login was successful
        assert success is True
        assert "successful" in message.lower()
        assert token is not None
        
        # Verify failed attempts were reset
        mock_user_repo.reset_failed_attempts.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_failed_attempts_increment_on_wrong_password(
        self, auth_service, mock_user_repo, mock_audit_repo
    ):
        """Test that failed login attempts are incremented on wrong password."""
        user = User(
            id=1,
            username="testuser",
            password_hash=bcrypt.hashpw(b"correct_password", bcrypt.gensalt()).decode(),
            failed_login_attempts=2,
            locked_until=None,
            is_active=True
        )
        
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_user_repo.increment_failed_attempts = AsyncMock()
        
        # Attempt login with wrong password
        success, message, token = await auth_service.authenticate(
            username="testuser",
            password="wrong_password",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify login failed
        assert success is False
        assert token is None
        
        # Verify failed attempts were incremented
        mock_user_repo.increment_failed_attempts.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_failed_attempts_reset_on_successful_login(
        self, auth_service, mock_user_repo, mock_audit_repo
    ):
        """Test that failed attempts are reset to 0 on successful login."""
        correct_password = "TestPassword123!"
        password_hash = bcrypt.hashpw(correct_password.encode(), bcrypt.gensalt()).decode()
        
        user = User(
            id=1,
            username="testuser",
            password_hash=password_hash,
            failed_login_attempts=3,
            locked_until=None,
            is_active=True
        )
        
        mock_user_repo.get_by_username = AsyncMock(return_value=user)
        mock_user_repo.reset_failed_attempts = AsyncMock()
        mock_user_repo.create_session = AsyncMock()
        mock_user_repo.update_last_login = AsyncMock()
        
        # Attempt login with correct password
        success, message, token = await auth_service.authenticate(
            username="testuser",
            password=correct_password,
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        # Verify login was successful
        assert success is True
        assert token is not None
        
        # Verify failed attempts were reset
        mock_user_repo.reset_failed_attempts.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_lockout_duration_constant(self, auth_service):
        """Test that lockout duration constant is correctly set."""
        assert auth_service.LOCKOUT_DURATION_MINUTES == 30
        assert auth_service.MAX_FAILED_ATTEMPTS == 5


class TestPasswordHashUniqueness:
    """Test password hash uniqueness to ensure proper salt usage."""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Create mock user repository."""
        repo = AsyncMock()
        repo.get_by_username = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_audit_repo(self):
        """Create mock audit repository."""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Create mock rate limiter."""
        limiter = AsyncMock()
        return limiter
    
    @pytest.fixture
    def mock_encryption(self):
        """Create mock encryption service."""
        encryption = MagicMock()
        return encryption
    
    @pytest.fixture
    def auth_service(self, mock_user_repo, mock_audit_repo, mock_rate_limiter, mock_encryption):
        """Create auth service with mocked dependencies."""
        return AuthService(
            user_repo=mock_user_repo,
            audit_repo=mock_audit_repo,
            rate_limiter=mock_rate_limiter,
            encryption=mock_encryption
        )
    
    def test_same_password_produces_different_hashes(self, auth_service):
        """Test that hashing the same password multiple times produces different hashes.
        
        This ensures that bcrypt is using proper salt randomness.
        """
        password = "TestPassword123!"
        
        # Hash the same password multiple times
        hash1 = auth_service._hash_password(password)
        hash2 = auth_service._hash_password(password)
        hash3 = auth_service._hash_password(password)
        
        # Verify all hashes are different
        assert hash1 != hash2, "Same password should produce different hashes"
        assert hash1 != hash3, "Same password should produce different hashes"
        assert hash2 != hash3, "Same password should produce different hashes"
        
        # Verify all hashes are valid bcrypt hashes
        assert hash1.startswith('$2b$'), "Hash should be bcrypt format"
        assert hash2.startswith('$2b$'), "Hash should be bcrypt format"
        assert hash3.startswith('$2b$'), "Hash should be bcrypt format"
        
        # Verify all hashes can verify the original password
        assert auth_service._verify_password(password, hash1)
        assert auth_service._verify_password(password, hash2)
        assert auth_service._verify_password(password, hash3)
    
    def test_different_passwords_produce_different_hashes(self, auth_service):
        """Test that different passwords produce different hashes."""
        passwords = [
            "TestPassword123!",
            "DifferentPass456@",
            "AnotherOne789#",
        ]
        
        hashes = [auth_service._hash_password(pwd) for pwd in passwords]
        
        # Verify all hashes are unique
        assert len(hashes) == len(set(hashes)), "Different passwords should produce different hashes"
        
        # Verify each hash only verifies its own password
        for i, password in enumerate(passwords):
            for j, hash_value in enumerate(hashes):
                if i == j:
                    assert auth_service._verify_password(password, hash_value)
                else:
                    assert not auth_service._verify_password(password, hash_value)
    
    def test_hash_format_is_bcrypt(self, auth_service):
        """Test that password hashes use bcrypt format."""
        password = "TestPassword123!"
        hash_value = auth_service._hash_password(password)
        
        # Bcrypt hashes start with $2b$ and have specific length
        assert hash_value.startswith('$2b$'), "Hash should use bcrypt format"
        assert len(hash_value) == 60, "Bcrypt hash should be 60 characters"
    
    def test_hash_contains_salt(self, auth_service):
        """Test that password hashes contain embedded salt."""
        password = "TestPassword123!"
        
        # Generate multiple hashes
        hashes = [auth_service._hash_password(password) for _ in range(5)]
        
        # Extract salt from each hash (bcrypt format: $2b$rounds$salt+hash)
        salts = [h[:29] for h in hashes]  # Salt is in first 29 characters
        
        # Verify all salts are different
        assert len(salts) == len(set(salts)), "Each hash should have a unique salt"
    
    @pytest.mark.asyncio
    async def test_multiple_users_same_password_different_hashes(
        self, auth_service, mock_user_repo, mock_audit_repo
    ):
        """Test that multiple users with the same password get different hashes."""
        password = "SharedPassword123!"
        
        # Track the hashes that would be stored
        stored_hashes = []
        
        def capture_hash(*args, **kwargs):
            # Capture the password_hash argument
            stored_hashes.append(kwargs.get('password_hash'))
            # Return a mock user
            return User(
                id=len(stored_hashes),
                username=kwargs.get('username'),
                password_hash=kwargs.get('password_hash'),
                is_active=True,
                failed_login_attempts=0
            )
        
        mock_user_repo.create = AsyncMock(side_effect=capture_hash)
        mock_audit_repo.log_create = AsyncMock()
        
        # Register multiple users with the same password
        users_data = [
            UserCreate(username="user1", password=password, role="user"),
            UserCreate(username="user2", password=password, role="user"),
            UserCreate(username="user3", password=password, role="user"),
        ]
        
        for user_data in users_data:
            await auth_service.register_user(user_data, created_by=1)
        
        # Verify all hashes are different
        assert len(stored_hashes) == 3
        assert len(set(stored_hashes)) == 3, "Same password for different users should produce different hashes"
        
        # Verify all hashes can verify the original password
        for hash_value in stored_hashes:
            assert auth_service._verify_password(password, hash_value)
