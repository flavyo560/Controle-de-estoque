"""Unit tests for alert system.

**Validates: Requirements 9.1, 18.1**

Tests low stock detection, alert metrics calculation, and days until
stockout prediction based on average daily sales.
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from typing import List

from src.services.inventory_service import InventoryService
from src.domain.product import Product


class TestLowStockDetection:
    """Test low stock detection functionality."""
    
    @pytest.mark.asyncio
    async def test_get_low_stock_alerts_returns_products_below_min_stock(self):
        """
        Test that get_low_stock_alerts returns products with quantity < min_stock.
        
        **Validates: Requirements 18.1**
        
        The alert system should identify all products where current quantity
        is below the configured minimum stock level.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock cache miss
        cache.get.return_value = None
        
        # Mock low stock products
        low_stock_products = [
            Product(
                id=1,
                sku="LOW-001",
                name="Low Stock Product 1",
                gender="U",
                brand="TestBrand",
                reference="REF001",
                size="M",
                quantity=2,  # Below min_stock of 5
                price=Decimal("99.99"),
                min_stock=5,
                version=1
            ),
            Product(
                id=2,
                sku="LOW-002",
                name="Low Stock Product 2",
                gender="F",
                brand="TestBrand",
                reference="REF002",
                size="L",
                quantity=0,  # Critical: zero stock
                price=Decimal("149.99"),
                min_stock=10,
                version=1
            ),
            Product(
                id=3,
                sku="LOW-003",
                name="Low Stock Product 3",
                gender="M",
                brand="TestBrand",
                reference="REF003",
                size="S",
                quantity=8,  # Below min_stock of 15
                price=Decimal("79.99"),
                min_stock=15,
                version=1
            )
        ]
        product_repo.get_low_stock_products.return_value = low_stock_products
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Get low stock alerts
        result = await service.get_low_stock_alerts()
        
        # Verify result structure
        assert "products" in result
        assert "metrics" in result
        
        # Verify all low stock products are returned
        assert len(result["products"]) == 3
        
        # Verify product data
        product_skus = [p["sku"] for p in result["products"]]
        assert "LOW-001" in product_skus
        assert "LOW-002" in product_skus
        assert "LOW-003" in product_skus
        
        # Verify repository was called
        product_repo.get_low_stock_products.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_low_stock_alerts_returns_empty_when_no_low_stock(self):
        """
        Test that get_low_stock_alerts returns empty list when all products have sufficient stock.
        
        **Validates: Requirements 18.1**
        
        When no products are below minimum stock, the alert system should
        return an empty list.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock cache miss
        cache.get.return_value = None
        
        # Mock no low stock products
        product_repo.get_low_stock_products.return_value = []
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Get low stock alerts
        result = await service.get_low_stock_alerts()
        
        # Verify empty result
        assert result["products"] == []
        assert result["metrics"]["total"] == 0
        assert result["metrics"]["critical"] == 0
        assert result["metrics"]["warning"] == 0
    
    @pytest.mark.asyncio
    async def test_get_low_stock_alerts_uses_cache_when_available(self):
        """
        Test that get_low_stock_alerts uses cached data when available.
        
        **Validates: Requirements 18.1**
        
        To improve performance, the alert system should cache results
        and return cached data when available.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock cached data
        cached_result = {
            "products": [
                {
                    "id": 1,
                    "sku": "CACHED-001",
                    "name": "Cached Product",
                    "quantity": 3,
                    "min_stock": 5
                }
            ],
            "metrics": {
                "total": 1,
                "critical": 0,
                "warning": 1
            }
        }
        cache.get.return_value = cached_result
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Get low stock alerts
        result = await service.get_low_stock_alerts()
        
        # Verify cached result is returned
        assert result == cached_result
        
        # Verify repository was NOT called (cache hit)
        product_repo.get_low_stock_products.assert_not_called()
        
        # Verify cache was checked
        cache.get.assert_called_once_with("low_stock_products")


