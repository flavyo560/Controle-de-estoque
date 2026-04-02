# Data Migration Tests

This test suite validates that database migrations preserve all data correctly and can be rolled back safely.

## Overview

The data migration tests ensure that:
1. **Data Preservation**: All existing data is preserved during migrations
2. **Rollback Safety**: Migrations can be rolled back to restore the original state
3. **Edge Cases**: Migrations handle special cases correctly (NULL values, special characters, large datasets)

## Test Structure

### TestDataMigrationPreservation
Tests that migrations preserve all data correctly:

- `test_migration_preserves_product_data`: Verifies product data (descriptions, prices, quantities) remains intact after adding version columns
- `test_migration_preserves_user_data`: Verifies user data remains intact after adding security fields
- `test_migration_preserves_sales_data`: Verifies sales data remains intact after adding version columns
- `test_migration_handles_null_values`: Verifies NULL values in optional fields are preserved

### TestDataMigrationRollback
Tests that migrations can be rolled back safely:

- `test_rollback_removes_version_column`: Verifies rollback removes added version column
- `test_rollback_removes_constraints`: Verifies rollback removes added constraints
- `test_rollback_restores_original_state`: Verifies complete rollback restores database to original state

### TestMigrationEdgeCases
Tests migration handling of edge cases:

- `test_migration_with_large_dataset`: Tests migration performance with 100+ products
- `test_migration_with_special_characters`: Tests preservation of special characters in text fields
- `test_migration_idempotency`: Tests that running migrations multiple times is safe

## Requirements Validated

- **Requirement 9.1**: Automated testing infrastructure with comprehensive test coverage
- **Requirement 11.1**: Database migration system with rollback capability

## Running the Tests

### Prerequisites

1. Database connection configured in `.env` file:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   # OR
   TEST_DATABASE_URL=postgresql://user:password@host:port/test_database
   ```

2. Database tables must exist (run migrations first):
   ```bash
   alembic upgrade head
   ```

### Run All Migration Tests

```bash
python -m pytest tests/unit/test_data_migrations.py -v
```

### Run Specific Test Class

```bash
# Test data preservation only
python -m pytest tests/unit/test_data_migrations.py::TestDataMigrationPreservation -v

# Test rollback only
python -m pytest tests/unit/test_data_migrations.py::TestDataMigrationRollback -v

# Test edge cases only
python -m pytest tests/unit/test_data_migrations.py::TestMigrationEdgeCases -v
```

### Run Specific Test

```bash
python -m pytest tests/unit/test_data_migrations.py::TestDataMigrationPreservation::test_migration_preserves_product_data -v
```

## Test Data

Each test creates its own test data and cleans up after execution using the `clean_database` fixture. Tests are isolated and can run in any order.

## What the Tests Validate

### Data Preservation Tests

1. **Product Migration**:
   - All product fields preserved (description, price, quantity, etc.)
   - Version column added with value=1
   - Edge cases: zero quantity, minimum price, zero minimum stock

2. **User Migration**:
   - All user fields preserved (username, password_hash, email, role)
   - Security fields added with default values (failed_login_attempts=0, locked_until=NULL)

3. **Sales Migration**:
   - All sales fields preserved (customer_id, user_id, amounts)
   - Version column added with value=1
   - Relationships maintained (foreign keys intact)

4. **NULL Value Handling**:
   - Optional fields with NULL values remain NULL after migration
   - Required fields maintain their values

### Rollback Tests

1. **Column Removal**:
   - Added columns (version, deleted_at) are removed
   - Original data remains intact

2. **Constraint Removal**:
   - Added constraints are removed
   - Database returns to original constraint state

3. **Complete Rollback**:
   - All migration changes are reversed
   - Column count matches original
   - Data integrity maintained

### Edge Case Tests

1. **Large Dataset**:
   - 100 products migrated successfully
   - All products have version=1 after migration
   - No data loss

2. **Special Characters**:
   - Quotes, double quotes, symbols preserved
   - No SQL injection issues
   - Text encoding correct

3. **Idempotency**:
   - Running migration twice produces same result
   - No duplicate columns or constraints
   - Data not modified on second run

## Expected Behavior

### Successful Test Run

When database is available and migrations are applied:
```
tests/unit/test_data_migrations.py::TestDataMigrationPreservation::test_migration_preserves_product_data PASSED
tests/unit/test_data_migrations.py::TestDataMigrationPreservation::test_migration_preserves_user_data PASSED
tests/unit/test_data_migrations.py::TestDataMigrationPreservation::test_migration_preserves_sales_data PASSED
tests/unit/test_data_migrations.py::TestDataMigrationPreservation::test_migration_handles_null_values PASSED
tests/unit/test_data_migrations.py::TestDataMigrationRollback::test_rollback_removes_version_column PASSED
tests/unit/test_data_migrations.py::TestDataMigrationRollback::test_rollback_removes_constraints PASSED
tests/unit/test_data_migrations.py::TestDataMigrationRollback::test_rollback_restores_original_state PASSED
tests/unit/test_data_migrations.py::TestMigrationEdgeCases::test_migration_with_large_dataset PASSED
tests/unit/test_data_migrations.py::TestMigrationEdgeCases::test_migration_with_special_characters PASSED
tests/unit/test_data_migrations.py::TestMigrationEdgeCases::test_migration_idempotency PASSED

========== 10 passed in 5.23s ==========
```

### No Database Connection

When database is not available:
```
ERROR tests/unit/test_data_migrations.py::... - ConnectionRefusedError
```

This is expected - configure DATABASE_URL in .env file.

## Integration with CI/CD

These tests should be run:
1. Before deploying migrations to production
2. After any changes to migration scripts
3. As part of the CI/CD pipeline (with test database)

## Troubleshooting

### ConnectionRefusedError

**Problem**: Tests fail with "ConnectionRefusedError"

**Solution**: 
1. Check DATABASE_URL in .env file
2. Verify database is running
3. Check network connectivity to database

### Table Does Not Exist

**Problem**: Tests fail with "relation does not exist"

**Solution**: Run migrations first:
```bash
alembic upgrade head
```

### Permission Denied

**Problem**: Tests fail with "permission denied"

**Solution**: Ensure database user has permissions to:
- CREATE/DROP tables
- CREATE/DROP columns
- CREATE/DROP constraints
- INSERT/UPDATE/DELETE data

## Notes

- Tests use the `clean_database` fixture to ensure isolation
- Each test creates its own test data
- Tests simulate migrations using SQL DDL commands
- Tests verify both upgrade and downgrade paths
- All assertions include descriptive error messages

## Related Files

- `migrations/versions/20260306_001_add_schema_constraints.py`: Migration adding version columns
- `migrations/versions/20260306_005_create_inventory_movements.py`: Migration creating inventory_movements table
- `migrations/scripts/migrate_products.py`: Script for migrating product data
- `migrations/scripts/backup_database.py`: Script for backing up database before migration
- `migrations/data_migration_guide.md`: Guide for running data migrations
