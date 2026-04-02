"""Error handling middleware for the application."""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

from src.exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    DuplicateError,
    InsufficientStockError,
    AuthenticationError,
    AuthorizationError,
    OptimisticLockError,
    DatabaseError,
    CacheError,
    ConfigurationError
)


class ErrorHandler:
    """
    Error handler for catching and logging exceptions.
    
    Maps exceptions to user-friendly error messages and logs
    stack traces for unexpected errors.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize error handler.
        
        Args:
            logger: Optional logger instance (creates one if not provided)
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an exception and return structured error response.
        
        Args:
            exception: The exception to handle
            context: Optional context information (user_id, request_id, etc.)
            
        Returns:
            Dictionary with error information for API response
        """
        context = context or {}
        
        # Add timestamp
        error_time = datetime.now().isoformat()
        
        # Handle known application exceptions
        if isinstance(exception, AppException):
            return self._handle_app_exception(exception, context, error_time)
        
        # Handle unexpected exceptions
        return self._handle_unexpected_exception(exception, context, error_time)
    
    def _handle_app_exception(
        self,
        exception: AppException,
        context: Dict[str, Any],
        error_time: str
    ) -> Dict[str, Any]:
        """
        Handle known application exceptions.
        
        Args:
            exception: Application exception
            context: Context information
            error_time: Timestamp of the error
            
        Returns:
            Structured error response
        """
        # Log the error with context
        log_data = {
            "error_code": exception.error_code,
            "error_message": exception.message,
            "details": exception.details,
            "context": context,
            "timestamp": error_time
        }
        
        # Log at appropriate level based on exception type
        if isinstance(exception, (ValidationError, NotFoundError, DuplicateError)):
            # Client errors - log at INFO level
            self.logger.info(
                f"{exception.error_code}: {exception.message}",
                extra=log_data
            )
        elif isinstance(exception, (AuthenticationError, AuthorizationError)):
            # Security errors - log at WARNING level
            self.logger.warning(
                f"{exception.error_code}: {exception.message}",
                extra=log_data
            )
        else:
            # Server errors - log at ERROR level
            self.logger.error(
                f"{exception.error_code}: {exception.message}",
                extra=log_data
            )
        
        # Return user-friendly error response
        return {
            "success": False,
            "error": exception.to_dict(),
            "timestamp": error_time
        }
    
    def _handle_unexpected_exception(
        self,
        exception: Exception,
        context: Dict[str, Any],
        error_time: str
    ) -> Dict[str, Any]:
        """
        Handle unexpected exceptions.
        
        Args:
            exception: Unexpected exception
            context: Context information
            error_time: Timestamp of the error
            
        Returns:
            Structured error response
        """
        # Get stack trace
        stack_trace = traceback.format_exc()
        
        # Log the error with full stack trace
        log_data = {
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "stack_trace": stack_trace,
            "context": context,
            "timestamp": error_time
        }
        
        self.logger.error(
            f"Unexpected error: {type(exception).__name__}: {str(exception)}",
            extra=log_data,
            exc_info=True
        )
        
        # Return generic error response (don't expose internal details)
        return {
            "success": False,
            "error": {
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {}
            },
            "timestamp": error_time
        }
    
    def get_user_friendly_message(self, exception: Exception) -> str:
        """
        Get user-friendly error message for an exception.
        
        Args:
            exception: The exception
            
        Returns:
            User-friendly error message
        """
        # Map exception types to user-friendly messages
        if isinstance(exception, ValidationError):
            return f"Erro de validação: {exception.message}"
        
        elif isinstance(exception, NotFoundError):
            return f"Não encontrado: {exception.message}"
        
        elif isinstance(exception, DuplicateError):
            return f"Registro duplicado: {exception.message}"
        
        elif isinstance(exception, InsufficientStockError):
            return f"Estoque insuficiente: {exception.message}"
        
        elif isinstance(exception, AuthenticationError):
            return f"Erro de autenticação: {exception.message}"
        
        elif isinstance(exception, AuthorizationError):
            return "Você não tem permissão para realizar esta operação."
        
        elif isinstance(exception, OptimisticLockError):
            return "O registro foi modificado por outro usuário. Por favor, recarregue e tente novamente."
        
        elif isinstance(exception, DatabaseError):
            return "Erro ao acessar o banco de dados. Por favor, tente novamente."
        
        elif isinstance(exception, CacheError):
            return "Erro temporário. Por favor, tente novamente."
        
        elif isinstance(exception, ConfigurationError):
            return "Erro de configuração do sistema. Por favor, contate o administrador."
        
        elif isinstance(exception, AppException):
            return exception.message
        
        else:
            return "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."
    
    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if the operation should be retried.
        
        Args:
            exception: The exception
            
        Returns:
            True if operation should be retried, False otherwise
        """
        # Retry on transient errors
        if isinstance(exception, (DatabaseError, CacheError)):
            return True
        
        # Don't retry on client errors
        if isinstance(exception, (
            ValidationError,
            NotFoundError,
            DuplicateError,
            InsufficientStockError,
            AuthenticationError,
            AuthorizationError,
            OptimisticLockError
        )):
            return False
        
        # Don't retry on configuration errors
        if isinstance(exception, ConfigurationError):
            return False
        
        # Don't retry unexpected errors by default
        return False
