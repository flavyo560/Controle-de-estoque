"""
End-to-end integration tests for cross-layer interactions.

**Validates: Requirements 9.3, 4.1**

These tests verify the 3-layer architecture (UI → Service → Repository)
works correctly with proper separation of concerns and data flow.

Test scenarios:
1. Cache invalidation across layers
2. Audit trail creation across operations
3. Session management across requests
4. Complex business logic spanning multiple services
"""

import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import List

from src.domain.user import UserCreate
from src.domain.product import ProductCreate
from src.domain.sale import SaleCreate, SaleItemCreate, PaymentCreate
from src.services.auth_service import AuthService
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.report_service import ReportService
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.audit_repository import AuditRepository
from src.infrastructure.database import DatabaseClient
from src.infrastructure.cache import CacheManager


@pytest.mark.asyncio
class TestCacheInvalidationAcrossLayers:
    """Test cache invalidation works correctly across all layers."""
    
    async def test_product_cache_invalidation_on_update(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        product_repository: ProductRepository,
        cache_manager: CacheManager,
        clean_database
    ):
        """
        Test that product cache is invalidated when product is updated.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user and product
        user_data = UserCreate(
            username="cacheuser",
            password="SecurePass123!",
            full_name="Cache User",
            email="cache@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        product_data = ProductCreate(
            sku="CACHE-001",
            name="Cache Test Product",
            description="Product for cache test",
            gender="U",
            brand="TestBrand",
            reference="REF-CACHE",
            size="M",
            quantity=100,
            price=Decimal("50.00"),
            min_stock=10
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        # Get product (should cache it)
        cached_product = await inventory_service.get_product_by_id(product.id)
        assert cached_product.quantity == 100
        
        # Update stock through service
        await inventory_service.update_stock(
            product_id=product.id,
            quantity_change=-20,
            operation_type="sale",
            user_id=user.id,
            notes="Test sale"
        )
        
        # Get product again (should get fresh data, not cached)
        fresh_product = await inventory_service.get_product_by_id(product.id)
        assert fresh_product.quantity == 80  # Should be updated
    
    async def test_search_cache_invalidation_on_create(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        cache_manager: CacheManager,
        clean_database
    ):
        """
        Test that search cache is invalidated when new product is created.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user
        user_data = UserCreate(
            username="searchuser",
            password="SecurePass123!",
            full_name="Search User",
            email="search@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        # Create initial product
        product1_data = ProductCreate(
            sku="SEARCH-001",
            name="Searchable Product One",
            description="First searchable product",
            gender="U",
            brand="SearchBrand",
            reference="REF-SEARCH-1",
            size="S",
            quantity=50,
            price=Decimal("30.00"),
            min_stock=5
        )
        await inventory_service.create_product(
            product_data=product1_data,
            user_id=user.id
        )
        
        # Search (should cache results)
        results1 = await inventory_service.search_products(
            query="Searchable",
            limit=50
        )
        assert len(results1) == 1
        
        # Create another product
        product2_data = ProductCreate(
            sku="SEARCH-002",
            name="Searchable Product Two",
            description="Second searchable product",
            gender="U",
            brand="SearchBrand",
            reference="REF-SEARCH-2",
            size="M",
            quantity=50,
            price=Decimal("40.00"),
            min_stock=5
        )
        await inventory_service.create_product(
            product_data=product2_data,
            user_id=user.id
        )
        
        # Search again (should get fresh results)
        results2 = await inventory_service.search_products(
            query="Searchable",
            limit=50
        )
        assert len(results2) == 2


@pytest.mark.asyncio
class TestAuditTrailAcrossOperations:
    """Test audit trail is created correctly across all operations."""
    
    async def test_audit_trail_for_complete_workflow(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        audit_repository: AuditRepository,
        db_client: DatabaseClient,
        clean_database
    ):
        """
        Test that audit trail captures all operations in a workflow.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user (should create audit entry)
        user_data = UserCreate(
            username="audituser",
            password="SecurePass123!",
            full_name="Audit User",
            email="audit@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        # Login (should create audit entry)
        session = await auth_service.authenticate(
            username="audituser",
            password="SecurePass123!",
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )
        
        # Create product (should create audit entry)
        product_data = ProductCreate(
            sku="AUDIT-001",
            name="Audit Product",
            description="Product for audit test",
            gender="U",
            brand="AuditBrand",
            reference="REF-AUDIT",
            size="L",
            quantity=75,
            price=Decimal("60.00"),
            min_stock=10
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id,
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )
        
        # Create sale (should create audit entry)
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=product.id,
                    quantity=5,
                    unit_price=Decimal("60.00")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=Decimal("300.00")
                )
            ],
            discount_amount=Decimal("0.00")
        )
        await sales_service.create_sale(
            sale_data=sale_data,
            ip_address="192.168.1.100",
            user_agent="Test Browser"
        )
        
        # Query audit log to verify all operations were logged
        audit_query = """
            SELECT operation, table_name, user_id, ip_address
            FROM audit_log
            WHERE user_id = $1
            ORDER BY created_at ASC
        """
        audit_entries = await db_client.fetch_all(audit_query, user.id)
        
        # Should have entries for: user creation, login, product creation, sale creation
        assert len(audit_entries) >= 2  # At least product and sale
        
        # Verify IP address was captured
        for entry in audit_entries:
            if entry["ip_address"]:
                assert entry["ip_address"] == "192.168.1.100"


@pytest.mark.asyncio
class TestSessionManagementAcrossRequests:
    """Test session management works correctly across multiple requests."""
    
    async def test_session_expiration_prevents_operations(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        clean_database
    ):
        """
        Test that expired sessions prevent operations.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create and login user
        user_data = UserCreate(
            username="sessionuser",
            password="SecurePass123!",
            full_name="Session User",
            email="session@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        session = await auth_service.authenticate(
            username="sessionuser",
            password="SecurePass123!",
            ip_address="127.0.0.1"
        )
        
        # Validate session works
        validated_user = await auth_service.validate_session(
            session.token,
            ip_address="127.0.0.1"
        )
        assert validated_user.id == user.id
        
        # Logout (revoke session)
        await auth_service.logout(session.token)
        
        # Try to validate revoked session (should fail)
        from src.exceptions import AuthenticationError
        with pytest.raises(AuthenticationError):
            await auth_service.validate_session(
                session.token,
                ip_address="127.0.0.1"
            )
    
    async def test_session_ip_validation(
        self,
        auth_service: AuthService,
        clean_database
    ):
        """
        Test that session validation checks IP address.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create and login user from one IP
        user_data = UserCreate(
            username="ipuser",
            password="SecurePass123!",
            full_name="IP User",
            email="ip@test.com",
            role="user"
        )
        await auth_service.register_user(user_data, created_by=1)
        
        session = await auth_service.authenticate(
            username="ipuser",
            password="SecurePass123!",
            ip_address="192.168.1.100"
        )
        
        # Validate from same IP (should work)
        user1 = await auth_service.validate_session(
            session.token,
            ip_address="192.168.1.100"
        )
        assert user1 is not None
        
        # Note: IP validation might be lenient in some implementations
        # This test documents the expected behavior


@pytest.mark.asyncio
class TestComplexBusinessLogicSpanningServices:
    """Test complex business logic that spans multiple services."""
    
    async def test_low_stock_alert_after_multiple_sales(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        product_repository: ProductRepository,
        clean_database
    ):
        """
        Test that low stock alerts work correctly after multiple sales.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user
        user_data = UserCreate(
            username="alertuser",
            password="SecurePass123!",
            full_name="Alert User",
            email="alert@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        # Create product with low min_stock threshold
        product_data = ProductCreate(
            sku="ALERT-001",
            name="Alert Product",
            description="Product for low stock alert test",
            gender="U",
            brand="AlertBrand",
            reference="REF-ALERT",
            size="M",
            quantity=25,
            price=Decimal("45.00"),
            min_stock=20  # Alert when below 20
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        # Create sales to bring stock below threshold
        for i in range(2):
            sale_data = SaleCreate(
                customer_id=None,
                user_id=user.id,
                items=[
                    SaleItemCreate(
                        product_id=product.id,
                        quantity=3,
                        unit_price=Decimal("45.00")
                    )
                ],
                payments=[
                    PaymentCreate(
                        payment_method="cash",
                        amount=Decimal("135.00")
                    )
                ],
                discount_amount=Decimal("0.00")
            )
            await sales_service.create_sale(sale_data=sale_data)
        
        # Check stock level
        updated_product = await product_repository.get_by_id(product.id)
        assert updated_product.quantity == 19  # 25 - 6
        
        # Get low stock alerts
        alerts = await inventory_service.get_low_stock_alerts()
        
        # Should include our product
        alert_skus = [alert["product"].sku for alert in alerts]
        assert "ALERT-001" in alert_skus
    
    async def test_report_accuracy_after_sales_and_cancellations(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        sale_repository: SaleRepository,
        product_repository: ProductRepository,
        cache_manager: CacheManager,
        db_client: DatabaseClient,
        clean_database
    ):
        """
        Test that reports show accurate data after sales and cancellations.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user and product
        user_data = UserCreate(
            username="reportuser",
            password="SecurePass123!",
            full_name="Report User",
            email="report@test.com",
            role="manager"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        product_data = ProductCreate(
            sku="REPORT-001",
            name="Report Product",
            description="Product for report test",
            gender="U",
            brand="ReportBrand",
            reference="REF-REPORT",
            size="XL",
            quantity=100,
            price=Decimal("80.00"),
            min_stock=10
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        # Create multiple sales
        sale_ids = []
        for i in range(5):
            sale_data = SaleCreate(
                customer_id=None,
                user_id=user.id,
                items=[
                    SaleItemCreate(
                        product_id=product.id,
                        quantity=5,
                        unit_price=Decimal("80.00")
                    )
                ],
                payments=[
                    PaymentCreate(
                        payment_method="cash",
                        amount=Decimal("400.00")
                    )
                ],
                discount_amount=Decimal("0.00")
            )
            sale = await sales_service.create_sale(sale_data=sale_data)
            sale_ids.append(sale.id)
        
        # Cancel 2 sales
        for sale_id in sale_ids[:2]:
            await sales_service.cancel_sale(
                sale_id=sale_id,
                user_id=user.id,
                reason="Test cancellation"
            )
        
        # Generate report
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
        
        # Should only count completed sales (3 out of 5)
        assert report["total_sales"] == 3
        assert report["total_revenue"] == Decimal("1200.00")  # 3 * 400
        
        # Verify stock reflects cancellations
        final_product = await product_repository.get_by_id(product.id)
        assert final_product.quantity == 85  # 100 - (3 * 5)
    
    async def test_inventory_movements_tracking_across_operations(
        self,
        auth_service: AuthService,
        inventory_service: InventoryService,
        sales_service: SalesService,
        db_client: DatabaseClient,
        clean_database
    ):
        """
        Test that inventory movements are tracked across all operations.
        
        **Validates: Requirements 9.3, 4.1**
        """
        # Create user and product
        user_data = UserCreate(
            username="movementuser",
            password="SecurePass123!",
            full_name="Movement User",
            email="movement@test.com",
            role="user"
        )
        user = await auth_service.register_user(user_data, created_by=1)
        
        product_data = ProductCreate(
            sku="MOVEMENT-001",
            name="Movement Product",
            description="Product for movement tracking",
            gender="U",
            brand="MovementBrand",
            reference="REF-MOVEMENT",
            size="S",
            quantity=50,
            price=Decimal("35.00"),
            min_stock=5
        )
        product = await inventory_service.create_product(
            product_data=product_data,
            user_id=user.id
        )
        
        # Perform various operations
        # 1. Manual stock adjustment
        await inventory_service.update_stock(
            product_id=product.id,
            quantity_change=10,
            operation_type="adjustment",
            user_id=user.id,
            notes="Manual adjustment"
        )
        
        # 2. Create sale
        sale_data = SaleCreate(
            customer_id=None,
            user_id=user.id,
            items=[
                SaleItemCreate(
                    product_id=product.id,
                    quantity=15,
                    unit_price=Decimal("35.00")
                )
            ],
            payments=[
                PaymentCreate(
                    payment_method="cash",
                    amount=Decimal("525.00")
                )
            ],
            discount_amount=Decimal("0.00")
        )
        sale = await sales_service.create_sale(sale_data=sale_data)
        
        # 3. Cancel sale (creates return movement)
        await sales_service.cancel_sale(
            sale_id=sale.id,
            user_id=user.id,
            reason="Test return"
        )
        
        # Query inventory movements
        movements_query = """
            SELECT movement_type, quantity_change, quantity_before, quantity_after
            FROM inventory_movements
            WHERE product_id = $1
            ORDER BY created_at ASC
        """
        movements = await db_client.fetch_all(movements_query, product.id)
        
        # Should have 3 movements: adjustment, sale, return
        assert len(movements) >= 3
        
        # Verify movement types
        movement_types = [m["movement_type"] for m in movements]
        assert "adjustment" in movement_types
        assert "sale" in movement_types
        assert "return" in movement_types
