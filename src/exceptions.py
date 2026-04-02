"""Custom exception hierarchy for the application."""

from typing import Optional, Dict, Any


class AppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize application exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Optional additional details about the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API responses.
        
        Returns:
            Dictionary with error information
        """
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(AppException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field: Optional field name that failed validation
            details: Optional additional details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=error_details
        )


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize not found error.
        
        Args:
            message: Human-readable error message
            resource_type: Optional type of resource (product, sale, user, etc.)
            resource_id: Optional ID of the resource
            details: Optional additional details
        """
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id is not None:
            error_details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=error_details
        )


class DuplicateError(AppException):
    """Raised when attempting to create a duplicate record."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize duplicate error.
        
        Args:
            message: Human-readable error message
            field: Optional field name that has duplicate value
            value: Optional duplicate value
            details: Optional additional details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = value
        
        super().__init__(
            message=message,
            error_code="DUPLICATE_ERROR",
            details=error_details
        )


class InsufficientStockError(AppException):
    """Raised when attempting to reduce stock below zero."""
    
    def __init__(
        self,
        message: str,
        product_id: Optional[int] = None,
        product_sku: Optional[str] = None,
        available: Optional[int] = None,
        requested: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize insufficient stock error.
        
        Args:
            message: Human-readable error message
            product_id: Optional product ID
            product_sku: Optional product SKU
            available: Optional available quantity
            requested: Optional requested quantity
            details: Optional additional details
        """
        error_details = details or {}
        if product_id is not None:
            error_details["product_id"] = product_id
        if product_sku:
            error_details["product_sku"] = product_sku
        if available is not None:
            error_details["available"] = available
        if requested is not None:
            error_details["requested"] = requested
        
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_STOCK",
            details=error_details
        )


class AuthenticationError(AppException):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authentication error.
        
        Args:
            message: Human-readable error message
            reason: Optional reason for failure (invalid_credentials, account_locked, etc.)
            details: Optional additional details
        """
        error_details = details or {}
        if reason:
            error_details["reason"] = reason
        
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=error_details
        )


class AuthorizationError(AppException):
    """Raised when user is not authorized for an operation."""
    
    def __init__(
        self,
        message: str,
        required_role: Optional[str] = None,
        user_role: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authorization error.
        
        Args:
            message: Human-readable error message
            required_role: Optional required role for the operation
            user_role: Optional user's current role
            details: Optional additional details
        """
        error_details = details or {}
        if required_role:
            error_details["required_role"] = required_role
        if user_role:
            error_details["user_role"] = user_role
        
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=error_details
        )


class OptimisticLockError(AppException):
    """Raised when optimistic locking fails due to version conflict."""
    
    def __init__(
        self,
        message: str,
        expected_version: Optional[int] = None,
        actual_version: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize optimistic lock error.
        
        Args:
            message: Human-readable error message
            expected_version: Optional expected version number
            actual_version: Optional actual version number
            details: Optional additional details
        """
        error_details = details or {}
        if expected_version is not None:
            error_details["expected_version"] = expected_version
        if actual_version is not None:
            error_details["actual_version"] = actual_version
        
        super().__init__(
            message=message,
            error_code="OPTIMISTIC_LOCK_ERROR",
            details=error_details
        )


class DatabaseError(AppException):
    """Raised when a database operation fails."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize database error.
        
        Args:
            message: Human-readable error message
            operation: Optional operation that failed (insert, update, delete, select)
            details: Optional additional details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=error_details
        )


class CacheError(AppException):
    """Raised when a cache operation fails."""
    
    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize cache error.
        
        Args:
            message: Human-readable error message
            operation: Optional operation that failed (get, set, delete)
            details: Optional additional details
        """
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=error_details
        )


class ConfigurationError(AppException):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Human-readable error message
            config_key: Optional configuration key that is invalid/missing
            details: Optional additional details
        """
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=error_details
        )
