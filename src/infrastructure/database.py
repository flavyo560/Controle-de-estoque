"""Database client with asyncpg connection pooling."""

from typing import Any, Dict, List, Optional, AsyncIterator
from contextlib import asynccontextmanager
import asyncpg
from asyncpg.pool import Pool
from asyncpg.connection import Connection


class DatabaseClient:
    """Database client with connection pooling for PostgreSQL using asyncpg."""
    
    def __init__(
        self,
        dsn: str,
        min_size: int = 10,
        max_size: int = 20,
        command_timeout: float = 60.0
    ):
        """
        Initialize database client.
        
        Args:
            dsn: Database connection string (PostgreSQL DSN)
            min_size: Minimum pool size (default: 10)
            max_size: Maximum pool size (default: 20)
            command_timeout: Command timeout in seconds (default: 60.0)
        """
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.command_timeout = command_timeout
        self._pool: Optional[Pool] = None
    
    async def connect(self) -> None:
        """Initialize connection pool."""
        self._pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=self.command_timeout
        )
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
    
    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[Connection]:
        """
        Context manager for database transactions.
        
        Usage:
            async with db.transaction() as conn:
                await conn.execute("INSERT ...")
                await conn.execute("UPDATE ...")
        
        Yields:
            Database connection with active transaction
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def fetch_one(
        self,
        query: str,
        *args: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch single row.
        
        Args:
            query: SQL query
            *args: Query parameters
            
        Returns:
            Dictionary with row data or None if not found
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(
        self,
        query: str,
        *args: Any
    ) -> List[Dict[str, Any]]:
        """
        Fetch all rows.
        
        Args:
            query: SQL query
            *args: Query parameters
            
        Returns:
            List of dictionaries with row data
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetch_val(
        self,
        query: str,
        *args: Any
    ) -> Any:
        """
        Fetch single value.
        
        Args:
            query: SQL query
            *args: Query parameters
            
        Returns:
            Single value from query result
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute(
        self,
        query: str,
        *args: Any
    ) -> str:
        """
        Execute query and return status.
        
        Args:
            query: SQL query
            *args: Query parameters
            
        Returns:
            Query execution status string
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)
