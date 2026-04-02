"""
Unit tests for import/export functionality.

Tests CSV export generation, import validation, and data integrity.

**Validates: Requirements 9.1, 13.1**
"""

import pytest
import csv
import os
from decimal import Decimal
from pathlib import Path
from typing import List, Dict

from src.services.import_export_service import ImportExportService
from src.domain.product import ProductCreate


class TestCSVExport:
    """Test CSV export functionality."""
    
    def test_export_generates_valid_csv(self, tmp_path):
        """
        Test that export generates a valid CSV file with correct structure.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Test data
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product 1',
                'price': '10.50',
                'quantity': '100'
            },
            {
                'sku': 'TEST002',
                'name': 'Test Product 2',
                'price': '25.99',
                'quantity': '50'
            }
        ]
        
        # Export to CSV
        filepath = tmp_path / "test_export.csv"
        result = service.export_to_csv(data, str(filepath))
        
        # Verify export succeeded
        assert result is True
        assert filepath.exists()
        
        # Read and verify CSV content
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Verify row count
        assert len(rows) == 2
        
        # Verify headers
        assert set(rows[0].keys()) == {'sku', 'name', 'price', 'quantity'}
        
        # Verify data
        assert rows[0]['sku'] == 'TEST001'
        assert rows[0]['name'] == 'Test Product 1'
        assert rows[0]['price'] == '10.50'
        assert rows[0]['quantity'] == '100'
        
        assert rows[1]['sku'] == 'TEST002'
        assert rows[1]['name'] == 'Test Product 2'
    
    def test_export_empty_data_returns_false(self, tmp_path):
        """
        Test that exporting empty data returns False.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        filepath = tmp_path / "empty_export.csv"
        result = service.export_to_csv([], str(filepath))
        
        assert result is False
        assert not filepath.exists()
    
    def test_export_creates_parent_directories(self, tmp_path):
        """
        Test that export creates parent directories if they don't exist.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        data = [{'sku': 'TEST001', 'name': 'Test'}]
        
        # Path with non-existent directories
        filepath = tmp_path / "subdir1" / "subdir2" / "export.csv"
        result = service.export_to_csv(data, str(filepath))
        
        assert result is True
        assert filepath.exists()
        assert filepath.parent.exists()
    
    def test_export_handles_complex_values(self, tmp_path):
        """
        Test that export converts complex values (dict, list, Decimal) to strings.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product',
                'price': Decimal('19.99'),
                'metadata': {'color': 'red', 'size': 'M'},
                'tags': ['new', 'sale']
            }
        ]
        
        filepath = tmp_path / "complex_export.csv"
        result = service.export_to_csv(data, str(filepath))
        
        assert result is True
        
        # Read and verify
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        # Complex values should be converted to strings
        assert "color" in rows[0]['metadata']
        assert "new" in rows[0]['tags']
        assert rows[0]['price'] == '19.99'
    
    def test_export_utf8_encoding(self, tmp_path):
        """
        Test that export uses UTF-8 BOM encoding for Excel compatibility.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Data with special characters
        data = [
            {
                'sku': 'TEST001',
                'name': 'Tênis Esportivo',
                'description': 'Produto com acentuação'
            }
        ]
        
        filepath = tmp_path / "utf8_export.csv"
        result = service.export_to_csv(data, str(filepath))
        
        assert result is True
        
        # Read with UTF-8 BOM encoding
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # Verify special characters are preserved
        assert 'Tênis' in content
        assert 'acentuação' in content


class TestCSVImport:
    """Test CSV import functionality."""
    
    def test_import_reads_valid_csv(self, tmp_path):
        """
        Test that import correctly reads a valid CSV file.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Create test CSV
        filepath = tmp_path / "test_import.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'price', 'quantity'])
            writer.writeheader()
            writer.writerow({'sku': 'TEST001', 'name': 'Product 1', 'price': '10.50', 'quantity': '100'})
            writer.writerow({'sku': 'TEST002', 'name': 'Product 2', 'price': '25.99', 'quantity': '50'})
        
        # Import CSV
        success, data, errors = service.import_from_csv(str(filepath))
        
        assert success is True
        assert len(errors) == 0
        assert len(data) == 2
        
        assert data[0]['sku'] == 'TEST001'
        assert data[0]['name'] == 'Product 1'
        assert data[1]['sku'] == 'TEST002'
    
    def test_import_file_not_found(self):
        """
        Test that import handles missing file gracefully.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        success, data, errors = service.import_from_csv("nonexistent.csv")
        
        assert success is False
        assert len(data) == 0
        assert len(errors) > 0
        assert "not found" in errors[0].lower()
    
    def test_import_empty_csv(self, tmp_path):
        """
        Test that import handles empty CSV file.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Create empty CSV with only headers
        filepath = tmp_path / "empty.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'price', 'quantity'])
            writer.writeheader()
        
        success, data, errors = service.import_from_csv(str(filepath))
        
        assert success is False
        assert len(data) == 0
        assert any("no data" in err.lower() for err in errors)
    
    def test_import_no_headers(self, tmp_path):
        """
        Test that import handles CSV without headers.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Create CSV without headers
        filepath = tmp_path / "no_headers.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            f.write("")
        
        success, data, errors = service.import_from_csv(str(filepath))
        
        assert success is False
        assert len(errors) > 0
    
    def test_import_strips_whitespace(self, tmp_path):
        """
        Test that import strips whitespace from values.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Create CSV with whitespace
        filepath = tmp_path / "whitespace.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'price', 'quantity'])
            writer.writeheader()
            writer.writerow({'sku': '  TEST001  ', 'name': '  Product  ', 'price': ' 10.50 ', 'quantity': ' 100 '})
        
        success, data, errors = service.import_from_csv(str(filepath))
        
        assert success is True
        assert data[0]['sku'] == 'TEST001'
        assert data[0]['name'] == 'Product'
        assert data[0]['price'] == '10.50'


