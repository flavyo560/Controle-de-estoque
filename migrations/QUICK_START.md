# Quick Start Guide - Database Migrations

## Prerequisites

1. **Install Dependencies:**
   ```bash
   pip install alembic sqlalchemy asyncpg psycopg2-binary python-dotenv
   ```

2. **Set Environment Variables:**
   
   Add to your `.env` file:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_DB_PASSWORD=your-database-password
   ```

   To get your database password:
   - Go to Supabase Dashboard
   - Navigate to: Project Settings → Database
   - Copy the database password (NOT the API key)

## Running Migrations

### First Time Setup

```bash
# Check current database version
alembic current

# View pending migrations
alembic history --verbose

# Apply all migrations
alembic upgrade head
```

### Expected Output

```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_schema_constraints
✓ Migration 001: Enhanced schema constraints applied successfully
INFO  [alembic.runtime.migration] Running upgrade 001_schema_constraints -> 002_audit_log
✓ Migration 002: Audit log table and triggers created successfully
INFO  [alembic.runtime.migration] Running upgrade 002_audit_log -> 003_performance_indexes
✓ Migration 003: Performance indexes created successfully
INFO  [alembic.runtime.migration] Running upgrade 003_performance_indexes -> 004_sessions_users
✓ Migration 004: Sessions table and user security fields created successfully
INFO  [alembic.runtime.migration] Running upgrade 004_sessions_users -> 005_inventory_movements
✓ Migration 005: Inventory movements table created successfully
```

## Verification

After running migrations, verify the changes:

```sql
-- Check if new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('audit_log', 'sessions', 'inventory_movements');

-- Check if new columns were added to produtos
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'produtos' 
AND column_name IN ('version', 'deleted_at', 'updated_at');

-- Check if constraints were added
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'produtos';

-- Check if indexes were created
SELECT indexname FROM pg_indexes 
WHERE tablename = 'produtos';
```

## Troubleshooting

### Connection Error

**Problem:** `Connection refused` or `could not connect to server`

**Solution:**
1. Verify `SUPABASE_URL` is correct
2. Verify `SUPABASE_DB_PASSWORD` is the database password, not API key
3. Check if your IP is allowed in Supabase (Database → Settings → Network)

### Migration Already Applied

**Problem:** `Target database is not up to date`

**Solution:**
```bash
# Check current version
alembic current

# If migrations are already applied, you'll see:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# 005_inventory_movements (head)
```

### Rollback a Migration

**Problem:** Need to undo a migration

**Solution:**
```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 003_performance_indexes

# Rollback all migrations
alembic downgrade base
```

## Common Commands

```bash
# Show current database version
alembic current

# Show migration history
alembic history

# Show detailed migration history
alembic history --verbose

# Apply all pending migrations
alembic upgrade head

# Apply one migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Show SQL without executing
alembic upgrade head --sql
```

## What Each Migration Does

| Migration | Description |
|-----------|-------------|
| 001 | Adds version columns, check constraints, unique constraints |
| 002 | Creates audit_log table with automatic triggers |
| 003 | Creates performance indexes on all tables |
| 004 | Creates sessions table and adds security fields to usuarios |
| 005 | Creates inventory_movements table for stock tracking |

## Next Steps

After migrations are applied:

1. ✅ Verify all tables and columns exist
2. ✅ Test constraints by trying to insert invalid data
3. ✅ Check audit_log is capturing changes
4. ✅ Update application code to use new fields
5. ✅ Implement session management in authentication service

## Need Help?

- See `ALEMBIC_README.md` for detailed Alembic documentation
- See `MIGRATION_SUMMARY.md` for complete migration details
- Check Alembic documentation: https://alembic.sqlalchemy.org/
