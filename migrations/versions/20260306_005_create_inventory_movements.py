"""Create inventory_movements table for stock tracking

Revision ID: 005_inventory_movements
Revises: 004_sessions_users
Create Date: 2026-03-06 15:30:00

This migration creates:
- inventory_movements table for tracking all stock changes
- Indexes for efficient querying
- Check constraints for data validation

Requirements: 19.2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_inventory_movements'
down_revision = '004_sessions_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration changes."""
    
    # ========================================================================
    # PART 1: Create inventory_movements table
    # ========================================================================
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id BIGSERIAL PRIMARY KEY,
            product_id BIGINT NOT NULL,
            movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('sale', 'purchase', 'adjustment', 'return')),
            quantity_change INTEGER NOT NULL,
            quantity_before INTEGER NOT NULL CHECK (quantity_before >= 0),
            quantity_after INTEGER NOT NULL CHECK (quantity_after >= 0),
            reference_type VARCHAR(20),
            reference_id BIGINT,
            user_id BIGINT,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)
    
    # Add foreign key to produtos if table exists
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'produtos') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                              WHERE constraint_name = 'fk_inventory_movements_product_id') THEN
                    ALTER TABLE inventory_movements ADD CONSTRAINT fk_inventory_movements_product_id 
                        FOREIGN KEY (product_id) REFERENCES produtos(id) ON DELETE RESTRICT;
                    RAISE NOTICE 'Added foreign key constraint to inventory_movements.product_id';
                END IF;
            END IF;
        END $;
    """)
    
    # Add foreign key to usuarios if table exists
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                              WHERE constraint_name = 'fk_inventory_movements_user_id') THEN
                    ALTER TABLE inventory_movements ADD CONSTRAINT fk_inventory_movements_user_id 
                        FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE SET NULL;
                    RAISE NOTICE 'Added foreign key constraint to inventory_movements.user_id';
                END IF;
            END IF;
        END $;
    """)
    
    # Add comments to table and columns
    op.execute("""
        COMMENT ON TABLE inventory_movements IS 'Complete history of all inventory stock changes';
        COMMENT ON COLUMN inventory_movements.id IS 'Unique identifier for movement record';
        COMMENT ON COLUMN inventory_movements.product_id IS 'ID of product affected by movement';
        COMMENT ON COLUMN inventory_movements.movement_type IS 'Type of movement: sale, purchase, adjustment, return';
        COMMENT ON COLUMN inventory_movements.quantity_change IS 'Change in quantity (positive for increase, negative for decrease)';
        COMMENT ON COLUMN inventory_movements.quantity_before IS 'Product quantity before this movement';
        COMMENT ON COLUMN inventory_movements.quantity_after IS 'Product quantity after this movement';
        COMMENT ON COLUMN inventory_movements.reference_type IS 'Type of related record (e.g., sale, purchase_order)';
        COMMENT ON COLUMN inventory_movements.reference_id IS 'ID of related record';
        COMMENT ON COLUMN inventory_movements.user_id IS 'ID of user who performed the movement';
        COMMENT ON COLUMN inventory_movements.notes IS 'Optional notes about the movement';
        COMMENT ON COLUMN inventory_movements.created_at IS 'Timestamp when movement was recorded';
    """)
    
    # ========================================================================
    # PART 2: Create indexes for inventory_movements
    # ========================================================================
    
    op.execute("""
        -- Index on product_id for product movement history
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_product_id 
            ON inventory_movements(product_id);
        
        -- Index on movement_type for filtering by type
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_type 
            ON inventory_movements(movement_type);
        
        -- Index on created_at for time-based queries
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_created_at 
            ON inventory_movements(created_at);
        
        -- Composite index on reference_type and reference_id for lookups
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_reference 
            ON inventory_movements(reference_type, reference_id) 
            WHERE reference_type IS NOT NULL AND reference_id IS NOT NULL;
        
        -- Index on user_id for user activity tracking
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_user_id 
            ON inventory_movements(user_id) 
            WHERE user_id IS NOT NULL;
        
        -- Composite index for product history with date range
        CREATE INDEX IF NOT EXISTS idx_inventory_movements_product_date 
            ON inventory_movements(product_id, created_at);
    """)
    
    # ========================================================================
    # PART 3: Add additional check constraints
    # ========================================================================
    
    op.execute("""
        -- Ensure quantity_after = quantity_before + quantity_change
        ALTER TABLE inventory_movements ADD CONSTRAINT chk_inventory_movements_quantity_consistency 
            CHECK (quantity_after = quantity_before + quantity_change);
        
        -- Ensure reference_id is provided when reference_type is set
        ALTER TABLE inventory_movements ADD CONSTRAINT chk_inventory_movements_reference_consistency 
            CHECK (
                (reference_type IS NULL AND reference_id IS NULL) OR 
                (reference_type IS NOT NULL AND reference_id IS NOT NULL)
            );
    """)
    
    print("✓ Migration 005: Inventory movements table created successfully")


def downgrade() -> None:
    """Revert migration changes."""
    
    # Remove indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_inventory_movements_product_id;
        DROP INDEX IF EXISTS idx_inventory_movements_type;
        DROP INDEX IF EXISTS idx_inventory_movements_created_at;
        DROP INDEX IF EXISTS idx_inventory_movements_reference;
        DROP INDEX IF EXISTS idx_inventory_movements_user_id;
        DROP INDEX IF EXISTS idx_inventory_movements_product_date;
    """)
    
    # Drop table
    op.execute("DROP TABLE IF EXISTS inventory_movements;")
    
    print("✓ Migration 005: Rolled back successfully")
