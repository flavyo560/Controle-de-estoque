"""Performance logging decorators and utilities."""

import time
import logging
import functools
from typing import Callable, Any
import asyncio


logger = logging.getLogger(__name__)


def log_performance(operation_name: str, threshold_ms: int = 1000):
    """
    Decorator to log operation performance.
    
    Logs execution time and warns if operation exceeds threshold.
    
    Args:
        operation_name: Name of the operation for logging
        threshold_ms: Threshold in milliseconds for slow operation warning
    
    Usage:
        @log_performance("create_product", threshold_ms=500)
        async def create_product(self, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation: {operation_name}",
                        extra={
                            "operation": operation_name,
                            "duration_ms": round(duration_ms, 2),
                            "threshold_ms": threshold_ms,
                            "args_count": len(args),
                            "kwargs_keys": list(kwargs.keys())
                        }
                    )
                else:
                    logger.debug(
                        f"Operation completed: {operation_name}",
                        extra={
                            "operation": operation_name,
                            "duration_ms": round(duration_ms, 2)
                        }
                    )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra={
                        "operation": operation_name,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                
                if duration_ms > threshold_ms:
                    logger.warning(
                        f"Slow operation: {operation_name}",
                        extra={
                            "operation": operation_name,
                            "duration_ms": round(duration_ms, 2),
                            "threshold_ms": threshold_ms
                        }
                    )
                else:
                    logger.debug(
                        f"Operation completed: {operation_name}",
                        extra={
                            "operation": operation_name,
                            "duration_ms": round(duration_ms, 2)
                        }
                    )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation failed: {operation_name}",
                    extra={
                        "operation": operation_name,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_query(query_name: str):
    """
    Decorator to log database queries with execution time.
    
    Args:
        query_name: Name of the query for logging
    
    Usage:
        @log_query("get_product_by_id")
        async def get_by_id(self, id: int):
            ...
    """
    return log_performance(f"query:{query_name}", threshold_ms=100)
