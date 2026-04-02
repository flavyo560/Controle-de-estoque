"""
Property-based tests for import/export functionality.

**Validates: Requirements 13.1, 13.2**

This module tests the round-trip consistency of CSV export and import operations.
"""

import pytest
from hypothesis import given, strategies as st, settings
from decimal import Decimal
from typing import List

from src.domain.product import Product
from src.services.import_export_service import ImportExportService
from src.repositories.product_repository import ProductRepository
from src.services.validation_service import ValidationService


# Custom strategy for valid product data
@st.composite
def valid_product_strategy(draw):
    """Generate valid product data for testing."""
    return Product(
        sku=draw(st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='-_'
            )
        )).strip() or "SKU001",  # Ensure not empty after strip
        name=draw(st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters=' .-_'
            )
        )).strip() or "Product Name",  # Ensure not empty after strip
        description=draw(st.one_of(
            st.none(),
            st.text(
                min_size=0,
                max_size=500,
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd'),
                    whitelist_characters=' .-_'
                )
            )
        )),
        gender=draw(st.sampled_from(['M', 'F', 'U'])),
        brand=draw(st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters=' .-_&'
            )
        )).strip() or "Brand",  # Ensure not empty after strip
        reference=draw(st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='-_'
            )
        )).strip() or "REF001",  # Ensure not empty after strip
        size=draw(st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='-_/'
            )
        )).strip() or "M",  # Ensure not empty after strip
        quantity=draw(st.integers(min_value=0, max_value=10000)),
        price=draw(st.decimals(
            min_value=Decimal('0.01'),
            max_value=Decimal('99999.99'),
            places=2
        )),
        barcode=draw(st.one_of(
            st.none(),
            st.text(
                min_size=1,
                max_size=50,
                alphabet=st.characters(whitelist_categories=('Nd',))
            )
        )),
        min_stock=draw(st.integers(min_value=0, max_value=100))
    )


