"""Unit tests for sales service."""

import pytest
from decimal import Decimal
from datetime import datetime

from src.services.sales_service import SalesService
from src.domain.sale import SaleCreate, SaleItemCreate, PaymentCreate
from src.domain.product import ProductCreate
from src.exceptions import (
    InsufficientStockError,
    NotFoundError,
    ValidationError
)


@pytest.mark.asyncio
class TestSalesService:
    """Test suite for SalesService."""
    
    async def test_create_sale_with_insufficient_stock(
        self,
        sales_service: SalesService,
        product_r