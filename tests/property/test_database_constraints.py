"""Property-based tests for database constraints.

**Validates: Requirements 10.2, 19.1**

These tests verify that database constraints are enforced correctly
across all operations, ensuring data integrity.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from typing import Optional

from src.domain.product import ProductCreate
from src.repositories.product_repository import ProductRepository
from src.services.inventory_service import InventoryService
from src.exceptions import InsufficientStockError


# Hypothesis strategies for generating test data
@st.composite
def product_create_strategy(draw):
    """Generate valid ProductCreate instances."""
    return ProductCreate(
        sku=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        name=draw(st.text(min_size=1, max_size=50)),
        description=draw(st.one_of(st.none(), st.text(max_size=200))),
        gender=draw(st.sampled_from(['M', 'F', 'U'])),
        brand=draw(st.text(min_size=1, max_size=30)),
        reference=draw(st.text(min_size=1, max_size=20)),
        size=draw(st.sampled_from(['P', 'M', 'G', 'GG', '36', '38', '40', '42'])),
        quantity=draw(st.integers(min_value=0, max_value=1000)),
        price=Decimal(str(draw(st.floats(min_value=0.01, max_value=10000.0, allow_nan=False, allow_infinity=False)))).quantize(Decimal('0.01')),
        barcode=draw(st.one_of(st.none(), st.text(min_size=8, max_size=13, alphabet=st.characters(whitelist_categories=('Nd',))))),
        min_stock=draw(st.integers(min_value=0, max_value=50))
    )


@st.composite
def stock_operation_strategy(draw):
    """Generate stock operation (quantity change)."""
    operation_type = draw(st.sampled_from(['add', 'subtract', 'set']))
    
    if operation_type == 'add':
        # Adding stock (positive change)
        return draw(st.integers(min_value=1, max_value=100))
    elif operation_type == 'subtract':
        # Subtracting stock (negative change)
        return draw(st.integers(min_value=-100, max_value=-1))
    else:
        # Setting to specific value
        return draw(st.integers(min_value=0, max_value=100))


class TestDatabaseConstraints:
    """Property-based tests for database constraints."""
    
    @pytest.mark.asyncio
    @given(
        product_data=product_create_strategy(),
        operations=st.lists(
            st.integers(min_value=-50, max_value=50),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=5000)
    async def test_quantity_non_negativity_invariant(
        self,
        product_data: ProductCreate,
        operations: list[int],
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 1: Quantity non-negativity invariant.
        
        **Validates: Requirements 10.2, 19.1**
        
        Test that products.quantity never goes below 0 after any sequence
        of stock operations. This verifies that:
        1. Database CHECK constraint prevents negative quantities
        2. Service layer validates stock before operations
        3. Transactions roll back on constraint violations
        
        The test generates random product data and random sequences of
        stock changes (additions and subtractions), then verifies that:
        - Valid operations succeed and maintain quantity >= 0
        - Invalid operations (that would make quantity < 0) are rejected
        - The product quantity in the database is always >= 0
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create initial product
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Track expected quantity
        expected_quantity = product.quantity
        
        # Apply each operation
        for quantity_change in operations:
            new_quantity = expected_quantity + quantity_change
            
            if new_quantity < 0:
                # Operation should fail with InsufficientStockError
                with pytest.raises(InsufficientStockError):
                    await inventory_service.update_stock(
                        product_id=product.id,
                        quantity_change=quantity_change,
                        user_id=1,
                        reference_type='test',
                        notes='Property test operation'
                    )
                
                # Quantity should remain unchanged
                updated_product = await product_repository.get_by_id(product.id)
                assert updated_product is not None
                assert updated_product.quantity == expected_quantity
                assert updated_product.quantity >= 0
            else:
                # Operation should succeed
                updated_product = await inventory_service.update_stock(
                    product_id=product.id,
                    quantity_change=quantity_change,
                    user_id=1,
                    reference_type='test',
                    notes='Property test operation'
                )
                
                # Update expected quantity
                expected_quantity = new_quantity
                
                # Verify quantity is correct and non-negative
                assert updated_product.quantity == expected_quantity
                assert updated_product.quantity >= 0
        
        # Final verification: fetch from database and verify quantity >= 0
        final_product = await product_repository.get_by_id(product.id)
        assert final_product is not None
        assert final_product.quantity >= 0
        assert final_product.quantity == expected_quantity
    
    @pytest.mark.asyncio
    @given(
        initial_quantity=st.integers(min_value=0, max_value=100),
        subtract_amount=st.integers(min_value=1, max_value=200)
    )
    @settings(max_examples=50, deadline=3000)
    async def test_insufficient_stock_rejection(
        self,
        initial_quantity: int,
        subtract_amount: int,
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property: Insufficient stock operations are always rejected.
        
        **Validates: Requirements 10.2, 19.1**
        
        Test that attempting to subtract more stock than available
        always fails and leaves the quantity unchanged.
        """
        # Assume we're trying to subtract more than available
        assume(subtract_amount > initial_quantity)
        
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create product with initial quantity
        product_data = ProductCreate(
            sku=f"TEST-{initial_quantity}-{subtract_amount}",
            name="Test Product",
            gender="U",
            brand="Test Brand",
            reference="TEST-REF",
            size="M",
            quantity=initial_quantity,
            price=Decimal("10.00"),
            min_stock=5
        )
        
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Try to subtract more than available
        with pytest.raises(InsufficientStockError):
            await inventory_service.update_stock(
                product_id=product.id,
                quantity_change=-subtract_amount,
                user_id=1,
                reference_type='test'
            )
        
        # Verify quantity unchanged
        updated_product = await product_repository.get_by_id(product.id)
        assert updated_product is not None
        assert updated_product.quantity == initial_quantity
        assert updated_product.quantity >= 0
    
    @pytest.mark.asyncio
    @given(
        quantity=st.integers(min_value=0, max_value=1000)
    )
    @settings(max_examples=50, deadline=3000)
    async def test_direct_update_maintains_non_negativity(
        self,
        quantity: int,
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property: Direct quantity updates maintain non-negativity.
        
        **Validates: Requirements 10.2**
        
        Test that directly updating product quantity (not through stock operations)
        also maintains the non-negativity constraint.
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create product
        product_data = ProductCreate(
            sku=f"DIRECT-{quantity}",
            name="Test Product",
            gender="U",
            brand="Test Brand",
            reference="TEST-REF",
            size="M",
            quantity=100,
            price=Decimal("10.00"),
            min_stock=5
        )
        
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Update quantity directly
        from src.domain.product import ProductUpdate
        update_data = ProductUpdate(quantity=quantity)
        
        updated_product = await inventory_service.update_product(
            product_id=product.id,
            product_data=update_data,
            user_id=1
        )
        
        # Verify quantity is non-negative
        assert updated_product.quantity >= 0
        assert updated_product.quantity == quantity
        
        # Verify in database
        db_product = await product_repository.get_by_id(product.id)
        assert db_product is not None
        assert db_product.quantity >= 0
        assert db_product.quantity == quantity
