"""Authentication service with security features."""

import re
import hashlib
import secrets
from typing import Tuple, Optional
from datetime import datetime, timedelta
import bcrypt

from src.domain.user import User, UserCreate
from src.repositories.user_repository import UserRepository
from src.repositories.audit_repository import AuditRepository
from src.infrastructure.rate_limiter import RateLimiter
from src.infrastructure.encryption import EncryptionService
from src.exceptions import ValidationError, DuplicateError, AuthenticationError


class PasswordPolicy:
    """Password policy enforcement for secure authentication."""
    
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @classmethod
    def validate(cls, password: str) -> Tuple[bool, str]:
        """
        Validate password against policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters"
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if cls.REQUIRE_SPECIAL and not any(c in cls.SPECIAL_CHARS for c in password):
            return False, f"Password must contain at least one special character: {cls.SPECIAL_CHARS}"
        
        return True, ""


class AuthService:
    """Authentication service with security features."""
    
    SESSION_DURATION_HOURS = 8
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    def __init__(
        self,
        user_repo: UserRepository,
        audit_repo: AuditRepository,
        rate_limiter: RateLimiter,
        encryption: EncryptionService
    ):
        """
        Initialize authentication service.
        
        Args:
            user_repo: User repository for database access
            audit_repo: Audit repository for logging
            rate_limiter: Rate limiter for login attempts
            encryption: Encryption service for session tokens
        """
        self.user_repo = user_repo
        self.audit_repo = audit_repo
        self.rate_limiter = rate_limiter
        self.encryption = encryption
    
    async def register_user(
        self,
        user_data: UserCreate,
        created_by: int
    ) -> User:
        """
        Register a new user with password validation.
        
        Args:
            user_data: User creation data with password
            created_by: ID of user creating this account
            
        Returns:
            Created user
            
        Raises:
            ValidationError: If password doesn't meet policy
            DuplicateError: If username already exists
        """
        # Validate password policy
        is_valid, error = PasswordPolicy.validate(user_data.password)
        if not is_valid:
            raise ValidationError(error)
        
        # Check for duplicate username
        existing = await self.user_repo.get_by_username(user_data.username)
        if existing:
            raise DuplicateError(f"Username {user_data.username} already exists")
        
        # Hash password with bcrypt
        password_hash = self._hash_password(user_data.password)
        
        # Create user
        user = await self.user_repo.create(
            username=user_data.username,
            password_hash=password_hash,
            full_name=user_data.full_name,
            email=user_data.email,
            role=user_data.role
        )
        
        # Audit trail
        if user.id is not None:
            await self.audit_repo.log_create(
                table="users",
                record_id=user.id,
                user_id=created_by,
                data={"username": user.username, "role": user.role}
            )
        
        return user
    
    async def authenticate(
        self,
        username: str,
        password: str,
        ip_address: str,
        user_agent: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Authenticate user with rate limiting and account lockout.
        
        Args:
            username: Username to authenticate
            password: Password to verify
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Tuple of (success, message, session_token)
        """
        # Check rate limit
        if not await self.rate_limiter.check_login_attempt(username, ip_address):
            await self.audit_repo.log_failed_login(
                username=username,
                ip_address=ip_address,
                reason="rate_limit_exceeded",
                user_agent=user_agent
            )
            return False, "Too many login attempts. Please try again later.", None
        
        # Get user
        user = await self.user_repo.get_by_username(username)
        if not user:
            await self.audit_repo.log_failed_login(
                username=username,
                ip_address=ip_address,
                reason="user_not_found",
                user_agent=user_agent
            )
            return False, "Invalid username or password", None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now():
            remaining = (user.locked_until - datetime.now()).seconds // 60
            return False, f"Account is locked. Try again in {remaining} minutes.", None
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            # Increment failed attempts
            if user.id is not None:
                await self.user_repo.increment_failed_attempts(user.id)
            
            # Lock account if threshold exceeded
            if user.failed_login_attempts + 1 >= self.MAX_FAILED_ATTEMPTS:
                lockout_until = datetime.now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                if user.id is not None:
                    await self.user_repo.lock_account(user.id, lockout_until)
                
                await self.audit_repo.log_failed_login(
                    username=username,
                    ip_address=ip_address,
                    reason="account_locked",
                    user_agent=user_agent
                )
                
                return False, f"Account locked due to too many failed attempts. Try again in {self.LOCKOUT_DURATION_MINUTES} minutes.", None
            
            await self.audit_repo.log_failed_login(
                username=username,
                ip_address=ip_address,
                reason="invalid_password",
                user_agent=user_agent
            )
            
            return False, "Invalid username or password", None
        
        # Reset failed attempts on successful login
        if user.id is None:
            raise AuthenticationError("User ID is missing")
        
        await self.user_repo.reset_failed_attempts(user.id)
        
        # Create session
        session_token = await self._create_session(user.id, ip_address, user_agent)
        
        # Update last login
        await self.user_repo.update_last_login(user.id)
        
        # Audit trail
        await self.audit_repo.log_login(
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return True, "Login successful", session_token
    
    async def _create_session(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str
    ) -> str:
        """
        Create encrypted session token.
        
        Args:
            user_id: User ID for the session
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Session token
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Hash token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Encrypt session data
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
        encrypted_data = self.encryption.encrypt(str(session_data))
        
        # Store session
        expires_at = datetime.now() + timedelta(hours=self.SESSION_DURATION_HOURS)
        await self.user_repo.create_session(
            user_id=user_id,
            token_hash=token_hash,
            encrypted_data=encrypted_data,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        return token
    
    async def validate_session(self, token: str) -> Tuple[bool, Optional[User]]:
        """
        Validate session token and return user.
        
        Args:
            token: Session token to validate
            
        Returns:
            Tuple of (is_valid, user)
        """
        # Hash token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Get session
        session = await self.user_repo.get_session_by_token(token_hash)
        if not session:
            return False, None
        
        # Check expiration
        if session.expires_at < datetime.now():
            await self.user_repo.revoke_session(session.id)
            return False, None
        
        # Get user
        user = await self.user_repo.get_by_id(session.user_id)
        if not user or not user.is_active:
            return False, None
        
        return True, user
    
    async def logout(
        self,
        token: str,
        ip_address: str,
        user_agent: str
    ) -> bool:
        """
        Logout user by revoking session.
        
        Args:
            token: Session token to revoke
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            True if logout successful, False otherwise
        """
        # Hash token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Get session
        session = await self.user_repo.get_session_by_token(token_hash)
        if not session:
            return False
        
        # Revoke session
        await self.user_repo.revoke_session(session.id)
        
        # Audit trail
        await self.audit_repo.log_logout(
            user_id=session.user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return True
    
    def _hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hashed password
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Bcrypt hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode(), password_hash.encode())
