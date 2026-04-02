"""Create performance indexes

Revision ID: 003_performance_indexes
Revises: 002_audit_log
Create Date: 2026-03-06 15:00:00

This migration creates indexes for:
- produtos: SKU, barcode, low stock queries, full-text search
- vendas: customer_id, user_id, status, created_at (already exist from migration 004)
- audit_log: user_id, table_name+record_id, created_at, operation (already created in 002)
- sessions: token_hash, user_id, expires_at (will be created when sessions table exists)

Requirements: 5.1, 14.2
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_performance_indexes'
down_revision = '002_audit_log'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration changes."""
    
    # ========================================================================
    # PART 1: Indexes for produtos table
    # ========================================================================
    
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'produtos') THEN
                -- Index on descricao (SKU equivalent) for lookups
                -- Only index non-deleted products
                CREATE INDEX IF NOT EXISTS idx_produtos_descricao 
                    ON produtos(descricao) 
                    WHERE deleted_at IS NULL;
                RAISE NOTICE 'Created index on produtos.descricao';
                
                -- Index on codigo_barras for barcode lookups
                -- Only index non-null, non-deleted products
                CREATE INDEX IF NOT EXISTS idx_produtos_codigo_barras 
                    ON produtos(codigo_barras) 
                    WHERE codigo_barras IS NOT NULL AND deleted_at IS NULL;
                RAISE NOTICE 'Created index on produtos.codigo_barras';
                
                -- Composite index for low stock queries
                -- Helps find products where qtd < estoque_minimo
                CREATE INDEX IF NOT EXISTS idx_produtos_low_stock 
                    ON produtos(qtd, estoque_minimo) 
                    WHERE deleted_at IS NULL;
                RAISE NOTICE 'Created index for low stock queries';
                
                -- Full-text search index on descricao
                -- Uses Portuguese text search configuration
                CREATE INDEX IF NOT EXISTS idx_produtos_search 
                    ON produtos USING gin(to_tsvector('portuguese', 
                        COALESCE(descricao, '') || ' ' || 
                        COALESCE(marca, '') || ' ' || 
                        COALESCE(referencia, '')
                    ))
                    WHERE deleted_at IS NULL;
                RAISE NOTICE 'Created full-text search index on produtos';
                
                -- Index on marca for filtering by brand
                CREATE INDEX IF NOT EXISTS idx_produtos_marca 
                    ON produtos(marca) 
                    WHERE deleted_at IS NULL;
                RAISE NOTICE 'Created index on produtos.marca';
                
                -- Index on genero for filtering by gender
                CREATE INDEX IF NOT EXISTS idx_produtos_genero 
                    ON produtos(genero) 
                    WHERE deleted_at IS NULL;
                RAISE NOTICE 'Created index on produtos.genero';
                
                -- Index on created_at for sorting by date
                CREATE INDEX IF NOT EXISTS idx_produtos_created_at 
                    ON produtos(created_at) 
                    WHERE deleted_at IS NULL;
                RAISE NOTICE 'Created index on produtos.created_at';
            END IF;
        END $;
    """)
    
    # ========================================================================
    # PART 2: Additional indexes for vendas table
    # ========================================================================
    
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'vendas') THEN
                -- Indexes already created in migration 004:
                -- - idx_vendas_data_hora
                -- - idx_vendas_cliente_id
                -- - idx_vendas_usuario_id
                -- - idx_vendas_status
                
                -- Add composite index for date range queries with status filter
                CREATE INDEX IF NOT EXISTS idx_vendas_data_status 
                    ON vendas(data_hora, status);
                RAISE NOTICE 'Created composite index on vendas(data_hora, status)';
                
                -- Add index on valor_final for revenue queries
                CREATE INDEX IF NOT EXISTS idx_vendas_valor_final 
                    ON vendas(valor_final) 
                    WHERE status = 'finalizada';
                RAISE NOTICE 'Created index on vendas.valor_final';
            END IF;
        END $;
    """)
    
    # ========================================================================
    # PART 3: Indexes for itens_venda table
    # ========================================================================
    
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'itens_venda') THEN
                -- Index on produto_id for product sales history
                CREATE INDEX IF NOT EXISTS idx_itens_venda_produto_id 
                    ON itens_venda(produto_id);
                RAISE NOTICE 'Created index on itens_venda.produto_id';
                
                -- Composite index for venda_id + produto_id lookups
                CREATE INDEX IF NOT EXISTS idx_itens_venda_venda_produto 
                    ON itens_venda(venda_id, produto_id);
                RAISE NOTICE 'Created composite index on itens_venda(venda_id, produto_id)';
            END IF;
        END $;
    """)
    
    # ========================================================================
    # PART 4: Indexes for clientes table
    # ========================================================================
    
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'clientes') THEN
                -- Indexes already created in migration 003:
                -- - idx_clientes_cpf
                -- - idx_clientes_nome
                -- - idx_clientes_telefone
                
                -- Add index on email for lookups
                CREATE INDEX IF NOT EXISTS idx_clientes_email 
                    ON clientes(email) 
                    WHERE email IS NOT NULL;
                RAISE NOTICE 'Created index on clientes.email';
            END IF;
        END $;
    """)
    
    # ========================================================================
    # PART 5: Indexes for usuarios table
    # ========================================================================
    
    op.execute("""
        DO $
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
                -- Index on username for login lookups
                CREATE INDEX IF NOT EXISTS idx_usuarios_username 
                    ON usuarios(username);
                RAISE NOTICE 'Created index on usuarios.username';
                
                -- Index on is_active for filtering active users
                CREATE INDEX IF NOT EXISTS idx_usuarios_is_active 
                    ON usuarios(is_active) 
                    WHERE is_active = true;
                RAISE NOTICE 'Created index on usuarios.is_active';
            END IF;
        END $;
    """)
    
    print("✓ Migration 003: Performance indexes created successfully")


def downgrade() -> None:
    """Revert migration changes."""
    
    # Remove produtos indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_produtos_descricao;
        DROP INDEX IF EXISTS idx_produtos_codigo_barras;
        DROP INDEX IF EXISTS idx_produtos_low_stock;
        DROP INDEX IF EXISTS idx_produtos_search;
        DROP INDEX IF EXISTS idx_produtos_marca;
        DROP INDEX IF EXISTS idx_produtos_genero;
        DROP INDEX IF EXISTS idx_produtos_created_at;
    """)
    
    # Remove vendas indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_vendas_data_status;
        DROP INDEX IF EXISTS idx_vendas_valor_final;
    """)
    
    # Remove itens_venda indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_itens_venda_produto_id;
        DROP INDEX IF EXISTS idx_itens_venda_venda_produto;
    """)
    
    # Remove clientes indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_clientes_email;
    """)
    
    # Remove usuarios indexes
    op.execute("""
        DROP INDEX IF EXISTS idx_usuarios_username;
        DROP INDEX IF EXISTS idx_usuarios_is_active;
    """)
    
    print("✓ Migration 003: Rolled back successfully")
