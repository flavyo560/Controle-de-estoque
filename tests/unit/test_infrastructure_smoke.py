"""Smoke tests for infrastructure components."""

import pytest
from src.infrastructure.encryption import EncryptionService
from src.infrastructure.cache import CacheManager
from src.infrastructure.rate_limiter import RateLimiter


def test_encryption_service_instantiation():
    """Test that EncryptionService can be instantiated."""
    master_key = EncryptionService.generate_master_key()
    service = EncryptionService(master_key)
    assert service is not None


def test_encryption_round_trip():
    """Test encryption and decryption round-trip."""
    master_key = EncryptionService.generate_master_key()
    service = EncryptionService(master_key)
    
    plaintext = "sensitive data"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)
    
    assert decrypted == plaintext
    assert encrypted != plaintext


def test_cache_manager_instantiation():
    """Test that CacheManager can be instantiated."""
    cache = CacheManager(backend="memory")
    assert cache is not None


@pytest.mark.anyio
async def test_cache_basic_operations():
    """Test basic cache operations."""
    cache = CacheManager(backend="memory")
    
    # Set and get
    await cache.set("test_key", "test_value", ttl=60)
    value = await cache.get("test_key")
    assert value == "test_value"
    
    # Delete
    await cache.delete("test_key")
    value = await cache.get("test_key")
    assert value is None


def test_rate_limiter_instantiation():
    """Test that RateLimiter can be instantiated."""
    limiter = RateLimiter()
    assert limiter is not None


@pytest.mark.anyio
async def test_rate_limiter_basic():
    """Test basic rate limiting."""
    limiter = RateLimiter()
    
    # First attempt should succeed
    allowed = await limiter.check_login_attempt("user1", "127.0.0.1", max_attempts=3, window_minutes=15)
    assert allowed is True
    
    # Second attempt should succeed
    allowed = await limiter.check_login_attempt("user1", "127.0.0.1", max_attempts=3, window_minutes=15)
    assert allowed is True
    
    # Third attempt should succeed
    allowed = await limiter.check_login_attempt("user1", "127.0.0.1", max_attempts=3, window_minutes=15)
    assert allowed is True
    
    # Fourth attempt should fail (exceeded limit)
    allowed = await limiter.check_login_attempt("user1", "127.0.0.1", max_attempts=3, window_minutes=15)
    assert allowed is False
