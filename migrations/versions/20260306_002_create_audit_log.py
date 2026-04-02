"""Create audit_log table and triggers

Revision ID: 002_audit_log
Revises: 001_schema_constraints
Create Date: 2026-03-06 14:45:00

This migration creates:
- audit_log table for tracking all data changes
- Trigger function for automatic audit logging
- Triggers on produtos, vendas, and usuarios tables
- Rules to prevent updates and deletes on audit_log (append-only)

Requirements: 3.1, 3.2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_audit_log'
down_revision = '001_schema_constraints'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration changes."""
    
    # ========================================================================
    # PART 1: Create audit_log table
    # ========================================================================
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT,
            operation VARCHAR(20) NOT NULL CHECK (operation IN ('CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'FAILED_LOGIN')),
            table_name VARCHAR(50),
            record_id BIGINT,
            old_values JSONB,
            new_values JSONB,
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)
    
    # Add comment to table
    op.execute("""
        COMMENT ON TABLE audit_log IS 'Append-only audit trail for all system operations';
        COMMENT ON COLUMN audit_log.id IS 'Unique identifier for audit record';
        COMMENT ON COLUMN audit_log.user_id IS 'ID of user who performed the operation';
        COMMENT ON COLUMN audit_log.operation IS 'Type of operation: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, FAILED_LOGIN';
        COMMENT ON COLUMN audit_log.table_name IS 'Name of table affected by operation';
        COMMENT ON COLUMN audit_log.record_id IS 'ID of record affected by operation';
        COMMENT ON COLUMN audit_log.old_values IS 'JSON snapshot of record before change';
        COMMENT ON COLUMN audit_log.new_values IS 'JSON snapshot of record after change';
        COMMENT ON COLUMN audit_log.ip_address IS 'IP address of user who performed operation';
        COMMENT ON COLUMN audit_log.user_agent IS 'User agent string of client';
        COMMENT ON COLUMN audit_log.created_at IS 'Timestamp when audit record was created';
    """)
    
    # ========================================================================
    # PART 2: Create indexes for audit_log
    # ========================================================================
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);
    """)
    
    # ========================================================================
    # PART 3: Create rules to prevent updates and deletes (append-only)
    # ========================================================================
    
    op.execute("""
        CREATE OR REPLACE RULE audit_log_no_update AS 
            ON UPDATE TO audit_log 
            DO INSTEAD NOTHING;
        
        CREATE OR REPLACE RULE audit_log_no_delete AS 
            ON DELETE TO audit_log 
            DO INSTEAD NOTHING;
    """)
    
    # ========================================================================
    # PART 4: Create trigger function for automatic audit logging
    # ========================================================================
    
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO audit_log (operation, table_name, record_id, old_values)
                VALUES ('DELETE', TG_TABLE_NAME, OLD.id, row_to_json(OLD));
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO audit_log (operation, table_name, record_id, old_values, new_values)
                VALUES ('UPDATE', TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO audit_log (operation, table_name, record_id, new_values)
                VALUES ('CREATE', TG_TABLE_NAME, NEW.id, row_to_json(NEW));
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $ LANGUAGE plpgsql;
    """)
    
    # ========================================================================
    # PART 5: Apply audit triggers to critical tables
    # ========================================================================
    
    # Trigger for produtos table
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'produtos') THEN
                DROP TRIGGER IF EXISTS audit_produtos ON produtos;
                CREATE TRIGGER audit_produtos 
                    AFTER INSERT OR UPDATE OR DELETE ON produtos
                    FOR EACH ROW 
                    EXECUTE FUNCTION audit_trigger_function();
                RAISE NOTICE 'Created audit trigger for produtos table';
            END IF;
        END $;
    """)
    
    # Trigger for vendas table
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vendas') THEN
                DROP TRIGGER IF EXISTS audit_vendas ON vendas;
                CREATE TRIGGER audit_vendas 
                    AFTER INSERT OR UPDATE OR DELETE ON vendas
                    FOR EACH ROW 
                    EXECUTE FUNCTION audit_trigger_function();
                RAISE NOTICE 'Created audit trigger for vendas table';
            END IF;
        END $;
    """)
    
    # Trigger for usuarios table
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                DROP TRIGGER IF EXISTS audit_usuarios ON usuarios;
                CREATE TRIGGER audit_usuarios 
                    AFTER INSERT OR UPDATE OR DELETE ON usuarios
                    FOR EACH ROW 
                    EXECUTE FUNCTION audit_trigger_function();
                RAISE NOTICE 'Created audit trigger for usuarios table';
            END IF;
        END $;
    """)
    
    # Trigger for clientes table
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'clientes') THEN
                DROP TRIGGER IF EXISTS audit_clientes ON clientes;
                CREATE TRIGGER audit_clientes 
                    AFTER INSERT OR UPDATE OR DELETE ON clientes
                    FOR EACH ROW 
                    EXECUTE FUNCTION audit_trigger_function();
                RAISE NOTICE 'Created audit trigger for clientes table';
            END IF;
        END $;
    """)
    
    print("✓ Migration 002: Audit log table and triggers created successfully")


def downgrade() -> None:
    """Revert migration changes."""
    
    # Remove triggers
    op.execute("""
        DROP TRIGGER IF EXISTS audit_produtos ON produtos;
        DROP TRIGGER IF EXISTS audit_vendas ON vendas;
        DROP TRIGGER IF EXISTS audit_usuarios ON usuarios;
        DROP TRIGGER IF EXISTS audit_clientes ON clientes;
    """)
    
    # Remove trigger function
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_function();")
    
    # Remove rules
    op.execute("""
        DROP RULE IF EXISTS audit_log_no_update ON audit_log;
        DROP RULE IF EXISTS audit_log_no_delete ON audit_log;
    """)
    
    # Drop table
    op.execute("DROP TABLE IF EXISTS audit_log;")
    
    print("✓ Migration 002: Rolled back successfully")
