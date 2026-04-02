"""Create sessions table and enhance usuarios with security fields

Revision ID: 004_sessions_users
Revises: 003_performance_indexes
Create Date: 2026-03-06 15:15:00

This migration:
- Adds security fields to usuarios table (failed_login_attempts, locked_until, last_login_at)
- Creates sessions table with encryption support
- Adds indexes for authentication queries

Requirements: 1.1, 1.2, 1.3
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_sessions_users'
down_revision = '003_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration changes."""
    
    # ========================================================================
    # PART 1: Enhance usuarios table with security fields
    # ========================================================================
    
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                -- Add failed_login_attempts column
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'failed_login_attempts') THEN
                    ALTER TABLE usuarios ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Added failed_login_attempts column to usuarios';
                END IF;
                
                -- Add locked_until column
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'locked_until') THEN
                    ALTER TABLE usuarios ADD COLUMN locked_until TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added locked_until column to usuarios';
                END IF;
                
                -- Add last_login_at column
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'last_login_at') THEN
                    ALTER TABLE usuarios ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added last_login_at column to usuarios';
                END IF;
                
                -- Add password_changed_at column
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'password_changed_at') THEN
                    ALTER TABLE usuarios ADD COLUMN password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                    RAISE NOTICE 'Added password_changed_at column to usuarios';
                END IF;
                
                -- Add is_active column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'is_active') THEN
                    ALTER TABLE usuarios ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
                    RAISE NOTICE 'Added is_active column to usuarios';
                END IF;
                
                -- Add role column if it doesn't exist
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'role') THEN
                    ALTER TABLE usuarios ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
                    RAISE NOTICE 'Added role column to usuarios';
                END IF;
                
                -- Add check constraint for role
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                              WHERE constraint_name = 'chk_usuarios_role') THEN
                    ALTER TABLE usuarios ADD CONSTRAINT chk_usuarios_role 
                        CHECK (role IN ('admin', 'manager', 'user'));
                    RAISE NOTICE 'Added role check constraint to usuarios';
                END IF;
                
                -- Add deleted_at column for soft deletes
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'deleted_at') THEN
                    ALTER TABLE usuarios ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
                    RAISE NOTICE 'Added deleted_at column to usuarios';
                END IF;
            END IF;
        END $;
    """)
    
    # Add comments to new columns
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                COMMENT ON COLUMN usuarios.failed_login_attempts IS 'Number of consecutive failed login attempts';
                COMMENT ON COLUMN usuarios.locked_until IS 'Timestamp until which account is locked due to failed attempts';
                COMMENT ON COLUMN usuarios.last_login_at IS 'Timestamp of last successful login';
                COMMENT ON COLUMN usuarios.password_changed_at IS 'Timestamp of last password change';
                COMMENT ON COLUMN usuarios.is_active IS 'Whether user account is active';
                COMMENT ON COLUMN usuarios.role IS 'User role: admin, manager, or user';
                COMMENT ON COLUMN usuarios.deleted_at IS 'Timestamp of soft delete (NULL if not deleted)';
            END IF;
        END $;
    """)
    
    # ========================================================================
    # PART 2: Create sessions table
    # ========================================================================
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            token_hash VARCHAR(255) NOT NULL UNIQUE,
            encrypted_data TEXT,
            ip_address INET,
            user_agent TEXT,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            revoked_at TIMESTAMP WITH TIME ZONE
        );
    """)
    
    # Add foreign key to usuarios if table exists
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                              WHERE constraint_name = 'fk_sessions_user_id') THEN
                    ALTER TABLE sessions ADD CONSTRAINT fk_sessions_user_id 
                        FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE;
                    RAISE NOTICE 'Added foreign key constraint to sessions.user_id';
                END IF;
            END IF;
        END $;
    """)
    
    # Add comments to sessions table
    op.execute("""
        COMMENT ON TABLE sessions IS 'User authentication sessions with encrypted tokens';
        COMMENT ON COLUMN sessions.id IS 'Unique identifier for session';
        COMMENT ON COLUMN sessions.user_id IS 'ID of user who owns this session';
        COMMENT ON COLUMN sessions.token_hash IS 'SHA-256 hash of session token';
        COMMENT ON COLUMN sessions.encrypted_data IS 'AES-256 encrypted session data';
        COMMENT ON COLUMN sessions.ip_address IS 'IP address from which session was created';
        COMMENT ON COLUMN sessions.user_agent IS 'User agent string of client';
        COMMENT ON COLUMN sessions.expires_at IS 'Timestamp when session expires';
        COMMENT ON COLUMN sessions.created_at IS 'Timestamp when session was created';
        COMMENT ON COLUMN sessions.revoked_at IS 'Timestamp when session was revoked (NULL if active)';
    """)
    
    # ========================================================================
    # PART 3: Create indexes for sessions table
    # ========================================================================
    
    op.execute("""
        -- Index on token_hash for session lookups (only active sessions)
        CREATE INDEX IF NOT EXISTS idx_sessions_token_hash 
            ON sessions(token_hash) 
            WHERE revoked_at IS NULL;
        
        -- Index on user_id for user session queries (only active sessions)
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
            ON sessions(user_id) 
            WHERE revoked_at IS NULL;
        
        -- Index on expires_at for cleanup of expired sessions
        CREATE INDEX IF NOT EXISTS idx_sessions_expires_at 
            ON sessions(expires_at) 
            WHERE revoked_at IS NULL;
        
        -- Index on created_at for session history
        CREATE INDEX IF NOT EXISTS idx_sessions_created_at 
            ON sessions(created_at);
    """)
    
    # ========================================================================
    # PART 4: Create indexes for usuarios security fields
    # ========================================================================
    
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                -- Index on locked_until for checking locked accounts
                CREATE INDEX IF NOT EXISTS idx_usuarios_locked_until 
                    ON usuarios(locked_until) 
                    WHERE locked_until IS NOT NULL AND locked_until > NOW();
                RAISE NOTICE 'Created index on usuarios.locked_until';
                
                -- Index on username for login lookups (only active, non-deleted users)
                CREATE INDEX IF NOT EXISTS idx_usuarios_username_active 
                    ON usuarios(username) 
                    WHERE is_active = TRUE AND deleted_at IS NULL;
                RAISE NOTICE 'Created index on usuarios.username for active users';
            END IF;
        END $;
    """)
    
    print("✓ Migration 004: Sessions table and user security fields created successfully")


def downgrade() -> None:
    """Revert migration changes."""
    
    # Remove indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_sessions_token_hash;
        DROP INDEX IF EXISTS idx_sessions_user_id;
        DROP INDEX IF EXISTS idx_sessions_expires_at;
        DROP INDEX IF EXISTS idx_sessions_created_at;
        DROP INDEX IF EXISTS idx_usuarios_locked_until;
        DROP INDEX IF EXISTS idx_usuarios_username_active;
    """)
    
    # Drop sessions table
    op.execute("DROP TABLE IF EXISTS sessions;")
    
    # Remove security fields from usuarios
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS chk_usuarios_role;
                ALTER TABLE usuarios DROP COLUMN IF EXISTS failed_login_attempts;
                ALTER TABLE usuarios DROP COLUMN IF EXISTS locked_until;
                ALTER TABLE usuarios DROP COLUMN IF EXISTS last_login_at;
                ALTER TABLE usuarios DROP COLUMN IF EXISTS password_changed_at;
                ALTER TABLE usuarios DROP COLUMN IF EXISTS is_active;
                ALTER TABLE usuarios DROP COLUMN IF EXISTS role;
                ALTER TABLE usuarios DROP COLUMN IF EXISTS deleted_at;
            END IF;
        END $;
    """)
    
    print("✓ Migration 004: Rolled back successfully")
