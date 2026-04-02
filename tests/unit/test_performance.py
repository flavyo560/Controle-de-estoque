"""Performance tests for database queries and cache effectiveness.

**Validates: Requirements 9.1, 5.1**

This module tests:
- Query execution time for common operations
- Cache hit rates meet targets (>70%)
- Database connection pool performance
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from decimal import Decimal

from src.infrastructure.database import DatabaseClient
from src.infrastructure.cache import CacheManager
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.audit_repository import AuditRepository
from src.domain.product import ProductCreate


# Performance thresholds
MAX_QUERY_TIME_MS = 500  # Requirement 5.1: <500ms for list queries
MIN_CACHE_HIT_RATE = 0.70  # Requirement 5.1: >70% cache hit rate
MAX_SINGLE_QUERY_TIME_MS = 100  # For single record queries


class TestQueryPerformance:
    """Test query execution times for common operations."""
    
    @pytest.mark.asyncio
    async def test_product_list_query_performance(
        self,
        db_client: DatabaseClient,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that listing products completes within 500ms.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create test products
        products_to_create = []
        for i in range(100):
            products_to_create.append(
                ProductCreate(
                    sku=f"PERF-{i:04d}",
                    barcode=f"123456789{i:04d}",
                    name=f"Performance Test Product {i}",
                    description="Test product for performance testing",
                    category="Test",
                    size="M",
                    color="Blue",
                    gender="U",
                    price=Decimal("99.99"),
                    cost=Decimal("50.00"),
                    quantity=100,
                    low_stock_threshold=10
                )
            )
        
        # Insert products
        for product_data in products_to_create:
            await product_repository.create(product_data)
        
        # Measure query time
        start_time = time.perf_counter()
        results = await product_repository.list(limit=100, offset=0)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Assert performance requirement
        assert execution_time_ms < MAX_QUERY_TIME_MS, (
            f"Product list query took {execution_time_ms:.2f}ms, "
            f"exceeds maximum of {MAX_QUERY_TIME_MS}ms"
        )
        assert len(results) >= 100, "Should return at least 100 products"
    
    @pytest.mark.asyncio
    async def test_product_search_query_performance(
        self,
        db_client: DatabaseClient,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that product search completes within 500ms.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create test products with searchable names
        for i in range(50):
            await product_repository.create(
                ProductCreate(
                    sku=f"SEARCH-{i:04d}",
                    barcode=f"987654321{i:04d}",
                    name=f"Searchable Product {i} Blue Shirt",
                    description="Searchable test product",
                    category="Clothing",
                    size="L",
                    color="Blue",
                    gender="M",
                    price=Decimal("79.99"),
                    cost=Decimal("40.00"),
                    quantity=50,
                    low_stock_threshold=5
                )
            )
        
        # Measure search query time
        start_time = time.perf_counter()
        results = await product_repository.search("Blue", limit=50)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Assert performance requirement
        assert execution_time_ms < MAX_QUERY_TIME_MS, (
            f"Product search query took {execution_time_ms:.2f}ms, "
            f"exceeds maximum of {MAX_QUERY_TIME_MS}ms"
        )
        assert len(results) > 0, "Should return search results"
    
    @pytest.mark.asyncio
    async def test_single_product_query_performance(
        self,
        db_client: DatabaseClient,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that fetching a single product by ID completes within 100ms.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create a test product
        product = await product_repository.create(
            ProductCreate(
                sku="SINGLE-001",
                barcode="1111111111111",
                name="Single Product Test",
                description="Test product",
                category="Test",
                size="M",
                color="Red",
                gender="U",
                price=Decimal("49.99"),
                cost=Decimal("25.00"),
                quantity=10,
                low_stock_threshold=2
            )
        )
        
        # Measure query time
        start_time = time.perf_counter()
        result = await product_repository.get_by_id(product.id)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Assert performance requirement
        assert execution_time_ms < MAX_SINGLE_QUERY_TIME_MS, (
            f"Single product query took {execution_time_ms:.2f}ms, "
            f"exceeds maximum of {MAX_SINGLE_QUERY_TIME_MS}ms"
        )
        assert result is not None, "Should return the product"
        assert result.id == product.id
    
    @pytest.mark.asyncio
    async def test_low_stock_query_performance(
        self,
        db_client: DatabaseClient,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that low stock query completes within 500ms.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create products with low stock
        for i in range(30):
            await product_repository.create(
                ProductCreate(
                    sku=f"LOW-{i:04d}",
                    barcode=f"222222222{i:04d}",
                    name=f"Low Stock Product {i}",
                    description="Low stock test",
                    category="Test",
                    size="S",
                    color="Green",
                    gender="F",
                    price=Decimal("29.99"),
                    cost=Decimal("15.00"),
                    quantity=3,  # Below threshold
                    low_stock_threshold=10
                )
            )
        
        # Measure query time
        start_time = time.perf_counter()
        results = await product_repository.get_low_stock_products()
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Assert performance requirement
        assert execution_time_ms < MAX_QUERY_TIME_MS, (
            f"Low stock query took {execution_time_ms:.2f}ms, "
            f"exceeds maximum of {MAX_QUERY_TIME_MS}ms"
        )
        assert len(results) >= 30, "Should return low stock products"
    
    @pytest.mark.asyncio
    async def test_sales_list_query_performance(
        self,
        db_client: DatabaseClient,
        sale_repository: SaleRepository,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that listing sales completes within 500ms.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create a test product first
        product = await product_repository.create(
            ProductCreate(
                sku="SALE-PROD-001",
                barcode="3333333333333",
                name="Sale Test Product",
                description="Product for sale testing",
                category="Test",
                size="M",
                color="Black",
                gender="U",
                price=Decimal("99.99"),
                cost=Decimal("50.00"),
                quantity=1000,
                low_stock_threshold=10
            )
        )
        
        # Create test sales
        from src.domain.sale import SaleCreate, SaleItemCreate, PaymentCreate
        from datetime import datetime
        
        for i in range(50):
            sale_data = SaleCreate(
                customer_id=None,
                user_id=1,
                items=[
                    SaleItemCreate(
                        product_id=product.id,
                        quantity=1,
                        unit_price=Decimal("99.99")
                    )
                ],
                payments=[
                    PaymentCreate(
                        payment_method="cash",
                        amount=Decimal("99.99")
                    )
                ],
                discount_amount=Decimal("0.00"),
                created_at=datetime.now()
            )
            await sale_repository.create(sale_data)
        
        # Measure query time
        start_time = time.perf_counter()
        results = await sale_repository.list(limit=50, offset=0)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Assert performance requirement
        assert execution_time_ms < MAX_QUERY_TIME_MS, (
            f"Sales list query took {execution_time_ms:.2f}ms, "
            f"exceeds maximum of {MAX_QUERY_TIME_MS}ms"
        )
        assert len(results) >= 50, "Should return at least 50 sales"


class TestCachePerformance:
    """Test cache hit rates and effectiveness."""
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_for_product_lookups(
        self,
        db_client: DatabaseClient,
        cache_manager: CacheManager,
        inventory_service: InventoryService,
        clean_database
    ):
        """
        Test that cache hit rate exceeds 70% for repeated product lookups.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create test products
        products = []
        for i in range(10):
            product = await inventory_service.create_product(
                ProductCreate(
                    sku=f"CACHE-{i:04d}",
                    barcode=f"444444444{i:04d}",
                    name=f"Cache Test Product {i}",
                    description="Cache test",
                    category="Test",
                    size="M",
                    color="Yellow",
                    gender="U",
                    price=Decimal("59.99"),
                    cost=Decimal("30.00"),
                    quantity=100,
                    low_stock_threshold=10
                ),
                user_id=1
            )
            products.append(product)
        
        # Clear cache to start fresh
        await cache_manager.invalidate_pattern("products:*")
        
        # Perform lookups with repetition to test cache
        total_lookups = 100
        cache_hits = 0
        cache_misses = 0
        
        for i in range(total_lookups):
            # Randomly select a product (with repetition)
            product_id = products[i % len(products)].id
            
            # Check if in cache before lookup
            cache_key = f"products:id:{product_id}"
            cached_value = await cache_manager.get(cache_key)
            
            if cached_value is not None:
                cache_hits += 1
            else:
                cache_misses += 1
            
            # Perform lookup (will cache if not cached)
            result = await inventory_service.get_product(product_id)
            assert result is not None
        
        # Calculate hit rate
        cache_hit_rate = cache_hits / total_lookups
        
        # Assert cache hit rate requirement
        assert cache_hit_rate >= MIN_CACHE_HIT_RATE, (
            f"Cache hit rate is {cache_hit_rate:.2%}, "
            f"below minimum of {MIN_CACHE_HIT_RATE:.2%}"
        )
    
    @pytest.mark.asyncio
    async def test_cache_hit_rate_for_search_queries(
        self,
        db_client: DatabaseClient,
        cache_manager: CacheManager,
        inventory_service: InventoryService,
        clean_database
    ):
        """
        Test that cache hit rate exceeds 70% for repeated search queries.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create test products
        for i in range(20):
            await inventory_service.create_product(
                ProductCreate(
                    sku=f"SEARCH-CACHE-{i:04d}",
                    barcode=f"555555555{i:04d}",
                    name=f"Searchable Cache Product {i}",
                    description="Search cache test",
                    category="Test",
                    size="L",
                    color="Purple",
                    gender="U",
                    price=Decimal("89.99"),
                    cost=Decimal("45.00"),
                    quantity=50,
                    low_stock_threshold=5
                ),
                user_id=1
            )
        
        # Clear cache
        await cache_manager.invalidate_pattern("products:search:*")
        
        # Perform repeated searches
        search_queries = ["Searchable", "Cache", "Product", "Purple"]
        total_searches = 100
        cache_hits = 0
        cache_misses = 0
        
        for i in range(total_searches):
            query = search_queries[i % len(search_queries)]
            cache_key = f"products:search:{query}:50"
            
            # Check cache before search
            cached_value = await cache_manager.get(cache_key)
            
            if cached_value is not None:
                cache_hits += 1
            else:
                cache_misses += 1
            
            # Perform search
            results = await inventory_service.search_products(query, limit=50)
            assert len(results) > 0
        
        # Calculate hit rate
        cache_hit_rate = cache_hits / total_searches
        
        # Assert cache hit rate requirement
        assert cache_hit_rate >= MIN_CACHE_HIT_RATE, (
            f"Search cache hit rate is {cache_hit_rate:.2%}, "
            f"below minimum of {MIN_CACHE_HIT_RATE:.2%}"
        )
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(
        self,
        db_client: DatabaseClient,
        cache_manager: CacheManager,
        inventory_service: InventoryService,
        clean_database
    ):
        """
        Test that cache is properly invalidated when products are updated.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create a product
        product = await inventory_service.create_product(
            ProductCreate(
                sku="CACHE-INV-001",
                barcode="6666666666666",
                name="Cache Invalidation Test",
                description="Test cache invalidation",
                category="Test",
                size="M",
                color="Orange",
                gender="U",
                price=Decimal("39.99"),
                cost=Decimal("20.00"),
                quantity=100,
                low_stock_threshold=10
            ),
            user_id=1
        )
        
        # First lookup (cache miss)
        result1 = await inventory_service.get_product(product.id)
        assert result1 is not None
        assert result1.name == "Cache Invalidation Test"
        
        # Second lookup (cache hit)
        cache_key = f"products:id:{product.id}"
        cached_before_update = await cache_manager.get(cache_key)
        assert cached_before_update is not None, "Product should be cached"
        
        # Update the product
        from src.domain.product import ProductUpdate
        await inventory_service.update_product(
            product.id,
            ProductUpdate(name="Updated Cache Test"),
            user_id=1
        )
        
        # Check that cache was invalidated
        cached_after_update = await cache_manager.get(cache_key)
        assert cached_after_update is None, "Cache should be invalidated after update"
        
        # Lookup again (should fetch from database)
        result2 = await inventory_service.get_product(product.id)
        assert result2 is not None
        assert result2.name == "Updated Cache Test"
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(
        self,
        cache_manager: CacheManager
    ):
        """
        Test that cache entries expire after TTL.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Set a value with short TTL
        await cache_manager.set("test_key", "test_value", ttl=1)
        
        # Immediately retrieve (should exist)
        value1 = await cache_manager.get("test_key")
        assert value1 == "test_value", "Value should be cached"
        
        # Wait for TTL to expire
        await asyncio.sleep(1.5)
        
        # Try to retrieve (should be expired)
        value2 = await cache_manager.get("test_key")
        assert value2 is None, "Value should be expired"


class TestConcurrentQueryPerformance:
    """Test performance under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_product_lookups(
        self,
        db_client: DatabaseClient,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that concurrent product lookups complete within acceptable time.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create test products
        products = []
        for i in range(20):
            product = await product_repository.create(
                ProductCreate(
                    sku=f"CONCURRENT-{i:04d}",
                    barcode=f"777777777{i:04d}",
                    name=f"Concurrent Test Product {i}",
                    description="Concurrent test",
                    category="Test",
                    size="M",
                    color="Gray",
                    gender="U",
                    price=Decimal("69.99"),
                    cost=Decimal("35.00"),
                    quantity=100,
                    low_stock_threshold=10
                )
            )
            products.append(product)
        
        # Perform concurrent lookups
        async def lookup_product(product_id: int):
            return await product_repository.get_by_id(product_id)
        
        start_time = time.perf_counter()
        
        # Create 50 concurrent lookup tasks
        tasks = [lookup_product(products[i % len(products)].id) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        
        # Assert all lookups succeeded
        assert all(r is not None for r in results), "All lookups should succeed"
        
        # Assert reasonable performance (should be faster than sequential)
        # 50 queries * 100ms = 5000ms sequential, expect < 2000ms concurrent
        assert execution_time_ms < 2000, (
            f"Concurrent lookups took {execution_time_ms:.2f}ms, "
            f"exceeds maximum of 2000ms"
        )
    
    @pytest.mark.asyncio
    async def test_connection_pool_under_load(
        self,
        db_client: DatabaseClient,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that connection pool handles concurrent requests efficiently.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create a test product
        product = await product_repository.create(
            ProductCreate(
                sku="POOL-TEST-001",
                barcode="8888888888888",
                name="Pool Test Product",
                description="Connection pool test",
                category="Test",
                size="L",
                color="White",
                gender="U",
                price=Decimal("79.99"),
                cost=Decimal("40.00"),
                quantity=1000,
                low_stock_threshold=10
            )
        )
        
        # Perform many concurrent queries to stress the pool
        async def query_product():
            return await product_repository.get_by_id(product.id)
        
        start_time = time.perf_counter()
        
        # Create 100 concurrent tasks (more than pool size)
        tasks = [query_product() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000
        
        # Assert all queries succeeded
        assert all(r is not None for r in results), "All queries should succeed"
        assert all(r.id == product.id for r in results), "All results should match"
        
        # Assert reasonable performance with connection pooling
        # Should handle 100 queries efficiently with pool
        assert execution_time_ms < 3000, (
            f"Connection pool queries took {execution_time_ms:.2f}ms, "
            f"exceeds maximum of 3000ms"
        )


class TestPerformanceMetrics:
    """Test performance monitoring and metrics collection."""
    
    @pytest.mark.asyncio
    async def test_query_time_logging(
        self,
        db_client: DatabaseClient,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that slow queries are properly identified.
        
        **Validates: Requirements 5.1, 9.1**
        """
        # Create a product
        product = await product_repository.create(
            ProductCreate(
                sku="METRIC-001",
                barcode="9999999999999",
                name="Metrics Test Product",
                description="Metrics test",
                category="Test",
                size="M",
                color="Pink",
                gender="F",
                price=Decimal("49.99"),
                cost=Decimal("25.00"),
                quantity=50,
                low_stock_threshold=5
            )
        )
        
        # Measure query time
        start_time = time.perf_counter()
        result = await product_repository.get_by_id(product.id)
        end_time = time.perf_counter()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Log if query is slow (>1 second per Requirement 5.1)
        if execution_time_ms > 1000:
            pytest.fail(
                f"Query took {execution_time_ms:.2f}ms, "
                f"exceeds 1 second threshold for logging"
            )
        
        assert result is not None
        assert result.id == product.id
