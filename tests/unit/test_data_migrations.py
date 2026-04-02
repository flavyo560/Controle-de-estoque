"""Tests for data migrations.

This module tests that database migrations:
1. Preserve all existing data
2. Can be rolled back to restore original state
3. Handle edge cases correctly

Requirements: 9.1, 11.1
"""

import pytest
import asyncio
from typing import Dict, List, Any
from datetime import datetime
from decimal import Decimal


@pytest.mark.asyncio
class TestDataMigrationPreservation:
    """Test that migrations preserve all data correctly."""
    
    async def test_migration_preserves_product_data(self, db_client, clean_database):
        """Test that product migration preserves all product data.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create test products with various data
        test_products = [
            {
                "descricao": "Test Product 1",
                "genero": "M",
                "marca": "TestBrand",
                "referencia": "REF001",
                "tamanho": "M",
                "qtd": 100,
                "preco": Decimal("99.99"),
                "estoque_minimo": 10
            },
            {
                "descricao": "Test Product 2",
                "genero": "F",
                "marca": "TestBrand",
                "referencia": "REF002",
                "tamanho": "L",
                "qtd": 50,
                "preco": Decimal("149.99"),
                "estoque_minimo": 5
            },
            {
                "descricao": "Test Product 3",
                "genero": "U",
                "marca": "AnotherBrand",
                "referencia": "REF003",
                "tamanho": "S",
                "qtd": 0,  # Edge case: zero quantity
                "preco": Decimal("0.01"),  # Edge case: minimum price
                "estoque_minimo": 0  # Edge case: zero minimum stock
            }
        ]
        
        # Insert test products
        product_ids = []
        for product in test_products:
            result = await db_client.fetch_one(
                """
                INSERT INTO produtos (descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                product["descricao"],
                product["genero"],
                product["marca"],
                product["referencia"],
                product["tamanho"],
                product["qtd"],
                product["preco"],
                product["estoque_minimo"]
            )
            product_ids.append(result["id"])
        
        # Store original data for comparison
        original_data = await db_client.fetch_all(
            """
            SELECT id, descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo
            FROM produtos
            WHERE id = ANY($1)
            ORDER BY id
            """,
            product_ids
        )
        
        # Simulate migration: Add version column if not exists
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        # Update products with version=1 (simulating migration)
        await db_client.execute(
            """
            UPDATE produtos 
            SET version = 1
            WHERE id = ANY($1) AND (version IS NULL OR version = 0)
            """,
            product_ids
        )
        
        # Verify all data is preserved after migration
        migrated_data = await db_client.fetch_all(
            """
            SELECT id, descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo, version
            FROM produtos
            WHERE id = ANY($1)
            ORDER BY id
            """,
            product_ids
        )
        
        # Assert all products still exist
        assert len(migrated_data) == len(original_data), "Migration lost products"
        
        # Assert all data fields are preserved
        for original, migrated in zip(original_data, migrated_data):
            assert migrated["id"] == original["id"]
            assert migrated["descricao"] == original["descricao"]
            assert migrated["genero"] == original["genero"]
            assert migrated["marca"] == original["marca"]
            assert migrated["referencia"] == original["referencia"]
            assert migrated["tamanho"] == original["tamanho"]
            assert migrated["qtd"] == original["qtd"]
            assert migrated["preco"] == original["preco"]
            assert migrated["estoque_minimo"] == original["estoque_minimo"]
            
            # Assert version was added
            assert migrated["version"] == 1, "Version not set correctly"
    
    async def test_migration_preserves_user_data(self, db_client, clean_database):
        """Test that user migration preserves all user data.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create test users
        test_users = [
            {
                "username": "testuser1",
                "password_hash": "hashed_password_1",
                "full_name": "Test User One",
                "email": "user1@test.com",
                "role": "user"
            },
            {
                "username": "testadmin",
                "password_hash": "hashed_password_2",
                "full_name": "Test Admin",
                "email": "admin@test.com",
                "role": "admin"
            }
        ]
        
        # Insert test users
        user_ids = []
        for user in test_users:
            result = await db_client.fetch_one(
                """
                INSERT INTO usuarios (username, password_hash, full_name, email, role)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                user["username"],
                user["password_hash"],
                user["full_name"],
                user["email"],
                user["role"]
            )
            user_ids.append(result["id"])
        
        # Store original data
        original_data = await db_client.fetch_all(
            """
            SELECT id, username, password_hash, full_name, email, role
            FROM usuarios
            WHERE id = ANY($1)
            ORDER BY id
            """,
            user_ids
        )
        
        # Simulate migration: Add security fields
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'failed_login_attempts') THEN
                    ALTER TABLE usuarios ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'usuarios' AND column_name = 'locked_until') THEN
                    ALTER TABLE usuarios ADD COLUMN locked_until TIMESTAMP WITH TIME ZONE;
                END IF;
            END $;
            """
        )
        
        # Verify all data is preserved
        migrated_data = await db_client.fetch_all(
            """
            SELECT id, username, password_hash, full_name, email, role, failed_login_attempts, locked_until
            FROM usuarios
            WHERE id = ANY($1)
            ORDER BY id
            """,
            user_ids
        )
        
        # Assert all users still exist
        assert len(migrated_data) == len(original_data)
        
        # Assert all original data fields are preserved
        for original, migrated in zip(original_data, migrated_data):
            assert migrated["id"] == original["id"]
            assert migrated["username"] == original["username"]
            assert migrated["password_hash"] == original["password_hash"]
            assert migrated["full_name"] == original["full_name"]
            assert migrated["email"] == original["email"]
            assert migrated["role"] == original["role"]
            
            # Assert new fields have default values
            assert migrated["failed_login_attempts"] == 0
            assert migrated["locked_until"] is None
    
    async def test_migration_preserves_sales_data(self, db_client, clean_database):
        """Test that sales migration preserves all sales data.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create test user first
        user_result = await db_client.fetch_one(
            """
            INSERT INTO usuarios (username, password_hash, full_name, role)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            "testuser",
            "hashed_password",
            "Test User",
            "user"
        )
        user_id = user_result["id"]
        
        # Create test customer
        customer_result = await db_client.fetch_one(
            """
            INSERT INTO clientes (nome, cpf, telefone)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            "Test Customer",
            "12345678901",
            "11999999999"
        )
        customer_id = customer_result["id"]
        
        # Create test sales
        test_sales = [
            {
                "cliente_id": customer_id,
                "usuario_id": user_id,
                "valor_total": Decimal("199.98"),
                "desconto": Decimal("0.00"),
                "valor_final": Decimal("199.98")
            },
            {
                "cliente_id": customer_id,
                "usuario_id": user_id,
                "valor_total": Decimal("500.00"),
                "desconto": Decimal("50.00"),
                "valor_final": Decimal("450.00")
            }
        ]
        
        # Insert test sales
        sale_ids = []
        for sale in test_sales:
            result = await db_client.fetch_one(
                """
                INSERT INTO vendas (cliente_id, usuario_id, valor_total, desconto, valor_final)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                sale["cliente_id"],
                sale["usuario_id"],
                sale["valor_total"],
                sale["desconto"],
                sale["valor_final"]
            )
            sale_ids.append(result["id"])
        
        # Store original data
        original_data = await db_client.fetch_all(
            """
            SELECT id, cliente_id, usuario_id, valor_total, desconto, valor_final
            FROM vendas
            WHERE id = ANY($1)
            ORDER BY id
            """,
            sale_ids
        )
        
        # Simulate migration: Add version column
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'vendas' AND column_name = 'version') THEN
                    ALTER TABLE vendas ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        # Update sales with version=1
        await db_client.execute(
            """
            UPDATE vendas 
            SET version = 1
            WHERE id = ANY($1) AND (version IS NULL OR version = 0)
            """,
            sale_ids
        )
        
        # Verify all data is preserved
        migrated_data = await db_client.fetch_all(
            """
            SELECT id, cliente_id, usuario_id, valor_total, desconto, valor_final, version
            FROM vendas
            WHERE id = ANY($1)
            ORDER BY id
            """,
            sale_ids
        )
        
        # Assert all sales still exist
        assert len(migrated_data) == len(original_data)
        
        # Assert all data fields are preserved
        for original, migrated in zip(original_data, migrated_data):
            assert migrated["id"] == original["id"]
            assert migrated["cliente_id"] == original["cliente_id"]
            assert migrated["usuario_id"] == original["usuario_id"]
            assert migrated["valor_total"] == original["valor_total"]
            assert migrated["desconto"] == original["desconto"]
            assert migrated["valor_final"] == original["valor_final"]
            assert migrated["version"] == 1
    
    async def test_migration_handles_null_values(self, db_client, clean_database):
        """Test that migration correctly handles NULL values in optional fields.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create product with NULL optional fields
        result = await db_client.fetch_one(
            """
            INSERT INTO produtos (descricao, genero, marca, referencia, tamanho, qtd, preco)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            "Product with NULLs",
            "U",
            "Brand",
            "REF",
            "M",
            10,
            Decimal("50.00")
        )
        product_id = result["id"]
        
        # Verify NULL fields before migration
        original = await db_client.fetch_one(
            """
            SELECT id, descricao, codigo_barras, estoque_minimo
            FROM produtos
            WHERE id = $1
            """,
            product_id
        )
        
        # codigo_barras should be NULL if not set
        # estoque_minimo might be NULL or have a default
        
        # Simulate migration
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        await db_client.execute(
            """
            UPDATE produtos 
            SET version = 1
            WHERE id = $1
            """,
            product_id
        )
        
        # Verify NULL fields are preserved after migration
        migrated = await db_client.fetch_one(
            """
            SELECT id, descricao, codigo_barras, estoque_minimo, version
            FROM produtos
            WHERE id = $1
            """,
            product_id
        )
        
        assert migrated["id"] == original["id"]
        assert migrated["descricao"] == original["descricao"]
        assert migrated["codigo_barras"] == original["codigo_barras"]
        # estoque_minimo might have been set to default during migration
        assert migrated["version"] == 1


@pytest.mark.asyncio
class TestDataMigrationRollback:
    """Test that migrations can be rolled back to restore original state."""
    
    async def test_rollback_removes_version_column(self, db_client, clean_database):
        """Test that rollback removes version column from products.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create test product
        result = await db_client.fetch_one(
            """
            INSERT INTO produtos (descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            "Test Product",
            "M",
            "Brand",
            "REF001",
            "M",
            100,
            Decimal("99.99"),
            10
        )
        product_id = result["id"]
        
        # Apply migration: Add version column
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        # Verify version column exists
        has_version = await db_client.fetch_val(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'produtos' AND column_name = 'version'
            """
        )
        assert has_version == "version", "Version column should exist after migration"
        
        # Rollback: Remove version column
        await db_client.execute(
            """
            ALTER TABLE produtos DROP COLUMN IF EXISTS version
            """
        )
        
        # Verify version column is removed
        has_version_after = await db_client.fetch_val(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'produtos' AND column_name = 'version'
            """
        )
        assert has_version_after is None, "Version column should be removed after rollback"
        
        # Verify product data is still intact
        product = await db_client.fetch_one(
            """
            SELECT id, descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo
            FROM produtos
            WHERE id = $1
            """,
            product_id
        )
        
        assert product is not None
        assert product["descricao"] == "Test Product"
        assert product["qtd"] == 100
        assert product["preco"] == Decimal("99.99")
    
    async def test_rollback_removes_constraints(self, db_client, clean_database):
        """Test that rollback removes added constraints.
        
        Validates: Requirements 9.1, 11.1
        """
        # Apply migration: Add check constraint
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                              WHERE constraint_name = 'test_chk_produtos_quantidade_nao_negativa') THEN
                    ALTER TABLE produtos ADD CONSTRAINT test_chk_produtos_quantidade_nao_negativa 
                        CHECK (qtd >= 0);
                END IF;
            END $;
            """
        )
        
        # Verify constraint exists
        has_constraint = await db_client.fetch_val(
            """
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE constraint_name = 'test_chk_produtos_quantidade_nao_negativa'
            """
        )
        assert has_constraint is not None, "Constraint should exist after migration"
        
        # Rollback: Remove constraint
        await db_client.execute(
            """
            ALTER TABLE produtos DROP CONSTRAINT IF EXISTS test_chk_produtos_quantidade_nao_negativa
            """
        )
        
        # Verify constraint is removed
        has_constraint_after = await db_client.fetch_val(
            """
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE constraint_name = 'test_chk_produtos_quantidade_nao_negativa'
            """
        )
        assert has_constraint_after is None, "Constraint should be removed after rollback"
    
    async def test_rollback_restores_original_state(self, db_client, clean_database):
        """Test complete rollback restores database to original state.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create test data
        result = await db_client.fetch_one(
            """
            INSERT INTO produtos (descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            "Original Product",
            "F",
            "OriginalBrand",
            "ORIG001",
            "L",
            50,
            Decimal("149.99"),
            5
        )
        product_id = result["id"]
        
        # Capture original state
        original_columns = await db_client.fetch_all(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'produtos'
            ORDER BY ordinal_position
            """
        )
        
        original_constraints = await db_client.fetch_all(
            """
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'produtos'
            ORDER BY constraint_name
            """
        )
        
        # Apply migration: Add version and deleted_at columns
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'deleted_at') THEN
                    ALTER TABLE produtos ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
                END IF;
            END $;
            """
        )
        
        # Verify migration applied
        migrated_columns = await db_client.fetch_all(
            """
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = 'produtos' AND column_name IN ('version', 'deleted_at')
            """
        )
        assert len(migrated_columns) == 2, "Migration should add 2 columns"
        
        # Rollback: Remove added columns
        await db_client.execute(
            """
            ALTER TABLE produtos DROP COLUMN IF EXISTS version;
            ALTER TABLE produtos DROP COLUMN IF EXISTS deleted_at;
            """
        )
        
        # Verify rollback restored original state
        restored_columns = await db_client.fetch_all(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'produtos'
            ORDER BY ordinal_position
            """
        )
        
        # Compare column counts (should match original)
        assert len(restored_columns) == len(original_columns), \
            "Rollback should restore original number of columns"
        
        # Verify product data is intact
        product = await db_client.fetch_one(
            """
            SELECT id, descricao, qtd, preco
            FROM produtos
            WHERE id = $1
            """,
            product_id
        )
        
        assert product["descricao"] == "Original Product"
        assert product["qtd"] == 50
        assert product["preco"] == Decimal("149.99")


@pytest.mark.asyncio
class TestMigrationEdgeCases:
    """Test migration handling of edge cases."""
    
    async def test_migration_with_large_dataset(self, db_client, clean_database):
        """Test migration performance with larger dataset.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create 100 test products
        product_ids = []
        for i in range(100):
            result = await db_client.fetch_one(
                """
                INSERT INTO produtos (descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                f"Product {i}",
                "U",
                "Brand",
                f"REF{i:03d}",
                "M",
                i * 10,
                Decimal(f"{i + 10}.99"),
                5
            )
            product_ids.append(result["id"])
        
        # Count products before migration
        count_before = await db_client.fetch_val(
            """
            SELECT COUNT(*) FROM produtos WHERE id = ANY($1)
            """,
            product_ids
        )
        assert count_before == 100
        
        # Apply migration
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        await db_client.execute(
            """
            UPDATE produtos 
            SET version = 1
            WHERE id = ANY($1)
            """,
            product_ids
        )
        
        # Count products after migration
        count_after = await db_client.fetch_val(
            """
            SELECT COUNT(*) FROM produtos WHERE id = ANY($1)
            """,
            product_ids
        )
        assert count_after == 100, "Migration should preserve all products"
        
        # Verify all have version=1
        version_count = await db_client.fetch_val(
            """
            SELECT COUNT(*) FROM produtos WHERE id = ANY($1) AND version = 1
            """,
            product_ids
        )
        assert version_count == 100, "All products should have version=1"
    
    async def test_migration_with_special_characters(self, db_client, clean_database):
        """Test migration preserves special characters in text fields.
        
        Validates: Requirements 9.1, 11.1
        """
        # Create product with special characters
        special_text = "Product with 'quotes', \"double quotes\", and symbols: @#$%&*"
        result = await db_client.fetch_one(
            """
            INSERT INTO produtos (descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            special_text,
            "U",
            "Brand's & Co.",
            "REF-001",
            "M",
            10,
            Decimal("99.99"),
            5
        )
        product_id = result["id"]
        
        # Apply migration
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        await db_client.execute(
            """
            UPDATE produtos SET version = 1 WHERE id = $1
            """,
            product_id
        )
        
        # Verify special characters are preserved
        product = await db_client.fetch_one(
            """
            SELECT descricao, marca FROM produtos WHERE id = $1
            """,
            product_id
        )
        
        assert product["descricao"] == special_text
        assert product["marca"] == "Brand's & Co."
    
    async def test_migration_idempotency(self, db_client, clean_database):
        """Test that running migration multiple times is safe (idempotent).
        
        Validates: Requirements 9.1, 11.1
        """
        # Create test product
        result = await db_client.fetch_one(
            """
            INSERT INTO produtos (descricao, genero, marca, referencia, tamanho, qtd, preco, estoque_minimo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            "Test Product",
            "M",
            "Brand",
            "REF001",
            "M",
            100,
            Decimal("99.99"),
            10
        )
        product_id = result["id"]
        
        # Apply migration first time
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        await db_client.execute(
            """
            UPDATE produtos SET version = 1 WHERE id = $1 AND (version IS NULL OR version = 0)
            """,
            product_id
        )
        
        # Get state after first migration
        first_state = await db_client.fetch_one(
            """
            SELECT id, descricao, qtd, preco, version FROM produtos WHERE id = $1
            """,
            product_id
        )
        
        # Apply migration second time (should be idempotent)
        await db_client.execute(
            """
            DO $
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'produtos' AND column_name = 'version') THEN
                    ALTER TABLE produtos ADD COLUMN version INTEGER NOT NULL DEFAULT 1;
                END IF;
            END $;
            """
        )
        
        await db_client.execute(
            """
            UPDATE produtos SET version = 1 WHERE id = $1 AND (version IS NULL OR version = 0)
            """,
            product_id
        )
        
        # Get state after second migration
        second_state = await db_client.fetch_one(
            """
            SELECT id, descricao, qtd, preco, version FROM produtos WHERE id = $1
            """,
            product_id
        )
        
        # Verify state is identical
        assert first_state == second_state, "Migration should be idempotent"
        assert second_state["version"] == 1
