"""Unit tests for inventory service.

**Validates: Requirements 18.1, 19.2**

Tests specific scenarios for inventory management including
duplicate SKU handling and insufficient stock validation.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from src.services.inventory_service import InventoryService
from src.domain.product import Product, ProductCreate, ProductUpdate
from src.exceptions import DuplicateError, InsufficientStockError, NotFoundError


class AsyncContextManagerMock:
    """Mock async context manager for database transactions."""
    async def __aenter__(self):
        return None
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


def get_transaction_mock():
    """Helper to create a transaction mock that returns an async context manager."""
    mock = MagicMock()
    mock.return_value = AsyncContextManagerMock()
    return mock


class TestInventoryServiceDuplicateSKU:
    """Test duplicate SKU handling in inventory service."""
    
    @pytest.mark.asyncio
    async def test_create_product_with_duplicate_sku_raises_error(self):
        """
        Test that creating a product with duplicate SKU raises DuplicateError.
        
        **Validates: Requirements 18.1**
        
        When attempting to create a product with a SKU that already exists,
        the service should raise a DuplicateError before attempting to
        create the product in the database.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock existing product with same SKU
        existing_product = Product(
            id=1,
            sku="DUPLICATE-SKU",
            name="Existing Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=10,
            price=Decimal("99.99"),
            min_stock=5,
            version=1
        )
        product_repo.get_by_sku.return_value = existing_product
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Attempt to create product with duplicate SKU
        product_data = ProductCreate(
            sku="DUPLICATE-SKU",
            name="New Product",
            gender="U",
            brand="TestBrand",
            reference="REF002",
            size="L",
            quantity=20,
            price=Decimal("149.99"),
            min_stock=5
        )
        
        # Should raise DuplicateError
        with pytest.raises(DuplicateError) as exc_info:
            await service.create_product(
                product_data=product_data,
                user_id=1
            )
        
        # Verify error message
        assert "DUPLICATE-SKU" in str(exc_info.value)
        assert "already exists" in str(exc_info.value)
        
        # Verify get_by_sku was called
        product_repo.get_by_sku.assert_called_once_with("DUPLICATE-SKU")
        
        # Verify create was NOT called (early return on duplicate)
        product_repo.create.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_product_with_unique_sku_succeeds(self):
        """
        Test that creating a product with unique SKU succeeds.
        
        **Validates: Requirements 18.1**
        
        When creating a product with a SKU that doesn't exist,
        the service should successfully create the product.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock no existing product (unique SKU)
        product_repo.get_by_sku.return_value = None
        
        # Mock created product
        created_product = Product(
            id=1,
            sku="UNIQUE-SKU",
            name="New Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=10,
            price=Decimal("99.99"),
            min_stock=5,
            version=1
        )
        product_repo.create.return_value = created_product
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Create product
        product_data = ProductCreate(
            sku="UNIQUE-SKU",
            name="New Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=10,
            price=Decimal("99.99"),
            min_stock=5
        )
        
        result = await service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Verify result
        assert result.id == 1
        assert result.sku == "UNIQUE-SKU"
        
        # Verify get_by_sku was called
        product_repo.get_by_sku.assert_called_once_with("UNIQUE-SKU")
        
        # Verify create was called
        product_repo.create.assert_called_once()
        
        # Verify audit log was created
        audit_repo.log_create.assert_called_once()


class TestInventoryServiceInsufficientStock:
    """Test insufficient stock handling in inventory service."""
    
    @pytest.mark.asyncio
    async def test_update_stock_with_insufficient_quantity_raises_error(self):
        """
        Test that reducing stock below zero raises InsufficientStockError.
        
        **Validates: Requirements 19.2**
        
        When attempting to reduce stock by more than the available quantity,
        the service should raise an InsufficientStockError and not modify
        the database.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock existing product with limited stock
        existing_product = Product(
            id=1,
            sku="LOW-STOCK",
            name="Low Stock Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=5,  # Only 5 in stock
            price=Decimal("99.99"),
            min_stock=5,
            version=1
        )
        product_repo.get_by_id.return_value = existing_product
        
        # Mock transaction context manager
        db_client.transaction = get_transaction_mock()
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Attempt to reduce stock by more than available
        with pytest.raises(InsufficientStockError) as exc_info:
            await service.update_stock(
                product_id=1,
                quantity_change=-10,  # Try to remove 10, but only 5 available
                user_id=1,
                reference_type="sale"
            )
        
        # Verify error message contains relevant information
        assert "Insufficient stock" in str(exc_info.value)
        assert "LOW-STOCK" in str(exc_info.value)
        assert "Current: 5" in str(exc_info.value)
        assert "Requested: 10" in str(exc_info.value)
        
        # Verify get_by_id was called
        product_repo.get_by_id.assert_called()
        
        # Verify update was NOT called (transaction should not proceed)
        product_repo.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_stock_with_sufficient_quantity_succeeds(self):
        """
        Test that reducing stock within available quantity succeeds.
        
        **Validates: Requirements 19.2**
        
        When reducing stock by an amount less than or equal to available quantity,
        the operation should succeed and update the database.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock existing product
        existing_product = Product(
            id=1,
            sku="GOOD-STOCK",
            name="Good Stock Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=10,
            price=Decimal("99.99"),
            min_stock=5,
            version=1
        )
        product_repo.get_by_id.return_value = existing_product
        
        # Mock updated product
        updated_product = Product(
            id=1,
            sku="GOOD-STOCK",
            name="Good Stock Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=5,  # Reduced by 5
            price=Decimal("99.99"),
            min_stock=5,
            version=2
        )
        product_repo.update.return_value = updated_product
        
        # Mock transaction context manager
        db_client.transaction = get_transaction_mock()
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Reduce stock by valid amount
        result = await service.update_stock(
            product_id=1,
            quantity_change=-5,  # Remove 5 from 10
            user_id=1,
            reference_type="sale"
        )
        
        # Verify result
        assert result.quantity == 5
        assert result.version == 2
        
        # Verify update was called with correct quantity
        product_repo.update.assert_called_once()
        call_args = product_repo.update.call_args
        assert call_args.kwargs['quantity'] == 5
    
    @pytest.mark.asyncio
    async def test_update_stock_to_exactly_zero_succeeds(self):
        """
        Test that reducing stock to exactly zero succeeds.
        
        **Validates: Requirements 19.2**
        
        Reducing stock to exactly zero (but not below) should be allowed.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock existing product
        existing_product = Product(
            id=1,
            sku="EXACT-ZERO",
            name="Exact Zero Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=5,
            price=Decimal("99.99"),
            min_stock=5,
            version=1
        )
        product_repo.get_by_id.return_value = existing_product
        
        # Mock updated product with zero quantity
        updated_product = Product(
            id=1,
            sku="EXACT-ZERO",
            name="Exact Zero Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=0,  # Exactly zero
            price=Decimal("99.99"),
            min_stock=5,
            version=2
        )
        product_repo.update.return_value = updated_product
        
        # Mock transaction context manager
        db_client.transaction = get_transaction_mock()
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Reduce stock to exactly zero
        result = await service.update_stock(
            product_id=1,
            quantity_change=-5,  # Remove all 5
            user_id=1,
            reference_type="sale"
        )
        
        # Verify result
        assert result.quantity == 0
        
        # Verify update was called
        product_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_stock_with_nonexistent_product_raises_error(self):
        """
        Test that updating stock for nonexistent product raises NotFoundError.
        
        **Validates: Requirements 19.2**
        
        When attempting to update stock for a product that doesn't exist,
        the service should raise a NotFoundError.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock no product found
        product_repo.get_by_id.return_value = None
        
        # Mock transaction context manager
        db_client.transaction = get_transaction_mock()
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Attempt to update stock for nonexistent product
        with pytest.raises(NotFoundError) as exc_info:
            await service.update_stock(
                product_id=999,
                quantity_change=-5,
                user_id=1,
                reference_type="sale"
            )
        
        # Verify error message
        assert "999" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()
        
        # Verify get_by_id was called
        product_repo.get_by_id.assert_called_once_with(999)
        
        # Verify update was NOT called
        product_repo.update.assert_not_called()


class TestInventoryServiceCacheInvalidation:
    """Test cache invalidation in inventory service."""
    
    @pytest.mark.asyncio
    async def test_create_product_invalidates_low_stock_cache(self):
        """
        Test that creating a product invalidates the low stock cache.
        
        **Validates: Requirements 18.1**
        
        When a new product is created, the low stock alerts cache should
        be invalidated to ensure fresh data on next query.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock no existing product
        product_repo.get_by_sku.return_value = None
        
        # Mock created product
        created_product = Product(
            id=1,
            sku="NEW-SKU",
            name="New Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=10,
            price=Decimal("99.99"),
            min_stock=5,
            version=1
        )
        product_repo.create.return_value = created_product
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Create product
        product_data = ProductCreate(
            sku="NEW-SKU",
            name="New Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=10,
            price=Decimal("99.99"),
            min_stock=5
        )
        
        await service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Verify low stock cache was invalidated
        cache.delete.assert_called_with("low_stock_products")
    
    @pytest.mark.asyncio
    async def test_update_stock_invalidates_product_cache(self):
        """
        Test that updating stock invalidates the product cache.
        
        **Validates: Requirements 19.2**
        
        When stock is updated, the product cache should be invalidated
        to ensure fresh data on next query.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock existing product
        existing_product = Product(
            id=1,
            sku="CACHE-TEST",
            name="Cache Test Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=10,
            price=Decimal("99.99"),
            min_stock=5,
            version=1
        )
        product_repo.get_by_id.return_value = existing_product
        
        # Mock updated product
        updated_product = Product(
            id=1,
            sku="CACHE-TEST",
            name="Cache Test Product",
            gender="U",
            brand="TestBrand",
            reference="REF001",
            size="M",
            quantity=8,
            price=Decimal("99.99"),
            min_stock=5,
            version=2
        )
        product_repo.update.return_value = updated_product
        
        # Mock transaction context manager
        db_client.transaction = get_transaction_mock()
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Update stock
        await service.update_stock(
            product_id=1,
            quantity_change=-2,
            user_id=1,
            reference_type="sale"
        )
        
        # Verify product cache was invalidated (by ID and SKU)
        assert cache.delete.call_count >= 2
        cache_delete_calls = [call.args[0] for call in cache.delete.call_args_list]
        assert "product:1" in cache_delete_calls
        assert "product:sku:CACHE-TEST" in cache_delete_calls
        assert "low_stock_products" in cache_delete_calls
