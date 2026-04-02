"""Rate limiting for login attempts and API calls using sliding window."""

from typing import Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio


class RateLimiter:
    """Rate limiting for login attempts and API calls with sliding window algorithm."""
    
    def __init__(self):
        """Initialize rate limiter with in-memory storage."""
        # In-memory storage (use Redis in production for distributed systems)
        self._login_attempts: Dict[str, list] = defaultdict(list)
        self._api_calls: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def check_login_attempt(
        self,
        username: str,
        ip_address: str,
        max_attempts: int = 5,
        window_minutes: int = 15
    ) -> bool:
        """
        Check if login attempt is allowed using sliding window.
        
        Args:
            username: Username attempting login
            ip_address: IP address of request
            max_attempts: Maximum attempts allowed (default: 5)
            window_minutes: Time window in minutes (default: 15)
            
        Returns:
            True if attempt is allowed, False if rate limit exceeded
        """
        async with self._lock:
            key = f"{username}:{ip_address}"
            now = datetime.now()
            cutoff = now - timedelta(minutes=window_minutes)
            
            # Remove old attempts outside the sliding window
            self._login_attempts[key] = [
                attempt for attempt in self._login_attempts[key]
                if attempt > cutoff
            ]
            
            # Check if limit exceeded
            if len(self._login_attempts[key]) >= max_attempts:
                return False
            
            # Record attempt
            self._login_attempts[key].append(now)
            return True
    
    async def reset_login_attempts(self, username: str, ip_address: str) -> None:
        """
        Reset login attempts for successful login.
        
        Args:
            username: Username that successfully logged in
            ip_address: IP address of successful login
        """
        async with self._lock:
            key = f"{username}:{ip_address}"
            if key in self._login_attempts:
                del self._login_attempts[key]
    
    async def check_api_rate_limit(
        self,
        user_id: int,
        endpoint: str,
        max_calls: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """
        Check API rate limit using sliding window.
        
        Args:
            user_id: User making the request
            endpoint: API endpoint being called
            max_calls: Maximum calls allowed (default: 100)
            window_seconds: Time window in seconds (default: 60)
            
        Returns:
            Tuple of (is_allowed, remaining_calls)
        """
        async with self._lock:
            key = f"{user_id}:{endpoint}"
            now = datetime.now()
            cutoff = now - timedelta(seconds=window_seconds)
            
            # Remove old calls outside the sliding window
            self._api_calls[key] = [
                call for call in self._api_calls[key]
                if call > cutoff
            ]
            
            current_calls = len(self._api_calls[key])
            
            # Check if limit would be exceeded by this call
            if current_calls >= max_calls:
                return False, 0
            
            # Record call
            self._api_calls[key].append(now)
            remaining = max_calls - current_calls - 1
            return True, remaining
