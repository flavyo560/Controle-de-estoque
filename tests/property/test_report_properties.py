"""Property-based tests for reporting operations.

**Validates: Requirements 20.1**

Tests universal properties of reporting system including
report sum consistency and data integrity.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from datetime import date, timedelta
from typing import List

from src.domain.product import ProductCreate
from src.domain.sale import SaleCreate, SaleItemCreate, PaymentCreate
from src.repositories.product_repository import ProductRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.audit_repository import AuditRepository
from src.services.inventory_service import InventoryService
from src.services.sales_service import SalesService
from src.services.report_service import ReportService


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
        quantity=draw(st.integers(min_value=50, max_value=200)),  # Ensure enough stock for multiple sales
        price=Decimal(str(draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False, allow_infinity=False)))).quantize(Decimal('0.01')),
        barcode=draw(st.one_of(st.none(), st.text(min_size=8, max_size=13, alphabet=st.characters(whitelist_categories=('Nd',))))),
        min_stock=draw(st.integers(min_value=0, max_value=10))
    )


class TestReportProperties:
    """Property-based tests for reporting operations."""
    
    @pytest.mark.asyncio
    @given(
        num_products=st.integers(min_value=1, max_value=5),
        num_sales=st.integers(min_value=1, max_value=10),
        seed=st.integers(min_value=0, max_value=1000000)
    )
    @settings(max_examples=30, deadline=10000)
    async def test_report_sum_consistency(
        self,
        num_products: int,
        num_sales: int,
        seed: int,
        db_client,
        product_repository,
        sale_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 17: Report sum consistency.
        
        **Validates: Requirements 20.1**
        
        Test that sum of individual sales equals total revenue in report.
        
        This verifies that:
        1. The report's total_revenue matches the sum of all sale final_amounts
        2. The sum of sales_by_period revenues equals total_revenue
        3. Data integrity is maintained in reporting calculations
        4. No sales are lost or double-counted in aggregations
        """
        # Create services
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        sales_service = SalesService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            audit_repo=audit_repository,
            db_client=db_client
        )
        
        report_service = ReportService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            cache=cache_manager,
            db=db_client
        )
        
        # Create products
        products = []
        for i in range(num_products):
            # Use seed to generate deterministic but varied products
            product_data = ProductCreate(
                sku=f"SKU{seed}{i:03d}",
                name=f"Product {seed} {i}",
                description=f"Test product {i}",
                gender=['M', 'F', 'U'][i % 3],
                brand=f"Brand{i % 3}",
                reference=f"REF{seed}{i}",
                size=['P', 'M', 'G'][i % 3],
                quantity=100,  # Enough for all sales
                price=Decimal(str(10.00 + (i * 5.5))).quantize(Decimal('0.01')),
                barcode=None,
                min_stock=5
            )
            product = await inventory_service.create_product(
                product_data=product_data,
                user_id=1
            )
            products.append(product)
        
        # Track expected total revenue
        expected_total_revenue = Decimal("0.00")
        created_sales = []
        
        # Create sales
        for sale_idx in range(num_sales):
            # Select a random product (deterministic based on seed and sale_idx)
            product_idx = (seed + sale_idx) % len(products)
            product = products[product_idx]
            
            # Determine quantity (1-5 items)
            quantity = 1 + ((seed + sale_idx) % 5)
            
            # Ensure we don't exceed stock
            if product.quantity < quantity:
                quantity = max(1, product.quantity)
            
            # Create sale item
            sale_item = SaleItemCreate(
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price
            )
            
            # Calculate amounts
            total_amount = Decimal(str(quantity)) * product.price
            discount_amount = Decimal("0.00")
            final_amount = total_amount - discount_amount
            
            # Create sale
            sale_data = SaleCreate(
                customer_id=None,
                user_id=1,
                items=[sale_item],
                payments=[
                    PaymentCreate(
                        payment_method="cash",
                        amount=final_amount
                    )
                ],
                discount_amount=discount_amount
            )
            
            try:
                sale = await sales_service.create_sale(sale_data)
                created_sales.append(sale)
                expected_total_revenue += final_amount
                
                # Update product quantity for next iteration
                updated_product = await product_repository.get_by_id(product.id)
                products[product_idx] = updated_product
            except Exception as e:
                # If sale fails (e.g., insufficient stock), skip it
                # This is acceptable for the property test
                pass
        
        # Assume we created at least one sale
        assume(len(created_sales) > 0)
        
        # Get report for all sales (use a wide date range)
        start_date = date.today() - timedelta(days=1)
        end_date = date.today() + timedelta(days=1)
        
        report = await report_service.get_sales_report(
            start_date=start_date,
            end_date=end_date,
            group_by="day"
        )
        
        # Property 1: Total revenue in report equals sum of individual sales
        reported_total_revenue = Decimal(str(report["total_revenue"]))
        assert reported_total_revenue == expected_total_revenue, \
            f"Report total revenue mismatch. " \
            f"Expected: {expected_total_revenue}, " \
            f"Reported: {reported_total_revenue}, " \
            f"Difference: {abs(reported_total_revenue - expected_total_revenue)}"
        
        # Property 2: Sum of period revenues equals total revenue
        period_sum = sum(
            Decimal(str(period["revenue"]))
            for period in report["sales_by_period"]
        )
        assert period_sum == reported_total_revenue, \
            f"Sum of period revenues doesn't match total revenue. " \
            f"Period sum: {period_sum}, " \
            f"Total revenue: {reported_total_revenue}, " \
            f"Difference: {abs(period_sum - reported_total_revenue)}"
        
        # Property 3: Number of sales in report matches created sales
        assert report["total_sales"] == len(created_sales), \
            f"Number of sales mismatch. " \
            f"Expected: {len(created_sales)}, " \
            f"Reported: {report['total_sales']}"
        
        # Property 4: Sum of period sales counts equals total sales
        period_sales_count = sum(
            period["sales_count"]
            for period in report["sales_by_period"]
        )
        assert period_sales_count == report["total_sales"], \
            f"Sum of period sales counts doesn't match total sales. " \
            f"Period sum: {period_sales_count}, " \
            f"Total sales: {report['total_sales']}"
        
        # Property 5: Verify against database directly
        db_query = """
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(final_amount), 0) as total
            FROM sales
            WHERE created_at::date >= $1 
                AND created_at::date <= $2
                AND status = 'completed'
                AND deleted_at IS NULL
        """
        db_result = await db_client.fetch_one(db_query, start_date, end_date)
        db_total = Decimal(str(db_result["total"]))
        db_count = db_result["count"]
        
        assert db_total == expected_total_revenue, \
            f"Database total doesn't match expected. " \
            f"Expected: {expected_total_revenue}, " \
            f"Database: {db_total}"
        
        assert db_count == len(created_sales), \
            f"Database count doesn't match created sales. " \
            f"Expected: {len(created_sales)}, " \
            f"Database: {db_count}"
    
    @pytest.mark.asyncio
    @given(
        num_products=st.integers(min_value=2, max_value=5),
        num_sales=st.integers(min_value=5, max_value=15),
        seed=st.integers(min_value=0, max_value=1000000)
    )
    @settings(max_examples=20, deadline=10000)
    async def test_report_sum_consistency_with_discounts(
        self,
        num_products: int,
        num_sales: int,
        seed: int,
        db_client,
        product_repository,
        sale_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 17: Report sum consistency with discounts.
        
        **Validates: Requirements 20.1**
        
        Test that sum of individual sales equals total revenue when discounts
        are applied. This verifies that final_amount (after discount) is used
        in calculations, not total_amount.
        """
        # Create services
        inventory_service = InventoryService(
            product_repo=product_repository,
            audit_repo=audit_repository,
            cache=cache_manager,
            db_client=db_client
        )
        
        sales_service = SalesService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            audit_repo=audit_repository,
            db_client=db_client
        )
        
        report_service = ReportService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            cache=cache_manager,
            db=db_client
        )
        
        # Create products
        products = []
        for i in range(num_products):
            product_data = ProductCreate(
                sku=f"DSKU{seed}{i:03d}",
                name=f"Discount Product {seed} {i}",
                description=f"Test product with discount {i}",
                gender=['M', 'F', 'U'][i % 3],
                brand=f"Brand{i % 3}",
                reference=f"DREF{seed}{i}",
                size=['P', 'M', 'G'][i % 3],
                quantity=150,
                price=Decimal(str(50.00 + (i * 10.0))).quantize(Decimal('0.01')),
                barcode=None,
                min_stock=5
            )
            product = await inventory_service.create_product(
                product_data=product_data,
                user_id=1
            )
            products.append(product)
        
        # Track expected total revenue (final amounts after discount)
        expected_total_revenue = Decimal("0.00")
        created_sales = []
        
        # Create sales with varying discounts
        for sale_idx in range(num_sales):
            product_idx = (seed + sale_idx) % len(products)
            product = products[product_idx]
            
            quantity = 1 + ((seed + sale_idx) % 3)
            
            if product.quantity < quantity:
                quantity = max(1, product.quantity)
            
            sale_item = SaleItemCreate(
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price
            )
            
            # Calculate amounts with discount
            total_amount = Decimal(str(quantity)) * product.price
            
            # Apply discount (0%, 5%, 10%, or 15%)
            discount_percent = [0, 5, 10, 15][sale_idx % 4]
            discount_amount = (total_amount * Decimal(str(discount_percent)) / Decimal("100")).quantize(Decimal('0.01'))
            final_amount = total_amount - discount_amount
            
            sale_data = SaleCreate(
                customer_id=None,
                user_id=1,
                items=[sale_item],
                payments=[
                    PaymentCreate(
                        payment_method="cash",
                        amount=final_amount
                    )
                ],
                discount_amount=discount_amount
            )
            
            try:
                sale = await sales_service.create_sale(sale_data)
                created_sales.append(sale)
                expected_total_revenue += final_amount
                
                updated_product = await product_repository.get_by_id(product.id)
                products[product_idx] = updated_product
            except Exception:
                pass
        
        assume(len(created_sales) > 0)
        
        # Get report
        start_date = date.today() - timedelta(days=1)
        end_date = date.today() + timedelta(days=1)
        
        report = await report_service.get_sales_report(
            start_date=start_date,
            end_date=end_date,
            group_by="day"
        )
        
        # Property: Total revenue equals sum of final amounts (after discount)
        reported_total_revenue = Decimal(str(report["total_revenue"]))
        assert reported_total_revenue == expected_total_revenue, \
            f"Report total revenue with discounts mismatch. " \
            f"Expected: {expected_total_revenue}, " \
            f"Reported: {reported_total_revenue}, " \
            f"Difference: {abs(reported_total_revenue - expected_total_revenue)}"
        
        # Verify sum of periods equals total
        period_sum = sum(
            Decimal(str(period["revenue"]))
            for period in report["sales_by_period"]
        )
        assert period_sum == reported_total_revenue, \
            f"Sum of period revenues with discounts doesn't match total. " \
            f"Period sum: {period_sum}, " \
            f"Total: {reported_total_revenue}"
    
    @pytest.mark.asyncio
    @given(
        seed=st.integers(min_value=0, max_value=1000000)
    )
    @settings(max_examples=20, deadline=10000)
    async def test_report_sum_consistency_empty_date_range(
        self,
        seed: int,
        db_client,
        product_repository,
        sale_repository,
        audit_repository,
        cache_manager,
        clean_database
    ):
        """
        Property 17: Report sum consistency with empty results.
        
        **Validates: Requirements 20.1**
        
        Test that report correctly handles date ranges with no sales.
        Total revenue should be 0 and sum of periods should also be 0.
        """
        report_service = ReportService(
            sale_repo=sale_repository,
            product_repo=product_repository,
            cache=cache_manager,
            db=db_client
        )
        
        # Use a date range in the past where no sales exist
        start_date = date(2020, 1, 1)
        end_date = date(2020, 1, 31)
        
        report = await report_service.get_sales_report(
            start_date=start_date,
            end_date=end_date,
            group_by="day"
        )
        
        # Property: Empty report should have zero totals
        assert report["total_revenue"] == 0.00, \
            f"Empty report should have zero revenue, got {report['total_revenue']}"
        
        assert report["total_sales"] == 0, \
            f"Empty report should have zero sales, got {report['total_sales']}"
        
        assert len(report["sales_by_period"]) == 0, \
            f"Empty report should have no periods, got {len(report['sales_by_period'])}"
        
        # Sum of empty periods should be zero
        period_sum = sum(
            Decimal(str(period["revenue"]))
            for period in report["sales_by_period"]
        )
        assert period_sum == Decimal("0.00"), \
            f"Sum of empty periods should be zero, got {period_sum}"
