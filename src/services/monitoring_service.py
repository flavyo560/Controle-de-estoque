"""Monitoring service for system health and performance metrics."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from src.infrastructure.database import DatabaseClient
from src.infrastructure.cache import CacheManager


logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring system health and performance."""
    
    def __init__(self, db_client: DatabaseClient, cache: CacheManager):
        """
        Initialize monitoring service.
        
        Args:
            db_client: Database client for health checks
            cache: Cache manager for cache metrics
        """
        self.db = db_client
        self.cache = cache
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health status.
        
        Returns:
            Dictionary with health status of all components
        """
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check database health
        try:
            await self.db.fetch_val("SELECT 1")
            health["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection OK"
            }
        except Exception as e:
            health["status"] = "unhealthy"
            health["components"]["database"] = {
                "status": "unhealthy",
                "message": f"Database error: {str(e)}"
            }
            logger.error(f"Database health check failed: {e}")
        
        # Check cache health
        try:
            test_key = "_health_check_"
            await self.cache.set(test_key, "ok", ttl=10)
            result = await self.cache.get(test_key)
            await self.cache.delete(test_key)
            
            if result == "ok":
                health["components"]["cache"] = {
                    "status": "healthy",
                    "message": "Cache connection OK"
                }
            else:
                health["status"] = "degraded"
                health["components"]["cache"] = {
                    "status": "degraded",
                    "message": "Cache read/write mismatch"
                }
        except Exception as e:
            health["status"] = "degraded"
            health["components"]["cache"] = {
                "status": "unhealthy",
                "message": f"Cache error: {str(e)}"
            }
            logger.error(f"Cache health check failed: {e}")
        
        return health
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "database": await self._get_database_metrics(),
            "cache": await self._get_cache_metrics()
        }
        
        return metrics
    
    async def get_business_metrics(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get business metrics for the last N hours.
        
        Args:
            hours: Number of hours to look back (default: 24)
            
        Returns:
            Dictionary with business metrics
        """
        start_time = datetime.now() - timedelta(hours=hours)
        
        # Sales metrics
        sales_query = """
            SELECT 
                COUNT(*) as total_sales,
                COALESCE(SUM(final_amount), 0) as total_revenue,
                COALESCE(AVG(final_amount), 0) as avg_sale_value,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sales,
                COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_sales
            FROM sales
            WHERE created_at >= $1
        """
        sales_data = await self.db.fetch_one(sales_query, start_time)
        
        # Low stock products
        low_stock_query = """
            SELECT COUNT(*) as low_stock_count
            FROM products
            WHERE quantity <= low_stock_threshold
              AND deleted_at IS NULL
        """
        low_stock_data = await self.db.fetch_one(low_stock_query)
        
        # Active users (users who logged in recently)
        active_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM sessions
            WHERE created_at >= $1
        """
        active_users_data = await self.db.fetch_one(active_users_query, start_time)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "period_hours": hours,
            "sales": {
                "total": sales_data["total_sales"],
                "completed": sales_data["completed_sales"],
                "cancelled": sales_data["cancelled_sales"],
                "total_revenue": float(sales_data["total_revenue"]),
                "avg_sale_value": float(sales_data["avg_sale_value"])
            },
            "inventory": {
                "low_stock_products": low_stock_data["low_stock_count"]
            },
            "users": {
                "active_users": active_users_data["active_users"]
            }
        }
    
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """
        Get database performance metrics.
        
        Returns:
            Dictionary with database metrics
        """
        try:
            # Get connection pool stats (if available)
            pool_stats = {
                "status": "available"
            }
            
            # Get slow queries count (from logs or monitoring table if exists)
            # This is a placeholder - implement based on your logging strategy
            slow_queries = {
                "count": 0,
                "threshold_ms": 1000
            }
            
            return {
                "pool": pool_stats,
                "slow_queries": slow_queries
            }
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {"error": str(e)}
    
    async def _get_cache_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.
        
        Returns:
            Dictionary with cache metrics
        """
        try:
            # For memory cache, we can track hits/misses
            # For Redis, we can get INFO stats
            
            if self.cache.backend == "memory":
                return {
                    "backend": "memory",
                    "entries": len(self.cache._memory_cache),
                    "status": "active"
                }
            elif self.cache.backend == "redis":
                # Get Redis INFO if available
                try:
                    info = await self.cache.redis.info()
                    return {
                        "backend": "redis",
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory": info.get("used_memory_human", "unknown"),
                        "status": "active"
                    }
                except:
                    return {
                        "backend": "redis",
                        "status": "unknown"
                    }
            
            return {"backend": self.cache.backend}
        except Exception as e:
            logger.error(f"Failed to get cache metrics: {e}")
            return {"error": str(e)}
    
    async def get_audit_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get audit trail summary for the last N hours.
        
        Args:
            hours: Number of hours to look back (default: 24)
            
        Returns:
            Dictionary with audit summary
        """
        start_time = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT 
                operation,
                table_name,
                COUNT(*) as count
            FROM audit_log
            WHERE created_at >= $1
            GROUP BY operation, table_name
            ORDER BY count DESC
        """
        
        rows = await self.db.fetch_all(query, start_time)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "period_hours": hours,
            "operations": [
                {
                    "operation": row["operation"],
                    "table": row["table_name"],
                    "count": row["count"]
                }
                for row in rows
            ]
        }
