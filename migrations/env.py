"""Alembic environment configuration for DEKIDS System.

This module configures Alembic to work with Supabase PostgreSQL database.
It handles both online (connected to database) and offline (SQL script generation) modes.
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import SQLAlchemy models for autogenerate support
# When models are created, import them here:
# from src.domain import product, user, sale, customer, audit
target_metadata = None  # Will be updated when models are created

# Get database URL from environment
def get_database_url() -> str:
    """
    Construct PostgreSQL connection URL from Supabase credentials.
    
    Returns:
        PostgreSQL connection string
    """
    supabase_url = os.getenv("SUPABASE_URL")
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL environment variable not set")
    
    # Extract project reference from Supabase URL
    # Format: https://PROJECT_REF.supabase.co
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    # Construct PostgreSQL connection string
    # Supabase uses port 5432 for direct PostgreSQL connections
    # Default credentials: postgres user with project password
    db_password = os.getenv("SUPABASE_DB_PASSWORD", "")
    
    if not db_password:
        # For development, try to use the service role key as password
        # In production, use proper database password
        print("WARNING: SUPABASE_DB_PASSWORD not set. Using SUPABASE_KEY as fallback.")
        db_password = os.getenv("SUPABASE_KEY", "")
    
    return f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    # Override sqlalchemy.url with our constructed URL
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
