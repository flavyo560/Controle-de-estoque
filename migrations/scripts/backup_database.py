"""Script to backup database before migration."""

import asyncio
import asyncpg
from datetime import datetime
import os
from pathlib import Path


async def backup_database():
    """Create a backup of the database."""
    # Load database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return False
    
    # Create backups directory
    backup_dir = Path("migrations/backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.sql"
    
    print(f"🔄 Creating backup: {backup_file}")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Get all tables
        tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """
        tables = await conn.fetch(tables_query)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Database Backup\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n")
            f.write(f"-- Tables: {len(tables)}\n\n")
            
            for table in tables:
                table_name = table['tablename']
                print(f"  📦 Backing up table: {table_name}")
                
                # Get table data
                rows = await conn.fetch(f"SELECT * FROM {table_name}")
                
                if rows:
                    f.write(f"\n-- Table: {table_name} ({len(rows)} rows)\n")
                    
                    # Get column names
                    columns = list(rows[0].keys())
                    
                    for row in rows:
                        values = []
                        for col in columns:
                            val = row[col]
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                # Escape single quotes
                                escaped = val.replace("'", "''")
                                values.append(f"'{escaped}'")
                            elif isinstance(val, datetime):
                                values.append(f"'{val.isoformat()}'")
                            else:
                                values.append(str(val))
                        
                        f.write(
                            f"INSERT INTO {table_name} ({', '.join(columns)}) "
                            f"VALUES ({', '.join(values)});\n"
                        )
        
        await conn.close()
        
        print(f"✅ Backup created successfully: {backup_file}")
        print(f"📊 Size: {backup_file.stat().st_size / 1024:.2f} KB")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False


if __name__ == "__main__":
    # Load .env
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(backup_database())
    exit(0 if success else 1)
