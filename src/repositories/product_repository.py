"""Product repository with full-text search and optimistic locking."""

from typing import Optional, List, Dict, Any
from decimal import Decimal

from src.domain.product import Product, ProductCreate, ProductUpdate
from src.repositories.base import BaseRepository
from src.infrastructure.database import DatabaseClient
from src.exceptions import OptimisticLockError


class ProductRepository(BaseRepository[Product]):
    """Repository for product data access with full-text search."""
    
    def __init__(self, db_client: DatabaseClient):
        """
        Initialize product repository.
        
        Args:
            db_client: Database client for connection pooling
        """
        super().__init__(db_client, "products")
    
    async def create(
        self,
        sku: str,
        name: str,
        gender: str,
        brand: str,
        reference: str,
        size: str,
        quantity: int,
        price: Decimal,
        description: Optional[str] = None,
        barcode: Optional[str] = None,
        min_stock: int = 5
    ) -> Product:
        """
        Create a new product.
        
        Args:
            sku: Stock keeping unit (unique)
            name: Product name
            gender: Gender (M/F/U)
            brand: Brand name
            reference: Product reference
            size: Product size
            quantity: Initial quantity
            price: Product price
            description: Product description
            barcode: Product barcode
            min_stock: Minimum stock level for alerts
            
        Returns:
            Created product
        """
        query = """
            INSERT INTO products (
                sku, name, description, gender, brand, reference, size,
                quantity, price, barcode, min_stock, version
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 1)
            RETURNING id, sku, name, description, gender, brand, reference, size,
                      quantity, price, barcode, min_stock, version,
                      created_at, updated_at, deleted_at
        """
        row = await self.db.fetch_one(
            query, sku, name, description, gender, brand, reference, size,
            quantity, price, barcode, min_stock
        )
        return Product(**row)
    
    async def get_by_id(self, id: int) -> Optional[Product]:
        """
        Get product by ID.
        
        Args:
            id: Product ID
            
        Returns:
            Product if found, None otherwise
        """
        query = """
            SELECT id, sku, name, description, gender, brand, reference, size,
                   quantity, price, barcode, min_stock, version,
                   created_at, updated_at, deleted_at
            FROM products
            WHERE id = $1 AND deleted_at IS NULL
        """
        row = await self.db.fetch_one(query, id)
        return Product(**row) if row else None
    
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get product by SKU.
        
        Args:
            sku: Stock keeping unit
            
        Returns:
            Product if found, None otherwise
        """
        query = """
            SELECT id, sku, name, description, gender, brand, reference, size,
                   quantity, price, barcode, min_stock, version,
                   created_at, updated_at, deleted_at
            FROM products
            WHERE sku = $1 AND deleted_at IS NULL
        """
        row = await self.db.fetch_one(query, sku)
        return Product(**row) if row else None

    
    async def update(
        self,
        id: int,
        version: int,
        **kwargs
    ) -> Optional[Product]:
        """
        Update a product with optimistic locking.
        
        Args:
            id: Product ID
            version: Current version for optimistic locking
            **kwargs: Fields to update
            
        Returns:
            Updated product if found and version matches, None otherwise
            
        Raises:
            OptimisticLockError: If version conflict detected
        """
        # Build SET clause dynamically
        set_clauses = []
        params = []
        param_index = 1
        
        for field, value in kwargs.items():
            if value is not None and field != 'version':
                set_clauses.append(f"{field} = ${param_index}")
                params.append(value)
                param_index += 1
        
        if not set_clauses:
            return await self.get_by_id(id)
        
        # Add version increment and updated_at
        set_clauses.append(f"version = ${param_index}")
        params.append(version + 1)
        param_index += 1
        
        set_clauses.append("updated_at = NOW()")
        
        # Add WHERE clause parameters
        params.extend([id, version])
        
        query = f"""
            UPDATE products
            SET {', '.join(set_clauses)}
            WHERE id = ${param_index} AND version = ${param_index + 1} AND deleted_at IS NULL
            RETURNING id, sku, name, description, gender, brand, reference, size,
                      quantity, price, barcode, min_stock, version,
                      created_at, updated_at, deleted_at
        """
        
        row = await self.db.fetch_one(query, *params)
        
        if not row:
            # Check if product exists
            existing = await self.get_by_id(id)
            if existing and existing.version != version:
                raise OptimisticLockError(
                    f"Version conflict: expected {version}, found {existing.version}"
                )
            return None
        
        return Product(**row)
    
    async def delete(self, id: int) -> bool:
        """
        Soft delete a product.
        
        Args:
            id: Product ID
            
        Returns:
            True if deleted, False if not found
        """
        query = """
            UPDATE products
            SET deleted_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
            RETURNING id
        """
        row = await self.db.fetch_one(query, id)
        return row is not None
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[Product]:
        """
        List all products with optional filtering and ordering.
        
        Args:
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            
        Returns:
            List of products
        """
        where_clause, params = self._build_where_clause(filters)
        order_clause = self._build_order_clause(order_by, order_desc)
        
        query = f"""
            SELECT id, sku, name, description, gender, brand, reference, size,
                   quantity, price, barcode, min_stock, version,
                   created_at, updated_at, deleted_at
            FROM products
            {where_clause}
            {order_clause}
        """
        
        rows = await self.db.fetch_all(query, *params)
        return [Product(**row) for row in rows]
    
    async def _list_with_pagination(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[Product]:
        """
        List products with pagination.
        
        Args:
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of products
        """
        where_clause, params = self._build_where_clause(filters)
        order_clause = self._build_order_clause(order_by, order_desc)
        
        # Add limit and offset to params
        params.extend([limit, offset])
        param_count = len(params)
        
        query = f"""
            SELECT id, sku, name, description, gender, brand, reference, size,
                   quantity, price, barcode, min_stock, version,
                   created_at, updated_at, deleted_at
            FROM products
            {where_clause}
            {order_clause}
            LIMIT ${param_count - 1} OFFSET ${param_count}
        """
        
        rows = await self.db.fetch_all(query, *params)
        return [Product(**row) for row in rows]
    
    async def search(
        self,
        query: str,
        limit: int = 20
    ) -> List[Product]:
        """
        Full-text search for products.
        
        Uses PostgreSQL tsvector for efficient full-text search across
        name, description, brand, and reference fields.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching products ordered by relevance
        """
        sql = """
            SELECT id, sku, name, description, gender, brand, reference, size,
                   quantity, price, barcode, min_stock, version,
                   created_at, updated_at, deleted_at,
                   ts_rank(
                       to_tsvector('portuguese', 
                           COALESCE(name, '') || ' ' || 
                           COALESCE(description, '') || ' ' || 
                           COALESCE(brand, '') || ' ' || 
                           COALESCE(reference, '')
                       ),
                       plainto_tsquery('portuguese', $1)
                   ) AS rank
            FROM products
            WHERE deleted_at IS NULL
              AND to_tsvector('portuguese', 
                      COALESCE(name, '') || ' ' || 
                      COALESCE(description, '') || ' ' || 
                      COALESCE(brand, '') || ' ' || 
                      COALESCE(reference, '')
                  ) @@ plainto_tsquery('portuguese', $1)
            ORDER BY rank DESC, name ASC
            LIMIT $2
        """
        
        rows = await self.db.fetch_all(sql, query, limit)
        return [Product(**{k: v for k, v in row.items() if k != 'rank'}) for row in rows]
    
    async def get_low_stock_products(self, threshold: Optional[int] = None) -> List[Product]:
        """
        Get products with quantity below minimum stock level.
        
        Args:
            threshold: Optional custom threshold (uses min_stock if not provided)
            
        Returns:
            List of low stock products ordered by urgency (lowest quantity first)
        """
        if threshold is not None:
            query = """
                SELECT id, sku, name, description, gender, brand, reference, size,
                       quantity, price, barcode, min_stock, version,
                       created_at, updated_at, deleted_at
                FROM products
                WHERE deleted_at IS NULL AND quantity < $1
                ORDER BY quantity ASC, name ASC
            """
            rows = await self.db.fetch_all(query, threshold)
        else:
            query = """
                SELECT id, sku, name, description, gender, brand, reference, size,
                       quantity, price, barcode, min_stock, version,
                       created_at, updated_at, deleted_at
                FROM products
                WHERE deleted_at IS NULL AND quantity < min_stock
                ORDER BY (quantity::float / NULLIF(min_stock, 0)) ASC, quantity ASC, name ASC
            """
            rows = await self.db.fetch_all(query)
        
        return [Product(**row) for row in rows]


    async def exists_by_sku(self, sku: str) -> bool:
        """
        Check if product exists by SKU using EXISTS (optimized).

        Args:
            sku: Product SKU

        Returns:
            True if product exists, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM products
                WHERE sku = $1 AND deleted_at IS NULL
            )
        """
        result = await self.db.fetch_val(query, sku)
        return result or False

    async def exists_by_id(self, id: int) -> bool:
        """
        Check if product exists by ID using EXISTS (optimized).

        Args:
            id: Product ID

        Returns:
            True if product exists, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM products
                WHERE id = $1 AND deleted_at IS NULL
            )
        """
        result = await self.db.fetch_val(query, id)
        return result or False


    async def exists_by_sku(self, sku: str) -> bool:
        """
        Check if product exists by SKU using EXISTS (optimized).
        
        Args:
            sku: Product SKU
            
        Returns:
            True if product exists, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM products
                WHERE sku = $1 AND deleted_at IS NULL
            )
        """
        result = await self.db.fetch_val(query, sku)
        return result or False
    
    async def exists_by_id(self, id: int) -> bool:
        """
        Check if product exists by ID using EXISTS (optimized).
        
        Args:
            id: Product ID
            
        Returns:
            True if product exists, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM products
                WHERE id = $1 AND deleted_at IS NULL
            )
        """
        result = await self.db.fetch_val(query, id)
        return result or False
