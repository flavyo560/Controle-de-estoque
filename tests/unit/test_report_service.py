"""
Unit tests for ReportService.

Tests cover:
- Sales report calculations and accuracy
- Inventory report calculations
- Revenue report with payment method breakdown
- Date range filtering
- Report caching
- Data aggregation accuracy
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from src.services.report_service import ReportService
from src.repositories.sale_repository import SaleRepository
from src.repositories.product_repository import ProductRepository
from src.infrastructure.cache import CacheManager
from src.infrastructure.database import DatabaseClient


@pytest.fixture
def mock_sale_repo():
    """Create mock sale repository."""
    return AsyncMock(spec=SaleRepository)


@pytest.fixture
def mock_product_repo():
    """Create mock product repository."""
    return AsyncMock(spec=ProductRepository)


@pytest.fixture
def mock_cache():
    """Create mock cache manager."""
    cache = AsyncMock(spec=CacheManager)
    cache.get.return_value = None  # Default: no cache hit
    return cache


@pytest.fixture
def mock_db():
    """Create mock database client."""
    return AsyncMock(spec=DatabaseClient)


@pytest.fixture
def report_service(mock_sale_repo, mock_product_repo, mock_cache, mock_db):
    """Create report service with mocked dependencies."""
    return ReportService(
        sale_repo=mock_sale_repo,
        product_repo=mock_product_repo,
        cache=mock_cache,
        db=mock_db
    )


class TestSalesReport:
    """Tests for sales report generation."""
    
    @pytest.mark.asyncio
    async def test_sales_report_basic_calculation(self, report_service, mock_db, mock_cache):
        """Test that sales report calculates totals correctly."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        # Mock database response for summary
        mock_db.fetch_one.return_value = {
            "total_sales": 10,
            "total_revenue": Decimal("1500.00"),
            "average_sale": Decimal("150.00")
        }
        
        # Mock database response for period grouping
        mock_db.fetch_all.return_value = [
            {
                "period": datetime(2024, 1, 1),
                "sales_count": 5,
                "revenue": Decimal("750.00")
            },
            {
                "period": datetime(2024, 1, 2),
                "sales_count": 5,
                "revenue": Decimal("750.00")
            }
        ]
        
        # Act
        result = await report_service.get_sales_report(start_date, end_date, "day")
        
        # Assert
        assert result["total_sales"] == 10
        assert result["total_revenue"] == 1500.00
        assert result["average_sale"] == 150.00
        assert len(result["sales_by_period"]) == 2
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"
        
    @pytest.mark.asyncio
    async def test_sales_report_date_range_filtering(self, report_service, mock_db, mock_cache):
        """Test that date range filtering works correctly."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_sales": 5,
            "total_revenue": Decimal("500.00"),
            "average_sale": Decimal("100.00")
        }
        mock_db.fetch_all.return_value = []
        
        # Act
        await report_service.get_sales_report(start_date, end_date, "day")
        
        # Assert - verify the query was called with correct date parameters
        calls = mock_db.fetch_one.call_args_list
        assert len(calls) == 1
        assert calls[0][0][1] == start_date
        assert calls[0][0][2] == end_date
        
    @pytest.mark.asyncio
    async def test_sales_report_grouping_by_day(self, report_service, mock_db, mock_cache):
        """Test sales report grouping by day."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 3)
        
        mock_db.fetch_one.return_value = {
            "total_sales": 3,
            "total_revenue": Decimal("300.00"),
            "average_sale": Decimal("100.00")
        }
        
        mock_db.fetch_all.return_value = [
            {"period": datetime(2024, 1, 1), "sales_count": 1, "revenue": Decimal("100.00")},
            {"period": datetime(2024, 1, 2), "sales_count": 1, "revenue": Decimal("100.00")},
            {"period": datetime(2024, 1, 3), "sales_count": 1, "revenue": Decimal("100.00")}
        ]
        
        # Act
        result = await report_service.get_sales_report(start_date, end_date, "day")
        
        # Assert
        assert result["group_by"] == "day"
        assert len(result["sales_by_period"]) == 3
        
    @pytest.mark.asyncio
    async def test_sales_report_grouping_by_week(self, report_service, mock_db, mock_cache):
        """Test sales report grouping by week."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_sales": 10,
            "total_revenue": Decimal("1000.00"),
            "average_sale": Decimal("100.00")
        }
        
        mock_db.fetch_all.return_value = [
            {"period": datetime(2024, 1, 1), "sales_count": 5, "revenue": Decimal("500.00")},
            {"period": datetime(2024, 1, 8), "sales_count": 5, "revenue": Decimal("500.00")}
        ]
        
        # Act
        result = await report_service.get_sales_report(start_date, end_date, "week")
        
        # Assert
        assert result["group_by"] == "week"
        assert len(result["sales_by_period"]) == 2
        
    @pytest.mark.asyncio
    async def test_sales_report_grouping_by_month(self, report_service, mock_db, mock_cache):
        """Test sales report grouping by month."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)
        
        mock_db.fetch_one.return_value = {
            "total_sales": 30,
            "total_revenue": Decimal("3000.00"),
            "average_sale": Decimal("100.00")
        }
        
        mock_db.fetch_all.return_value = [
            {"period": datetime(2024, 1, 1), "sales_count": 10, "revenue": Decimal("1000.00")},
            {"period": datetime(2024, 2, 1), "sales_count": 10, "revenue": Decimal("1000.00")},
            {"period": datetime(2024, 3, 1), "sales_count": 10, "revenue": Decimal("1000.00")}
        ]
        
        # Act
        result = await report_service.get_sales_report(start_date, end_date, "month")
        
        # Assert
        assert result["group_by"] == "month"
        assert len(result["sales_by_period"]) == 3
        
    @pytest.mark.asyncio
    async def test_sales_report_zero_sales(self, report_service, mock_db, mock_cache):
        """Test sales report with no sales in date range."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_sales": 0,
            "total_revenue": Decimal("0.00"),
            "average_sale": Decimal("0.00")
        }
        mock_db.fetch_all.return_value = []
        
        # Act
        result = await report_service.get_sales_report(start_date, end_date, "day")
        
        # Assert
        assert result["total_sales"] == 0
        assert result["total_revenue"] == 0.00
        assert result["average_sale"] == 0.00
        assert len(result["sales_by_period"]) == 0
        
    @pytest.mark.asyncio
    async def test_sales_report_uses_cache(self, report_service, mock_db, mock_cache):
        """Test that sales report uses cached data when available."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        cached_report = {
            "total_sales": 10,
            "total_revenue": 1500.00,
            "average_sale": 150.00,
            "sales_by_period": [],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "group_by": "day"
        }
        mock_cache.get.return_value = cached_report
        
        # Act
        result = await report_service.get_sales_report(start_date, end_date, "day")
        
        # Assert
        assert result == cached_report
        mock_db.fetch_one.assert_not_called()
        mock_db.fetch_all.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_sales_report_caches_result(self, report_service, mock_db, mock_cache):
        """Test that sales report caches the result."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_sales": 10,
            "total_revenue": Decimal("1500.00"),
            "average_sale": Decimal("150.00")
        }
        mock_db.fetch_all.return_value = []
        
        # Act
        await report_service.get_sales_report(start_date, end_date, "day")
        
        # Assert
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert "sales_report:2024-01-01:2024-01-31:day" in call_args[0][0]
        assert call_args[1]["ttl"] == 3600  # 1 hour


class TestInventoryReport:
    """Tests for inventory report generation."""
    
    @pytest.mark.asyncio
    async def test_inventory_report_basic_calculation(self, report_service, mock_db, mock_cache):
        """Test that inventory report calculates totals correctly."""
        # Arrange
        mock_db.fetch_one.return_value = {
            "total_products": 5,
            "total_stock_value": Decimal("5000.00"),
            "low_stock_count": 2
        }
        
        mock_db.fetch_all.return_value = [
            {
                "id": 1,
                "sku": "SKU001",
                "name": "Product 1",
                "quantity": 10,
                "min_stock": 5,
                "price": Decimal("100.00"),
                "stock_value": Decimal("1000.00")
            },
            {
                "id": 2,
                "sku": "SKU002",
                "name": "Product 2",
                "quantity": 3,
                "min_stock": 5,
                "price": Decimal("200.00"),
                "stock_value": Decimal("600.00")
            }
        ]
        
        # Act
        result = await report_service.get_inventory_report(include_movements=False)
        
        # Assert
        assert result["total_products"] == 5
        assert result["total_stock_value"] == 5000.00
        assert result["low_stock_count"] == 2
        assert len(result["products"]) == 2
        assert result["products"][0]["is_low_stock"] is False
        assert result["products"][1]["is_low_stock"] is True
        
    @pytest.mark.asyncio
    async def test_inventory_report_low_stock_detection(self, report_service, mock_db, mock_cache):
        """Test that low stock products are correctly identified."""
        # Arrange
        mock_db.fetch_one.return_value = {
            "total_products": 3,
            "total_stock_value": Decimal("1000.00"),
            "low_stock_count": 2
        }
        
        mock_db.fetch_all.return_value = [
            {"id": 1, "sku": "SKU001", "name": "Product 1", "quantity": 10, "min_stock": 5, "price": Decimal("50.00"), "stock_value": Decimal("500.00")},
            {"id": 2, "sku": "SKU002", "name": "Product 2", "quantity": 3, "min_stock": 5, "price": Decimal("50.00"), "stock_value": Decimal("150.00")},
            {"id": 3, "sku": "SKU003", "name": "Product 3", "quantity": 2, "min_stock": 10, "price": Decimal("50.00"), "stock_value": Decimal("100.00")}
        ]
        
        # Act
        result = await report_service.get_inventory_report(include_movements=False)
        
        # Assert
        assert result["low_stock_count"] == 2
        low_stock_products = [p for p in result["products"] if p["is_low_stock"]]
        assert len(low_stock_products) == 2
        assert low_stock_products[0]["sku"] == "SKU002"
        assert low_stock_products[1]["sku"] == "SKU003"
        
    @pytest.mark.asyncio
    async def test_inventory_report_with_movements(self, report_service, mock_db, mock_cache):
        """Test inventory report includes movements when requested."""
        # Arrange
        mock_db.fetch_one.return_value = {
            "total_products": 1,
            "total_stock_value": Decimal("1000.00"),
            "low_stock_count": 0
        }
        
        # First call returns products, second call returns movements
        mock_db.fetch_all.side_effect = [
            [{"id": 1, "sku": "SKU001", "name": "Product 1", "quantity": 10, "min_stock": 5, "price": Decimal("100.00"), "stock_value": Decimal("1000.00")}],
            [
                {
                    "id": 1,
                    "product_id": 1,
                    "sku": "SKU001",
                    "product_name": "Product 1",
                    "movement_type": "sale",
                    "quantity_change": -2,
                    "quantity_before": 12,
                    "quantity_after": 10,
                    "created_at": datetime(2024, 1, 15, 10, 30)
                }
            ]
        ]
        
        # Act
        result = await report_service.get_inventory_report(include_movements=True)
        
        # Assert
        assert "movements" in result
        assert len(result["movements"]) == 1
        assert result["movements"][0]["movement_type"] == "sale"
        assert result["movements"][0]["quantity_change"] == -2
        
    @pytest.mark.asyncio
    async def test_inventory_report_without_movements(self, report_service, mock_db, mock_cache):
        """Test inventory report excludes movements when not requested."""
        # Arrange
        mock_db.fetch_one.return_value = {
            "total_products": 1,
            "total_stock_value": Decimal("1000.00"),
            "low_stock_count": 0
        }
        
        mock_db.fetch_all.return_value = [
            {"id": 1, "sku": "SKU001", "name": "Product 1", "quantity": 10, "min_stock": 5, "price": Decimal("100.00"), "stock_value": Decimal("1000.00")}
        ]
        
        # Act
        result = await report_service.get_inventory_report(include_movements=False)
        
        # Assert
        assert "movements" not in result
        
    @pytest.mark.asyncio
    async def test_inventory_report_uses_cache(self, report_service, mock_db, mock_cache):
        """Test that inventory report uses cached data when available."""
        # Arrange
        cached_report = {
            "total_products": 5,
            "total_stock_value": 5000.00,
            "low_stock_count": 2,
            "products": []
        }
        mock_cache.get.return_value = cached_report
        
        # Act
        result = await report_service.get_inventory_report(include_movements=False)
        
        # Assert
        assert result == cached_report
        mock_db.fetch_one.assert_not_called()
        mock_db.fetch_all.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_inventory_report_caches_result(self, report_service, mock_db, mock_cache):
        """Test that inventory report caches the result."""
        # Arrange
        mock_db.fetch_one.return_value = {
            "total_products": 1,
            "total_stock_value": Decimal("1000.00"),
            "low_stock_count": 0
        }
        mock_db.fetch_all.return_value = []
        
        # Act
        await report_service.get_inventory_report(include_movements=False)
        
        # Assert
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert "inventory_report:" in call_args[0][0]
        assert call_args[1]["ttl"] == 300  # 5 minutes


class TestRevenueReport:
    """Tests for revenue report generation."""
    
    @pytest.mark.asyncio
    async def test_revenue_report_basic_calculation(self, report_service, mock_db, mock_cache):
        """Test that revenue report calculates totals correctly."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_revenue": Decimal("1000.00")
        }
        
        mock_db.fetch_all.return_value = [
            {
                "payment_method": "cash",
                "transaction_count": 5,
                "total_amount": Decimal("500.00")
            },
            {
                "payment_method": "credit_card",
                "transaction_count": 3,
                "total_amount": Decimal("300.00")
            },
            {
                "payment_method": "pix",
                "transaction_count": 2,
                "total_amount": Decimal("200.00")
            }
        ]
        
        # Act
        result = await report_service.get_revenue_report(start_date, end_date)
        
        # Assert
        assert result["total_revenue"] == 1000.00
        assert len(result["payment_methods"]) == 3
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"
        
    @pytest.mark.asyncio
    async def test_revenue_report_payment_method_breakdown(self, report_service, mock_db, mock_cache):
        """Test that payment method breakdown is calculated correctly."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_revenue": Decimal("1000.00")
        }
        
        mock_db.fetch_all.return_value = [
            {"payment_method": "cash", "transaction_count": 5, "total_amount": Decimal("600.00")},
            {"payment_method": "credit_card", "transaction_count": 3, "total_amount": Decimal("400.00")}
        ]
        
        # Act
        result = await report_service.get_revenue_report(start_date, end_date)
        
        # Assert
        assert result["payment_methods"][0]["method"] == "cash"
        assert result["payment_methods"][0]["total_amount"] == 600.00
        assert result["payment_methods"][0]["percentage"] == 60.0
        assert result["payment_methods"][1]["method"] == "credit_card"
        assert result["payment_methods"][1]["total_amount"] == 400.00
        assert result["payment_methods"][1]["percentage"] == 40.0
        
    @pytest.mark.asyncio
    async def test_revenue_report_zero_revenue(self, report_service, mock_db, mock_cache):
        """Test revenue report with no revenue."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_revenue": Decimal("0.00")
        }
        mock_db.fetch_all.return_value = []
        
        # Act
        result = await report_service.get_revenue_report(start_date, end_date)
        
        # Assert
        assert result["total_revenue"] == 0.00
        assert len(result["payment_methods"]) == 0
        
    @pytest.mark.asyncio
    async def test_revenue_report_percentage_calculation_with_zero_total(self, report_service, mock_db, mock_cache):
        """Test that percentage calculation handles zero total revenue."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_revenue": Decimal("0.00")
        }
        
        # This shouldn't happen in practice, but test defensive coding
        mock_db.fetch_all.return_value = [
            {"payment_method": "cash", "transaction_count": 0, "total_amount": Decimal("0.00")}
        ]
        
        # Act
        result = await report_service.get_revenue_report(start_date, end_date)
        
        # Assert
        assert result["payment_methods"][0]["percentage"] == 0.0
        
    @pytest.mark.asyncio
    async def test_revenue_report_uses_cache(self, report_service, mock_db, mock_cache):
        """Test that revenue report uses cached data when available."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        cached_report = {
            "total_revenue": 1000.00,
            "payment_methods": [],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        mock_cache.get.return_value = cached_report
        
        # Act
        result = await report_service.get_revenue_report(start_date, end_date)
        
        # Assert
        assert result == cached_report
        mock_db.fetch_one.assert_not_called()
        mock_db.fetch_all.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_revenue_report_caches_result(self, report_service, mock_db, mock_cache):
        """Test that revenue report caches the result."""
        # Arrange
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        mock_db.fetch_one.return_value = {
            "total_revenue": Decimal("1000.00")
        }
        mock_db.fetch_all.return_value = []
        
        # Act
        await report_service.get_revenue_report(start_date, end_date)
        
        # Assert
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args
        assert "revenue_report:2024-01-01:2024-01-31" in call_args[0][0]
        assert call_args[1]["ttl"] == 3600  # 1 hour


class TestCacheInvalidation:
    """Tests for report cache invalidation."""
    
    @pytest.mark.asyncio
    async def test_invalidate_report_cache(self, report_service, mock_cache):
        """Test that cache invalidation clears all report caches."""
        # Act
        await report_service.invalidate_report_cache()
        
        # Assert
        assert mock_cache.invalidate_pattern.call_count == 3
        calls = [call[0][0] for call in mock_cache.invalidate_pattern.call_args_list]
        assert "sales_report:*" in calls
        assert "inventory_report:*" in calls
        assert "revenue_report:*" in calls
