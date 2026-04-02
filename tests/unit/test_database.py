"""Unit tests for database client."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.infrastructure.database import DatabaseClient
import asyncpg


@pytest.fixture
def db_client():
    """Create database client instance."""
    return DatabaseClient(
        dsn="postgresql://user:pass@localhost/testdb",
        min_size=5,
        max_size=10,
        command_timeout=30.0
    )


class TestDatabaseClientInitialization:
    """Test suite for database client initialization."""
    
    def test_init_with_default_parameters(self):
        """Test initialization with default parameters."""
        client = 