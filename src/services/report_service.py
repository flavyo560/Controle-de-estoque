"""
Report service for generating business reports with data accuracy.

This module provides reporting functionality with:
- Sales reports with date range filtering and grouping
- Inventory reports with stock levels and movements
- Revenue reports with payment method breakdown
- Database aggregation for accuracy
- Caching with invalidation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from src.repositories.sale_repository import SaleRepository
from src.repositories.product_repository import ProductRepository
from src.infrastructure.cache import CacheManager
from src.infrastructure.database import DatabaseClient


class ReportService:
    """Service for generating business reports."""
    
    def __init__(
        self,
        sale_repo: SaleRepository,
        product_repo: ProductRepository,
        cache: CacheManager,
        db: DatabaseClient
    ):
        """
        Initialize report service.
        
        Args:
            sale_repo: Sale repository
            product_repo: Product repository
            cache: Cache manager
            db: Database client for direct queries
        """
        self.sale_repo = sale_repo
        self.product_repo = product_repo
        self.cache = cache
        self.db = db
    
    async def get_sales_report(
        self,
        start_date: date,
        end_date: date,
        group_by: str = "day"
    ) -> Dict[str, Any]:
        """
        Generate sales report with date range filtering and grouping.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            group_by: Grouping period (day, week, month)
            
        Returns:
            Dictionary containing:
            - total_sales: Total number of sales
            - total_revenue: Total revenue amount
            - average_sale: Average sale amount
            - sales_by_period: List of sales grouped by period
            - start_date: Report start date
            - end_date: Report end date
        """
        # Check cache first
        cache_key = f"sales_report:{start_date}:{end_date}:{group_by}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Query database with aggregation
        query = """
            SELECT 
                COUNT(*) as total_sales,
                COALESCE(SUM(final_amount), 0) as total_revenue,
                COALESCE(AVG(final_amount), 0) as average_sale
            FROM sales
            WHERE created_at::date >= $1 
                AND created_at::date <= $2
                AND status = 'completed'
                AND deleted_at IS NULL
        """
        
        result = await self.db.fetch_one(query, start_date, end_date)
        
        # Get sales grouped by period
        if group_by == "day":
            date_trunc = "day"
        elif group_by == "week":
            date_trunc = "week"
        elif group_by == "month":
            date_trunc = "month"
        else:
            date_trunc = "day"
        
        period_query = f"""
            SELECT 
                DATE_TRUNC('{date_trunc}', created_at) as period,
                COUNT(*) as sales_count,
                COALESCE(SUM(final_amount), 0) as revenue
            FROM sales
            WHERE created_at::date >= $1 
                AND created_at::date <= $2
                AND status = 'completed'
                AND deleted_at IS NULL
            GROUP BY period
            ORDER BY period
        """
        
        period_results = await self.db.fetch_all(period_query, start_date, end_date)
        
        report = {
            "total_sales": result["total_sales"],
            "total_revenue": float(result["total_revenue"]),
            "average_sale": float(result["average_sale"]),
            "sales_by_period": [
                {
                    "period": row["period"].isoformat() if isinstance(row["period"], datetime) else str(row["period"]),
                    "sales_count": row["sales_count"],
                    "revenue": float(row["revenue"])
                }
                for row in period_results
            ],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by
        }
        
        # Cache for 1 hour
        await self.cache.set(cache_key, report, ttl=3600)
        
        return report
    
    async def get_inventory_report(
        self,
        include_movements: bool = False
    ) -> Dict[str, Any]:
        """
        Generate inventory report with stock levels and movements.
        
        Args:
            include_movements: Whether to include recent movements
            
        Returns:
            Dictionary containing:
            - total_products: Total number of products
            - total_stock_value: Total value of inventory
            - low_stock_count: Number of products below minimum stock
            - products: List of products with stock info
            - movements: Optional list of recent movements
        """
        # Check cache first
        cache_key = f"inventory_report:{include_movements}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Query for inventory summary
        summary_query = """
            SELECT 
                COUNT(*) as total_products,
                COALESCE(SUM(quantity * price), 0) as total_stock_value,
                COUNT(*) FILTER (WHERE quantity < min_stock) as low_stock_count
            FROM products
            WHERE deleted_at IS NULL
        """
        
        summary = await self.db.fetch_one(summary_query)
        
        # Query for product details
        products_query = """
            SELECT 
                id,
                sku,
                name,
                quantity,
                min_stock,
                price,
                (quantity * price) as stock_value
            FROM products
            WHERE deleted_at IS NULL
            ORDER BY name
        """
        
        products = await self.db.fetch_all(products_query)
        
        report = {
            "total_products": summary["total_products"],
            "total_stock_value": float(summary["total_stock_value"]),
            "low_stock_count": summary["low_stock_count"],
            "products": [
                {
                    "id": p["id"],
                    "sku": p["sku"],
                    "name": p["name"],
                    "quantity": p["quantity"],
                    "min_stock": p["min_stock"],
                    "price": float(p["price"]),
                    "stock_value": float(p["stock_value"]),
                    "is_low_stock": p["quantity"] < p["min_stock"]
                }
                for p in products
            ]
        }
        
        # Include movements if requested
        if include_movements:
            movements_query = """
                SELECT 
                    im.id,
                    im.product_id,
                    p.sku,
                    p.name as product_name,
                    im.movement_type,
                    im.quantity_change,
                    im.quantity_before,
                    im.quantity_after,
                    im.created_at
                FROM inventory_movements im
                JOIN products p ON im.product_id = p.id
                WHERE im.created_at >= NOW() - INTERVAL '30 days'
                ORDER BY im.created_at DESC
                LIMIT 100
            """
            
            movements = await self.db.fetch_all(movements_query)
            report["movements"] = [
                {
                    "id": m["id"],
                    "product_id": m["product_id"],
                    "sku": m["sku"],
                    "product_name": m["product_name"],
                    "movement_type": m["movement_type"],
                    "quantity_change": m["quantity_change"],
                    "quantity_before": m["quantity_before"],
                    "quantity_after": m["quantity_after"],
                    "created_at": m["created_at"].isoformat()
                }
                for m in movements
            ]
        
        # Cache for 5 minutes
        await self.cache.set(cache_key, report, ttl=300)
        
        return report
    
    async def get_revenue_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate revenue report with payment method breakdown.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Dictionary containing:
            - total_revenue: Total revenue
            - payment_methods: Breakdown by payment method
            - start_date: Report start date
            - end_date: Report end date
        """
        # Check cache first
        cache_key = f"revenue_report:{start_date}:{end_date}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Query for total revenue
        total_query = """
            SELECT COALESCE(SUM(final_amount), 0) as total_revenue
            FROM sales
            WHERE created_at::date >= $1 
                AND created_at::date <= $2
                AND status = 'completed'
                AND deleted_at IS NULL
        """
        
        total_result = await self.db.fetch_one(total_query, start_date, end_date)
        
        # Query for payment method breakdown
        payment_query = """
            SELECT 
                p.payment_method,
                COUNT(DISTINCT p.sale_id) as transaction_count,
                COALESCE(SUM(p.amount), 0) as total_amount
            FROM payments p
            JOIN sales s ON p.sale_id = s.id
            WHERE s.created_at::date >= $1 
                AND s.created_at::date <= $2
                AND s.status = 'completed'
                AND s.deleted_at IS NULL
            GROUP BY p.payment_method
            ORDER BY total_amount DESC
        """
        
        payment_results = await self.db.fetch_all(payment_query, start_date, end_date)
        
        report = {
            "total_revenue": float(total_result["total_revenue"]),
            "payment_methods": [
                {
                    "method": row["payment_method"],
                    "transaction_count": row["transaction_count"],
                    "total_amount": float(row["total_amount"]),
                    "percentage": (float(row["total_amount"]) / float(total_result["total_revenue"]) * 100) 
                                  if float(total_result["total_revenue"]) > 0 else 0
                }
                for row in payment_results
            ],
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        # Cache for 1 hour
        await self.cache.set(cache_key, report, ttl=3600)
        
        return report
    
    async def invalidate_report_cache(self) -> None:
        """Invalidate all report caches when data changes."""
        await self.cache.invalidate_pattern("sales_report:*")
        await self.cache.invalidate_pattern("inventory_report:*")
        await self.cache.invalidate_pattern("revenue_report:*")
