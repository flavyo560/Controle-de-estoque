"""Property-based tests for sales operations.

**Validates: Requirements 19.1**

Tests universal properties of sales management including
transaction atomicity and sale cancellation idempotence.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from typing import List

from src.domain.product import ProductCreate
from src.domain.sale import SaleCreate, SaleItemCreate, PaymentCreate
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.audit_repository import AuditRepository
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.exceptions import InsufficientStockError, ValidationError, NotFoundError


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
        quantity=draw(st.integers(min_value=10, max_value=100)),
        price=Decimal(str(draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)))).quantize(Decimal('0.01')),
        barcode=draw(st.one_of(st.none(), st.text(min_size=8, max_size=13, alphabet=st.characters(whitelist_categories=('Nd',))))),
        min_stock=draw(st.integers(min_value=0, max_value=10))
    )


@st.composite
def sale_item_strategy(draw, product_id: int, max_quantity: int):
    """Generate valid SaleItemCreate instances for testing."""
    quantity = draw(st.integers(min_value=1, max_value=max_quantity + 10))  # Can exceed stock
    unit_price = Decimal(str(draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)))).quantize(Decimal('0.01'))
    
    return SaleItemCreate(
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price
    )


class TestSalesProperties:
    """Property-based tests for sales operations."""
    
    @pytest.mark.asyncio
    @given(
        product_data=product_create_strategy(),
        requested_quantity_multiplier=st.floats(min_value=1.1, max_value=3.0)  # Request more than available
    )
    @settings(max_examples=50, deadline=5000)
    async def test_sale_transaction_atomicity_insufficient_stock(
        self,
        product_data: ProductCreate,
        requested_quantity_multiplier: float,
        db_client,
        product_repository,
        sale_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 12: Sale transaction atomicity.
        
        **Validates: Requirements 19.1**
        
        Test that failed sales don't modify stock. When a sale fails due to
        insufficient stock, the product quantity must remain unchanged.
        
        This verifies that:
        1. Failed sales don't create sale records
        2. Failed sales don't modify product stock
        3. Failed sales don't create inventory movements
        4. Transaction rollback works correctly
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create sales service
        sales_service = SalesService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            audit_repo=audit_repository,
            db_client=db_client
        )
        
        # Create product with initial stock
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        initial_quantity = product.quantity
        
        # Calculate requested quantity that exceeds available stock
        requested_quantity = int(initial_quantity * requested_quantity_multiplier)
        assume(requested_quantity > initial_quantity)  # Ensure we request more than available
        
        # Create sale data with insufficient stock
        sale_item = SaleItemCreate(
            product_id=product.id,
            quantity=requested_quantity,
            unit_price=product.price
        )
        
        total_amount = Decimal(str(requested_quantity)) * product.price
        
        sale_data = SaleCreate(
            customer_id=None,
            user_id=1,
            items=[sale_item],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=total_amount
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        # Attempt to create sale - should fail with InsufficientStockError
        with pytest.raises(InsufficientStockError) as exc_info:
            await sales_service.create_sale(sale_data)
        
        # Verify error message contains relevant information
        assert str(initial_quantity) in str(exc_info.value)
        assert str(requested_quantity) in str(exc_info.value)
        
        # Property: Stock quantity must remain unchanged after failed sale
        updated_product = await product_repository.get_by_id(product.id)
        assert updated_product is not None, "Product should still exist"
        assert updated_product.quantity == initial_quantity, \
            f"Stock quantity changed after failed sale. " \
            f"Initial: {initial_quantity}, Current: {updated_product.quantity}"
        
        # Verify no sale was created
        sales_query = """
            SELECT COUNT(*) as count
            FROM sales
            WHERE user_id = $1
        """
        sales_count = await db_client.fetch_val(sales_query, 1)
        assert sales_count == 0, \
            f"Sale record was created despite failure. Count: {sales_count}"
        
        # Verify no inventory movements were created
        movements_query = """
            SELECT COUNT(*) as count
            FROM inventory_movements
            WHERE product_id = $1 AND movement_type = 'OUT'
        """
        movements_count = await db_client.fetch_val(movements_query, product.id)
        assert movements_count == 0, \
            f"Inventory movement was created despite failure. Count: {movements_count}"
    
    @pytest.mark.asyncio
    @given(
        product_data=product_create_strategy(),
        sale_quantity=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=5000)
    async def test_sale_transaction_atomicity_invalid_payment(
        self,
        product_data: ProductCreate,
        sale_quantity: int,
        db_client,
        product_repository,
        sale_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 12: Sale transaction atomicity (payment validation).
        
        **Validates: Requirements 19.1**
        
        Test that failed sales don't modify stock when payment validation fails.
        When a sale fails due to payment amount mismatch, the product quantity
        must remain unchanged.
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create sales service
        sales_service = SalesService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            audit_repo=audit_repository,
            db_client=db_client
        )
        
        # Create product with sufficient stock
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Ensure we have enough stock
        assume(product.quantity >= sale_quantity)
        
        initial_quantity = product.quantity
        
        # Create sale data with mismatched payment amount
        sale_item = SaleItemCreate(
            product_id=product.id,
            quantity=sale_quantity,
            unit_price=product.price
        )
        
        total_amount = Decimal(str(sale_quantity)) * product.price
        incorrect_payment = total_amount - Decimal("10.00")  # Pay less than required
        
        sale_data = SaleCreate(
            customer_id=None,
            user_id=1,
            items=[sale_item],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=incorrect_payment
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        # Attempt to create sale - should fail with ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await sales_service.create_sale(sale_data)
        
        # Verify error message mentions payment mismatch
        assert "payment" in str(exc_info.value).lower()
        
        # Property: Stock quantity must remain unchanged after failed sale
        updated_product = await product_repository.get_by_id(product.id)
        assert updated_product is not None, "Product should still exist"
        assert updated_product.quantity == initial_quantity, \
            f"Stock quantity changed after failed sale. " \
            f"Initial: {initial_quantity}, Current: {updated_product.quantity}"
        
        # Verify no sale was created
        sales_query = """
            SELECT COUNT(*) as count
            FROM sales
            WHERE user_id = $1
        """
        sales_count = await db_client.fetch_val(sales_query, 1)
        assert sales_count == 0, \
            f"Sale record was created despite failure. Count: {sales_count}"
        
        # Verify no inventory movements were created
        movements_query = """
            SELECT COUNT(*) as count
            FROM inventory_movements
            WHERE product_id = $1 AND movement_type = 'OUT'
        """
        movements_count = await db_client.fetch_val(movements_query, product.id)
        assert movements_count == 0, \
            f"Inventory movement was created despite failure. Count: {movements_count}"
    
    @pytest.mark.asyncio
    @given(
        product_data=product_create_strategy(),
        sale_quantity=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=50, deadline=5000)
    async def test_sale_transaction_atomicity_nonexistent_product(
        self,
        product_data: ProductCreate,
        sale_quantity: int,
        db_client,
        product_repository,
        sale_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 12: Sale transaction atomicity (nonexistent product).
        
        **Validates: Requirements 19.1**
        
        Test that failed sales don't create partial records when a product
        doesn't exist. This verifies transaction rollback for multi-item sales.
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create sales service
        sales_service = SalesService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            audit_repo=audit_repository,
            db_client=db_client
        )
        
        # Create first product
        product1 = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        assume(product1.quantity >= sale_quantity)
        
        initial_quantity = product1.quantity
        
        # Use a non-existent product ID
        nonexistent_product_id = 99999
        
        # Create sale data with one valid and one invalid product
        sale_items = [
            SaleItemCreate(
                product_id=product1.id,
                quantity=sale_quantity,
                unit_price=product1.price
            ),
            SaleItemCreate(
                product_id=nonexistent_product_id,
                quantity=1,
                unit_price=Decimal("10.00")
            )
        ]
        
        total_amount = (Decimal(str(sale_quantity)) * product1.price) + Decimal("10.00")
        
        sale_data = SaleCreate(
            customer_id=None,
            user_id=1,
            items=sale_items,
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=total_amount
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        # Attempt to create sale - should fail with NotFoundError
        with pytest.raises(NotFoundError):
            await sales_service.create_sale(sale_data)
        
        # Property: Stock quantity must remain unchanged for valid product
        updated_product = await product_repository.get_by_id(product1.id)
        assert updated_product is not None, "Product should still exist"
        assert updated_product.quantity == initial_quantity, \
            f"Stock quantity changed after failed sale. " \
            f"Initial: {initial_quantity}, Current: {updated_product.quantity}"
        
        # Verify no sale was created
        sales_query = """
            SELECT COUNT(*) as count
            FROM sales
            WHERE user_id = $1
        """
        sales_count = await db_client.fetch_val(sales_query, 1)
        assert sales_count == 0, \
            f"Sale record was created despite failure. Count: {sales_count}"
        
        # Verify no inventory movements were created for the valid product
        movements_query = """
            SELECT COUNT(*) as count
            FROM inventory_movements
            WHERE product_id = $1 AND movement_type = 'OUT'
        """
        movements_count = await db_client.fetch_val(movements_query, product1.id)
        assert movements_count == 0, \
            f"Inventory movement was created despite failure. Count: {movements_count}"
    
    @pytest.mark.asyncio
    @given(
        product_data=product_create_strategy(),
        sale_quantity=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30, deadline=5000)
    async def test_successful_sale_modifies_stock(
        self,
        product_data: ProductCreate,
        sale_quantity: int,
        db_client,
        product_repository,
        sale_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property: Successful sales correctly modify stock.
        
        **Validates: Requirements 19.1**
        
        Test that successful sales DO modify stock correctly. This is the
        positive case to verify that atomicity works both ways.
        """
        # Create inventory service
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        # Create sales service
        sales_service = SalesService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            audit_repo=audit_repository,
            db_client=db_client
        )
        
        # Create product with sufficient stock
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=1
        )
        
        # Ensure we have enough stock
        assume(product.quantity >= sale_quantity)
        
        initial_quantity = product.quantity
        
        # Create valid sale data
        sale_item = SaleItemCreate(
            product_id=product.id,
            quantity=sale_quantity,
            unit_price=product.price
        )
        
        total_amount = Decimal(str(sale_quantity)) * product.price
        
        sale_data = SaleCreate(
            customer_id=None,
            user_id=1,
            items=[sale_item],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=total_amount
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        # Create sale - should succeed
        sale = await sales_service.create_sale(sale_data)
        
        assert sale is not None, "Sale should be created"
        assert sale.id is not None, "Sale should have an ID"
        
        # Property: Stock quantity must be reduced by sale quantity
        expected_quantity = initial_quantity - sale_quantity
        updated_product = await product_repository.get_by_id(product.id)
        assert updated_product is not None, "Product should still exist"
        assert updated_product.quantity == expected_quantity, \
            f"Stock quantity not updated correctly. " \
            f"Initial: {initial_quantity}, Sale: {sale_quantity}, " \
            f"Expected: {expected_quantity}, Current: {updated_product.quantity}"
        
        # Verify sale was created
        sales_query = """
            SELECT COUNT(*) as count
            FROM sales
            WHERE id = $1
        """
        sales_count = await db_client.fetch_val(sales_query, sale.id)
        assert sales_count == 1, "Sale record should exist"
        
        # Verify inventory movement was created
        movements_query = """
            SELECT COUNT(*) as count
            FROM inventory_movements
            WHERE product_id = $1 AND movement_type = 'OUT'
        """
        movements_count = await db_client.fetch_val(movements_query, product.id)
        assert movements_count == 1, \
            f"Inventory movement should be created. Count: {movements_count}"
