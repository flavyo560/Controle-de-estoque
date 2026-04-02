"""Sale repository with transaction support for complex operations."""

from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date

from src.domain.sale import Sale, SaleItem, Payment, SaleCreate
from src.repositories.base import BaseRepository
from src.infrastructure.database import DatabaseClient
from src.exceptions import OptimisticLockError


class SaleRepository(BaseRepository[Sale]):
    """Repository for sale data access with transaction support."""
    
    def __init__(self, db_client: DatabaseClient):
        """
        Initialize sale repository.
        
        Args:
            db_client: Database client for connection pooling
        """
        super().__init__(db_client, "sales")
    
    async def create(self, **kwargs) -> Sale:
        """Not implemented - use create_sale instead."""
        raise NotImplementedError("Use create_sale method instead")
    
    async def create_sale(
        self,
        customer_id: Optional[int],
        user_id: int,
        total_amount: Decimal,
        discount_amount: Decimal,
        final_amount: Decimal,
        items: List[Dict[str, Any]],
        payments: List[Dict[str, Any]]
    ) -> Sale:
        """
        Create a sale with items and payments in a transaction.
        
        Args:
            customer_id: Customer ID (optional)
            user_id: User ID who created the sale
            total_amount: Total amount before discount
            discount_amount: Discount amount
            final_amount: Final amount after discount
            items: List of sale items
            payments: List of payments
            
        Returns:
            Created sale with items and payments
        """
        async with self.db.transaction():
            # Create sale
            sale_query = """
                INSERT INTO sales (
                    customer_id, user_id, total_amount, discount_amount,
                    final_amount, status, version
                )
                VALUES ($1, $2, $3, $4, $5, 'completed', 1)
                RETURNING id, customer_id, user_id, total_amount, discount_amount,
                          final_amount, status, cancelled_at, cancellation_reason,
                          cancelled_by, version, created_at, updated_at
            """
            sale_row = await self.db.fetch_one(
                sale_query, customer_id, user_id, total_amount,
                discount_amount, final_amount
            )
            sale = Sale(**sale_row)
            
            # Create sale items
            sale_items = []
            for item in items:
                item_query = """
                    INSERT INTO sale_items (
                        sale_id, product_id, product_snapshot, quantity,
                        unit_price, subtotal
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id, sale_id, product_id, product_snapshot, quantity,
                              unit_price, subtotal, created_at
                """
                item_row = await self.db.fetch_one(
                    item_query,
                    sale.id,
                    item['product_id'],
                    item['product_snapshot'],
                    item['quantity'],
                    item['unit_price'],
                    item['subtotal']
                )
                sale_items.append(SaleItem(**item_row))
            
            # Create payments
            sale_payments = []
            for payment in payments:
                payment_query = """
                    INSERT INTO payments (sale_id, payment_method, amount)
                    VALUES ($1, $2, $3)
                    RETURNING id, sale_id, payment_method, amount, created_at
                """
                payment_row = await self.db.fetch_one(
                    payment_query,
                    sale.id,
                    payment['payment_method'],
                    payment['amount']
                )
                sale_payments.append(Payment(**payment_row))
            
            # Attach items and payments to sale
            sale.items = sale_items
            sale.payments = sale_payments
            
            return sale

    
    async def get_by_id(self, id: int) -> Optional[Sale]:
        """
        Get sale by ID with items and payments.
        
        Args:
            id: Sale ID
            
        Returns:
            Sale if found, None otherwise
        """
        # Get sale
        sale_query = """
            SELECT id, customer_id, user_id, total_amount, discount_amount,
                   final_amount, status, cancelled_at, cancellation_reason,
                   cancelled_by, version, created_at, updated_at
            FROM sales
            WHERE id = $1
        """
        sale_row = await self.db.fetch_one(sale_query, id)
        if not sale_row:
            return None
        
        sale = Sale(**sale_row)
        
        # Get sale items
        items_query = """
            SELECT id, sale_id, product_id, product_snapshot, quantity,
                   unit_price, subtotal, created_at
            FROM sale_items
            WHERE sale_id = $1
            ORDER BY id
        """
        item_rows = await self.db.fetch_all(items_query, id)
        sale.items = [SaleItem(**row) for row in item_rows]
        
        # Get payments
        payments_query = """
            SELECT id, sale_id, payment_method, amount, created_at
            FROM payments
            WHERE sale_id = $1
            ORDER BY id
        """
        payment_rows = await self.db.fetch_all(payments_query, id)
        sale.payments = [Payment(**row) for row in payment_rows]
        
        return sale
    
    async def update(self, id: int, **kwargs) -> Optional[Sale]:
        """Not implemented - sales are immutable after creation."""
        raise NotImplementedError("Sales cannot be updated, only cancelled")
    
    async def delete(self, id: int) -> bool:
        """Not implemented - use cancel_sale instead."""
        raise NotImplementedError("Use cancel_sale method instead")
    
    async def cancel_sale(
        self,
        sale_id: int,
        cancelled_by: int,
        cancellation_reason: str,
        version: int
    ) -> Optional[Sale]:
        """
        Cancel a sale with optimistic locking.
        
        Args:
            sale_id: Sale ID
            cancelled_by: User ID who cancelled the sale
            cancellation_reason: Reason for cancellation
            version: Current version for optimistic locking
            
        Returns:
            Cancelled sale if found and version matches, None otherwise
            
        Raises:
            OptimisticLockError: If version conflict detected
        """
        query = """
            UPDATE sales
            SET status = 'cancelled',
                cancelled_at = NOW(),
                cancellation_reason = $2,
                cancelled_by = $3,
                version = $4,
                updated_at = NOW()
            WHERE id = $1 AND version = $5 AND status = 'completed'
            RETURNING id, customer_id, user_id, total_amount, discount_amount,
                      final_amount, status, cancelled_at, cancellation_reason,
                      cancelled_by, version, created_at, updated_at
        """
        
        row = await self.db.fetch_one(
            query, sale_id, cancellation_reason, cancelled_by,
            version + 1, version
        )
        
        if not row:
            # Check if sale exists and get current version
            existing = await self.get_by_id(sale_id)
            if existing and existing.version != version:
                raise OptimisticLockError(
                    f"Version conflict: expected {version}, found {existing.version}"
                )
            return None
        
        # Get full sale with items and payments
        return await self.get_by_id(sale_id)
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[Sale]:
        """
        List all sales with optional filtering and ordering.
        
        Note: This does not load items and payments. Use get_by_id for full details.
        
        Args:
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            
        Returns:
            List of sales (without items and payments)
        """
        where_clause, params = self._build_where_clause_sales(filters)
        order_clause = self._build_order_clause(order_by, order_desc)
        
        query = f"""
            SELECT id, customer_id, user_id, total_amount, discount_amount,
                   final_amount, status, cancelled_at, cancellation_reason,
                   cancelled_by, version, created_at, updated_at
            FROM sales
            {where_clause}
            {order_clause}
        """
        
        rows = await self.db.fetch_all(query, *params)
        return [Sale(**row) for row in rows]
    
    async def _list_with_pagination(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[Sale]:
        """
        List sales with pagination.
        
        Note: This does not load items and payments. Use get_by_id for full details.
        
        Args:
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of sales (without items and payments)
        """
        where_clause, params = self._build_where_clause_sales(filters)
        order_clause = self._build_order_clause(order_by, order_desc)
        
        # Add limit and offset to params
        params.extend([limit, offset])
        param_count = len(params)
        
        query = f"""
            SELECT id, customer_id, user_id, total_amount, discount_amount,
                   final_amount, status, cancelled_at, cancellation_reason,
                   cancelled_by, version, created_at, updated_at
            FROM sales
            {where_clause}
            {order_clause}
            LIMIT ${param_count - 1} OFFSET ${param_count}
        """
        
        rows = await self.db.fetch_all(query, *params)
        return [Sale(**row) for row in rows]
    
    async def get_sales_by_date_range(
        self,
        start_date: date,
        end_date: date,
        status: Optional[str] = None
    ) -> List[Sale]:
        """
        Get sales within a date range for reporting.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            status: Optional status filter (completed, cancelled)
            
        Returns:
            List of sales (without items and payments)
        """
        if status:
            query = """
                SELECT id, customer_id, user_id, total_amount, discount_amount,
                       final_amount, status, cancelled_at, cancellation_reason,
                       cancelled_by, version, created_at, updated_at
                FROM sales
                WHERE DATE(created_at) >= $1
                  AND DATE(created_at) <= $2
                  AND status = $3
                ORDER BY created_at DESC
            """
            rows = await self.db.fetch_all(query, start_date, end_date, status)
        else:
            query = """
                SELECT id, customer_id, user_id, total_amount, discount_amount,
                       final_amount, status, cancelled_at, cancellation_reason,
                       cancelled_by, version, created_at, updated_at
                FROM sales
                WHERE DATE(created_at) >= $1
                  AND DATE(created_at) <= $2
                ORDER BY created_at DESC
            """
            rows = await self.db.fetch_all(query, start_date, end_date)
        
        return [Sale(**row) for row in rows]
    
    def _build_where_clause_sales(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Any]]:
        """
        Build WHERE clause from filters dictionary for sales.
        
        Sales table doesn't have deleted_at column.
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            Tuple of (where_clause, params) for parameterized query
        """
        if not filters:
            return "", []
        
        conditions = []
        params = []
        param_index = 1
        
        for field, value in filters.items():
            if value is None:
                conditions.append(f"{field} IS NULL")
            else:
                conditions.append(f"{field} = ${param_index}")
                params.append(value)
                param_index += 1
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        return where_clause, params

    async def exists_by_id(self, id: int) -> bool:
        """
        Check if sale exists by ID using EXISTS (optimized).
        
        Args:
            id: Sale ID
            
        Returns:
            True if sale exists, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM sales
                WHERE id = $1
            )
        """
        result = await self.db.fetch_val(query, id)
        return result or False
    
    async def get_sales_summary_by_date_range(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Get aggregated sales summary for date range (optimized with single query).
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Dictionary with total_sales, total_revenue, avg_sale_value
        """
        query = """
            SELECT 
                COUNT(*) as total_sales,
                COALESCE(SUM(final_amount), 0) as total_revenue,
                COALESCE(AVG(final_amount), 0) as avg_sale_value
            FROM sales
            WHERE DATE(created_at) >= $1
              AND DATE(created_at) <= $2
              AND status = 'completed'
        """
        result = await self.db.fetch_one(query, start_date, end_date)
        return result or {"total_sales": 0, "total_revenue": 0, "avg_sale_value": 0}
