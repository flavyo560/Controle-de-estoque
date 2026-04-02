"""Pytest configuration and fixtures for testing."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime

from src.infrastructure.database import DatabaseClient
from src.infrastructure.cache import CacheManager
from src.infrastructure.encryption import EncryptionService
from src.infrastructure.rate_limiter import RateLimiter
from src.repositories.user_repository import UserRepository
from src.repositories.audit_repository import AuditRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.services.auth_service import AuthService
from src.services.validation_service import ValidationService
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db_url() -> str:
    """Get test database URL from environment."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    load_dotenv(".env.development")  # Try development env too
    
    # Get database URL (prefer TEST_DATABASE_URL, fall back to DATABASE_URL)
    db_url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    
    if not db_url:
        pytest.skip("No database URL configured. Set DATABASE_URL or TEST_DATABASE_URL environment variable.")
    
    return db_url


@pytest.fixture(scope="function")
async def db_client(test_db_url: str) -> AsyncGenerator[DatabaseClient, None]:
    """Create database client for testing."""
    client = DatabaseClient(
        dsn=test_db_url,
        min_size=1,
        max_size=5,
        command_timeout=30.0
    )
    await client.connect()
    yield client
    await client.disconnect()
    yield client
    await client.disconnect()


@pytest.fixture
def cache_manager() -> CacheManager:
    """Create in-memory cache manager for testing."""
    return CacheManager(backend="memory")


@pytest.fixture
def encryption_service() -> EncryptionService:
    """Create encryption service for testing."""
    return EncryptionService(master_key="test_key_32_characters_long_12")


@pytest.fixture
def rate_limiter(cache_manager: CacheManager) -> RateLimiter:
    """Create rate limiter for testing."""
    return RateLimiter(cache=cache_manager)


@pytest.fixture
def validation_service() -> ValidationService:
    """Create validation service for testing."""
    return ValidationService()


@pytest.fixture
async def user_repository(
    db_client: DatabaseClient,
    cache_manager: CacheManager
) -> UserRepository:
    """Create user repository for testing."""
    return UserRepository(db_client, cache_manager)


@pytest.fixture
async def audit_repository(db_client: DatabaseClient) -> AuditRepository:
    """Create audit repository for testing."""
    return AuditRepository(db_client)


@pytest.fixture
async def product_repository(db_client: DatabaseClient) -> ProductRepository:
    """Create product repository for testing."""
    return ProductRepository(db_client)


@pytest.fixture
async def sale_repository(db_client: DatabaseClient) -> SaleRepository:
    """Create sale repository for testing."""
    return SaleRepository(db_client)


@pytest.fixture
async def auth_service(
    user_repository: UserRepository,
    audit_repository: AuditRepository,
    rate_limiter: RateLimiter,
    encryption_service: EncryptionService
) -> AuthService:
    """Create auth service for testing."""
    return AuthService(
        user_repo=user_repository,
        audit_repo=audit_repository,
        rate_limiter=rate_limiter,
        encryption=encryption_service
    )


@pytest.fixture
async def inventory_service(
    product_repository: ProductRepository,
    audit_repository: AuditRepository,
    cache_manager: CacheManager,
    db_client: DatabaseClient
) -> InventoryService:
    """Create inventory service for testing."""
    return InventoryService(
        product_repo=product_repository,
        audit_repo=audit_repository,
        cache=cache_manager,
        db_client=db_client
    )


@pytest.fixture
async def sales_service(
    sale_repository: SaleRepository,
    product_repository: ProductRepository,
    audit_repository: AuditRepository,
    db_client: DatabaseClient
) -> SalesService:
    """Create sales service for testing."""
    return SalesService(
        sale_repo=sale_repository,
        product_repo=product_repository,
        audit_repo=audit_repository,
        db_client=db_client
    )


@pytest.fixture
async def clean_database(db_client: DatabaseClient) -> AsyncGenerator[None, None]:
    """Clean database before and after test."""
    # Clean before test
    await _clean_test_data(db_client)
    
    yield
    
    # Clean after test
    await _clean_test_data(db_client)


async def _clean_test_data(db_client: DatabaseClient) -> None:
    """Remove all test data from database."""
    tables = [
        "payments",
        "sale_items",
        "sales",
        "inventory_movements",
        "products",
        "sessions",
        "audit_log",
        "users",
        "customers"
    ]
    
    for table in tables:
        try:
            await db_client.execute(f"DELETE FROM {table} WHERE id > 0")
        except Exception:
            # Table might not exist in test database
            pass


@pytest.fixture
def sample_product_data() -> dict:
    """Sample product data for testing."""
    return {
        "sku": "TEST-001",
        "barcode": "1234567890123",
        "name": "Test Product",
        "description": "Test product description",
        "category": "Test Category",
        "size": "M",
        "color": "Blue",
        "gender": "U",
        "price": 99.99,
        "cost": 50.00,
        "quantity": 100,
        "low_stock_threshold": 10
    }


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "email": "test@example.com",
        "role": "user"
    }


@pytest.fixture
def sample_sale_data() -> dict:
    """Sample sale data for testing."""
    return {
        "customer_id": None,
        "user_id": 1,
        "items": [
            {
                "product_id": 1,
                "quantity": 2,
                "unit_price": 99.99
            }
        ],
        "payments": [
            {
                "payment_method": "cash",
                "amount": 199.98
            }
        ],
        "discount_amount": 0.00
    }


# Hypothesis strategies for property-based testing
try:
    from hypothesis import strategies as st
    from decimal import Decimal
    
    @pytest.fixture
    def product_strategy():
        """Hypothesis strategy for generating valid products."""
        return st.builds(
            dict,
            sku=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))),
            name=st.text(min_size=1, max_size=200),
            price=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("99999.99"), places=2),
            quantity=st.integers(min_value=0, max_value=10000),
            gender=st.sampled_from(['M', 'F', 'U'])
        )
    
    @pytest.fixture
    def user_strategy():
        """Hypothesis strategy for generating valid users."""
        return st.builds(
            dict,
            username=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))),
            password=st.text(min_size=12, max_size=100),
            email=st.emails(),
            role=st.sampled_from(['admin', 'manager', 'user'])
        )

except ImportError:
    # Hypothesis not installed
    pass
