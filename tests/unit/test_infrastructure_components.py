"""Comprehensive unit tests for infrastructure components.

**Validates: Requirements 1.3, 1.4, 5.3, 9.1**

These tests verify that infrastructure components (encryption, cache, rate limiter)
work correctly in isolation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.infrastructure.encryption import EncryptionService
from src.infrastructure.cache import CacheManager
from src.infrastructure.rate_limiter import RateLimiter


class TestEncryptionService:
    """Tests for encryption/decryption functionality."""
    
    def test_encryption_round_trip(self):
        """
        Test encryption/decryption round-trip.
        
        **Validates: Requirements 1.3, 9.1**
        
        Verify that encrypt(decrypt(x)) == x for any plaintext.
        """
        master_key = EncryptionService.generate_master_key()
        service = EncryptionService(master_key)
        
        test_cases = [
            "simple text",
            "text with special chars: !@#$%^&*()",
            "números e acentos: 123 áéíóú",
            "empty string should work too: ",
            "a" * 1000,  # Long text
            '{"json": "data", "number": 123}',  # JSON-like data
        ]
        
        for plaintext in test_cases:
            encrypted = service.encrypt(plaintext)
            decrypted = service.decrypt(encrypted)
            
            assert decrypted == plaintext, f"Round-trip failed for: {plaintext[:50]}"
            assert encrypted != plaintext, "Encrypted text should differ from plaintext"
    
    def test_encryption_produces_different_ciphertext(self):
        """
        Test that encrypting the same plaintext produces different ciphertext.
        
        **Validates: Requirements 1.3, 9.1**
        
        This verifies that encryption uses proper initialization vectors (IVs)
        or nonces, making each encryption unique even for the same input.
        """
        master_key = EncryptionService.generate_master_key()
        service = EncryptionService(master_key)
        
        plaintext = "same text encrypted twice"
        
        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)
        
        # Ciphertexts should be different (due to random IV/nonce)
        assert encrypted1 != encrypted2, "Same plaintext should produce different ciphertexts"
        
        # But both should decrypt to the same plaintext
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext
    
    def test_encryption_with_different_keys(self):
        """
        Test that different keys produce different results.
        
        **Validates: Requirements 1.3, 9.1**
        """
        key1 = EncryptionService.generate_master_key()
        key2 = EncryptionService.generate_master_key()
        
        service1 = EncryptionService(key1)
        service2 = EncryptionService(key2)
        
        plaintext = "secret message"
        
        encrypted1 = service1.encrypt(plaintext)
        encrypted2 = service2.encrypt(plaintext)
        
        # Different keys should produce different ciphertexts
        assert encrypted1 != encrypted2
        
        # Each service can only decrypt its own ciphertext
        assert service1.decrypt(encrypted1) == plaintext
        assert service2.decrypt(encrypted2) == plaintext
        
        # Cross-decryption should fail
        with pytest.raises(Exception):
            service1.decrypt(encrypted2)
        
        with pytest.raises(Exception):
            service2.decrypt(encrypted1)
    
    def test_master_key_generation(self):
        """
        Test master key generation.
        
        **Validates: Requirements 1.3, 9.1**
        """
        key1 = EncryptionService.generate_master_key()
        key2 = EncryptionService.generate_master_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should have correct length (44 chars for base64 encoded 32 bytes)
        assert len(key1) == 44
        assert len(key2) == 44
    
    def test_encryption_empty_string(self):
        """
        Test encryption of empty string.
        
        **Validates: Requirements 1.3, 9.1**
        """
        master_key = EncryptionService.generate_master_key()
        service = EncryptionService(master_key)
        
        plaintext = ""
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext


class TestCacheManager:
    """Tests for cache functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """
        Test cache entries expire after TTL.
        
        **Validates: Requirements 5.3, 9.1**
        
        Verify that cached values are automatically removed after
        their time-to-live (TTL) expires.
        """
        cache = CacheManager(backend="memory")
        
        # Set value with 1 second TTL
        await cache.set("test_key", "test_value", ttl=1)
        
        # Value should be available immediately
        value = await cache.get("test_key")
        assert value == "test_value"
        
        # Wait for TTL to expire
        await asyncio.sleep(1.5)
        
        # Value should be None after expiration
        value = await cache.get("test_key")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_cache_returns_none_for_expired_entries(self):
        """
        Test cache returns None for expired entries.
        
        **Validates: Requirements 5.3, 9.1**
        """
        cache = CacheManager(backend="memory")
        
        # Set multiple values with different TTLs
        await cache.set("short_ttl", "value1", ttl=1)
        await cache.set("long_ttl", "value2", ttl=10)
        
        # Both should be available initially
        assert await cache.get("short_ttl") == "value1"
        assert await cache.get("long_ttl") == "value2"
        
        # Wait for short TTL to expire
        await asyncio.sleep(1.5)
        
        # Short TTL should be None, long TTL should still exist
        assert await cache.get("short_ttl") is None
        assert await cache.get("long_ttl") == "value2"
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """
        Test basic cache set and get operations.
        
        **Validates: Requirements 5.3, 9.1**
        """
        cache = CacheManager(backend="memory")
        
        # Test with different data types
        test_cases = [
            ("string_key", "string_value"),
            ("int_key", 12345),
            ("float_key", 123.45),
            ("bool_key", True),
            ("list_key", [1, 2, 3, 4, 5]),
            ("dict_key", {"name": "test", "value": 123}),
            ("none_key", None),
        ]
        
        for key, value in test_cases:
            await cache.set(key, value, ttl=60)
            retrieved = await cache.get(key)
            assert retrieved == value, f"Failed for key={key}, value={value}"
    
    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """
        Test cache delete operation.
        
        **Validates: Requirements 5.3, 9.1**
        """
        cache = CacheManager(backend="memory")
        
        # Set value
        await cache.set("test_key", "test_value", ttl=60)
        assert await cache.get("test_key") == "test_value"
        
        # Delete value
        await cache.delete("test_key")
        assert await cache.get("test_key") is None
    
    @pytest.mark.asyncio
    async def test_cache_invalidate_pattern(self):
        """
        Test cache pattern invalidation.
        
        **Validates: Requirements 5.3, 9.1**
        """
        cache = CacheManager(backend="memory")
        
        # Set multiple keys with pattern
        await cache.set("product:1", "value1", ttl=60)
        await cache.set("product:2", "value2", ttl=60)
        await cache.set("product:3", "value3", ttl=60)
        await cache.set("user:1", "user_value", ttl=60)
        
        # Verify all are set
        assert await cache.get("product:1") == "value1"
        assert await cache.get("product:2") == "value2"
        assert await cache.get("product:3") == "value3"
        assert await cache.get("user:1") == "user_value"
        
        # Invalidate product pattern
        await cache.invalidate_pattern("product:*")
        
        # Product keys should be gone, user key should remain
        assert await cache.get("product:1") is None
        assert await cache.get("product:2") is None
        assert await cache.get("product:3") is None
        assert await cache.get("user:1") == "user_value"
    
    @pytest.mark.asyncio
    async def test_cache_overwrite_existing_key(self):
        """
        Test overwriting existing cache key.
        
        **Validates: Requirements 5.3, 9.1**
        """
        cache = CacheManager(backend="memory")
        
        # Set initial value
        await cache.set("test_key", "value1", ttl=60)
        assert await cache.get("test_key") == "value1"
        
        # Overwrite with new value
        await cache.set("test_key", "value2", ttl=60)
        assert await cache.get("test_key") == "value2"
    
    @pytest.mark.asyncio
    async def test_cache_nonexistent_key(self):
        """
        Test getting nonexistent key returns None.
        
        **Validates: Requirements 5.3, 9.1**
        """
        cache = CacheManager(backend="memory")
        
        value = await cache.get("nonexistent_key")
        assert value is None


