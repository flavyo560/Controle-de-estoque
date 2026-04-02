"""Audit repository for audit trail logging."""

from typing import Optional, Dict, Any
from src.domain.audit import AuditLog, AuditLogCreate
from src.infrastructure.database import DatabaseClient


class AuditRepository:
    """Repository for audit trail with append-only operations."""
    
    def __init__(self, db_client: DatabaseClient):
        """
        Initialize audit repository.
        
        Args:
            db_client: Database client for connection pooling
        """
        self.db = db_client
    
    async def log_create(
        self,
        table: str,
        record_id: int,
        user_id: int,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a CREATE operation.
        
        Args:
            table: Table name where record was created
            record_id: ID of created record
            user_id: ID of user who created the record
            data: New record data
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created audit log entry
        """
        query = """
            INSERT INTO audit_log (user_id, operation, table_name, record_id, new_values, ip_address, user_agent)
            VALUES ($1, 'CREATE', $2, $3, $4, $5, $6)
            RETURNING id, user_id, operation, table_name, record_id, old_values, new_values,
                      ip_address, user_agent, created_at
        """
        row = await self.db.fetch_one(
            query, user_id, table, record_id, data, ip_address, user_agent
        )
        return AuditLog(**row)
    
    async def log_update(
        self,
        table: str,
        record_id: int,
        user_id: int,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log an UPDATE operation.
        
        Args:
            table: Table name where record was updated
            record_id: ID of updated record
            user_id: ID of user who updated the record
            old_data: Previous record data
            new_data: New record data
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created audit log entry
        """
        query = """
            INSERT INTO audit_log (user_id, operation, table_name, record_id, old_values, new_values, ip_address, user_agent)
            VALUES ($1, 'UPDATE', $2, $3, $4, $5, $6, $7)
            RETURNING id, user_id, operation, table_name, record_id, old_values, new_values,
                      ip_address, user_agent, created_at
        """
        row = await self.db.fetch_one(
            query, user_id, table, record_id, old_data, new_data, ip_address, user_agent
        )
        return AuditLog(**row)
    
    async def log_delete(
        self,
        table: str,
        record_id: int,
        user_id: int,
        data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a DELETE operation.
        
        Args:
            table: Table name where record was deleted
            record_id: ID of deleted record
            user_id: ID of user who deleted the record
            data: Deleted record data
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created audit log entry
        """
        query = """
            INSERT INTO audit_log (user_id, operation, table_name, record_id, old_values, ip_address, user_agent)
            VALUES ($1, 'DELETE', $2, $3, $4, $5, $6)
            RETURNING id, user_id, operation, table_name, record_id, old_values, new_values,
                      ip_address, user_agent, created_at
        """
        row = await self.db.fetch_one(
            query, user_id, table, record_id, data, ip_address, user_agent
        )
        return AuditLog(**row)
    
    async def log_login(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str
    ) -> AuditLog:
        """
        Log a successful LOGIN operation.
        
        Args:
            user_id: ID of user who logged in
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created audit log entry
        """
        query = """
            INSERT INTO audit_log (user_id, operation, ip_address, user_agent)
            VALUES ($1, 'LOGIN', $2, $3)
            RETURNING id, user_id, operation, table_name, record_id, old_values, new_values,
                      ip_address, user_agent, created_at
        """
        row = await self.db.fetch_one(query, user_id, ip_address, user_agent)
        return AuditLog(**row)
    
    async def log_logout(
        self,
        user_id: int,
        ip_address: str,
        user_agent: str
    ) -> AuditLog:
        """
        Log a LOGOUT operation.
        
        Args:
            user_id: ID of user who logged out
            ip_address: IP address of the request
            user_agent: User agent string
            
        Returns:
            Created audit log entry
        """
        query = """
            INSERT INTO audit_log (user_id, operation, ip_address, user_agent)
            VALUES ($1, 'LOGOUT', $2, $3)
            RETURNING id, user_id, operation, table_name, record_id, old_values, new_values,
                      ip_address, user_agent, created_at
        """
        row = await self.db.fetch_one(query, user_id, ip_address, user_agent)
        return AuditLog(**row)
    
    async def log_failed_login(
        self,
        username: str,
        ip_address: str,
        reason: str,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a FAILED_LOGIN operation.
        
        Args:
            username: Username that attempted to log in
            ip_address: IP address of the request
            reason: Reason for failure (user_not_found, invalid_password, rate_limit_exceeded, account_locked)
            user_agent: User agent string
            
        Returns:
            Created audit log entry
        """
        query = """
            INSERT INTO audit_log (operation, new_values, ip_address, user_agent)
            VALUES ('FAILED_LOGIN', $1, $2, $3)
            RETURNING id, user_id, operation, table_name, record_id, old_values, new_values,
                      ip_address, user_agent, created_at
        """
        data = {"username": username, "reason": reason}
        row = await self.db.fetch_one(query, data, ip_address, user_agent)
        return AuditLog(**row)
