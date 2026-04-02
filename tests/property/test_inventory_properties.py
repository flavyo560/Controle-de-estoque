"""Property-based tests for inventory operations.

**Validates: Requirements 19.2**

Tests universal properties of inventory management including
stock update consistency and inventory movement tracking.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from typing import List

from src.domain.product import ProductCreate
from src.repositories.product_repository import ProductRepository
from src.services.inventory_service import InventoryService
from src.exceptions import InsufficientStockError


@st.composite
def product_create_strategy(draw):
    """Generate valid ProductCreate instances for testing."""
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


class TestInventoryProperties:
    """Property-based tests for inventory operations."""
    
    @pytest.mark.asyncio
    @given(
        product_data=product_create_strategy(),
        stock_changes=st.lists(
            st.integers(min_value=-50, max_value=50),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=5000)
    async def test_stock_update_consistency(
        self,
        product_data: ProductCreate,
        stock_changes: List[int],
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 10: Stock update consistency.
        
        **Validates: Requirements 19.2**
        
        Test that quantity_after = quantity_before + quantity_change for all
        valid stock operations. This verifies that:
        1. Stock updates are applied correctly
        2. The quantity calculation is accurate
        3. Inventory movements record the correct before/after quantities
        
        The test generates random product data and random sequences of
        stock changes, then verifies that:
        - Valid operations update quantity correctly
        - Invalid operations (negative result) are rejected
        - The final quantity matches the sum of all applied changes
        - Inventory movements are created with correct quantities
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
        applied_changes: List[int] = []
        
        # Apply each stock change
        for quantity_change in stock_changes:
            new_quantity = expected_quantity + quantity_change
            
            if new_quantity < 0:
                # Operation should fail - quantity would go negative
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
                assert updated_product.quantity == expected_quantity, \
                    f"Quantity changed after failed operation. " \
                    f"Expected: {expected_quantity}, Got: {updated_product.quantity}"
            else:
                # Operation should succeed
                quantity_before = expected_quantity
                
                updated_product = await inventory_service.update_stock(
                    product_id=product.id,
                    quantity_change=quantity_change,
                    user_id=1,
                    reference_type='test',
                    notes='Property test operation'
                )
                
                # Property: quantity_after = quantity_before + quantity_change
                assert updated_product.quantity == quantity_before + quantity_change, \
                    f"Stock update consistency violated. " \
                    f"Before: {quantity_before}, Change: {quantity_change}, " \
                    f"Expected After: {quantity_before + quantity_change}, " \
                    f"Actual After: {updated_product.quantity}"
                
                # Update expected quantity
                expected_quantity = new_quantity
                applied_changes.append(quantity_change)
                
                # Verify quantity is non-negative
                assert updated_product.quantity >= 0, \
                    f"Quantity became negative: {updated_product.quantity}"
        
        # Final verification: fetch from database and verify quantity
        final_product = await product_repository.get_by_id(product.id)
        assert final_product is not None
        assert final_product.quantity == expected_quantity, \
            f"Final quantity mismatch. Expected: {expected_quantity}, " \
            f"Got: {final_product.quantity}"
        
        # Verify final quantity equals initial + sum of applied changes
        expected_final = product_data.quantity + sum(applied_changes)
        assert final_product.quantity == expected_final, \
            f"Final quantity doesn't match initial + changes. " \
            f"Initial: {product_data.quantity}, Changes: {applied_changes}, " \
            f"Expected: {expected_final}, Got: {final_product.quantity}"
    
    @pytest.mark.asyncio
    @given(
        initial_quantity=st.integers(min_value=0, max_value=100),
        quantity_change=st.integers(min_value=-200, max_value=200)
    )
    @settings(max_examples=100, deadline=3000)
    async def test_single_stock_update_consistency(
        self,
        initial_quantity: int,
        quantity_change: int,
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property: Single stock update maintains consistency.
        
        **Validates: Requirements 19.2**
        
        Test that a single stock update operation maintains the invariant
        quantity_after = quantity_before + quantity_change.
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create product with initial quantity
        product_data = ProductCreate(
            sku=f"SINGLE-{initial_quantity}-{quantity_change}",
            name="Single Update Test Product",
            gender="U",
            brand="TestBrand",
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
        
        # Calculate expected new quantity
        expected_new_quantity = initial_quantity + quantity_change
        
        if expected_new_quantity < 0:
            # Should fail with InsufficientStockError
            with pytest.raises(InsufficientStockError):
                await inventory_service.update_stock(
                    product_id=product.id,
                    quantity_change=quantity_change,
                    user_id=1,
                    reference_type='test'
                )
            
            # Verify quantity unchanged
            updated_product = await product_repository.get_by_id(product.id)
            assert updated_product is not None
            assert updated_product.quantity == initial_quantity
        else:
            # Should succeed
            updated_product = await inventory_service.update_stock(
                product_id=product.id,
                quantity_change=quantity_change,
                user_id=1,
                reference_type='test'
            )
            
            # Property: quantity_after = quantity_before + quantity_change
            assert updated_product.quantity == expected_new_quantity, \
                f"Stock update consistency violated. " \
                f"Before: {initial_quantity}, Change: {quantity_change}, " \
                f"Expected: {expected_new_quantity}, Got: {updated_product.quantity}"
            
            # Verify in database
            db_product = await product_repository.get_by_id(product.id)
            assert db_product is not None
            assert db_product.quantity == expected_new_quantity
    
    @pytest.mark.asyncio
    @given(
        product_data=product_create_strategy(),
        operations=st.lists(
            st.tuples(
                st.sampled_from(['add', 'subtract']),
                st.integers(min_value=1, max_value=50)
            ),
            min_size=1,
            max_size=15
        )
    )
    @settings(max_examples=50, deadline=5000)
    async def test_inventory_movement_completeness(
        self,
        product_data: ProductCreate,
        operations: List[tuple],
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 11: Inventory movement completeness.
        
        **Validates: Requirements 19.2**
        
        Test that every stock change creates an inventory_movement record
        with correct before/after quantities.
        
        This verifies that:
        1. All stock changes are tracked
        2. Inventory movements record accurate quantities
        3. The audit trail is complete
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
        
        # Track expected quantity and successful operations
        current_quantity = product.quantity
        successful_operations = 0
        
        # Apply each operation
        for operation_type, amount in operations:
            quantity_change = amount if operation_type == 'add' else -amount
            new_quantity = current_quantity + quantity_change
            
            if new_quantity < 0:
                # Operation will fail - skip
                try:
                    await inventory_service.update_stock(
                        product_id=product.id,
                        quantity_change=quantity_change,
                        user_id=1,
                        reference_type='test'
                    )
                except InsufficientStockError:
                    # Expected failure - no movement should be created
                    pass
            else:
                # Operation should succeed
                await inventory_service.update_stock(
                    product_id=product.id,
                    quantity_change=quantity_change,
                    user_id=1,
                    reference_type='test'
                )
                current_quantity = new_quantity
                successful_operations += 1
        
        # Verify inventory movements were created
        # Query inventory_movements table
        movements_query = """
            SELECT product_id, quantity_change, quantity_before, quantity_after
            FROM inventory_movements
            WHERE product_id = $1
            ORDER BY created_at ASC
        """
        movements = await db_client.fetch_all(movements_query, product.id)
        
        # Property: Number of movements equals number of successful operations
        assert len(movements) == successful_operations, \
            f"Inventory movement count mismatch. " \
            f"Expected: {successful_operations}, Got: {len(movements)}"
        
        # Verify each movement has correct before/after quantities
        expected_quantity = product_data.quantity
        for movement in movements:
            quantity_before = movement['quantity_before']
            quantity_after = movement['quantity_after']
            quantity_change = movement['quantity_change']
            
            # Property: quantity_after = quantity_before + quantity_change
            assert quantity_after == quantity_before + quantity_change, \
                f"Movement consistency violated. " \
                f"Before: {quantity_before}, Change: {quantity_change}, " \
                f"After: {quantity_after}"
            
            # Verify quantity_before matches expected
            assert quantity_before == expected_quantity, \
                f"Movement quantity_before mismatch. " \
                f"Expected: {expected_quantity}, Got: {quantity_before}"
            
            # Update expected for next iteration
            expected_quantity = quantity_after
        
        # Final verification: last movement's quantity_after matches current product quantity
        if movements:
            final_product = await product_repository.get_by_id(product.id)
            assert final_product is not None
            assert final_product.quantity == movements[-1]['quantity_after'], \
                f"Final product quantity doesn't match last movement. " \
                f"Product: {final_product.quantity}, " \
                f"Last Movement: {movements[-1]['quantity_after']}"

    @pytest.mark.asyncio
    @given(
        products_data=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=100),  # quantity
                st.integers(min_value=1, max_value=50)    # min_stock
            ),
            min_size=5,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=5000)
    async def test_alert_threshold_consistency(
        self,
        products_data: List[tuple],
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 16: Alert threshold consistency.
        
        **Validates: Requirements 18.1**
        
        Test that alerts are shown if and only if quantity < min_stock.
        
        This is the fundamental invariant of the alert system:
        - A product MUST appear in low stock alerts if quantity < min_stock
        - A product MUST NOT appear in low stock alerts if quantity >= min_stock
        
        The test generates random products with various quantity and min_stock
        values and verifies that the alert system correctly identifies which
        products should trigger alerts based solely on the threshold comparison.
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create products with specified quantities and min_stock values
        created_products = []
        expected_low_stock_ids = set()
        expected_ok_stock_ids = set()
        
        for idx, (quantity, min_stock) in enumerate(products_data):
            product_data = ProductCreate(
                sku=f"ALERT-TEST-{idx}",
                name=f"Alert Test Product {idx}",
                gender="U",
                brand="TestBrand",
                reference=f"REF-{idx}",
                size="M",
                quantity=quantity,
                price=Decimal("99.99"),
                min_stock=min_stock
            )
            
            product = await inventory_service.create_product(
                product_data=product_data,
                user_id=1
            )
            created_products.append(product)
            
            # Determine if this product should be in low stock alerts
            if quantity < min_stock:
                expected_low_stock_ids.add(product.id)
            else:
                expected_ok_stock_ids.add(product.id)
        
        # Get low stock alerts
        alerts_result = await inventory_service.get_low_stock_alerts()
        alert_products = alerts_result["products"]
        alert_product_ids = {p["id"] for p in alert_products}
        
        # Property: Products in alerts if and only if quantity < min_stock
        
        # Part 1: All products with quantity < min_stock MUST be in alerts
        for product_id in expected_low_stock_ids:
            assert product_id in alert_product_ids, \
                f"Product {product_id} has quantity < min_stock but is NOT in alerts. " \
                f"This violates the alert threshold consistency property."
        
        # Part 2: No products with quantity >= min_stock should be in alerts
        for product_id in expected_ok_stock_ids:
            assert product_id not in alert_product_ids, \
                f"Product {product_id} has quantity >= min_stock but IS in alerts. " \
                f"This violates the alert threshold consistency property."
        
        # Part 3: Verify the alert list contains exactly the expected products
        assert alert_product_ids == expected_low_stock_ids, \
            f"Alert product IDs don't match expected low stock IDs. " \
            f"Expected: {expected_low_stock_ids}, Got: {alert_product_ids}"
        
        # Part 4: Verify metrics are consistent with the alert list
        assert alerts_result["metrics"]["total"] == len(expected_low_stock_ids), \
            f"Alert metrics total doesn't match expected count. " \
            f"Expected: {len(expected_low_stock_ids)}, " \
            f"Got: {alerts_result['metrics']['total']}"
        
        # Part 5: Verify each product in alerts satisfies quantity < min_stock
        for alert_product in alert_products:
            quantity = alert_product["quantity"]
            min_stock = alert_product["min_stock"]
            assert quantity < min_stock, \
                f"Product {alert_product['id']} in alerts but quantity ({quantity}) " \
                f">= min_stock ({min_stock}). Alert threshold consistency violated."
        
        # Part 6: Verify no products are missing from alerts
        # Query database directly to double-check
        direct_query = """
            SELECT id, quantity, min_stock
            FROM products
            WHERE deleted_at IS NULL AND quantity < min_stock
        """
        direct_low_stock = await db_client.fetch_all(direct_query)
        direct_low_stock_ids = {row['id'] for row in direct_low_stock}
        
        assert alert_product_ids == direct_low_stock_ids, \
            f"Alert system results don't match direct database query. " \
            f"Alert IDs: {alert_product_ids}, Direct query IDs: {direct_low_stock_ids}"
    
    @pytest.mark.asyncio
    @given(
        quantity=st.integers(min_value=0, max_value=100),
        min_stock=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100, deadline=3000)
    async def test_single_product_alert_threshold(
        self,
        quantity: int,
        min_stock: int,
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property: Single product alert threshold consistency.
        
        **Validates: Requirements 18.1**
        
        Test that a single product appears in alerts if and only if
        quantity < min_stock. This is a simplified version of the
        full alert threshold consistency property.
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
            sku=f"SINGLE-ALERT-{quantity}-{min_stock}",
            name="Single Alert Test Product",
            gender="U",
            brand="TestBrand",
            reference="TEST-REF",
            size="M",
            quantity=quantity,
            price=Decimal("99.99"),
            min_stock=min_stock
        )
        
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Get low stock alerts
        alerts_result = await inventory_service.get_low_stock_alerts()
        alert_product_ids = {p["id"] for p in alerts_result["products"]}
        
        # Property: Product in alerts if and only if quantity < min_stock
        should_be_in_alerts = quantity < min_stock
        is_in_alerts = product.id in alert_product_ids
        
        assert is_in_alerts == should_be_in_alerts, \
            f"Alert threshold consistency violated for product {product.id}. " \
            f"Quantity: {quantity}, Min Stock: {min_stock}, " \
            f"Should be in alerts: {should_be_in_alerts}, " \
            f"Is in alerts: {is_in_alerts}"
    
    @pytest.mark.asyncio
    @given(
        initial_quantity=st.integers(min_value=0, max_value=100),
        min_stock=st.integers(min_value=5, max_value=50),
        stock_changes=st.lists(
            st.integers(min_value=-20, max_value=20),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=50, deadline=5000)
    async def test_alert_threshold_after_stock_changes(
        self,
        initial_quantity: int,
        min_stock: int,
        stock_changes: List[int],
        db_client,
        product_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property: Alert threshold consistency after stock changes.
        
        **Validates: Requirements 18.1**
        
        Test that alert threshold consistency is maintained after
        stock updates. A product should appear in alerts if and only
        if its current quantity < min_stock, regardless of how many
        stock changes have occurred.
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
            sku=f"DYNAMIC-ALERT-{initial_quantity}-{min_stock}",
            name="Dynamic Alert Test Product",
            gender="U",
            brand="TestBrand",
            reference="TEST-REF",
            size="M",
            quantity=initial_quantity,
            price=Decimal("99.99"),
            min_stock=min_stock
        )
        
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Track current quantity
        current_quantity = initial_quantity
        
        # Apply stock changes and verify alert consistency after each change
        for quantity_change in stock_changes:
            new_quantity = current_quantity + quantity_change
            
            if new_quantity < 0:
                # Skip invalid operations
                continue
            
            # Update stock
            await inventory_service.update_stock(
                product_id=product.id,
                quantity_change=quantity_change,
                user_id=1,
                reference_type='test'
            )
            current_quantity = new_quantity
            
            # Get fresh alerts (cache should be invalidated)
            alerts_result = await inventory_service.get_low_stock_alerts()
            alert_product_ids = {p["id"] for p in alerts_result["products"]}
            
            # Property: Product in alerts if and only if current_quantity < min_stock
            should_be_in_alerts = current_quantity < min_stock
            is_in_alerts = product.id in alert_product_ids
            
            assert is_in_alerts == should_be_in_alerts, \
                f"Alert threshold consistency violated after stock change. " \
                f"Current Quantity: {current_quantity}, Min Stock: {min_stock}, " \
                f"Should be in alerts: {should_be_in_alerts}, " \
                f"Is in alerts: {is_in_alerts}, " \
                f"Change applied: {quantity_change}"