class TestRateLimiter:
    """Tests for rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_sliding_window(self):
        """
        Test rate limiter sliding window behavior.
        
        **Validates: Requirements 1.4, 9.1**
        
        Verify that the rate limiter correctly implements a sliding window
        that blocks requests after the limit is exceeded.
        """
        limiter = RateLimiter()
        
        username = "test_user"
        ip_address = "192.168.1.1"
        max_attempts = 3
        window_minutes = 15
        
        # First 3 attempts should succeed
        for i in range(max_attempts):
            allowed = await limiter.check_login_attempt(
                username, ip_address, max_attempts, window_minutes
            )
            assert allowed is True, f"Attempt {i+1} should be allowed"
        
        # 4th attempt should be blocked
        allowed = await limiter.check_login_attempt(
            username, ip_address, max_attempts, window_minutes
        )
        assert allowed is False, "4th attempt should be blocked"
        
        # 5th attempt should also be blocked
        allowed = await limiter.check_login_attempt(
            username, ip_address, max_attempts, window_minutes
        )
        assert allowed is False, "5th attempt should be blocked"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_resets_after_time_window(self):
        """
        Test rate limiter resets after time window.
        
        **Validates: Requirements 1.4, 9.1**
        
        Verify that the rate limiter allows requests again after
        the time window expires.
        """
        limiter = RateLimiter()
        
        username = "test_user2"
        ip_address = "192.168.1.2"
        max_attempts = 2
        window_minutes = 1  # 1 minute window for faster testing
        
        # Use up the limit
        for i in range(max_attempts):
            allowed = await limiter.check_login_attempt(
                username, ip_address, max_attempts, window_minutes
            )
            assert allowed is True
        
        # Next attempt should be blocked
        allowed = await limiter.check_login_attempt(
            username, ip_address, max_attempts, window_minutes
        )
        assert allowed is False
        
        # Wait for window to expire (1 minute + buffer)
        # Note: In real tests, you might want to mock time instead
        # For now, we'll use a shorter window for testing
        await asyncio.sleep(61)
        
        # Should be allowed again after window expires
        allowed = await limiter.check_login_attempt(
            username, ip_address, max_attempts, window_minutes
        )
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_different_users_independent(self):
        """
        Test that different users have independent rate limits.
        
        **Validates: Requirements 1.4, 9.1**
        """
        limiter = RateLimiter()
        
        max_attempts = 2
        window_minutes = 15
        
        # User 1 uses up their limit
        for i in range(max_attempts):
            allowed = await limiter.check_login_attempt(
                "user1", "192.168.1.1", max_attempts, window_minutes
            )
            assert allowed is True
        
        # User 1 should be blocked
        allowed = await limiter.check_login_attempt(
            "user1", "192.168.1.1", max_attempts, window_minutes
        )
        assert allowed is False
        
        # User 2 should still be allowed (independent limit)
        allowed = await limiter.check_login_attempt(
            "user2", "192.168.1.2", max_attempts, window_minutes
        )
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_api_rate_limit(self):
        """
        Test API rate limiting.
        
        **Validates: Requirements 1.4, 9.1**
        """
        limiter = RateLimiter()
        
        user_id = 123
        endpoint = "/api/products"
        max_requests = 5
        window_seconds = 60
        
        # First 5 requests should succeed
        for i in range(max_requests):
            allowed, remaining = await limiter.check_api_rate_limit(
                user_id, endpoint, max_requests, window_seconds
            )
            assert allowed is True, f"Request {i+1} should be allowed"
            assert remaining >= 0, f"Remaining should be non-negative"
        
        # 6th request should be blocked
        allowed, remaining = await limiter.check_api_rate_limit(
            user_id, endpoint, max_requests, window_seconds
        )
        assert allowed is False, "6th request should be blocked"
        assert remaining == 0, "Remaining should be 0"
    
    @pytest.mark.asyncio
    async def test_rate_limiter_zero_attempts_blocks_immediately(self):
        """
        Test that max_attempts=0 blocks all requests.
        
        **Validates: Requirements 1.4, 9.1**
        """
        limiter = RateLimiter()
        
        # With max_attempts=0, first attempt should be blocked
        allowed = await limiter.check_login_attempt(
            "user", "192.168.1.1", max_attempts=0, window_minutes=15
        )
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_rate_limiter_high_limit_allows_many_requests(self):
        """
        Test that high limits allow many requests.
        
        **Validates: Requirements 1.4, 9.1**
        """
        limiter = RateLimiter()
        
        username = "power_user"
        ip_address = "192.168.1.100"
        max_attempts = 100
        window_minutes = 15
        
        # Should allow many attempts
        for i in range(50):
            allowed = await limiter.check_login_attempt(
                username, ip_address, max_attempts, window_minutes
            )
            assert allowed is True, f"Attempt {i+1} should be allowed"


class TestInfrastructureIntegration:
    """Integration tests for infrastructure components working together."""
    
    @pytest.mark.asyncio
    async def test_cache_and_encryption_together(self):
        """
        Test using cache and encryption together.
        
        **Validates: Requirements 1.3, 5.3, 9.1**
        """
        # Create services
        master_key = EncryptionService.generate_master_key()
        encryption = EncryptionService(master_key)
        cache = CacheManager(backend="memory")
        
        # Encrypt sensitive data
        sensitive_data = "user_password_hash"
        encrypted_data = encryption.encrypt(sensitive_data)
        
        # Store encrypted data in cache
        await cache.set("user:1:password", encrypted_data, ttl=60)
        
        # Retrieve and decrypt
        cached_encrypted = await cache.get("user:1:password")
        decrypted_data = encryption.decrypt(cached_encrypted)
        
        assert decrypted_data == sensitive_data
    
    @pytest.mark.asyncio
    async def test_rate_limiter_with_cache(self):
        """
        Test rate limiter with cache for storing encrypted data.
        
        **Validates: Requirements 1.4, 5.3, 9.1**
        """
        cache = CacheManager(backend="memory")
        limiter = RateLimiter()
        
        # Rate limiter should work independently
        allowed = await limiter.check_login_attempt(
            "user", "192.168.1.1", max_attempts=3, window_minutes=15
        )
        assert allowed is True
        
        # Cache can be used to store rate limit data if needed
        cache_key = "rate_limit:user:192.168.1.1"
        await cache.set(cache_key, {"attempts": 1}, ttl=900)
        cached_data = await cache.get(cache_key)
        assert cached_data == {"attempts": 1}


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
