"""
Unit tests for error handling.

Tests cover:
- Each exception type is raised correctly
- Error messages are user-friendly
- Error handler processes exceptions correctly
- Error responses have correct structure

Validates Requirements 9.1, 8.1
"""

import pytest
import logging
from decimal import Decimal
from unittest.mock import Mock, patch

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
from src.infrastructure.error_handler import ErrorHandler


class TestAppException:
    """Tests for base AppException class."""
    
    def test_app_exception_initialization(self):
        """Test AppException initialization with all parameters."""
        exc = AppException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        assert str(exc) == "Test error"
    
    def test_app_exception_without_details(self):
        """Test AppException initialization without details."""
        exc = AppException(
            message="Test error",
            error_code="TEST_ERROR"
        )
        
        assert exc.details == {}
    
    def test_app_exception_to_dict(self):
        """Test AppException to_dict method."""
        exc = AppException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"field": "value"}
        )
        
        result = exc.to_dict()
        
        assert result == {
            "error": "TEST_ERROR",
            "message": "Test error",
            "details": {"field": "value"}
        }


class TestValidationError:
    """Tests for ValidationError exception."""
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field name."""
        exc = ValidationError(
            message="Invalid email format",
            field="email"
        )
        
        assert exc.message == "Invalid email format"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field"] == "email"
    
    def test_validation_error_without_field(self):
        """Test ValidationError without field name."""
        exc = ValidationError(message="Invalid input")
        
        assert exc.message == "Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert "field" not in exc.details
    
    def test_validation_error_with_additional_details(self):
        """Test ValidationError with additional details."""
        exc = ValidationError(
            message="Price must be positive",
            field="price",
            details={"value": -10, "min": 0}
        )
        
        assert exc.details["field"] == "price"
        assert exc.details["value"] == -10
        assert exc.details["min"] == 0
    
    def test_validation_error_message_is_user_friendly(self):
        """Test that validation error messages are user-friendly."""
        exc = ValidationError(
            message="O campo 'email' deve conter um endereço de email válido",
            field="email"
        )
        
        # Message should be in Portuguese and descriptive
        assert "email" in exc.message.lower()
        assert "válido" in exc.message.lower()
        # Should not contain technical jargon
        assert "exception" not in exc.message.lower()
        assert "stack" not in exc.message.lower()


class TestNotFoundError:
    """Tests for NotFoundError exception."""
    
    def test_not_found_error_with_resource_info(self):
        """Test NotFoundError with resource type and ID."""
        exc = NotFoundError(
            message="Product not found",
            resource_type="product",
            resource_id=123
        )
        
        assert exc.message == "Product not found"
        assert exc.error_code == "NOT_FOUND"
        assert exc.details["resource_type"] == "product"
        assert exc.details["resource_id"] == 123
    
    def test_not_found_error_without_resource_info(self):
        """Test NotFoundError without resource information."""
        exc = NotFoundError(message="Resource not found")
        
        assert exc.message == "Resource not found"
        assert exc.error_code == "NOT_FOUND"
        assert "resource_type" not in exc.details
        assert "resource_id" not in exc.details
    
    def test_not_found_error_message_is_user_friendly(self):
        """Test that not found error messages are user-friendly."""
        exc = NotFoundError(
            message="Produto não encontrado",
            resource_type="product",
            resource_id=999
        )
        
        # Message should be in Portuguese and clear
        assert "não encontrado" in exc.message.lower()
        # Should not expose internal details
        assert "database" not in exc.message.lower()
        assert "table" not in exc.message.lower()


class TestDuplicateError:
    """Tests for DuplicateError exception."""
    
    def test_duplicate_error_with_field_and_value(self):
        """Test DuplicateError with field and value."""
        exc = DuplicateError(
            message="SKU already exists",
            field="sku",
            value="ABC123"
        )
        
        assert exc.message == "SKU already exists"
        assert exc.error_code == "DUPLICATE_ERROR"
        assert exc.details["field"] == "sku"
        assert exc.details["value"] == "ABC123"
    
    def test_duplicate_error_without_details(self):
        """Test DuplicateError without field and value."""
        exc = DuplicateError(message="Duplicate record")
        
        assert exc.message == "Duplicate record"
        assert exc.error_code == "DUPLICATE_ERROR"
        assert "field" not in exc.details
        assert "value" not in exc.details
    
    def test_duplicate_error_message_is_user_friendly(self):
        """Test that duplicate error messages are user-friendly."""
        exc = DuplicateError(
            message="Já existe um produto com este SKU",
            field="sku",
            value="TEST123"
        )
        
        # Message should be clear about what's duplicated
        assert "já existe" in exc.message.lower() or "duplicado" in exc.message.lower()
        # Should not contain SQL error messages
        assert "unique constraint" not in exc.message.lower()
        assert "violation" not in exc.message.lower()


class TestInsufficientStockError:
    """Tests for InsufficientStockError exception."""
    
    def test_insufficient_stock_error_with_all_details(self):
        """Test InsufficientStockError with all details."""
        exc = InsufficientStockError(
            message="Not enough stock",
            product_id=1,
            product_sku="ABC123",
            available=5,
            requested=10
        )
        
        assert exc.message == "Not enough stock"
        assert exc.error_code == "INSUFFICIENT_STOCK"
        assert exc.details["product_id"] == 1
        assert exc.details["product_sku"] == "ABC123"
        assert exc.details["available"] == 5
        assert exc.details["requested"] == 10
    
    def test_insufficient_stock_error_minimal(self):
        """Test InsufficientStockError with minimal details."""
        exc = InsufficientStockError(message="Insufficient stock")
        
        assert exc.message == "Insufficient stock"
        assert exc.error_code == "INSUFFICIENT_STOCK"
        assert "product_id" not in exc.details
    
    def test_insufficient_stock_error_message_is_user_friendly(self):
        """Test that insufficient stock error messages are user-friendly."""
        exc = InsufficientStockError(
            message="Estoque insuficiente. Disponível: 5, Solicitado: 10",
            available=5,
            requested=10
        )
        
        # Message should clearly indicate the problem
        assert "estoque" in exc.message.lower() or "stock" in exc.message.lower()
        # Should provide actionable information
        assert "5" in exc.message
        assert "10" in exc.message


class TestAuthenticationError:
    """Tests for AuthenticationError exception."""
    
    def test_authentication_error_with_reason(self):
        """Test AuthenticationError with reason."""
        exc = AuthenticationError(
            message="Invalid credentials",
            reason="invalid_password"
        )
        
        assert exc.message == "Invalid credentials"
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert exc.details["reason"] == "invalid_password"
    
    def test_authentication_error_without_reason(self):
        """Test AuthenticationError without reason."""
        exc = AuthenticationError(message="Authentication failed")
        
        assert exc.message == "Authentication failed"
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert "reason" not in exc.details
    
    def test_authentication_error_message_is_user_friendly(self):
        """Test that authentication error messages are user-friendly."""
        exc = AuthenticationError(
            message="Usuário ou senha incorretos",
            reason="invalid_credentials"
        )
        
        # Message should be clear but not too specific (security)
        assert "usuário" in exc.message.lower() or "senha" in exc.message.lower()
        # Should not reveal which field is wrong
        assert exc.message != "Senha incorreta"  # Too specific
        # Should not contain technical details
        assert "hash" not in exc.message.lower()
        assert "bcrypt" not in exc.message.lower()


class TestAuthorizationError:
    """Tests for AuthorizationError exception."""
    
    def test_authorization_error_with_roles(self):
        """Test AuthorizationError with role information."""
        exc = AuthorizationError(
            message="Insufficient permissions",
            required_role="admin",
            user_role="user"
        )
        
        assert exc.message == "Insufficient permissions"
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert exc.details["required_role"] == "admin"
        assert exc.details["user_role"] == "user"
    
    def test_authorization_error_without_roles(self):
        """Test AuthorizationError without role information."""
        exc = AuthorizationError(message="Access denied")
        
        assert exc.message == "Access denied"
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert "required_role" not in exc.details
    
    def test_authorization_error_message_is_user_friendly(self):
        """Test that authorization error messages are user-friendly."""
        exc = AuthorizationError(
            message="Você não tem permissão para realizar esta operação"
        )
        
        # Message should be clear about permission issue
        assert "permissão" in exc.message.lower() or "acesso" in exc.message.lower()
        # Should not reveal system internals
        assert "role" not in exc.message.lower()
        assert "authorization" not in exc.message.lower()


class TestOptimisticLockError:
    """Tests for OptimisticLockError exception."""
    
    def test_optimistic_lock_error_with_versions(self):
        """Test OptimisticLockError with version information."""
        exc = OptimisticLockError(
            message="Record was modified by another user",
            expected_version=1,
            actual_version=2
        )
        
        assert exc.message == "Record was modified by another user"
        assert exc.error_code == "OPTIMISTIC_LOCK_ERROR"
        assert exc.details["expected_version"] == 1
        assert exc.details["actual_version"] == 2
    
    def test_optimistic_lock_error_without_versions(self):
        """Test OptimisticLockError without version information."""
        exc = OptimisticLockError(message="Concurrent modification detected")
        
        assert exc.message == "Concurrent modification detected"
        assert exc.error_code == "OPTIMISTIC_LOCK_ERROR"
        assert "expected_version" not in exc.details
    
    def test_optimistic_lock_error_message_is_user_friendly(self):
        """Test that optimistic lock error messages are user-friendly."""
        exc = OptimisticLockError(
            message="O registro foi modificado por outro usuário. Recarregue e tente novamente."
        )
        
        # Message should explain what happened and what to do
        assert "modificado" in exc.message.lower() or "alterado" in exc.message.lower()
        assert "recarreg" in exc.message.lower() or "tente novamente" in exc.message.lower()
        # Should not contain technical terms
        assert "version" not in exc.message.lower()
        assert "lock" not in exc.message.lower()


class TestDatabaseError:
    """Tests for DatabaseError exception."""
    
    def test_database_error_with_operation(self):
        """Test DatabaseError with operation information."""
        exc = DatabaseError(
            message="Failed to insert record",
            operation="insert"
        )
        
        assert exc.message == "Failed to insert record"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.details["operation"] == "insert"
    
    def test_database_error_without_operation(self):
        """Test DatabaseError without operation information."""
        exc = DatabaseError(message="Database error")
        
        assert exc.message == "Database error"
        assert exc.error_code == "DATABASE_ERROR"
        assert "operation" not in exc.details
    
    def test_database_error_message_is_user_friendly(self):
        """Test that database error messages are user-friendly."""
        exc = DatabaseError(
            message="Erro ao acessar o banco de dados. Tente novamente."
        )
        
        # Message should be generic and not expose database details
        assert "banco de dados" in exc.message.lower() or "database" in exc.message.lower()
        # Should not contain SQL or technical details
        assert "sql" not in exc.message.lower()
        assert "constraint" not in exc.message.lower()
        assert "foreign key" not in exc.message.lower()


class TestCacheError:
    """Tests for CacheError exception."""
    
    def test_cache_error_with_operation(self):
        """Test CacheError with operation information."""
        exc = CacheError(
            message="Failed to get cache value",
            operation="get"
        )
        
        assert exc.message == "Failed to get cache value"
        assert exc.error_code == "CACHE_ERROR"
        assert exc.details["operation"] == "get"
    
    def test_cache_error_without_operation(self):
        """Test CacheError without operation information."""
        exc = CacheError(message="Cache error")
        
        assert exc.message == "Cache error"
        assert exc.error_code == "CACHE_ERROR"
        assert "operation" not in exc.details


class TestConfigurationError:
    """Tests for ConfigurationError exception."""
    
    def test_configuration_error_with_config_key(self):
        """Test ConfigurationError with config key."""
        exc = ConfigurationError(
            message="Missing required configuration",
            config_key="DATABASE_URL"
        )
        
        assert exc.message == "Missing required configuration"
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert exc.details["config_key"] == "DATABASE_URL"
    
    def test_configuration_error_without_config_key(self):
        """Test ConfigurationError without config key."""
        exc = ConfigurationError(message="Invalid configuration")
        
        assert exc.message == "Invalid configuration"
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert "config_key" not in exc.details
    
    def test_configuration_error_message_is_user_friendly(self):
        """Test that configuration error messages are user-friendly."""
        exc = ConfigurationError(
            message="Erro de configuração. Contate o administrador."
        )
        
        # Message should direct user to admin
        assert "configuração" in exc.message.lower() or "configuration" in exc.message.lower()
        assert "administrador" in exc.message.lower() or "admin" in exc.message.lower()


class TestErrorHandler:
    """Tests for ErrorHandler class."""
    
    def test_error_handler_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler()
        assert handler.logger is not None
    
    def test_error_handler_with_custom_logger(self):
        """Test ErrorHandler with custom logger."""
        logger = logging.getLogger("test")
        handler = ErrorHandler(logger=logger)
        assert handler.logger == logger
    
    def test_handle_validation_error(self):
        """Test handling ValidationError."""
        handler = ErrorHandler()
        exc = ValidationError(message="Invalid input", field="email")
        
        result = handler.handle_exception(exc)
        
        assert result["success"] is False
        assert result["error"]["error"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "Invalid input"
        assert result["error"]["details"]["field"] == "email"
        assert "timestamp" in result
    
    def test_handle_not_found_error(self):
        """Test handling NotFoundError."""
        handler = ErrorHandler()
        exc = NotFoundError(
            message="Product not found",
            resource_type="product",
            resource_id=123
        )
        
        result = handler.handle_exception(exc)
        
        assert result["success"] is False
        assert result["error"]["error"] == "NOT_FOUND"
        assert result["error"]["message"] == "Product not found"
    
    def test_handle_authentication_error(self):
        """Test handling AuthenticationError."""
        handler = ErrorHandler()
        exc = AuthenticationError(
            message="Invalid credentials",
            reason="invalid_password"
        )
        
        result = handler.handle_exception(exc)
        
        assert result["success"] is False
        assert result["error"]["error"] == "AUTHENTICATION_ERROR"
    
    def test_handle_database_error(self):
        """Test handling DatabaseError."""
        handler = ErrorHandler()
        exc = DatabaseError(message="Connection failed", operation="connect")
        
        result = handler.handle_exception(exc)
        
        assert result["success"] is False
        assert result["error"]["error"] == "DATABASE_ERROR"
    
    def test_handle_unexpected_exception(self):
        """Test handling unexpected exception."""
        handler = ErrorHandler()
        exc = ValueError("Unexpected error")
        
        result = handler.handle_exception(exc)
        
        assert result["success"] is False
        assert result["error"]["error"] == "INTERNAL_ERROR"
        # Should not expose internal error details
        assert "ValueError" not in result["error"]["message"]
        assert result["error"]["message"] == "An unexpected error occurred. Please try again later."
    
    def test_handle_exception_with_context(self):
        """Test handling exception with context."""
        handler = ErrorHandler()
        exc = ValidationError(message="Invalid input")
        context = {"user_id": 123, "request_id": "abc"}
        
        result = handler.handle_exception(exc, context=context)
        
        assert result["success"] is False
        assert "timestamp" in result
    
    def test_get_user_friendly_message_validation_error(self):
        """Test user-friendly message for ValidationError."""
        handler = ErrorHandler()
        exc = ValidationError(message="Invalid email")
        
        message = handler.get_user_friendly_message(exc)
        
        assert "validação" in message.lower()
        assert "Invalid email" in message
    
    def test_get_user_friendly_message_not_found_error(self):
        """Test user-friendly message for NotFoundError."""
        handler = ErrorHandler()
        exc = NotFoundError(message="Product not found")
        
        message = handler.get_user_friendly_message(exc)
        
        assert "não encontrado" in message.lower()
    
    def test_get_user_friendly_message_insufficient_stock_error(self):
        """Test user-friendly message for InsufficientStockError."""
        handler = ErrorHandler()
        exc = InsufficientStockError(message="Not enough stock")
        
        message = handler.get_user_friendly_message(exc)
        
        assert "estoque insuficiente" in message.lower()
    
    def test_get_user_friendly_message_authorization_error(self):
        """Test user-friendly message for AuthorizationError."""
        handler = ErrorHandler()
        exc = AuthorizationError(message="Access denied")
        
        message = handler.get_user_friendly_message(exc)
        
        assert "permissão" in message.lower()
    
    def test_get_user_friendly_message_optimistic_lock_error(self):
        """Test user-friendly message for OptimisticLockError."""
        handler = ErrorHandler()
        exc = OptimisticLockError(message="Concurrent modification")
        
        message = handler.get_user_friendly_message(exc)
        
        assert "modificado" in message.lower()
        assert "recarregue" in message.lower()
    
    def test_get_user_friendly_message_database_error(self):
        """Test user-friendly message for DatabaseError."""
        handler = ErrorHandler()
        exc = DatabaseError(message="Connection failed")
        
        message = handler.get_user_friendly_message(exc)
        
        assert "banco de dados" in message.lower()
        assert "tente novamente" in message.lower()
    
    def test_get_user_friendly_message_unexpected_error(self):
        """Test user-friendly message for unexpected error."""
        handler = ErrorHandler()
        exc = ValueError("Something went wrong")
        
        message = handler.get_user_friendly_message(exc)
        
        assert "erro inesperado" in message.lower()
        assert "tente novamente" in message.lower()
        # Should not expose internal error details
        assert "ValueError" not in message
        assert "Something went wrong" not in message
    
    def test_should_retry_database_error(self):
        """Test should_retry returns True for DatabaseError."""
        handler = ErrorHandler()
        exc = DatabaseError(message="Connection timeout")
        
        assert handler.should_retry(exc) is True
    
    def test_should_retry_cache_error(self):
        """Test should_retry returns True for CacheError."""
        handler = ErrorHandler()
        exc = CacheError(message="Cache unavailable")
        
        assert handler.should_retry(exc) is True
    
    def test_should_retry_validation_error(self):
        """Test should_retry returns False for ValidationError."""
        handler = ErrorHandler()
        exc = ValidationError(message="Invalid input")
        
        assert handler.should_retry(exc) is False
    
    def test_should_retry_authentication_error(self):
        """Test should_retry returns False for AuthenticationError."""
        handler = ErrorHandler()
        exc = AuthenticationError(message="Invalid credentials")
        
        assert handler.should_retry(exc) is False
    
    def test_should_retry_configuration_error(self):
        """Test should_retry returns False for ConfigurationError."""
        handler = ErrorHandler()
        exc = ConfigurationError(message="Missing config")
        
        assert handler.should_retry(exc) is False
    
    def test_should_retry_unexpected_error(self):
        """Test should_retry returns False for unexpected errors."""
        handler = ErrorHandler()
        exc = ValueError("Unexpected")
        
        assert handler.should_retry(exc) is False
    
    @patch('src.infrastructure.error_handler.logging.getLogger')
    def test_error_handler_logs_validation_error_at_info_level(self, mock_get_logger):
        """Test that ValidationError is logged at INFO level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ErrorHandler(logger=mock_logger)
        exc = ValidationError(message="Invalid input")
        
        handler.handle_exception(exc)
        
        mock_logger.info.assert_called_once()
    
    @patch('src.infrastructure.error_handler.logging.getLogger')
    def test_error_handler_logs_authentication_error_at_warning_level(self, mock_get_logger):
        """Test that AuthenticationError is logged at WARNING level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ErrorHandler(logger=mock_logger)
        exc = AuthenticationError(message="Invalid credentials")
        
        handler.handle_exception(exc)
        
        mock_logger.warning.assert_called_once()
    
    @patch('src.infrastructure.error_handler.logging.getLogger')
    def test_error_handler_logs_database_error_at_error_level(self, mock_get_logger):
        """Test that DatabaseError is logged at ERROR level."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ErrorHandler(logger=mock_logger)
        exc = DatabaseError(message="Connection failed")
        
        handler.handle_exception(exc)
        
        mock_logger.error.assert_called_once()
    
    @patch('src.infrastructure.error_handler.logging.getLogger')
    def test_error_handler_logs_unexpected_error_with_stack_trace(self, mock_get_logger):
        """Test that unexpected errors are logged with stack trace."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ErrorHandler(logger=mock_logger)
        exc = ValueError("Unexpected error")
        
        handler.handle_exception(exc)
        
        # Should log with exc_info=True to include stack trace
        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        assert call_kwargs.get('exc_info') is True


class TestErrorMessageQuality:
    """Tests to ensure error messages are user-friendly across all exception types."""
    
    def test_all_error_messages_are_in_portuguese_or_english(self):
        """Test that error messages don't mix languages inappropriately."""
        handler = ErrorHandler()
        
        exceptions = [
            ValidationError(message="Campo inválido"),
            NotFoundError(message="Produto não encontrado"),
            DuplicateError(message="SKU já existe"),
            InsufficientStockError(message="Estoque insuficiente"),
            AuthenticationError(message="Credenciais inválidas"),
            AuthorizationError(message="Sem permissão"),
            OptimisticLockError(message="Registro modificado"),
            DatabaseError(message="Erro no banco de dados"),
            CacheError(message="Erro no cache"),
            ConfigurationError(message="Erro de configuração")
        ]
        
        for exc in exceptions:
            message = handler.get_user_friendly_message(exc)
            # Message should exist and be non-empty
            assert message
            assert len(message) > 0
    
    def test_error_messages_do_not_expose_technical_details(self):
        """Test that error messages don't expose technical implementation details."""
        technical_terms = [
            "exception", "stack trace", "traceback", "sql", "query",
            "constraint", "foreign key", "primary key", "index",
            "bcrypt", "hash", "token", "session_id", "connection pool"
        ]
        
        handler = ErrorHandler()
        
        exceptions = [
            ValidationError(message="O email fornecido é inválido"),
            NotFoundError(message="O produto solicitado não foi encontrado"),
            DatabaseError(message="Erro ao acessar dados"),
            AuthenticationError(message="Usuário ou senha incorretos")
        ]
        
        for exc in exceptions:
            message = handler.get_user_friendly_message(exc).lower()
            for term in technical_terms:
                assert term not in message, f"Technical term '{term}' found in message: {message}"
    
    def test_error_messages_provide_actionable_guidance(self):
        """Test that error messages provide guidance on what to do next."""
        handler = ErrorHandler()
        
        # OptimisticLockError should tell user to reload
        exc = OptimisticLockError(message="Record modified")
        message = handler.get_user_friendly_message(exc)
        assert "recarregue" in message.lower() or "tente novamente" in message.lower()
        
        # DatabaseError should tell user to try again
        exc = DatabaseError(message="Connection failed")
        message = handler.get_user_friendly_message(exc)
        assert "tente novamente" in message.lower()
        
        # ConfigurationError should tell user to contact admin
        exc = ConfigurationError(message="Invalid config")
        message = handler.get_user_friendly_message(exc)
        assert "administrador" in message.lower() or "contate" in message.lower()
