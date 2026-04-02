# Import/Export Testing Documentation

## Overview

This document describes the comprehensive test suite for the import/export functionality of the DEKIDS inventory system. The tests validate CSV export generation, import validation, and data integrity as specified in Requirements 9.1 and 13.1.

## Implementation Summary

### New Components Created

1. **src/services/import_export_service.py**
   - `ImportExportService` class providing CSV import/export functionality
   - Export to CSV with UTF-8 BOM encoding for Excel compatibility
   - Import from CSV with validation and error reporting
   - Product data validation against Pydantic models
   - Preview functionality for import operations

2. **tests/unit/test_import_export.py**
   - Comprehensive test suite with 21 unit tests
   - Tests for export, import, validation, and integration scenarios

## Test Coverage

### CSV Export Tests (5 tests)

1. **test_export_generates_valid_csv**
   - Validates that export creates a properly formatted CSV file
   - Verifies headers and data integrity
   - **Validates: Requirements 9.1, 13.1**

2. **test_export_empty_data_returns_false**
   - Ensures empty data is rejected
   - **Validates: Requirements 9.1, 13.1**

3. **test_export_creates_parent_directories**
   - Verifies automatic directory creation
   - **Validates: Requirements 9.1, 13.1**

4. **test_export_handles_complex_values**
   - Tests conversion of Decimal, dict, and list types to strings
   - **Validates: Requirements 9.1, 13.1**

5. **test_export_utf8_encoding**
   - Validates UTF-8 BOM encoding for Excel compatibility
   - Tests special character preservation (acentuação)
   - **Validates: Requirements 9.1, 13.1**

### CSV Import Tests (5 tests)

6. **test_import_reads_valid_csv**
   - Validates successful import of well-formed CSV
   - **Validates: Requirements 9.1, 13.1**

7. **test_import_file_not_found**
   - Tests graceful handling of missing files
   - **Validates: Requirements 9.1, 13.1**

8. **test_import_empty_csv**
   - Ensures empty CSV files are rejected
   - **Validates: Requirements 9.1, 13.1**

9. **test_import_no_headers**
   - Tests handling of CSV without headers
   - **Validates: Requirements 9.1, 13.1**

10. **test_import_strips_whitespace**
    - Validates automatic whitespace trimming
    - **Validates: Requirements 9.1, 13.1**

### Product Data Validation Tests (8 tests)

11. **test_validate_correct_product_data**
    - Validates acceptance of correct product data
    - **Validates: Requirements 9.1, 13.1**

12. **test_validate_missing_required_columns**
    - Detects missing required columns (sku, name, price, quantity)
    - **Validates: Requirements 9.1, 13.1**

13. **test_validate_invalid_price**
    - Tests rejection of negative and non-numeric prices
    - **Validates: Requirements 9.1, 13.1**

14. **test_validate_invalid_quantity**
    - Tests rejection of negative and non-numeric quantities
    - **Validates: Requirements 9.1, 13.1**

15. **test_validate_invalid_sku**
    - Tests rejection of empty or too-long SKUs
    - **Validates: Requirements 9.1, 13.1**

16. **test_validate_invalid_gender**
    - Tests rejection of invalid gender values (must be M, F, or U)
    - **Validates: Requirements 9.1, 13.1**

17. **test_validate_multiple_rows_with_errors**
    - Validates that all errors are reported across multiple rows
    - Ensures valid rows are still processed
    - **Validates: Requirements 9.1, 13.1**

18. **test_validate_uses_default_values**
    - Tests that optional fields use appropriate defaults
    - **Validates: Requirements 9.1, 13.1**

### Import Preview Tests (2 tests)

19. **test_preview_returns_first_n_rows**
    - Validates preview functionality returns only requested rows
    - **Validates: Requirements 13.1**

20. **test_preview_handles_fewer_rows**
    - Tests preview with files smaller than requested size
    - **Validates: Requirements 13.1**

### Integration Tests (1 test)

21. **test_export_then_import_roundtrip**
    - Tests complete export → import → validate cycle
    - Ensures data integrity through full roundtrip
    - **Validates: Requirements 9.1, 13.1**

## Existing Export Tests

The following tests already existed for the legacy export functionality in `relatorios.py`:

1. **test_exportar_relatorio_csv_basico** - Basic CSV export
2. **test_exportar_relatorio_csv_vazio** - Empty data handling
3. **test_exportar_relatorio_csv_cria_diretorios** - Directory creation
4. **test_exportar_relatorio_csv_com_valores_complexos** - Complex values
5. **test_exportar_relatorio_csv_encoding_utf8_bom** - UTF-8 BOM encoding

All existing tests continue to pass.

## Requirements Validation

### Requirement 9.1 (Automated Testing Infrastructure)
- ✅ Unit tests for all import/export functions
- ✅ Integration tests for complete workflows
- ✅ Mock-free testing using temporary files

### Requirement 13.1 (Bulk Import and Export)
- ✅ CSV export with all product fields
- ✅ CSV import with validation
- ✅ Validation reports all errors before import
- ✅ Preview functionality for first 10 rows
- ✅ UTF-8 BOM encoding for Excel compatibility

## Test Execution

### Run All Import/Export Tests
```bash
python -m pytest tests/unit/test_import_export.py -v
```

### Run Specific Test Classes
```bash
# Export tests only
python -m pytest tests/unit/test_import_export.py::TestCSVExport -v

# Import tests only
python -m pytest tests/unit/test_import_export.py::TestCSVImport -v

# Validation tests only
python -m pytest tests/unit/test_import_export.py::TestProductDataValidation -v
```

### Run Legacy Export Tests
```bash
python -m pytest tests/unit/test_relatorios.py -k "exportar_relatorio_csv" -v
```

## Test Results

**All 21 new tests PASSED** ✅
**All 5 existing export tests PASSED** ✅

Total: 26 tests covering import/export functionality

## Key Features Tested

1. **Export Functionality**
   - Valid CSV generation with proper structure
   - UTF-8 BOM encoding for Excel compatibility
   - Complex value handling (Decimal, dict, list)
   - Directory creation
   - Empty data rejection

2. **Import Functionality**
   - CSV file reading
   - Header validation
   - Whitespace trimming
   - Error handling for missing files
   - Empty file detection

3. **Data Validation**
   - Required field checking
   - Data type validation (price, quantity)
   - Range validation (price > 0, quantity >= 0)
   - Length validation (SKU, name)
   - Enum validation (gender)
   - Default value assignment
   - Multi-row error reporting

4. **Preview Functionality**
   - First N rows preview
   - Handling of small files

5. **Integration**
   - Complete export → import → validate roundtrip
   - Data integrity preservation

## Usage Example

```python
from src.services.import_export_service import ImportExportService

service = ImportExportService()

# Export products to CSV
products = [
    {
        'sku': 'PROD001',
        'name': 'Test Product',
        'price': '19.99',
        'quantity': '100'
    }
]
service.export_to_csv(products, 'products.csv')

# Preview import
success, preview, errors = service.preview_import('products.csv', num_rows=10)

# Import and validate
success, data, errors = service.import_from_csv('products.csv')
valid_products, validation_errors = service.validate_product_data(data)
```

## Notes

- All tests use temporary directories (`tmp_path` fixture) for file operations
- Tests are isolated and don't affect the actual database
- UTF-8 BOM encoding ensures Excel compatibility
- Validation follows Pydantic model constraints from `src/domain/product.py`
- Error messages are user-friendly and include row numbers
