"""Script to migrate products to new schema with version control."""

import asyncio
import asyncpg
import os
from datetime import datetime


async def migrate_products():
    """Migrate products to add version column and verify constraints."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    print("🔄 Starting product migration...")
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Check if version column exists
        check_column = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products' AND column_name = 'version'
        """
        has_version = await conn.fetchval(check_column)
        
        if not has_version:
            print("❌ Version column not found. Run Alembic migrations first:")
            print("   alembic upgrade head")
            await conn.close()
            return False
        
        # Get products without version
        count_query = """
            SELECT COUNT(*) FROM products WHERE version IS NULL OR version = 0
        """
        count = await conn.fetchval(count_query)
        
        if count == 0:
            print("✅ All products already migrated")
            await conn.close()
            return True
        
        print(f"📦 Found {count} products to migrate")
        
        # Update products with version=1
        update_query = """
            UPDATE products 
            SET version = 1,
                updated_at = NOW()
            WHERE version IS NULL OR version = 0
        """
        
        result = await conn.execute(update_query)
        print(f"✅ Updated {count} products with version=1")
        
        # Verify constraints
        print("🔍 Verifying constraints...")
        
        # Check for negative quantities
        negative_qty = await conn.fetch("""
            SELECT id, sku, quantity 
            FROM products 
            WHERE quantity < 0 AND deleted_at IS NULL
        """)
        
        if negative_qty:
            print(f"⚠️  Found {len(negative_qty)} products with negative quantity:")
            for row in negative_qty[:5]:  # Show first 5
                print(f"   - ID {row['id']}: {row['sku']} (qty: {row['quantity']})")
            
            # Fix negative quantities
            fix_qty = input("\n🔧 Fix negative quantities to 0? (y/n): ")
            if fix_qty.lower() == 'y':
                await conn.execute("""
                    UPDATE products 
                    SET quantity = 0, updated_at = NOW()
                    WHERE quantity < 0 AND deleted_at IS NULL
                """)
                print("✅ Fixed negative quantities")
        
        # Check for invalid prices
        invalid_price = await conn.fetch("""
            SELECT id, sku, price 
            FROM products 
            WHERE price <= 0 AND deleted_at IS NULL
        """)
        
        if invalid_price:
            print(f"⚠️  Found {len(invalid_price)} products with invalid price:")
            for row in invalid_price[:5]:
                print(f"   - ID {row['id']}: {row['sku']} (price: {row['price']})")
            print("   ⚠️  Manual review required for pricing")
        
        # Add low_stock_threshold if missing
        await conn.execute("""
            UPDATE products 
            SET low_stock_threshold = 10
            WHERE low_stock_threshold IS NULL AND deleted_at IS NULL
        """)
        
        await conn.close()
        
        print("\n✅ Product migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(migrate_products())
    exit(0 if success else 1)
