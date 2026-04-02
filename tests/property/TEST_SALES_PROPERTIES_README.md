# Sales Transaction Atomicity Property Tests

## Overview

This test suite implements **Property 12: Sale transaction atomicity** as specified in task 39.2 of the sistema-estoque-melhorado spec.

**Validates: Requirements 19.1**

## Test Coverage

The test suite includes 4 comprehensive property-based tests:

### 1. `test_sale_transaction_atomicity_insufficient_stock`
Tests that when a sale fails due to insufficient stock:
- Product quantity remains unchanged
- No sale record is created
- No inventory movements are recorded
- Transaction rollback works correctly

**Strategy**: Generates random products and requests quantities exceeding available stock (1.1x to 3.0x multiplier).

### 2. `test_sale_transaction_atomicity_invalid_payment`
Tests that when a sale fails due to payment validation (payment amount doesn't match total):
- Product quantity remains unchanged
- No sale record is created
- No inventory movements are recorded

**Strategy**: Creates valid products but provides incorrect payment amounts (total - $10.00).

### 3. `test_sale_transaction_atomicity_nonexistent_product`
Tests that when a sale fails due to a nonexistent product in multi-item sales:
- Stock for valid products remains unchanged
- No partial sale records are created
- Transaction rollback prevents partial updates

**Strategy**: Creates multi-item sales with one valid and one nonexistent product.

### 4. `test_successful_sale_modifies_stock` (Positive Test)
Tests that successful sales DO correctly modify stock:
- Product quantity is reduced by sale quantity
- Sale record is created
- Inventory movement is recorded

**Strategy**: Creates valid sales with sufficient stock to verify atomicity works both ways.

## Running the Tests

### Prerequisites

1. **Database Connection**: Tests require a PostgreSQL database connection
   - Set `DATABASE_URL` or `TEST_DATABASE_URL` environment variable
   - Example: `postgresql://user:pass@localhost:5432/testdb`

2. **Database Schema**: Ensure all migrations are applied
   ```bash
   alembic upgrade head
   ```

3. **Dependencies**: Install test dependencies
   ```bash
   pip install pytest pytest-asyncio hypothesis
   ```

### Execute Tests

Run all sales property tests:
```bash
python -m pytest tests/property/test_sales_properties.py -v
```

Run with Hypothesis statistics:
```bash
python -m pytest tests/property/test_sales_properties.py -v --hypothesis-show-statistics
```

Run specific test:
```bash
python -m pytest tests/property/test_sales_properties.py::TestSalesProperties::test_sale_transaction_atomicity_insufficient_stock -v
```

### Expected Behavior

- **Insufficient Stock Test**: Should generate 50 examples, all failing with `InsufficientStockError`
- **Invalid Payment Test**: Should generate 50 examples, all failing with `ValidationError`
- **Nonexistent Product Test**: Should generate 50 examples, all failing with `NotFoundError`
- **Successful Sale Test**: Should generate 30 examples, all succeeding with correct stock updates

## Test Configuration

- **Max Examples**: 50 for failure tests, 30 for success test
- **Deadline**: 5000ms per test case
- **Hypothesis Profile**: default

## Property Validation

Each test validates the core property:

> **When a sale transaction fails for ANY reason, the system state must remain unchanged - no partial updates, no orphaned records, no stock modifications.**

This ensures:
1. **Atomicity**: All operations succeed or all fail together
2. **Consistency**: Database constraints are maintained
3. **Isolation**: Concurrent transactions don't interfere
4. **Durability**: Committed changes persist, rolled back changes don't

## Troubleshooting

### Database Connection Errors
```
ConnectionRefusedError: [WinError 1225] O computador remoto recusou a conexão de rede
```

**Solution**: Ensure PostgreSQL is running and `DATABASE_URL` is correctly configured.

### Test Timeout
If tests timeout, increase the deadline:
```python
@settings(max_examples=50, deadline=10000)  # 10 seconds
```

### Hypothesis Flaky Tests
If tests occasionally fail, check for:
- Race conditions in async code
- Database connection pool exhaustion
- Insufficient test data cleanup

## Integration with CI/CD

Add to your CI pipeline:
```yaml
- name: Run Property Tests
  run: |
    python -m pytest tests/property/test_sales_properties.py -v --hypothesis-show-statistics
  env:
    DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
```

## Related Files

- **Implementation**: `src/services/sales_service.py`
- **Domain Models**: `src/domain/sale.py`, `src/domain/product.py`
- **Repositories**: `src/repositories/sale_repository.py`, `src/repositories/product_repository.py`
- **Spec**: `.kiro/specs/sistema-estoque-melhorado/tasks.md` (Task 39.2)
- **Requirements**: `.kiro/specs/sistema-estoque-melhorado/requirements.md` (Requirement 19.1)
