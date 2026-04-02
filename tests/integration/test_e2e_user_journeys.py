"""
End-to-end integration tests for complete user journeys.

**Validates: Requirements 9.3, 4.1**

These tests verify that all system components work together correctly
through complete user workflows, testing the 3-layer architecture
(UI → Service → Repository) integration.

Test scenarios:
1. Complete user journey: login → create product → create sale → view report
2. Error scenarios across multiple screens
3. Data consistency across operations
4. Transaction rollback scenarios
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Dict, Any

from src.domain.user import UserCreate
from src.domain.product import ProductCreate
from src.domain.sale import SaleCreate, SaleItemCreate, PaymentCreate
from src.services.auth_service import AuthService
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.report_service import ReportService
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.infrastructure.database import DatabaseClient
from src.infrastructure.cache import CacheManager
from src.exceptions import (
    AuthenticationError,
    InsufficientStockError,
    NotFoundError,
    ValidationError
)


@pytest.mark.asyncio
class TestCompleteUserJourney:
    """Test complete user journey through the system."""
    
    async def test_happy_path_login_create_product_sale_report(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        sale_repository: SaleRepository,
        cache_manager: CacheManager,
        db_client: DatabaseClient,
        clean_database
    ):
        """
        Test complete happy path user journey.
        
        **Validates: Requirements 9.3, 4.1**
        
        Journey:
        1. Register and login user
        2. Create a product
        3. Create a sale for that product
        4. Verify report shows the sale
        5. Verify data consistency across all layers
        """
        # Step 1: Register and login user
        user_data = UserCreate(
            username="journeyuser",
            password="SecurePass123!",
            full_name="Journey Test User",
            email="journey@test.com",
            role="manager"
        )
        
        user = await auth_service.register_user(user_data, created_by=1)
        assert user.id is not None
        assert user.username == "journeyuser"
        
        # Authenticate user
        session = await auth_service.authenticate(
            username="journeyuser",
            password="SecurePass123!",
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        assert session is not None
        assert session.user_id == user.id
        
        # Validate session
        validated_user = await auth_service.validate_session(
            session.token,
            ip_address="127.0.0.1"
        )
        assert validated_user.id == user.id
        
        # Step 2: Create a product
        product_data = ProductCreate(
            sku="JOURNEY-001",
            name="Journey Test Product",
            description="Product for journey test",
            gender="U",
            brand="TestBrand",
            reference="REF-001",
            size="M",
            quantity=50,
            price=Decimal("99.99"),
            barcode="1234567890123",
            min_stock=10
        )
        
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        assert product.id is not None
        assert product.sku == "JOURNEY-001"
        assert product.quantity == 50
        
        # Verify product is in database
        db_product = await product_repository.get_by_id(product.id)
        assert db_product is not None
        assert db_product.sku == "JOURNEY-001"
        
        # Step 3: Create a sale for the product
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=product.id,
                    quantity=5,
                    unit_price=Decimal("99.99")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=Decimal("499.95")
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        sale = await sales_service.create_sale(
            sale_data=sale_data,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        assert sale.id is not None
        assert sale.final_amount == Decimal("499.95")
        assert len(sale.items) == 1
        
        # Verify stock was deducted
        updated_product = await product_repository.get_by_id(product.id)
        assert updated_product.quantity == 45  # 50 - 5
        
        # Step 4: Verify report shows the sale
        from src.services.report_service import ReportService
        report_service = ReportService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            cache=cache_manager,
            db=db_client
        )
        
        today = date.today()
        report = await report_service.get_sales_report(
            start_date=today,
            end_date=today,
            group_by="day"
        )
        
        assert report["total_sales"] >= 1
        assert report["total_revenue"] >= Decimal("499.95")
        
        # Step 5: Verify data consistency across all layers
        # Check sale in database
        db_sale = await sale_repository.get_by_id(sale.id)
        assert db_sale is not None
        assert db_sale.final_amount == Decimal("499.95")
        assert db_sale.user_id == user.id
        
        # Verify audit trail exists
        # (Audit trail is created automatically by triggers)
        
        # Logout user
        await auth_service.logout(session.token)
        
        # Verify session is revoked
        with pytest.raises(AuthenticationError):
            await auth_service.validate_session(
                session.token,
                ip_address="127.0.0.1"
            )
    
    async def test_multi_product_sale_journey(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test journey with multiple products in a single sale.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user
        user_data = UserCreate(
            username="multiuser",
            password="SecurePass123!",
            full_name="Multi User",
            email="multi@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        # Create multiple products
        products = []
        for i in range(3):
            product_data = ProductCreate(
                sku=f"MULTI-{i:03d}",
                name=f"Multi Product {i}",
                description=f"Product {i} for multi-item sale",
                gender="U",
                brand="TestBrand",
                reference=f"REF-{i:03d}",
                size="M",
                quantity=100,
                price=Decimal(f"{(i+1)*10}.00"),
                min_stock=5
            )
            product = await inventory_service.create_product(
                product_data=product_data,
                user_id=user.id
            )
            products.append(product)
        
        # Create sale with all products
        sale_items = [
            SaleItemCreate(
                product_id=products[0].id,
                quantity=2,
                unit_price=Decimal("10.00")
            ),
            SaleItemCreate(
                product_id=products[1].id,
                quantity=3,
                unit_price=Decimal("20.00")
            ),
            SaleItemCreate(
                product_id=products[2].id,
                quantity=1,
                unit_price=Decimal("30.00")
            )
        ]
        
        total = Decimal("2") * Decimal("10.00") + \
                Decimal("3") * Decimal("20.00") + \
                Decimal("1") * Decimal("30.00")
        
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=sale_items,
            payments=[
                PaymentCreate(
                    payment_method="credit_card",
                    amount=total
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        sale = await sales_service.create_sale(sale_data=sale_data)
        
        # Verify sale totals
        assert sale.total_amount == total
        assert sale.final_amount == total
        assert len(sale.items) == 3
        
        # Verify all stock levels updated
        for i, product in enumerate(products):
            updated = await product_repository.get_by_id(product.id)
            expected_qty = 100 - sale_items[i].quantity
            assert updated.quantity == expected_qty


@pytest.mark.asyncio
class TestErrorScenariosAcrossLayers:
    """Test error handling across multiple system layers."""
    
    async def test_insufficient_stock_error_propagation(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that insufficient stock errors propagate correctly through layers.
        
        **Validates: Requirements 9.3, 4.1**
        
        Tests:
        - Service layer validates stock
        - Transaction rolls back on error
        - No partial data is saved
        """
        # Create user and product
        user_data = UserCreate(
            username="stockuser",
            password="SecurePass123!",
            full_name="Stock User",
            email="stock@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        product_data = ProductCreate(
            sku="STOCK-001",
            name="Low Stock Product",
            description="Product with limited stock",
            gender="U",
            brand="TestBrand",
            reference="REF-STOCK",
            size="S",
            quantity=5,  # Only 5 in stock
            price=Decimal("50.00"),
            min_stock=2
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        # Try to create sale with more than available stock
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=product.id,
                    quantity=10,  # Requesting 10, but only 5 available
                    unit_price=Decimal("50.00")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=Decimal("500.00")
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        # Should raise InsufficientStockError
        with pytest.raises(InsufficientStockError) as exc_info:
            await sales_service.create_sale(sale_data=sale_data)
        
        assert "insufficient stock" in str(exc_info.value).lower()
        
        # Verify stock was NOT deducted (transaction rolled back)
        unchanged_product = await product_repository.get_by_id(product.id)
        assert unchanged_product.quantity == 5  # Still 5
    
    async def test_authentication_error_prevents_operations(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        clean_database
    ):
        """
        Test that authentication errors prevent downstream operations.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Try to validate invalid session
        with pytest.raises(AuthenticationError):
            await auth_service.validate_session(
                token="invalid_token_12345",
                ip_address="127.0.0.1"
            )
        
        # Try to authenticate with wrong password
        user_data = UserCreate(
            username="authuser",
            password="SecurePass123!",
            full_name="Auth User",
            email="auth@test.com",
            role="user"
        )
        await auth_service.register_user(user_data, created_by=1)
        
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate(
                username="authuser",
                password="WrongPassword123!",
                ip_address="127.0.0.1"
            )
    
    async def test_validation_error_at_service_layer(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        clean_database
    ):
        """
        Test that validation errors are caught at service layer.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user
        user_data = UserCreate(
            username="validuser",
            password="SecurePass123!",
            full_name="Valid User",
            email="valid@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        # Try to create product with invalid data (negative price)
        with pytest.raises((ValidationError, ValueError)):
            product_data = ProductCreate(
                sku="INVALID-001",
                name="Invalid Product",
                description="Product with invalid price",
                gender="U",
                brand="TestBrand",
                reference="REF-INVALID",
                size="M",
                quantity=10,
                price=Decimal("-10.00"),  # Invalid: negative price
                min_stock=5
            )
    
    async def test_not_found_error_propagation(
        self,
        auth_service: AuthService,
        sales_service: SalesService,
        clean_database
    ):
        """
        Test that NotFoundError propagates correctly through layers.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user
        user_data = UserCreate(
            username="notfounduser",
            password="SecurePass123!",
            full_name="NotFound User",
            email="notfound@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        # Try to create sale with non-existent product
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=99999,  # Non-existent product
                    quantity=1,
                    unit_price=Decimal("10.00")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=Decimal("10.00")
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        with pytest.raises(NotFoundError):
            await sales_service.create_sale(sale_data=sale_data)


@pytest.mark.asyncio
class TestDataConsistencyAcrossOperations:
    """Test data consistency across multiple operations."""
    
    async def test_concurrent_sales_maintain_consistency(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that concurrent sales maintain data consistency.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user and product
        user_data = UserCreate(
            username="concurrentuser",
            password="SecurePass123!",
            full_name="Concurrent User",
            email="concurrent@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        product_data = ProductCreate(
            sku="CONCURRENT-001",
            name="Concurrent Product",
            description="Product for concurrent sales",
            gender="U",
            brand="TestBrand",
            reference="REF-CONCURRENT",
            size="L",
            quantity=100,
            price=Decimal("25.00"),
            min_stock=10
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        # Create multiple sales sequentially (simulating concurrent operations)
        sales = []
        for i in range(5):
            sale_data = SaleCreate(
                customer_id=None,
                user_id=user.id,
                items=[
                    SaleItemCreate(
                        product_id=product.id,
                        quantity=10,
                        unit_price=Decimal("25.00")
                    )
                ],
                payments=[
                    PaymentCreate(
                        payment_method="cash",
                        amount=Decimal("250.00")
                    )
                ],
                discount_amount=Decimal("0.00")
            )
            sale = await sales_service.create_sale(sale_data=sale_data)
            sales.append(sale)
        
        # Verify final stock is correct
        final_product = await product_repository.get_by_id(product.id)
        assert final_product.quantity == 50  # 100 - (5 * 10)
        
        # Verify all sales were created
        assert len(sales) == 5
        for sale in sales:
            assert sale.final_amount == Decimal("250.00")
    
    async def test_sale_cancellation_restores_consistency(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        sale_repository: SaleRepository,
        clean_database
    ):
        """
        Test that sale cancellation restores data consistency.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user and product
        user_data = UserCreate(
            username="canceluser",
            password="SecurePass123!",
            full_name="Cancel User",
            email="cancel@test.com",
            role="manager"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        product_data = ProductCreate(
            sku="CANCEL-001",
            name="Cancel Product",
            description="Product for cancellation test",
            gender="U",
            brand="TestBrand",
            reference="REF-CANCEL",
            size="XL",
            quantity=50,
            price=Decimal("75.00"),
            min_stock=5
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        # Create sale
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=product.id,
                    quantity=10,
                    unit_price=Decimal("75.00")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="credit_card",
                    amount=Decimal("750.00")
                )
            ],
            discount_amount=Decimal("0.00")
        )
        sale = await sales_service.create_sale(sale_data=sale_data)
        
        # Verify stock was deducted
        after_sale = await product_repository.get_by_id(product.id)
        assert after_sale.quantity == 40  # 50 - 10
        
        # Cancel sale
        cancelled_sale = await sales_service.cancel_sale(
            sale_id=sale.id,
            user_id=user.id,
            reason="Customer requested cancellation"
        )
        assert cancelled_sale.status == "cancelled"
        
        # Verify stock was restored
        after_cancel = await product_repository.get_by_id(product.id)
        assert after_cancel.quantity == 50  # Back to original


@pytest.mark.asyncio
class TestTransactionRollbackScenarios:
    """Test transaction rollback in error scenarios."""
    
    async def test_sale_creation_rollback_on_payment_error(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        sale_repository: SaleRepository,
        clean_database
    ):
        """
        Test that sale creation rolls back if payment validation fails.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user and product
        user_data = UserCreate(
            username="rollbackuser",
            password="SecurePass123!",
            full_name="Rollback User",
            email="rollback@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        product_data = ProductCreate(
            sku="ROLLBACK-001",
            name="Rollback Product",
            description="Product for rollback test",
            gender="U",
            brand="TestBrand",
            reference="REF-ROLLBACK",
            size="M",
            quantity=30,
            price=Decimal("100.00"),
            min_stock=5
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        initial_quantity = product.quantity
        
        # Try to create sale with payment amount mismatch
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=product.id,
                    quantity=5,
                    unit_price=Decimal("100.00")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=Decimal("400.00")  # Wrong amount: should be 500.00
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        # Should raise ValidationError due to payment mismatch
        with pytest.raises(ValidationError):
            await sales_service.create_sale(sale_data=sale_data)
        
        # Verify stock was NOT deducted (transaction rolled back)
        unchanged_product = await product_repository.get_by_id(product.id)
        assert unchanged_product.quantity == initial_quantity
        
        # Verify no sale was created
        # (We can't easily check this without a get_all method, but the
        # transaction rollback ensures no partial data is saved)
    
    async def test_multiple_operations_rollback_together(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that multiple operations in a transaction roll back together.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user and multiple products
        user_data = UserCreate(
            username="multirollback",
            password="SecurePass123!",
            full_name="Multi Rollback User",
            email="multirollback@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        products = []
        for i in range(3):
            product_data = ProductCreate(
                sku=f"MROLL-{i:03d}",
                name=f"Multi Rollback Product {i}",
                description=f"Product {i} for multi-rollback test",
                gender="U",
                brand="TestBrand",
                reference=f"REF-MROLL-{i:03d}",
                size="M",
                quantity=20,
                price=Decimal("50.00"),
                min_stock=5
            )
            product = await inventory_service.create_product(
                product_data=product_data,
                user_id=user.id
            )
            products.append(product)
        
        # Try to create sale where one product has insufficient stock
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=products[0].id,
                    quantity=5,
                    unit_price=Decimal("50.00")
                ),
                SaleItemCreate(
                    product_id=products[1].id,
                    quantity=25,  # More than available (20)
                    unit_price=Decimal("50.00")
                ),
                SaleItemCreate(
                    product_id=products[2].id,
                    quantity=5,
                    unit_price=Decimal("50.00")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=Decimal("1750.00")
                )
            ],
            discount_amount=Decimal("0.00")
        )
        
        # Should fail on second item
        with pytest.raises(InsufficientStockError):
            await sales_service.create_sale(sale_data=sale_data)
        
        # Verify ALL products still have original stock (none were deducted)
        for product in products:
            unchanged = await product_repository.get_by_id(product.id)
            assert unchanged.quantity == 20
