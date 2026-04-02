# End-to-End Integration Tests

**Validates: Requirements 9.3, 4.1**

This directory contains comprehensive end-to-end integration tests that verify the complete DEKIDS system works correctly across all layers (UI → Service → Repository).

## Test Files

### test_e2e_user_journeys.py

Complete user journey tests covering:

1. **TestCompleteUserJourney**
   - `test_happy_path_login_create_product_sale_report`: Full workflow from login to report generation
   - `test_multi_product_sale_journey`: Multiple products in a single sale

2. **TestErrorScenariosAcrossLayers**
   - `test_insufficient_stock_error_propagation`: Stock validation across layers
   - `test_authentication_error_prevents_operations`: Auth errors block operations
   - `test_validation_error_at_service_layer`: Service layer validation
   - `test_not_found_error_propagation`: NotFoundError handling

3. **TestDataConsistencyAcrossOperations**
   - `test_concurrent_sales_maintain_consistency`: Concurrent operations
   - `test_sale_cancellation_restores_consistency`: Cancellation rollback

4. **TestTransactionRollbackScenarios**
   - `test_sale_creation_rollback_on_payment_error`: Payment validation rollback
   - `test_multiple_operations_rollback_together`: Multi-operation transactions

### test_e2e_cross_layer_integration.py

Cross-layer integration tests covering:

1. **TestCacheInvalidationAcrossLayers**
   - `test_product_cache_invalidation_on_update`: Cache invalidation on updates
   - `test_search_cache_invalidation_on_create`: Search cache invalidation

2. **TestAuditTrailAcrossOperations**
   - `test_audit_trail_for_complete_workflow`: Audit logging verification

3. **TestSessionManagementAcrossRequests**
   - `test_session_expiration_prevents_operations`: Session expiration handling
   - `test_session_ip_validation`: IP address validation

4. **TestComplexBusinessLogicSpanningServices**
   - `test_low_stock_alert_after_multiple_sales`: Low stock alerts
   - `test_report_accuracy_after_sales_and_cancellations`: Report accuracy
   - `test_inventory_movements_tracking_across_operations`: Movement tracking

## Test Coverage

These tests validate:

- **3-Layer Architecture (Requirement 4.1)**: UI → Service → Repository separation
- **Integration Testing (Requirement 9.3)**: All layers working together
- **Transaction Safety**: Rollback on errors
- **Data Consistency**: Across all operations
- **Error Propagation**: Errors handled correctly at each layer
- **Cache Management**: Invalidation and consistency
- **Audit Trail**: Complete operation logging
- **Session Management**: Authentication and authorization
- **Business Logic**: Complex workflows spanning multiple services

## Running the Tests

### Prerequisites

1. Database must be running and accessible
2. Environment variables configured (DATABASE_URL or TEST_DATABASE_URL)
3. All migrations applied

### Run All Integration Tests

```bash
pytest tests/integration/ -v
```

### Run Specific Test File

```bash
pytest tests/integration/test_e2e_user_journeys.py -v
```

### Run Specific Test Class

```bash
pytest tests/integration/test_e2e_user_journeys.py::TestCompleteUserJourney -v
```

### Run Specific Test

```bash
pytest tests/integration/test_e2e_user_journeys.py::TestCompleteUserJourney::test_happy_path_login_create_product_sale_report -v
```

### Run with Coverage

```bash
pytest tests/integration/ --cov=src --cov-report=html
```

## Test Database Setup

These tests require a clean database for each test. The `clean_database` fixture handles this automatically.

### Manual Database Setup

If you need to manually set up the test database:

```bash
# Apply migrations
alembic upgrade head

# Run tests
pytest tests/integration/ -v
```

## Test Patterns

### Complete User Journey Pattern

```python
async def test_complete_journey(
    auth_service,
    inventory_service,
    sales_service,
    clean_database
):
    # 1. Create and authenticate user
    user = await auth_service.register_user(...)
    session = await auth_service.authenticate(...)
    
    # 2. Perform business operations
    product = await inventory_service.create_product(...)
    sale = await sales_service.create_sale(...)
    
    # 3. Verify results
    assert sale.final_amount == expected_amount
    assert product.quantity == expected_quantity
```

### Error Scenario Pattern

```python
async def test_error_scenario(
    service,
    clean_database
):
    # Setup
    entity = await service.create(...)
    
    # Trigger error condition
    with pytest.raises(ExpectedError):
        await service.operation_that_should_fail(...)
    
    # Verify no side effects
    unchanged = await repository.get_by_id(entity.id)
    assert unchanged.state == original_state
```

### Transaction Rollback Pattern

```python
async def test_transaction_rollback(
    service,
    repository,
    clean_database
):
    # Setup initial state
    initial_state = await repository.get_state()
    
    # Attempt operation that should fail
    with pytest.raises(ValidationError):
        await service.complex_operation(...)
    
    # Verify rollback
    final_state = await repository.get_state()
    assert final_state == initial_state
```

## Troubleshooting

### Database Connection Errors

If you see `ConnectionRefusedError`:
- Verify DATABASE_URL is set correctly
- Ensure database is running
- Check network connectivity

### Test Failures Due to Data

If tests fail due to existing data:
- The `clean_database` fixture should handle cleanup
- Manually clean: `DELETE FROM <table> WHERE id > 0`

### Async Test Issues

If you see async-related errors:
- Ensure pytest-asyncio is installed
- Check that fixtures are properly marked with `async`
- Verify event loop configuration in conftest.py

## Best Practices

1. **Use clean_database fixture**: Always use this fixture to ensure clean state
2. **Test isolation**: Each test should be independent
3. **Descriptive names**: Test names should describe what they test
4. **Comprehensive assertions**: Verify all expected outcomes
5. **Error testing**: Test both success and failure paths
6. **Documentation**: Add docstrings explaining what each test validates

## Future Enhancements

Potential additions to the test suite:

1. **Performance Tests**: Measure response times under load
2. **Concurrency Tests**: Test true concurrent operations with asyncio.gather
3. **UI Integration**: Add Flet UI component tests
4. **API Tests**: Test REST API endpoints when implemented
5. **Security Tests**: Test authentication and authorization edge cases
6. **Data Migration Tests**: Test database migration scenarios