class TestProductDataValidation:
    """Test product data validation during import."""
    
    def test_validate_correct_product_data(self):
        """
        Test that validation accepts correct product data.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product',
                'price': '19.99',
                'quantity': '100',
                'description': 'A test product',
                'gender': 'M',
                'brand': 'TestBrand',
                'reference': 'REF001',
                'size': 'M',
                'min_stock': '10'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(errors) == 0
        assert len(valid_products) == 1
        assert valid_products[0].sku == 'TEST001'
        assert valid_products[0].name == 'Test Product'
        assert valid_products[0].price == Decimal('19.99')
        assert valid_products[0].quantity == 100
    
    def test_validate_missing_required_columns(self):
        """
        Test that validation detects missing required columns.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Missing 'price' column
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product',
                'quantity': '100'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
        assert any("missing required columns" in err.lower() for err in errors)
        assert any("price" in err.lower() for err in errors)
    
    def test_validate_invalid_price(self):
        """
        Test that validation detects invalid price values.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Test negative price
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product',
                'price': '-10.50',
                'quantity': '100'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
        assert any("price" in err.lower() for err in errors)
        
        # Test invalid price format
        data = [
            {
                'sku': 'TEST002',
                'name': 'Test Product',
                'price': 'invalid',
                'quantity': '100'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
        assert any("invalid price" in err.lower() for err in errors)
    
    def test_validate_invalid_quantity(self):
        """
        Test that validation detects invalid quantity values.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Test negative quantity
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product',
                'price': '10.50',
                'quantity': '-5'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
        assert any("quantity" in err.lower() and "negative" in err.lower() for err in errors)
        
        # Test invalid quantity format
        data = [
            {
                'sku': 'TEST002',
                'name': 'Test Product',
                'price': '10.50',
                'quantity': 'abc'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
        assert any("invalid quantity" in err.lower() for err in errors)
    
    def test_validate_invalid_sku(self):
        """
        Test that validation detects invalid SKU values.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Test empty SKU
        data = [
            {
                'sku': '',
                'name': 'Test Product',
                'price': '10.50',
                'quantity': '100'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
        assert any("sku" in err.lower() for err in errors)
        
        # Test SKU too long
        data = [
            {
                'sku': 'A' * 51,  # 51 characters
                'name': 'Test Product',
                'price': '10.50',
                'quantity': '100'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
    
    def test_validate_invalid_gender(self):
        """
        Test that validation detects invalid gender values.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product',
                'price': '10.50',
                'quantity': '100',
                'gender': 'X'  # Invalid gender
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(valid_products) == 0
        assert len(errors) > 0
        assert any("gender" in err.lower() for err in errors)
    
    def test_validate_multiple_rows_with_errors(self):
        """
        Test that validation reports all errors from multiple rows.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        data = [
            {
                'sku': 'TEST001',
                'name': 'Valid Product',
                'price': '10.50',
                'quantity': '100'
            },
            {
                'sku': 'TEST002',
                'name': 'Invalid Product',
                'price': '-5.00',  # Invalid price
                'quantity': '50'
            },
            {
                'sku': 'TEST003',
                'name': 'Another Invalid',
                'price': '15.00',
                'quantity': 'abc'  # Invalid quantity
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        # Should have 1 valid product and 2 errors
        assert len(valid_products) == 1
        assert len(errors) == 2
        assert valid_products[0].sku == 'TEST001'
    
    def test_validate_uses_default_values(self):
        """
        Test that validation uses default values for optional fields.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Minimal data with only required fields
        data = [
            {
                'sku': 'TEST001',
                'name': 'Test Product',
                'price': '10.50',
                'quantity': '100'
            }
        ]
        
        valid_products, errors = service.validate_product_data(data)
        
        assert len(errors) == 0
        assert len(valid_products) == 1
        
        product = valid_products[0]
        assert product.gender == 'U'  # Default
        assert product.brand == 'Unknown'  # Default
        assert product.reference == 'TEST001'  # Defaults to SKU
        assert product.size == 'U'  # Default
        assert product.min_stock == 5  # Default


class TestImportPreview:
    """Test import preview functionality."""
    
    def test_preview_returns_first_n_rows(self, tmp_path):
        """
        Test that preview returns only the first N rows.
        
        **Validates: Requirements 13.1**
        """
        service = ImportExportService()
        
        # Create CSV with 15 rows
        filepath = tmp_path / "preview_test.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'price', 'quantity'])
            writer.writeheader()
            for i in range(15):
                writer.writerow({
                    'sku': f'TEST{i:03d}',
                    'name': f'Product {i}',
                    'price': '10.00',
                    'quantity': '100'
                })
        
        # Preview first 10 rows
        success, preview_data, errors = service.preview_import(str(filepath), num_rows=10)
        
        assert success is True
        assert len(errors) == 0
        assert len(preview_data) == 10
        assert preview_data[0]['sku'] == 'TEST000'
        assert preview_data[9]['sku'] == 'TEST009'
    
    def test_preview_handles_fewer_rows(self, tmp_path):
        """
        Test that preview handles files with fewer rows than requested.
        
        **Validates: Requirements 13.1**
        """
        service = ImportExportService()
        
        # Create CSV with only 5 rows
        filepath = tmp_path / "small_preview.csv"
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['sku', 'name', 'price', 'quantity'])
            writer.writeheader()
            for i in range(5):
                writer.writerow({
                    'sku': f'TEST{i:03d}',
                    'name': f'Product {i}',
                    'price': '10.00',
                    'quantity': '100'
                })
        
        # Request 10 rows but only 5 exist
        success, preview_data, errors = service.preview_import(str(filepath), num_rows=10)
        
        assert success is True
        assert len(errors) == 0
        assert len(preview_data) == 5


class TestImportExportIntegration:
    """Test integration between import and export."""
    
    def test_export_then_import_roundtrip(self, tmp_path):
        """
        Test that data exported can be imported back correctly.
        
        **Validates: Requirements 9.1, 13.1**
        """
        service = ImportExportService()
        
        # Original data
        original_data = [
            {
                'sku': 'TEST001',
                'name': 'Product 1',
                'price': '19.99',
                'quantity': '100',
                'description': 'Test product 1',
                'gender': 'M',
                'brand': 'TestBrand',
                'reference': 'REF001',
                'size': 'M',
                'min_stock': '10'
            },
            {
                'sku': 'TEST002',
                'name': 'Product 2',
                'price': '29.99',
                'quantity': '50',
                'description': 'Test product 2',
                'gender': 'F',
                'brand': 'TestBrand',
                'reference': 'REF002',
                'size': 'L',
                'min_stock': '5'
            }
        ]
        
        # Export
        export_path = tmp_path / "export.csv"
        export_result = service.export_to_csv(original_data, str(export_path))
        assert export_result is True
        
        # Import
        import_success, imported_data, import_errors = service.import_from_csv(str(export_path))
        assert import_success is True
        assert len(import_errors) == 0
        assert len(imported_data) == 2
        
        # Validate imported data
        valid_products, validation_errors = service.validate_product_data(imported_data)
        assert len(validation_errors) == 0
        assert len(valid_products) == 2
        
        # Verify data integrity
        assert valid_products[0].sku == 'TEST001'
        assert valid_products[0].name == 'Product 1'
        assert valid_products[0].price == Decimal('19.99')
        assert valid_products[0].quantity == 100
        
        assert valid_products[1].sku == 'TEST002'
        assert valid_products[1].name == 'Product 2'
