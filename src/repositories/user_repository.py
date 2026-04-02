"""User repository for database access with security features."""

from typing import Optional
from datetime import datetime
from src.domain.user import User, UserCreate, Session
from src.infrastructure.database import DatabaseClient
from src.infrastructure.cache import CacheManager


class UserRepository:
    """Repository for user data access with parameterized queries."""
    
    def __init__(self, db_client: DatabaseClient, cache: Optional[CacheManager] = None):
        """
        Initialize user repository.
        
        Args:
            db_client: Database client for connection pooling
            cache: Optional cache manager for session caching
        """
        self.db = db_client
        self.cache = cache or CacheManager(backend="memory")
    
    async def create(
        self,
        username: str,
        password_hash: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        role: str = 'user'
    ) -> User:
        """
        Create a new user.
        
        Args:
            username: Unique username
            password_hash: Bcrypt hashed password
            full_name: User's full name
            email: User's email address
            role: User role (admin, manager, user)
            
        Returns:
            Created user
        """
        query = """
            INSERT INTO users (username, password_hash, full_name, email, role, password_changed_at)
            VALUES ($1, $2, $3, $4, $5, NOW())
            RETURNING id, username, password_hash, full_name, email, role, is_active,
                      failed_login_attempts, locked_until, last_login_at, password_changed_at,
                      created_at, updated_at, deleted_at
        """
        row = await self.db.fetch_one(query, username, password_hash, full_name, email, role)
        return User(**row)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User if found, None otherwise
        """
        query = """
            SELECT id, username, password_hash, full_name, email, role, is_active,
                   failed_login_attempts, locked_until, last_login_at, password_changed_at,
                   created_at, updated_at, deleted_at
            FROM users
            WHERE username = $1 AND deleted_at IS NULL
        """
        row = await self.db.fetch_one(query, username)
        return User(**row) if row else None
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User if found, None otherwise
        """
        query = """
            SELECT id, username, password_hash, full_name, email, role, is_active,
                   failed_login_attempts, locked_until, last_login_at, password_changed_at,
                   created_at, updated_at, deleted_at
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
        """
        row = await self.db.fetch_one(query, user_id)
        return User(**row) if row else None
    
    async def increment_failed_attempts(self, user_id: int) -> None:
        """
        Increment failed login attempts counter.
        
        Args:
            user_id: User ID to update
        """
        query = """
            UPDATE users
            SET failed_login_attempts = failed_login_attempts + 1
            WHERE id = $1
        """
        await self.db.execute(query, user_id)
    
    async def lock_account(self, user_id: int, locked_until: datetime) -> None:
        """
        Lock user account until specified time.
        
        Args:
            user_id: User ID to lock
            locked_until: Datetime when account will be unlocked
        """
        query = """
            UPDATE users
            SET locked_until = $2
            WHERE id = $1
        """
        await self.db.execute(query, user_id, locked_until)
    
    async def reset_failed_attempts(self, user_id: int) -> None:
        """
        Reset failed login attempts counter.
        
        Args:
            user_id: User ID to reset
        """
        query = """
            UPDATE users
            SET failed_login_attempts = 0, locked_until = NULL
            WHERE id = $1
        """
        await self.db.execute(query, user_id)
    
    async def update_last_login(self, user_id: int) -> None:
        """
        Update last login timestamp.
        
        Args:
            user_id: User ID to update
        """
        query = """
            UPDATE users
            SET last_login_at = NOW()
            WHERE id = $1
        """
        await self.db.execute(query, user_id)
    
    async def create_session(
        self,
        user_id: int,
        token_hash: str,
        encrypted_data: str,
        ip_address: str,
        user_agent: str,
        expires_at: datetime
    ) -> Session:
        """
        Create a new session.
        
        Args:
            user_id: User ID for the session
            token_hash: Hashed session token
            encrypted_data: Encrypted session data
            ip_address: IP address of the request
            user_agent: User agent string
            expires_at: Session expiration datetime
            
        Returns:
            Created session
        """
        query = """
            INSERT INTO sessions (user_id, token_hash, encrypted_data, ip_address, user_agent, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, user_id, token_hash, encrypted_data, ip_address, user_agent,
                      expires_at, created_at, revoked_at
        """
        row = await self.db.fetch_one(
            query, user_id, token_hash, encrypted_data, ip_address, user_agent, expires_at
        )
        return Session(**row)
    
    async def get_session_by_token(self, token_hash: str) -> Optional[Session]:
        """
        Get session by token hash with caching.
        
        Args:
            token_hash: Hashed session token
            
        Returns:
            Session if found and not revoked, None otherwise
        """
        # Try cache first
        cache_key = f"session:token:{token_hash}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Session(**cached)
        
        # Fetch from database
        query = """
            SELECT id, user_id, token_hash, encrypted_data, ip_address, user_agent,
                   expires_at, created_at, revoked_at
            FROM sessions
            WHERE token_hash = $1 AND revoked_at IS NULL
        """
        row = await self.db.fetch_one(query, token_hash)
        if row:
            session = Session(**row)
            await self._cache_session(session)
            return session
        return None
    
    async def revoke_session(self, session_id: int) -> None:
        """
        Revoke a session and invalidate cache.
        
        Args:
            session_id: Session ID to revoke
        """
        # Get token_hash before revoking
        get_query = """
            SELECT token_hash FROM sessions WHERE id = $1
        """
        row = await self.db.fetch_one(get_query, session_id)
        
        # Revoke session
        update_query = """
            UPDATE sessions
            SET revoked_at = NOW()
            WHERE id = $1
        """
        await self.db.execute(update_query, session_id)
        
        # Invalidate cache
        if row:
            await self._invalidate_session_cache(row["token_hash"])
    
    async def revoke_all_user_sessions(self, user_id: int) -> None:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id: User ID whose sessions to revoke
        """
        query = """
            UPDATE sessions
            SET revoked_at = NOW()
            WHERE user_id = $1 AND revoked_at IS NULL
        """
        await self.db.execute(query, user_id)

    async def _cache_session(self, session: Session) -> None:
        """
        Cache session data.
        
        Args:
            session: Session to cache
        """
        if not session.id:
            return
        
        cache_key = f"session:token:{session.token_hash}"
        # Cache until expiration
        ttl = int((session.expires_at - datetime.now()).total_seconds())
        if ttl > 0:
            await self.cache.set(
                cache_key,
                session.model_dump(),
                ttl=ttl
            )
    
    async def _invalidate_session_cache(self, token_hash: str) -> None:
        """
        Invalidate session cache.
        
        Args:
            token_hash: Session token hash
        """
        cache_key = f"session:token:{token_hash}"
        await self.cache.delete(cache_key)
