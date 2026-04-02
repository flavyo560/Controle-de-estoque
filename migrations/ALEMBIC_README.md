# Alembic Database Migrations

This directory contains Alembic database migrations for the DEKIDS system.

## Setup

Alembic is configured to work with Supabase PostgreSQL database. The configuration is in:
- `alembic.ini` - Main Alembic configuration
- `migrations/env.py` - Environment setup and database connection
- `migrations/script.py.mako` - Template for new migration files

## Environment Variables

Before running migrations, ensure these environment variables are set in `.env`:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-database-password
```

To get your database password:
1. Go to Supabase Dashboard → Project Settings → Database
2. Copy the database password (not the API key)

## Common Commands

### Create a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration for manual SQL
alembic revision -m "description of changes"
```

### Apply migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade by one version
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade <revision_id>
```

### Rollback migrations

```bash
# Downgrade by one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade all migrations
alembic downgrade base
```

### View migration history

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Migration File Structure

Each migration file contains:
- `revision` - Unique identifier for this migration
- `down_revision` - Previous migration this depends on
- `upgrade()` - Function to apply changes
- `downgrade()` - Function to revert changes

Example:

```python
def upgrade() -> None:
    """Apply migration changes."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    """Revert migration changes."""
    op.drop_table('users')
```

## Best Practices

1. **Always test migrations** on a development database first
2. **Write reversible migrations** - every upgrade should have a corresponding downgrade
3. **Use transactions** - migrations run in transactions by default
4. **Keep migrations small** - one logical change per migration
5. **Don't modify existing migrations** - create new ones instead
6. **Backup before production migrations** - always backup production data first

## Troubleshooting

### Connection Issues

If you get connection errors:
1. Verify `SUPABASE_URL` and `SUPABASE_DB_PASSWORD` are set correctly
2. Check if your IP is allowed in Supabase (Database → Settings → Network)
3. Ensure you're using the database password, not the API key

### Migration Conflicts

If migrations are out of sync:
```bash
# Check current state
alembic current

# View history
alembic history

# Stamp database to specific revision (use with caution)
alembic stamp <revision_id>
```

### Failed Migration

If a migration fails:
1. The transaction is automatically rolled back
2. Fix the issue in the migration file
3. Run the migration again

## Integration with Application

The application checks for pending migrations on startup. To disable this:
1. Set `AUTO_MIGRATE=false` in `.env`
2. Run migrations manually before starting the application

## Migration Workflow

1. **Development**: Create and test migrations locally
2. **Staging**: Apply migrations to staging environment
3. **Production**: After testing, apply to production with backup

```bash
# Development
alembic revision --autogenerate -m "add user table"
alembic upgrade head

# Staging
alembic upgrade head

# Production (with backup)
# 1. Backup database
# 2. Apply migration
alembic upgrade head
# 3. Verify application works
# 4. If issues, rollback
alembic downgrade -1
```
