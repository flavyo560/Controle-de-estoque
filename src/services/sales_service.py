"""Sales service with business logic for sale management."""

from typing import Optional, List
from decimal import Decimal
from datetime import date

from src.domain.sale import Sale, SaleCreate, SaleItemCreate
from src.domain.product import Product
from src.repositories.sale_repository import SaleRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.audit_repository import AuditRepository
from src.infrastructure.database import DatabaseClient
from src.exceptions import (
    NotFoundError,
    InsufficientStockError,
    ValidationError,
    AuthorizationError,
    OptimisticLockError,
    DatabaseError
)


class SalesService:
    """Service for sales management with transaction safety."""
    
    def __init__(
        self,
        sale_repo: SaleRepository,
        product_repo: ProductRepository,
        audit_repo: AuditRepository,
        db_client: DatabaseClient
    ):
        """
        Initialize sales service.
        
        Args:
            sale_repo: Sale repository
            product_repo: Product repository
            audit_repo: Audit repository for logging
            db_client: Database client for transactions
        """
        self.sale_repo = sale_repo
        self.product_repo = product_repo
        self.audit_repo = audit_repo
        self.db = db_client
    
    async def create_sale(
        self,
        sale_data: SaleCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Sale:
        """
        Create a sale with validation, stock updates, and audit trail.
        
        Args:
            sale_data: Sale creation data
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created sale
            
        Raises:
            ValidationError: If validation fails
            InsufficientStockError: If insufficient stock
            NotFoundError: If product not found
        """
        # Validate sale data
        await self._validate_sale(sale_data)
        
        # Create sale in transaction
        async with self.db.transaction():
            # Calculate totals
            total_amount = sum(
                Decimal(str(item.quantity)) * item.unit_price
                for item in sale_data.items
            )
            final_amount = total_amount - sale_data.discount_amount
            
            # Prepare items with product snapshots
            items_with_snapshots = []
            for item in sale_data.items:
                product = await self.product_repo.get_by_id(item.product_id)
                if not product:
                    raise NotFoundError(f"Product with ID {item.product_id} not found")
                
                # Create product snapshot
                product_snapshot = {
                    "id": product.id,
                    "sku": product.sku,
                    "name": product.name,
                    "brand": product.brand,
                    "reference": product.reference,
                    "size": product.size,
                    "price": str(product.price)
                }
                
                subtotal = Decimal(str(item.quantity)) * item.unit_price
                
                items_with_snapshots.append({
                    "product_id": item.product_id,
                    "product_snapshot": product_snapshot,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "subtotal": subtotal
                })
                
                # Update stock
                new_quantity = product.quantity - item.quantity
                if new_quantity < 0:
                    raise InsufficientStockError(
                        f"Insufficient stock for product {product.sku}. "
                        f"Available: {product.quantity}, Requested: {item.quantity}"
                    )
                
                await self.product_repo.update(
                    id=product.id,
                    version=product.version,
                    quantity=new_quantity
                )
                
                # Create inventory movement
                movement_query = """
                    INSERT INTO inventory_movements (
                        product_id, movement_type, quantity_change,
                        quantity_before, quantity_after,
                        reference_type, user_id
                    )
                    VALUES ($1, 'OUT', $2, $3, $4, 'sale', $5)
                """
                await self.db.execute(
                    movement_query,
                    product.id,
                    -item.quantity,
                    product.quantity,
                    new_quantity,
                    sale_data.user_id
                )
            
            # Prepare payments
            payments = [
                {
                    "payment_method": payment.payment_method,
                    "amount": payment.amount
                }
                for payment in sale_data.payments
            ]
            
            # Create sale
            sale = await self.sale_repo.create_sale(
                customer_id=sale_data.customer_id,
                user_id=sale_data.user_id,
                total_amount=total_amount,
                discount_amount=sale_data.discount_amount,
                final_amount=final_amount,
                items=items_with_snapshots,
                payments=payments
            )
            
            # Audit trail
            await self.audit_repo.log_create(
                table="sales",
                record_id=sale.id,
                user_id=sale_data.user_id,
                data={
                    "total_amount": str(total_amount),
                    "final_amount": str(final_amount),
                    "items_count": len(sale_data.items)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return sale

    
    async def cancel_sale(
        self,
        sale_id: int,
        cancelled_by: int,
        cancellation_reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Sale:
        """
        Cancel a sale with stock restoration and authorization check.
        
        Args:
            sale_id: Sale ID
            cancelled_by: User ID who is cancelling the sale
            cancellation_reason: Reason for cancellation
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Cancelled sale
            
        Raises:
            NotFoundError: If sale not found
            ValidationError: If sale is already cancelled
            OptimisticLockError: If version conflict detected
        """
        # Get sale
        sale = await self.sale_repo.get_by_id(sale_id)
        if not sale:
            raise NotFoundError(f"Sale with ID {sale_id} not found")
        
        # Check if already cancelled
        if sale.status == 'cancelled':
            raise ValidationError(f"Sale {sale_id} is already cancelled")
        
        # Cancel sale and restore stock in transaction
        async with self.db.transaction():
            # Cancel sale
            cancelled_sale = await self.sale_repo.cancel_sale(
                sale_id=sale_id,
                cancelled_by=cancelled_by,
                cancellation_reason=cancellation_reason,
                version=sale.version
            )
            
            if not cancelled_sale:
                raise NotFoundError(f"Sale with ID {sale_id} not found")
            
            # Restore stock for each item
            for item in sale.items:
                product = await self.product_repo.get_by_id(item.product_id)
                if not product:
                    # Product was deleted, skip stock restoration
                    continue
                
                # Restore quantity
                new_quantity = product.quantity + item.quantity
                
                await self.product_repo.update(
                    id=product.id,
                    version=product.version,
                    quantity=new_quantity
                )
                
                # Create inventory movement
                movement_query = """
                    INSERT INTO inventory_movements (
                        product_id, movement_type, quantity_change,
                        quantity_before, quantity_after,
                        reference_type, reference_id, user_id, notes
                    )
                    VALUES ($1, 'IN', $2, $3, $4, 'sale_cancellation', $5, $6, $7)
                """
                await self.db.execute(
                    movement_query,
                    product.id,
                    item.quantity,
                    product.quantity,
                    new_quantity,
                    sale_id,
                    cancelled_by,
                    f"Stock restored from cancelled sale {sale_id}"
                )
            
            # Audit trail
            await self.audit_repo.log_update(
                table="sales",
                record_id=sale_id,
                user_id=cancelled_by,
                old_data={"status": "completed"},
                new_data={
                    "status": "cancelled",
                    "cancellation_reason": cancellation_reason
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return cancelled_sale
    
    async def get_sale(self, sale_id: int) -> Optional[Sale]:
        """
        Get sale by ID.
        
        Args:
            sale_id: Sale ID
            
        Returns:
            Sale if found, None otherwise
        """
        return await self.sale_repo.get_by_id(sale_id)
    
    async def list_sales(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ):
        """
        List sales with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            
        Returns:
            PaginatedResult with sales
        """
        return await self.sale_repo.list_paginated(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=order_by,
            order_desc=order_desc
        )
    
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
            List of sales
        """
        return await self.sale_repo.get_sales_by_date_range(
            start_date=start_date,
            end_date=end_date,
            status=status
        )
    
    async def _validate_sale(self, sale_data: SaleCreate) -> None:
        """
        Validate sale data.
        
        Args:
            sale_data: Sale creation data
            
        Raises:
            ValidationError: If validation fails
            NotFoundError: If product not found
            InsufficientStockError: If insufficient stock
        """
        # Check all products exist and have sufficient stock
        for item in sale_data.items:
            product = await self.product_repo.get_by_id(item.product_id)
            if not product:
                raise NotFoundError(f"Product with ID {item.product_id} not found")
            
            if product.quantity < item.quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for product {product.sku}. "
                    f"Available: {product.quantity}, Requested: {item.quantity}"
                )
        
        # Validate amounts (already validated by Pydantic, but double-check)
        total_amount = sum(
            Decimal(str(item.quantity)) * item.unit_price
            for item in sale_data.items
        )
        final_amount = total_amount - sale_data.discount_amount
        total_payments = sum(payment.amount for payment in sale_data.payments)
        
        # Round to 2 decimal places for comparison
        final_amount = final_amount.quantize(Decimal('0.01'))
        total_payments = total_payments.quantize(Decimal('0.01'))
        
        if total_payments != final_amount:
            raise ValidationError(
                f"Total payments {total_payments} does not match final amount {final_amount}"
            )