class TestImportExportRoundTrip:
    """Test suite for import/export round-trip consistency."""
    
    # Feature: sistema-estoque-melhorado, Property 15: Export-import round-trip consistency
    @given(products=st.lists(valid_product_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_export_import_round_trip_preserves_all_fields(
        self,
        products: List[Product]
    ):
        """
        **Validates: Requirements 13.1, 13.2**
        
        Property: For any valid product data, exporting to CSV then importing 
        from CSV should produce equivalent product records with all fields preserved.
        
        This test verifies that:
        1. Export produces valid CSV format
        2. Import can parse the exported CSV
        3. All product fields are preserved exactly (no data loss)
        4. Field types and values remain consistent
        """
        # Create service instance
        validator = ValidationService()
        import_export_service = ImportExportService(product_repo=None, validator=validator)
        
        # Export products to CSV
        csv_content = await import_export_service.export_products_to_csv(products)
        
        # Verify CSV is not empty
        assert csv_content, "Export should produce non-empty CSV content"
        assert len(csv_content) > 0, "CSV content should have length > 0"
        
        # Import products from CSV
        imported_products = await import_export_service.import_products_from_csv(csv_content)
        
        # Verify same number of products
        assert len(imported_products) == len(products), \
            f"Expected {len(products)} products, got {len(imported_products)}"
        
        # Verify each product's fields are preserved
        for original, imported in zip(products, imported_products):
            # String fields
            assert imported.sku == original.sku, \
                f"SKU mismatch: expected '{original.sku}', got '{imported.sku}'"
            assert imported.name == original.name, \
                f"Name mismatch: expected '{original.name}', got '{imported.name}'"
            assert imported.gender == original.gender, \
                f"Gender mismatch: expected '{original.gender}', got '{imported.gender}'"
            assert imported.brand == original.brand, \
                f"Brand mismatch: expected '{original.brand}', got '{imported.brand}'"
            assert imported.reference == original.reference, \
                f"Reference mismatch: expected '{original.reference}', got '{imported.reference}'"
            assert imported.size == original.size, \
                f"Size mismatch: expected '{original.size}', got '{imported.size}'"
            
            # Optional string fields (handle None and empty string equivalence)
            original_desc = original.description or ''
            imported_desc = imported.description or ''
            assert imported_desc == original_desc, \
                f"Description mismatch: expected '{original_desc}', got '{imported_desc}'"
            
            original_barcode = original.barcode or ''
            imported_barcode = imported.barcode or ''
            assert imported_barcode == original_barcode, \
                f"Barcode mismatch: expected '{original_barcode}', got '{imported_barcode}'"
            
            # Numeric fields
            assert imported.quantity == original.quantity, \
                f"Quantity mismatch: expected {original.quantity}, got {imported.quantity}"
            assert imported.min_stock == original.min_stock, \
                f"Min stock mismatch: expected {original.min_stock}, got {imported.min_stock}"
            
            # Decimal field (price) - must preserve precision
            assert imported.price == original.price, \
                f"Price mismatch: expected {original.price}, got {imported.price}"
            assert isinstance(imported.price, Decimal), \
                f"Price should be Decimal, got {type(imported.price)}"
            
            # Verify price has at most 2 decimal places
            price_tuple = imported.price.as_tuple()
            assert price_tuple.exponent >= -2, \
                f"Price should have at most 2 decimal places, got {imported.price}"
    
    # Feature: sistema-estoque-melhorado, Property 15: Export-import round-trip consistency
    @given(products=st.lists(valid_product_strategy(), min_size=1, max_size=5))
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_export_import_round_trip_is_idempotent(
        self,
        products: List[Product]
    ):
        """
        **Validates: Requirements 13.1, 13.2**
        
        Property: Multiple export-import cycles should produce identical results.
        
        This test verifies that:
        export(import(export(products))) == export(products)
        """
        # Create service instance
        validator = ValidationService()
        import_export_service = ImportExportService(product_repo=None, validator=validator)
        
        # First export
        csv_content_1 = await import_export_service.export_products_to_csv(products)
        
        # Import and re-export
        imported_products_1 = await import_export_service.import_products_from_csv(csv_content_1)
        csv_content_2 = await import_export_service.export_products_to_csv(imported_products_1)
        
        # Import again and re-export
        imported_products_2 = await import_export_service.import_products_from_csv(csv_content_2)
        csv_content_3 = await import_export_service.export_products_to_csv(imported_products_2)
        
        # CSV content should be identical after first round-trip
        assert csv_content_2 == csv_content_3, \
            "Multiple export-import cycles should produce identical CSV content"
        
        # Verify products are identical
        assert len(imported_products_1) == len(imported_products_2)
        for p1, p2 in zip(imported_products_1, imported_products_2):
            assert p1.sku == p2.sku
            assert p1.name == p2.name
            assert p1.price == p2.price
            assert p1.quantity == p2.quantity
    
    # Feature: sistema-estoque-melhorado, Property 15: Export-import round-trip consistency
    @pytest.mark.asyncio
    async def test_export_empty_list_produces_empty_csv(self):
        """
        **Validates: Requirements 13.2**
        
        Property: Exporting an empty list should produce empty CSV content.
        """
        validator = ValidationService()
        import_export_service = ImportExportService(product_repo=None, validator=validator)
        
        csv_content = await import_export_service.export_products_to_csv([])
        assert csv_content == "", "Empty product list should produce empty CSV"
    
    # Feature: sistema-estoque-melhorado, Property 15: Export-import round-trip consistency
    @pytest.mark.asyncio
    async def test_import_empty_csv_raises_validation_error(self):
        """
        **Validates: Requirements 13.1, 13.3**
        
        Property: Importing empty CSV content should raise ValidationError.
        """
        from src.exceptions import ValidationError
        
        validator = ValidationService()
        import_export_service = ImportExportService(product_repo=None, validator=validator)
        
        with pytest.raises(ValidationError) as exc_info:
            await import_export_service.import_products_from_csv("")
        
        assert "empty" in str(exc_info.value).lower()
    
    # Feature: sistema-estoque-melhorado, Property 15: Export-import round-trip consistency
    @pytest.mark.asyncio
    async def test_import_csv_with_missing_headers_raises_validation_error(self):
        """
        **Validates: Requirements 13.1, 13.3**
        
        Property: Importing CSV with missing required headers should raise ValidationError.
        """
        from src.exceptions import ValidationError
        
        validator = ValidationService()
        import_export_service = ImportExportService(product_repo=None, validator=validator)
        
        # CSV with only some headers
        incomplete_csv = "sku,name,price\nTEST001,Test Product,10.99\n"
        
        with pytest.raises(ValidationError) as exc_info:
            await import_export_service.import_products_from_csv(incomplete_csv)
        
        error_message = str(exc_info.value).lower()
        assert "missing" in error_message or "header" in error_message