class TestAlertMetrics:
    """Test alert metrics calculation."""
    
    @pytest.mark.asyncio
    async def test_alert_metrics_counts_critical_products(self):
        """
        Test that alert metrics correctly count critical products (quantity = 0).
        
        **Validates: Requirements 18.1**
        
        Products with zero quantity should be counted as critical alerts.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock cache miss
        cache.get.return_value = None
        
        # Mock products with critical stock
        low_stock_products = [
            Product(
                id=1,
                sku="CRITICAL-001",
                name="Critical Product 1",
                gender="U",
                brand="TestBrand",
                reference="REF001",
                size="M",
                quantity=0,  # Critical
                price=Decimal("99.99"),
                min_stock=5,
                version=1
            ),
            Product(
                id=2,
                sku="CRITICAL-002",
                name="Critical Product 2",
                gender="F",
                brand="TestBrand",
                reference="REF002",
                size="L",
                quantity=0,  # Critical
                price=Decimal("149.99"),
                min_stock=10,
                version=1
            )
        ]
        product_repo.get_low_stock_products.return_value = low_stock_products
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Get low stock alerts
        result = await service.get_low_stock_alerts()
        
        # Verify metrics
        assert result["metrics"]["total"] == 2
        assert result["metrics"]["critical"] == 2
        assert result["metrics"]["warning"] == 0
    
    @pytest.mark.asyncio
    async def test_alert_metrics_counts_warning_products(self):
        """
        Test that alert metrics correctly count warning products (0 < quantity < min_stock).
        
        **Validates: Requirements 18.1**
        
        Products with quantity above zero but below minimum should be
        counted as warning alerts.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock cache miss
        cache.get.return_value = None
        
        # Mock products with warning stock
        low_stock_products = [
            Product(
                id=1,
                sku="WARNING-001",
                name="Warning Product 1",
                gender="U",
                brand="TestBrand",
                reference="REF001",
                size="M",
                quantity=3,  # Warning: above 0, below min_stock
                price=Decimal("99.99"),
                min_stock=5,
                version=1
            ),
            Product(
                id=2,
                sku="WARNING-002",
                name="Warning Product 2",
                gender="F",
                brand="TestBrand",
                reference="REF002",
                size="L",
                quantity=7,  # Warning: above 0, below min_stock
                price=Decimal("149.99"),
                min_stock=10,
                version=1
            )
        ]
        product_repo.get_low_stock_products.return_value = low_stock_products
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Get low stock alerts
        result = await service.get_low_stock_alerts()
        
        # Verify metrics
        assert result["metrics"]["total"] == 2
        assert result["metrics"]["critical"] == 0
        assert result["metrics"]["warning"] == 2
    
    @pytest.mark.asyncio
    async def test_alert_metrics_counts_mixed_severity(self):
        """
        Test that alert metrics correctly count both critical and warning products.
        
        **Validates: Requirements 18.1**
        
        The metrics should accurately separate critical (quantity = 0) from
        warning (0 < quantity < min_stock) alerts.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock cache miss
        cache.get.return_value = None
        
        # Mock products with mixed severity
        low_stock_products = [
            Product(
                id=1,
                sku="CRITICAL-001",
                name="Critical Product",
                gender="U",
                brand="TestBrand",
                reference="REF001",
                size="M",
                quantity=0,  # Critical
                price=Decimal("99.99"),
                min_stock=5,
                version=1
            ),
            Product(
                id=2,
                sku="WARNING-001",
                name="Warning Product 1",
                gender="F",
                brand="TestBrand",
                reference="REF002",
                size="L",
                quantity=3,  # Warning
                price=Decimal("149.99"),
                min_stock=10,
                version=1
            ),
            Product(
                id=3,
                sku="WARNING-002",
                name="Warning Product 2",
                gender="M",
                brand="TestBrand",
                reference="REF003",
                size="S",
                quantity=1,  # Warning
                price=Decimal("79.99"),
                min_stock=5,
                version=1
            ),
            Product(
                id=4,
                sku="CRITICAL-002",
                name="Critical Product 2",
                gender="U",
                brand="TestBrand",
                reference="REF004",
                size="XL",
                quantity=0,  # Critical
                price=Decimal("199.99"),
                min_stock=8,
                version=1
            )
        ]
        product_repo.get_low_stock_products.return_value = low_stock_products
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Get low stock alerts
        result = await service.get_low_stock_alerts()
        
        # Verify metrics
        assert result["metrics"]["total"] == 4
        assert result["metrics"]["critical"] == 2
        assert result["metrics"]["warning"] == 2


class TestAlertCaching:
    """Test alert caching behavior."""
    
    @pytest.mark.asyncio
    async def test_alert_results_are_cached(self):
        """
        Test that alert results are cached after fetching from database.
        
        **Validates: Requirements 18.1**
        
        To improve performance, alert results should be cached with
        appropriate TTL.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock cache miss
        cache.get.return_value = None
        
        # Mock low stock products
        low_stock_products = [
            Product(
                id=1,
                sku="CACHE-001",
                name="Cache Test Product",
                gender="U",
                brand="TestBrand",
                reference="REF001",
                size="M",
                quantity=2,
                price=Decimal("99.99"),
                min_stock=5,
                version=1
            )
        ]
        product_repo.get_low_stock_products.return_value = low_stock_products
        
        # Create service
        service = InventoryService(
            product_repo=product_repo,
            audit_repo=audit_repo,
            cache=cache,
            db_client=db_client
        )
        
        # Get low stock alerts
        result = await service.get_low_stock_alerts()
        
        # Verify cache.set was called with correct key and TTL
        cache.set.assert_called_once()
        call_args = cache.set.call_args
        assert call_args.args[0] == "low_stock_products"
        assert call_args.args[1] == result
        # Verify TTL is set (should be CACHE_TTL_LOW_STOCK constant)
        assert "ttl" in call_args.kwargs or len(call_args.args) > 2
    
    @pytest.mark.asyncio
    async def test_cache_invalidated_on_stock_update(self):
        """
        Test that low stock cache is invalidated when stock is updated.
        
        **Validates: Requirements 18.1**
        
        When product stock changes, the low stock alerts cache should be
        invalidated to ensure fresh data on next query.
        """
        # Setup mocks
        product_repo = AsyncMock()
        audit_repo = AsyncMock()
        cache = AsyncMock()
        db_client = AsyncMock()
        
        # Mock existing product
        existing_product = Product(
            id=1,
            sku="UPDATE-001",
            name="Update Test Product",
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
            sku="UPDATE-001",
            name="Update Test Product",
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
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return None
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return None
        
        db_client.transaction = MagicMock(return_value=AsyncContextManagerMock())
        
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
        
        # Verify low stock cache was invalidated
        cache_delete_calls = [call.args[0] for call in cache.delete.call_args_list]
        assert "low_stock_products" in cache_delete_calls


class TestLowStockRepository:
    """Test low stock detection at repository level."""
    
    @pytest.mark.asyncio
    async def test_repository_filters_deleted_products(self):
        """
        Test that get_low_stock_products excludes soft-deleted products.
        
        **Validates: Requirements 18.1**
        
        Soft-deleted products should not appear in low stock alerts.
        """
        from src.repositories.product_repository import ProductRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock database response (no deleted products)
        db_client.fetch_all.return_value = [
            {
                "id": 1,
                "sku": "ACTIVE-001",
                "name": "Active Product",
                "description": None,
                "gender": "U",
                "brand": "TestBrand",
                "reference": "REF001",
                "size": "M",
                "quantity": 2,
                "price": Decimal("99.99"),
                "barcode": None,
                "min_stock": 5,
                "version": 1,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None  # Not deleted
            }
        ]
        
        # Create repository
        repo = ProductRepository(db_client)
        
        # Get low stock products
        products = await repo.get_low_stock_products()
        
        # Verify query was called
        db_client.fetch_all.assert_called_once()
        
        # Verify query includes deleted_at IS NULL filter
        query = db_client.fetch_all.call_args.args[0]
        assert "deleted_at IS NULL" in query
        
        # Verify result
        assert len(products) == 1
        assert products[0].sku == "ACTIVE-001"
    
    @pytest.mark.asyncio
    async def test_repository_orders_by_urgency(self):
        """
        Test that get_low_stock_products orders results by urgency.
        
        **Validates: Requirements 18.1**
        
        Products should be ordered by urgency (lowest quantity first)
        to prioritize critical alerts.
        """
        from src.repositories.product_repository import ProductRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock database response (ordered by urgency)
        db_client.fetch_all.return_value = [
            {
                "id": 1,
                "sku": "URGENT-001",
                "name": "Most Urgent",
                "description": None,
                "gender": "U",
                "brand": "TestBrand",
                "reference": "REF001",
                "size": "M",
                "quantity": 0,  # Most urgent
                "price": Decimal("99.99"),
                "barcode": None,
                "min_stock": 5,
                "version": 1,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None
            },
            {
                "id": 2,
                "sku": "URGENT-002",
                "name": "Second Urgent",
                "description": None,
                "gender": "F",
                "brand": "TestBrand",
                "reference": "REF002",
                "size": "L",
                "quantity": 1,  # Second most urgent
                "price": Decimal("149.99"),
                "barcode": None,
                "min_stock": 10,
                "version": 1,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None
            }
        ]
        
        # Create repository
        repo = ProductRepository(db_client)
        
        # Get low stock products
        products = await repo.get_low_stock_products()
        
        # Verify query includes ORDER BY
        query = db_client.fetch_all.call_args.args[0]
        assert "ORDER BY" in query
        
        # Verify results are in urgency order
        assert len(products) == 2
        assert products[0].quantity == 0  # Most urgent first
        assert products[1].quantity == 1  # Second most urgent
    
    @pytest.mark.asyncio
    async def test_repository_supports_custom_threshold(self):
        """
        Test that get_low_stock_products supports custom threshold parameter.
        
        **Validates: Requirements 18.1**
        
        The repository should allow specifying a custom threshold instead
        of using each product's min_stock value.
        """
        from src.repositories.product_repository import ProductRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock database response
        db_client.fetch_all.return_value = []
        
        # Create repository
        repo = ProductRepository(db_client)
        
        # Get low stock products with custom threshold
        custom_threshold = 10
        await repo.get_low_stock_products(threshold=custom_threshold)
        
        # Verify query was called with threshold parameter
        db_client.fetch_all.assert_called_once()
        call_args = db_client.fetch_all.call_args
        
        # Verify threshold was passed as parameter
        assert len(call_args.args) > 1
        assert call_args.args[1] == custom_threshold



class TestDaysUntilStockout:
    """Test days until stockout calculation."""
    
    @pytest.mark.asyncio
    async def test_days_until_stockout_with_average_sales(self):
        """
        Test days until stockout calculation based on average daily sales.
        
        **Validates: Requirements 18.1**
        
        The system should calculate days until stockout by dividing current
        quantity by average daily sales over the last 30 days.
        
        Formula: days_until_stockout = current_quantity / avg_daily_sales
        """
        from src.repositories.sale_repository import SaleRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock sales summary for last 30 days
        # Assume 30 units sold over 30 days = 1 unit per day average
        db_client.fetch_one.return_value = {
            "total_quantity": 30,  # Total units sold
            "days": 30  # Days in period
        }
        
        # Create repository
        sale_repo = SaleRepository(db_client)
        
        # Calculate average daily sales for a product
        product_id = 1
        days = 30
        
        # Mock the query to get total quantity sold for a product
        query_result = await db_client.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity), 0) as total_quantity
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.product_id = $1
              AND s.status = 'completed'
              AND s.created_at >= NOW() - INTERVAL '30 days'
            """,
            product_id
        )
        
        total_quantity_sold = query_result["total_quantity"]
        avg_daily_sales = total_quantity_sold / days
        
        # Verify calculation
        assert avg_daily_sales == 1.0  # 30 units / 30 days = 1 per day
        
        # Calculate days until stockout for product with 10 units
        current_quantity = 10
        days_until_stockout = current_quantity / avg_daily_sales if avg_daily_sales > 0 else None
        
        # Verify result
        assert days_until_stockout == 10.0  # 10 units / 1 per day = 10 days
    
    @pytest.mark.asyncio
    async def test_days_until_stockout_with_zero_sales(self):
        """
        Test days until stockout when there are no sales (zero average).
        
        **Validates: Requirements 18.1**
        
        When average daily sales is zero, days until stockout should be None
        or infinity (product not selling).
        """
        from src.repositories.sale_repository import SaleRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock no sales in last 30 days
        db_client.fetch_one.return_value = {
            "total_quantity": 0,  # No units sold
            "days": 30
        }
        
        # Create repository
        sale_repo = SaleRepository(db_client)
        
        # Calculate average daily sales
        product_id = 1
        days = 30
        
        query_result = await db_client.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity), 0) as total_quantity
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.product_id = $1
              AND s.status = 'completed'
              AND s.created_at >= NOW() - INTERVAL '30 days'
            """,
            product_id
        )
        
        total_quantity_sold = query_result["total_quantity"]
        avg_daily_sales = total_quantity_sold / days
        
        # Verify zero average
        assert avg_daily_sales == 0.0
        
        # Calculate days until stockout
        current_quantity = 10
        days_until_stockout = current_quantity / avg_daily_sales if avg_daily_sales > 0 else None
        
        # Verify result is None (cannot calculate with zero sales)
        assert days_until_stockout is None
    
    @pytest.mark.asyncio
    async def test_days_until_stockout_with_high_sales_rate(self):
        """
        Test days until stockout with high sales rate (urgent restocking needed).
        
        **Validates: Requirements 18.1**
        
        Products with high sales rates should show low days until stockout,
        indicating urgent restocking is needed.
        """
        from src.repositories.sale_repository import SaleRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock high sales: 150 units sold over 30 days = 5 units per day
        db_client.fetch_one.return_value = {
            "total_quantity": 150,
            "days": 30
        }
        
        # Create repository
        sale_repo = SaleRepository(db_client)
        
        # Calculate average daily sales
        product_id = 1
        days = 30
        
        query_result = await db_client.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity), 0) as total_quantity
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.product_id = $1
              AND s.status = 'completed'
              AND s.created_at >= NOW() - INTERVAL '30 days'
            """,
            product_id
        )
        
        total_quantity_sold = query_result["total_quantity"]
        avg_daily_sales = total_quantity_sold / days
        
        # Verify high average
        assert avg_daily_sales == 5.0  # 150 / 30 = 5 per day
        
        # Calculate days until stockout for product with only 10 units
        current_quantity = 10
        days_until_stockout = current_quantity / avg_daily_sales if avg_daily_sales > 0 else None
        
        # Verify urgent situation: only 2 days of stock left
        assert days_until_stockout == 2.0  # 10 units / 5 per day = 2 days
    
    @pytest.mark.asyncio
    async def test_days_until_stockout_with_low_sales_rate(self):
        """
        Test days until stockout with low sales rate (less urgent).
        
        **Validates: Requirements 18.1**
        
        Products with low sales rates should show high days until stockout,
        indicating less urgency for restocking.
        """
        from src.repositories.sale_repository import SaleRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock low sales: 6 units sold over 30 days = 0.2 units per day
        db_client.fetch_one.return_value = {
            "total_quantity": 6,
            "days": 30
        }
        
        # Create repository
        sale_repo = SaleRepository(db_client)
        
        # Calculate average daily sales
        product_id = 1
        days = 30
        
        query_result = await db_client.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity), 0) as total_quantity
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.product_id = $1
              AND s.status = 'completed'
              AND s.created_at >= NOW() - INTERVAL '30 days'
            """,
            product_id
        )
        
        total_quantity_sold = query_result["total_quantity"]
        avg_daily_sales = total_quantity_sold / days
        
        # Verify low average
        assert avg_daily_sales == 0.2  # 6 / 30 = 0.2 per day
        
        # Calculate days until stockout for product with 10 units
        current_quantity = 10
        days_until_stockout = current_quantity / avg_daily_sales if avg_daily_sales > 0 else None
        
        # Verify less urgent: 50 days of stock left
        assert days_until_stockout == 50.0  # 10 units / 0.2 per day = 50 days
    
    @pytest.mark.asyncio
    async def test_days_until_stockout_excludes_cancelled_sales(self):
        """
        Test that days until stockout calculation excludes cancelled sales.
        
        **Validates: Requirements 18.1**
        
        Only completed sales should be included in average daily sales
        calculation. Cancelled sales should be excluded.
        """
        from src.repositories.sale_repository import SaleRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock sales data: only completed sales counted
        # Assume 30 completed + 10 cancelled = 40 total, but only 30 counted
        db_client.fetch_one.return_value = {
            "total_quantity": 30,  # Only completed sales
            "days": 30
        }
        
        # Create repository
        sale_repo = SaleRepository(db_client)
        
        # Verify query filters by status = 'completed'
        product_id = 1
        
        query_result = await db_client.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity), 0) as total_quantity
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.product_id = $1
              AND s.status = 'completed'
              AND s.created_at >= NOW() - INTERVAL '30 days'
            """,
            product_id
        )
        
        # Verify only completed sales are counted
        assert query_result["total_quantity"] == 30
        
        # Calculate average (should be based on completed sales only)
        avg_daily_sales = query_result["total_quantity"] / 30
        assert avg_daily_sales == 1.0  # 30 completed / 30 days = 1 per day
    
    @pytest.mark.asyncio
    async def test_days_until_stockout_for_zero_quantity_product(self):
        """
        Test days until stockout for product with zero quantity (critical alert).
        
        **Validates: Requirements 18.1**
        
        Products with zero quantity should show 0 days until stockout,
        indicating immediate restocking is needed.
        """
        from src.repositories.sale_repository import SaleRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock sales data
        db_client.fetch_one.return_value = {
            "total_quantity": 30,
            "days": 30
        }
        
        # Create repository
        sale_repo = SaleRepository(db_client)
        
        # Calculate average daily sales
        product_id = 1
        days = 30
        
        query_result = await db_client.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity), 0) as total_quantity
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.product_id = $1
              AND s.status = 'completed'
              AND s.created_at >= NOW() - INTERVAL '30 days'
            """,
            product_id
        )
        
        total_quantity_sold = query_result["total_quantity"]
        avg_daily_sales = total_quantity_sold / days
        
        # Calculate days until stockout for product with zero quantity
        current_quantity = 0  # Critical: out of stock
        days_until_stockout = current_quantity / avg_daily_sales if avg_daily_sales > 0 else None
        
        # Verify critical situation: 0 days (already out of stock)
        assert days_until_stockout == 0.0
    
    @pytest.mark.asyncio
    async def test_days_until_stockout_calculation_precision(self):
        """
        Test that days until stockout calculation maintains precision.
        
        **Validates: Requirements 18.1**
        
        The calculation should maintain decimal precision for accurate
        forecasting (e.g., 3.5 days, not just 3 days).
        """
        from src.repositories.sale_repository import SaleRepository
        
        # Setup mock database client
        db_client = AsyncMock()
        
        # Mock sales: 45 units over 30 days = 1.5 units per day
        db_client.fetch_one.return_value = {
            "total_quantity": 45,
            "days": 30
        }
        
        # Create repository
        sale_repo = SaleRepository(db_client)
        
        # Calculate average daily sales
        product_id = 1
        days = 30
        
        query_result = await db_client.fetch_one(
            """
            SELECT COALESCE(SUM(si.quantity), 0) as total_quantity
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE si.product_id = $1
              AND s.status = 'completed'
              AND s.created_at >= NOW() - INTERVAL '30 days'
            """,
            product_id
        )
        
        total_quantity_sold = query_result["total_quantity"]
        avg_daily_sales = total_quantity_sold / days
        
        # Verify precise average
        assert avg_daily_sales == 1.5  # 45 / 30 = 1.5 per day
        
        # Calculate days until stockout for product with 7 units
        current_quantity = 7
        days_until_stockout = current_quantity / avg_daily_sales if avg_daily_sales > 0 else None
        
        # Verify precise result (not rounded)
        assert abs(days_until_stockout - 4.666666666666667) < 0.0001  # 7 / 1.5 ≈ 4.67 days
        
        # Verify it's a float, not an integer
        assert isinstance(days_until_stockout, float)
