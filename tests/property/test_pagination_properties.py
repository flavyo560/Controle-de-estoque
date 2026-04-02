"""Property-based tests for pagination functionality.

**Validates: Requirements 5.1**

Tests pagination completeness and consistency across the BaseRepository pattern.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import List, Set
from decimal import Decimal

from src.repositories.product_repository import ProductRepository
from src.infrastructure.database import DatabaseClient


class TestPaginationProperties:
    """Property-based tests for pagination."""
    
    @pytest.mark.asyncio
    @given(
        num_products=st.integers(min_value=1, max_value=100),
        page_size=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=50, deadline=5000)
    async def test_pagination_completeness(
        self,
        num_products: int,
        page_size: int,
        db_client,
        product_repository,
        clean_database
    ):
        """
        Property 8: Pagination completeness.
        
        **Validates: Requirements 5.1**
        
        Test that all items appear exactly once across all pages.
        When paginating through a dataset, every item should appear
        exactly once - no duplicates and no missing items.
        
        Property: For any dataset and page_size, the union of all pages
        equals the complete dataset, with no duplicates.
        """
        # Setup: Create test products
        repo = product_repository
        created_ids: Set[int] = set()
        
        try:
            # Create products with unique SKUs
            for i in range(num_products):
                product = await repo.create(
                    sku=f"TEST-PAGINATION-{i}",
                    name=f"Test Product {i}",
                    gender="U",
                    brand="TestBrand",
                    reference=f"REF{i}",
                    size="M",
                    quantity=10,
                    price=Decimal("99.99"),
                    min_stock=5
                )
                created_ids.add(product.id)
            
            # Paginate through all products
            collected_ids: Set[int] = set()
            page = 1
            total_pages = (num_products + page_size - 1) // page_size
            
            while page <= total_pages:
                result = await repo.list_paginated(
                    page=page,
                    page_size=page_size,
                    filters={"brand": "TestBrand"}
                )
                
                # Collect IDs from this page
                page_ids = {p.id for p in result.items}
                
                # Check for duplicates within the page
                assert len(page_ids) == len(result.items), \
                    f"Page {page} contains duplicate items"
                
                # Check for duplicates across pages
                duplicates = collected_ids & page_ids
                assert not duplicates, \
                    f"Items {duplicates} appear on multiple pages"
                
                collected_ids.update(page_ids)
                page += 1
            
            # Property: All created items appear exactly once
            assert collected_ids == created_ids, \
                f"Pagination incomplete. Created: {len(created_ids)}, " \
                f"Collected: {len(collected_ids)}, " \
                f"Missing: {created_ids - collected_ids}, " \
                f"Extra: {collected_ids - created_ids}"
            
        finally:
            # Cleanup: Delete test products
            for product_id in created_ids:
                await repo.delete(product_id)
    
    @pytest.mark.asyncio
    @given(
        num_products=st.integers(min_value=10, max_value=50),
        page_size=st.integers(min_value=1, max_value=15)
    )
    @settings(max_examples=30, deadline=5000)
    async def test_pagination_page_size_consistency(
        self,
        num_products: int,
        page_size: int,
        db_client,
        product_repository,
        clean_database
    ):
        """
        Property 9: Page size consistency.
        
        **Validates: Requirements 5.1**
        
        Test that all pages except the last have exactly page_size items.
        The last page may have fewer items if the total doesn't divide evenly.
        
        Property: For pages 1 to (total_pages - 1), each page has exactly
        page_size items. The last page has (total % page_size) or page_size items.
        """
        # Setup: Create test products
        repo = product_repository
        created_ids: Set[int] = set()
        
        try:
            # Create products
            for i in range(num_products):
                product = await repo.create(
                    sku=f"TEST-PAGESIZE-{i}",
                    name=f"Test Product {i}",
                    gender="U",
                    brand="TestPageSize",
                    reference=f"REF{i}",
                    size="M",
                    quantity=10,
                    price=Decimal("99.99"),
                    min_stock=5
                )
                created_ids.add(product.id)
            
            # Calculate expected pages
            total_pages = (num_products + page_size - 1) // page_size
            expected_last_page_size = num_products % page_size
            if expected_last_page_size == 0:
                expected_last_page_size = page_size
            
            # Check each page
            for page in range(1, total_pages + 1):
                result = await repo.list_paginated(
                    page=page,
                    page_size=page_size,
                    filters={"brand": "TestPageSize"}
                )
                
                if page < total_pages:
                    # All pages except last should have exactly page_size items
                    assert len(result.items) == page_size, \
                        f"Page {page} has {len(result.items)} items, expected {page_size}"
                else:
                    # Last page should have remaining items
                    assert len(result.items) == expected_last_page_size, \
                        f"Last page {page} has {len(result.items)} items, " \
                        f"expected {expected_last_page_size}"
                
                # Verify pagination metadata
                assert result.page == page
                assert result.page_size == page_size
                assert result.total == num_products
                assert result.total_pages == total_pages
                assert result.has_next == (page < total_pages)
                assert result.has_prev == (page > 1)
        
        finally:
            # Cleanup
            for product_id in created_ids:
                await repo.delete(product_id)
    
    @pytest.mark.asyncio
    @given(
        num_products=st.integers(min_value=5, max_value=30),
        page_size=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=30, deadline=5000)
    async def test_pagination_order_consistency(
        self,
        num_products: int,
        page_size: int,
        db_client,
        product_repository,
        clean_database
    ):
        """
        Property: Pagination order consistency.
        
        **Validates: Requirements 5.1**
        
        Test that items maintain consistent order across pages.
        When ordering by a field, the concatenation of all pages
        should produce the same order as a non-paginated query.
        """
        # Setup: Create test products with sequential names
        repo = product_repository
        created_ids: Set[int] = set()
        
        try:
            # Create products with sortable names
            for i in range(num_products):
                product = await repo.create(
                    sku=f"TEST-ORDER-{i:03d}",
                    name=f"Product {i:03d}",
                    gender="U",
                    brand="TestOrder",
                    reference=f"REF{i}",
                    size="M",
                    quantity=10,
                    price=Decimal("99.99"),
                    min_stock=5
                )
                created_ids.add(product.id)
            
            # Get all products without pagination (ordered by name)
            all_products = await repo.list(
                filters={"brand": "TestOrder"},
                order_by="name",
                order_desc=False
            )
            all_names = [p.name for p in all_products]
            
            # Get products with pagination (ordered by name)
            paginated_names: List[str] = []
            page = 1
            total_pages = (num_products + page_size - 1) // page_size
            
            while page <= total_pages:
                result = await repo.list_paginated(
                    page=page,
                    page_size=page_size,
                    filters={"brand": "TestOrder"},
                    order_by="name",
                    order_desc=False
                )
                paginated_names.extend([p.name for p in result.items])
                page += 1
            
            # Property: Paginated order matches non-paginated order
            assert paginated_names == all_names, \
                f"Order mismatch. Expected: {all_names}, Got: {paginated_names}"
        
        finally:
            # Cleanup
            for product_id in created_ids:
                await repo.delete(product_id)


@pytest.mark.asyncio
async def test_pagination_empty_dataset(db_client, product_repository):
    """
    Test pagination behavior with empty dataset.
    
    **Validates: Requirements 5.1**
    
    When there are no items, pagination should return empty results
    with correct metadata (total=0, total_pages=0).
    """
    repo = product_repository
    
    result = await repo.list_paginated(
        page=1,
        page_size=20,
        filters={"brand": "NonExistentBrand"}
    )
    
    assert result.items == []
    assert result.total == 0
    assert result.page == 1
    assert result.page_size == 20
    assert result.total_pages == 0
    assert not result.has_next
    assert not result.has_prev


@pytest.mark.asyncio
async def test_pagination_boundary_pages(db_client, product_repository, clean_database):
    """
    Test pagination with boundary page numbers.
    
    **Validates: Requirements 5.1**
    
    Test that requesting page 0, negative pages, or pages beyond
    total_pages are handled gracefully.
    """
    repo = product_repository
    created_ids: Set[int] = set()
    
    try:
        # Create a few products
        for i in range(5):
            product = await repo.create(
                sku=f"TEST-BOUNDARY-{i}",
                name=f"Test Product {i}",
                gender="U",
                brand="TestBoundary",
                reference=f"REF{i}",
                size="M",
                quantity=10,
                price=Decimal("99.99"),
                min_stock=5
            )
            created_ids.add(product.id)
        
        # Test page 0 (should be treated as page 1)
        result = await repo.list_paginated(
            page=0,
            page_size=2,
            filters={"brand": "TestBoundary"}
        )
        assert result.page == 1
        assert len(result.items) > 0
        
        # Test page beyond total_pages (should return empty)
        result = await repo.list_paginated(
            page=100,
            page_size=2,
            filters={"brand": "TestBoundary"}
        )
        assert result.items == []
        assert result.page == 100
        assert not result.has_next
    
    finally:
        # Cleanup
        for product_id in created_ids:
            await repo.delete(product_id)

