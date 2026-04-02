"""Inventory service with business logic for product management."""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from src.domain.product import Product, ProductCreate, ProductUpdate
from src.repositories.product_repository import ProductRepository
from src.repositories.audit_repository import AuditRepository
from src.infrastructure.cache import CacheManager
from src.infrastructure.database import DatabaseClient
from src.exceptions import (
    DuplicateError,
    NotFoundError,
    InsufficientStockError,
    OptimisticLockError,
    DatabaseError
)


class InventoryService:
    """Service for inventory management with caching and audit trail."""
    
    CACHE_TTL_PRODUCT = 300  # 5 minutes
    CACHE_TTL_LOW_STOCK = 300  # 5 minutes
    CACHE_TTL_SEARCH = 120  # 2 minutes
    
    def __init__(
        self,
        product_repo: ProductRepository,
        audit_repo: AuditRepository,
        cache: CacheManager,
        db_client: DatabaseClient
    ):
        """
        Initialize inventory service.
        
        Args:
            product_repo: Product repository
            audit_repo: Audit repository for logging
            cache: Cache manager
            db_client: Database client for transactions
        """
        self.product_repo = product_repo
        self.audit_repo = audit_repo
        self.cache = cache
        self.db = db_client
    
    async def create_product(
        self,
        product_data: ProductCreate,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Product:
        """
        Create a new product with validation and audit trail.
        
        Args:
            product_data: Product creation data
            user_id: ID of user creating the product
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created product
            
        Raises:
            DuplicateError: If SKU already exists
        """
        # Check for duplicate SKU
        existing = await self.product_repo.get_by_sku(product_data.sku)
        if existing:
            raise DuplicateError(f"Product with SKU {product_data.sku} already exists")
        
        # Create product
        product = await self.product_repo.create(
            sku=product_data.sku,
            name=product_data.name,
            description=product_data.description,
            gender=product_data.gender,
            brand=product_data.brand,
            reference=product_data.reference,
            size=product_data.size,
            quantity=product_data.quantity,
            price=product_data.price,
            barcode=product_data.barcode,
            min_stock=product_data.min_stock
        )
        
        # Audit trail
        await self.audit_repo.log_create(
            table="products",
            record_id=product.id,
            user_id=user_id,
            data={
                "sku": product.sku,
                "name": product.name,
                "quantity": product.quantity,
                "price": str(product.price)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Cache the new product
        await self._cache_product(product)
        
        # Invalidate low stock cache
        await self.cache.delete("low_stock_products")
        
        return product
    
    async def get_product(self, product_id: int) -> Optional[Product]:
        """
        Get product by ID with caching.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product if found, None otherwise
        """
        # Try cache first
        cache_key = f"product:{product_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Product(**cached)
        
        # Fetch from database
        product = await self.product_repo.get_by_id(product_id)
        if product:
            await self._cache_product(product)
        
        return product
    
    async def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get product by SKU with caching.
        
        Args:
            sku: Stock keeping unit
            
        Returns:
            Product if found, None otherwise
        """
        # Try cache first
        cache_key = f"product:sku:{sku}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Product(**cached)
        
        # Fetch from database
        product = await self.product_repo.get_by_sku(sku)
        if product:
            await self._cache_product(product)
        
        return product

    
    async def update_product(
        self,
        product_id: int,
        product_data: ProductUpdate,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Product:
        """
        Update a product with cache invalidation and audit trail.
        
        Args:
            product_id: Product ID
            product_data: Product update data
            user_id: ID of user updating the product
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Updated product
            
        Raises:
            NotFoundError: If product not found
            OptimisticLockError: If version conflict detected
        """
        # Get current product
        current = await self.product_repo.get_by_id(product_id)
        if not current:
            raise NotFoundError(f"Product with ID {product_id} not found")
        
        # Build update dict (only non-None values)
        update_dict = {
            k: v for k, v in product_data.model_dump().items()
            if v is not None
        }
        
        if not update_dict:
            return current
        
        # Update product with optimistic locking
        updated = await self.product_repo.update(
            id=product_id,
            version=current.version,
            **update_dict
        )
        
        if not updated:
            raise NotFoundError(f"Product with ID {product_id} not found")
        
        # Audit trail
        old_data = {k: getattr(current, k) for k in update_dict.keys()}
        new_data = {k: getattr(updated, k) for k in update_dict.keys()}
        
        await self.audit_repo.log_update(
            table="products",
            record_id=product_id,
            user_id=user_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Invalidate cache
        await self._invalidate_product_cache(current)
        
        # Invalidate low stock cache if quantity changed
        if 'quantity' in update_dict or 'min_stock' in update_dict:
            await self.cache.delete("low_stock_products")
        
        return updated
    
    async def update_stock(
        self,
        product_id: int,
        quantity_change: int,
        user_id: int,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Product:
        """
        Update product stock with transaction safety and inventory movements.
        
        Args:
            product_id: Product ID
            quantity_change: Change in quantity (positive or negative)
            user_id: ID of user making the change
            reference_type: Type of reference (sale, purchase, adjustment)
            reference_id: ID of the reference record
            notes: Optional notes about the change
            
        Returns:
            Updated product
            
        Raises:
            NotFoundError: If product not found
            InsufficientStockError: If quantity would go below zero
        """
        async with self.db.transaction():
            # Get current product with row lock
            product = await self.product_repo.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")
            
            # Calculate new quantity
            new_quantity = product.quantity + quantity_change
            if new_quantity < 0:
                raise InsufficientStockError(
                    f"Insufficient stock for product {product.sku}. "
                    f"Current: {product.quantity}, Requested: {abs(quantity_change)}"
                )
            
            # Update product quantity
            updated = await self.product_repo.update(
                id=product_id,
                version=product.version,
                quantity=new_quantity
            )
            
            if not updated:
                raise NotFoundError(f"Product with ID {product_id} not found")
            
            # Create inventory movement record
            movement_query = """
                INSERT INTO inventory_movements (
                    product_id, movement_type, quantity_change,
                    quantity_before, quantity_after,
                    reference_type, reference_id, user_id, notes
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            movement_type = 'IN' if quantity_change > 0 else 'OUT'
            
            await self.db.execute(
                movement_query,
                product_id,
                movement_type,
                quantity_change,
                product.quantity,
                new_quantity,
                reference_type,
                reference_id,
                user_id,
                notes
            )
            
            # Invalidate cache
            await self._invalidate_product_cache(product)
            await self.cache.delete("low_stock_products")
            
            return updated
    
    async def get_low_stock_alerts(self) -> Dict[str, Any]:
        """
        Get low stock alerts with caching and metrics.
        
        Returns:
            Dictionary with low stock products and metrics
        """
        # Try cache first
        cache_key = "low_stock_products"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Fetch from database
        products = await self.product_repo.get_low_stock_products()
        
        # Calculate metrics
        total_low_stock = len(products)
        critical_count = sum(1 for p in products if p.quantity == 0)
        warning_count = sum(1 for p in products if 0 < p.quantity < p.min_stock)
        
        result = {
            "products": [p.model_dump() for p in products],
            "metrics": {
                "total": total_low_stock,
                "critical": critical_count,
                "warning": warning_count
            }
        }
        
        # Cache result
        await self.cache.set(cache_key, result, ttl=self.CACHE_TTL_LOW_STOCK)
        
        return result
    
    async def search_products(
        self,
        query: str,
        limit: int = 20
    ) -> List[Product]:
        """
        Search products with caching.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching products
        """
        # Try cache first
        cache_key = f"search:{query}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [Product(**p) for p in cached]
        
        # Search in database
        products = await self.product_repo.search(query, limit)
        
        # Cache results
        await self.cache.set(
            cache_key,
            [p.model_dump() for p in products],
            ttl=self.CACHE_TTL_SEARCH
        )
        
        return products
    
    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ):
        """
        List products with pagination.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            
        Returns:
            PaginatedResult with products
        """
        return await self.product_repo.list_paginated(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=order_by,
            order_desc=order_desc
        )
    
    async def delete_product(
        self,
        product_id: int,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Soft delete a product.
        
        Args:
            product_id: Product ID
            user_id: ID of user deleting the product
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            True if deleted, False if not found
        """
        # Get product before deletion
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            return False
        
        # Delete product
        deleted = await self.product_repo.delete(product_id)
        
        if deleted:
            # Audit trail
            await self.audit_repo.log_delete(
                table="products",
                record_id=product_id,
                user_id=user_id,
                data={
                    "sku": product.sku,
                    "name": product.name,
                    "quantity": product.quantity
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Invalidate cache
            await self._invalidate_product_cache(product)
            await self.cache.delete("low_stock_products")
        
        return deleted
    
    async def _cache_product(self, product: Product) -> None:
        """Cache a product by ID and SKU."""
        product_dict = product.model_dump()
        
        # Cache by ID
        await self.cache.set(
            f"product:{product.id}",
            product_dict,
            ttl=self.CACHE_TTL_PRODUCT
        )
        
        # Cache by SKU
        await self.cache.set(
            f"product:sku:{product.sku}",
            product_dict,
            ttl=self.CACHE_TTL_PRODUCT
        )
    
    async def _invalidate_product_cache(self, product: Product) -> None:
        """Invalidate all cache entries for a product."""
        await self.cache.delete(f"product:{product.id}")
        await self.cache.delete(f"product:sku:{product.sku}")
        
        # Invalidate search cache (pattern-based)
        await self.cache.invalidate_pattern("search:*")
