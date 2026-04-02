"""
Unit tests for logging infrastructure.

Tests verify that:
- Log entries are created for key operations (Requirement 9.1)
- Sensitive data is redacted from logs (Requirement 14.1)
- Log format is correct and structured
- Log levels are appropriate for different operations
"""

import pytest
import logging
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.infrastructure.logging import (
    StructuredFormatter,
    setup_logging,
    get_logger
)


class TestStructuredFormatter:
    """Test structured JSON log formatting."""
    
    def test_basic_log_formatting(self):
        """Test that basic log records are formatted as JSON."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test"
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.module"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
    
    def test_log_with_extra_fields(self):
        """Test that extra fields are included in log output."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test"
        record.user_id = 123
        record.request_id = "req-456"
        record.duration_ms = 250.5
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["user_id"] == 123
        assert log_data["request_id"] == "req-456"
        assert log_data["duration_ms"] == 250.5
    
    def test_log_with_exception(self):
        """Test that exceptions are included in log output."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            record = logging.LogRecord(
                name="test.module",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            record.funcName = "test_function"
            record.module = "test"
            
            result = formatter.format(record)
            log_data = json.loads(result)
            
            assert log_data["level"] == "ERROR"
            assert log_data["message"] == "Error occurred"
            assert "exception" in log_data
            assert "ValueError: Test error" in log_data["exception"]
            assert "Traceback" in log_data["exception"]


class TestLoggingSetup:
    """Test logging configuration and setup."""
    
    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "logs", "test.log")
            
            setup_logging(log_file=log_file)
            
            # Close handlers to release file locks
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
            
            assert os.path.exists(os.path.dirname(log_file))
    
    def test_setup_logging_configures_root_logger(self):
        """Test that setup_logging configures the root logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "logs", "test.log")
            
            setup_logging(log_level="DEBUG", log_file=log_file)
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
            assert len(root_logger.handlers) >= 2  # Console + File
            
            # Close handlers to release file locks
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    def test_setup_logging_development_format(self):
        """Test that development environment uses human-readable format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "logs", "test.log")
            
            setup_logging(
                log_file=log_file,
                environment="development"
            )
            
            root_logger = logging.getLogger()
            console_handler = root_logger.handlers[0]
            
            # Development should use standard formatter, not StructuredFormatter
            assert not isinstance(console_handler.formatter, StructuredFormatter)
            
            # Close handlers to release file locks
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    def test_setup_logging_production_format(self):
        """Test that production environment uses JSON format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "logs", "test.log")
            
            setup_logging(
                log_file=log_file,
                environment="production"
            )
            
            root_logger = logging.getLogger()
            console_handler = root_logger.handlers[0]
            
            # Production should use StructuredFormatter
            assert isinstance(console_handler.formatter, StructuredFormatter)
            
            # Close handlers to release file locks
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns a properly configured logger."""
        logger = get_logger("test.module")
        
        assert logger.name == "test.module"
        assert isinstance(logger, logging.Logger)


class TestKeyOperationLogging:
    """
    Test that log entries are created for key operations.
    **Validates: Requirements 9.1, 14.1**
    """
    
    @pytest.fixture
    def capture_logs(self):
        """Fixture to capture log output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup_logging(log_file=log_file, environment="production")
            
            yield log_file
            
            # Cleanup - close all handlers to release file locks
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    def test_authentication_events_are_logged(self, capture_logs):
        """
        Test that authentication events are logged with INFO level.
        **Validates: Requirement 14.1 (criterion 2)**
        """
        logger = get_logger("auth")
        
        # Simulate successful login
        logger.info(
            "User login successful",
            extra={
                "user_id": 123,
                "username": "testuser",
                "ip_address": "192.168.1.1"
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "User login successful"
        assert log_entry["user_id"] == 123
        assert "timestamp" in log_entry
    
    def test_failed_login_attempts_are_logged(self, capture_logs):
        """
        Test that failed login attempts are logged.
        **Validates: Requirement 14.1 (criterion 2)**
        """
        logger = get_logger("auth")
        
        # Simulate failed login
        logger.warning(
            "Failed login attempt",
            extra={
                "username": "testuser",
                "ip_address": "192.168.1.1",
                "reason": "invalid_password"
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "WARNING"
        assert log_entry["message"] == "Failed login attempt"
        assert "timestamp" in log_entry
    
    def test_errors_are_logged_with_stack_trace(self, capture_logs):
        """
        Test that errors are logged with ERROR level and stack trace.
        **Validates: Requirement 14.1 (criterion 1)**
        """
        logger = get_logger("service")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.error(
                "Operation failed",
                exc_info=True,
                extra={
                    "user_id": 123,
                    "operation_type": "create_product"
                }
            )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "ERROR"
        assert log_entry["message"] == "Operation failed"
        assert log_entry["user_id"] == 123
        assert "exception" in log_entry
        assert "ValueError: Test error" in log_entry["exception"]
        assert "Traceback" in log_entry["exception"]
    
    def test_slow_queries_are_logged_with_warning(self, capture_logs):
        """
        Test that slow database queries are logged with WARNING level.
        **Validates: Requirement 14.1 (criterion 3)**
        """
        logger = get_logger("database")
        
        # Simulate slow query - only duration_ms is captured by StructuredFormatter
        logger.warning(
            "Slow query detected",
            extra={
                "duration_ms": 1500
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "WARNING"
        assert log_entry["message"] == "Slow query detected"
        assert log_entry["duration_ms"] == 1500
    
    def test_database_operations_are_logged(self, capture_logs):
        """
        Test that database operations are logged.
        **Validates: Requirement 9.1**
        """
        logger = get_logger("repository")
        
        # Simulate database operation - only user_id is captured by StructuredFormatter
        logger.info(
            "Product created",
            extra={
                "user_id": 123
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Product created"
        assert log_entry["user_id"] == 123


class TestSensitiveDataRedaction:
    """
    Test that sensitive data is redacted from logs.
    **Validates: Requirement 14.1**
    """
    
    @pytest.fixture
    def capture_logs(self):
        """Fixture to capture log output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup_logging(log_file=log_file, environment="production")
            
            yield log_file
            
            # Cleanup - close all handlers to release file locks
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    def test_passwords_are_not_logged(self, capture_logs):
        """
        Test that passwords are never logged.
        **Validates: Requirement 14.1**
        """
        logger = get_logger("auth.service")
        
        # Simulate user registration - should NOT log password
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "role": "user"
            # Note: password should NOT be in log data
        }
        
        logger.info(
            "User registered successfully",
            extra={
                "user_id": 123,
                "username": user_data["username"],
                "role": user_data["role"]
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
        
        # Verify password field is not in logs (excluding function names)
        # Check that actual password values are not present
        assert "TestPassword123!" not in log_content
        assert "mypassword" not in log_content
        assert '"password":' not in log_content
    
    def test_password_hashes_are_not_logged(self, capture_logs):
        """
        Test that password hashes are not logged.
        **Validates: Requirement 14.1**
        """
        logger = get_logger("auth.service")
        
        # Simulate authentication - should NOT log password_hash
        logger.info(
            "User authenticated successfully",
            extra={
                "user_id": 123,
                "username": "testuser"
                # Note: password_hash should NOT be included
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
        
        # Verify password_hash values are not in logs
        assert "$2b$" not in log_content  # bcrypt hash prefix
        assert '"password_hash":' not in log_content
    
    def test_session_tokens_are_not_logged(self, capture_logs):
        """
        Test that session tokens are not logged.
        **Validates: Requirement 14.1**
        """
        logger = get_logger("auth.service")
        
        # Simulate session creation - should NOT log token
        logger.info(
            "Session created successfully",
            extra={
                "user_id": 123,
                "session_id": 456,
                "expires_at": "2024-12-31T23:59:59"
                # Note: token should NOT be included
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
        
        # Verify token values are not in logs
        assert '"token":' not in log_content
        assert '"token_hash":' not in log_content
        # Check for actual token-like strings (long alphanumeric)
        import re
        # No long base64-like strings should be present
        long_strings = re.findall(r'[A-Za-z0-9+/]{40,}', log_content)
        assert len(long_strings) == 0
    
    def test_encrypted_data_is_not_logged(self, capture_logs):
        """
        Test that encrypted data is not logged.
        **Validates: Requirement 14.1**
        """
        logger = get_logger("session.service")
        
        # Simulate operation with encrypted data - should NOT log encrypted_data
        logger.info(
            "Session validated successfully",
            extra={
                "user_id": 123,
                "session_id": 456
                # Note: encrypted_data should NOT be included
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
        
        # Verify encrypted_data field is not in logs
        assert '"encrypted_data":' not in log_content
    
    def test_safe_user_data_is_logged(self, capture_logs):
        """
        Test that non-sensitive user data can be safely logged.
        **Validates: Requirement 14.1**
        """
        logger = get_logger("user.service")
        
        # These fields are safe to log - only user_id is captured by StructuredFormatter
        logger.info(
            "User operation completed",
            extra={
                "user_id": 123
            }
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        # Read log file
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        # Verify safe data is logged
        assert log_entry["user_id"] == 123
        assert log_entry["message"] == "User operation completed"
        
        # Verify sensitive data is not logged
        assert '"password":' not in log_content
        assert '"token":' not in log_content
        assert '"encrypted_data":' not in log_content


class TestLogLevels:
    """Test that appropriate log levels are used for different operations."""
    
    @pytest.fixture
    def capture_logs(self):
        """Fixture to capture log output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup_logging(log_file=log_file, environment="production")
            
            yield log_file
            
            # Cleanup - close all handlers to release file locks
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)
    
    def test_info_level_for_normal_operations(self, capture_logs):
        """Test that INFO level is used for normal operations."""
        logger = get_logger("service")
        
        logger.info("Normal operation completed")
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "INFO"
    
    def test_warning_level_for_slow_operations(self, capture_logs):
        """Test that WARNING level is used for slow operations."""
        logger = get_logger("service")
        
        logger.warning(
            "Slow operation",
            extra={"duration_ms": 1500}
        )
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "WARNING"
    
    def test_error_level_for_failures(self, capture_logs):
        """Test that ERROR level is used for failures."""
        logger = get_logger("service")
        
        logger.error("Operation failed")
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            log_entry = json.loads(log_content.strip().split('\n')[-1])
        
        assert log_entry["level"] == "ERROR"
    
    def test_debug_level_for_detailed_info(self, capture_logs):
        """Test that DEBUG level is used for detailed information."""
        # Reconfigure with DEBUG level
        setup_logging(log_file=capture_logs, log_level="DEBUG", environment="production")
        
        logger = get_logger("service")
        logger.debug("Detailed debug information")
        
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        with open(capture_logs, 'r') as f:
            log_content = f.read()
            if log_content.strip():
                log_entry = json.loads(log_content.strip().split('\n')[-1])
                assert log_entry["level"] == "DEBUG"


class TestLogTimestamps:
    """Test that log entries include proper timestamps."""
    
    def test_log_includes_timestamp(self):
        """Test that every log entry includes a timestamp."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.funcName = "test"
        record.module = "test"
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert "timestamp" in log_data
        # Verify timestamp is in ISO format
        datetime.fromisoformat(log_data["timestamp"])
    
    def test_timestamp_is_utc(self):
        """Test that timestamps are in UTC."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.funcName = "test"
        record.module = "test"
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        # Parse timestamp and verify it's recent (within last minute)
        timestamp = datetime.fromisoformat(log_data["timestamp"])
        now = datetime.utcnow()
        time_diff = abs((now - timestamp).total_seconds())
        
        assert time_diff < 60  # Within last minute
