"""Base repository pattern with generic CRUD operations and pagination."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from src.infrastructure.database import DatabaseClient


T = TypeVar('T')


@dataclass
class PaginatedResult(Generic[T]):
    """Result of a paginated query."""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> 'PaginatedResult[T]':
        """
        Create a paginated result.
        
        Args:
            items: Items for current page
            total: Total number of items
            page: Current page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            PaginatedResult instance
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository with generic CRUD operations.
    
    Provides common database operations with pagination, filtering, and ordering.
    Subclasses must implement abstract methods for specific entity types.
    """
    
    def __init__(self, db_client: DatabaseClient, table_name: str):
        """
        Initialize base repository.
        
        Args:
            db_client: Database client for connection pooling
            table_name: Name of the database table
        """
        self.db = db_client
        self.table_name = table_name
    
    @abstractmethod
    async def create(self, **kwargs) -> T:
        """
        Create a new record.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            Created entity
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Update a record.
        
        Args:
            id: Record ID
            **kwargs: Field values to update
            
        Returns:
            Updated entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """
        Delete a record (soft delete).
        
        Args:
            id: Record ID
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[T]:
        """
        List all records with optional filtering and ordering.
        
        Args:
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            
        Returns:
            List of entities
        """
        pass
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            Number of records
        """
        where_clause, params = self._build_where_clause(filters)
        query = f"SELECT COUNT(*) FROM {self.table_name} {where_clause}"
        
        result = await self.db.fetch_val(query, *params)
        return result or 0
    
    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> PaginatedResult[T]:
        """
        List records with pagination, filtering, and ordering.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            
        Returns:
            PaginatedResult with items and pagination metadata
        """
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        if page_size > 100:
            page_size = 100
        
        # Get total count
        total = await self.count(filters)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get items for current page
        items = await self._list_with_pagination(
            filters=filters,
            order_by=order_by,
            order_desc=order_desc,
            limit=page_size,
            offset=offset
        )
        
        return PaginatedResult.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    @abstractmethod
    async def _list_with_pagination(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> List[T]:
        """
        Internal method to list records with pagination.
        
        Subclasses must implement this to return properly typed entities.
        
        Args:
            filters: Dictionary of field:value filters
            order_by: Field name to order by
            order_desc: If True, order descending
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of entities
        """
        pass
    
    def _build_where_clause(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Any]]:
        """
        Build WHERE clause from filters dictionary.
        
        Args:
            filters: Dictionary of field:value filters
            
        Returns:
            Tuple of (where_clause, params) for parameterized query
        """
        if not filters:
            return "WHERE deleted_at IS NULL", []
        
        conditions = ["deleted_at IS NULL"]
        params = []
        param_index = 1
        
        for field, value in filters.items():
            if value is None:
                conditions.append(f"{field} IS NULL")
            else:
                conditions.append(f"{field} = ${param_index}")
                params.append(value)
                param_index += 1
        
        where_clause = "WHERE " + " AND ".join(conditions)
        return where_clause, params
    
    def _build_order_clause(
        self,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> str:
        """
        Build ORDER BY clause.
        
        Args:
            order_by: Field name to order by
            order_desc: If True, order descending
            
        Returns:
            ORDER BY clause string
        """
        if not order_by:
            return "ORDER BY id DESC"
        
        direction = "DESC" if order_desc else "ASC"
        return f"ORDER BY {order_by} {direction}"
