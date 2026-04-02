"""
Import/Export Service for bulk data operations.

This module provides CSV import and export functionality for products.
"""

import csv
import io
from typing import List, Dict, Any
from decimal import Decimal
from pathlib import Path

from src.domain.product import Product, ProductCreate
from src.repositories.product_repository import ProductRepository
from src.services.validation_service import ValidationService
from src.exceptions import ValidationError


class ImportExportService:
    """Service for importing and exporting data in CSV format."""
    
    def __init__(
        self,
        product_repo: ProductRepository = None,
        validator: ValidationService = None
    ):
        """
        Initialize the import/export service.
        
        Args:
            product_repo: Repository for product data access (optional for round-trip tests)
            validator: Service for input validation (optional, will create if not provided)
        """
        self.product_repo = product_repo
        self.validator = validator or ValidationService()
    
    async def export_products_to_csv(self, products: List[Product]) -> str:
        """
        Export products to CSV format.
        
        Args:
            products: List of Product objects to export
            
        Returns:
            CSV content as string
            
        Validates: Requirements 13.2
        """
        if not products:
            return ""
        
        # Define CSV headers matching Product fields
        headers = [
            'sku', 'name', 'description', 'gender', 'brand',
            'reference', 'size', 'quantity', 'price', 'barcode', 'min_stock'
        ]
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        for product in products:
            row = {
                'sku': product.sku,
                'name': product.name,
                'description': product.description or '',
                'gender': product.gender,
                'brand': product.brand,
                'reference': product.reference,
                'size': product.size,
                'quantity': product.quantity,
                'price': str(product.price),  # Convert Decimal to string
                'barcode': product.barcode or '',
                'min_stock': product.min_stock
            }
            writer.writerow(row)
        
        return output.getvalue()
    
    async def import_products_from_csv(self, csv_content: str) -> List[Product]:
        """
        Import products from CSV format.
        
        Args:
            csv_content: CSV content as string
            
        Returns:
            List of Product objects created from CSV
            
        Raises:
            ValidationError: If CSV format is invalid or data validation fails
            
        Validates: Requirements 13.1, 13.3
        """
        if not csv_content or not csv_content.strip():
            raise ValidationError("CSV content is empty")
        
        # Parse CSV
        input_stream = io.StringIO(csv_content)
        reader = csv.DictReader(input_stream)
        
        # Validate headers
        expected_headers = {
            'sku', 'name', 'description', 'gender', 'brand',
            'reference', 'size', 'quantity', 'price', 'barcode', 'min_stock'
        }
        
        if not reader.fieldnames:
            raise ValidationError("CSV has no headers")
        
        actual_headers = set(reader.fieldnames)
        missing_headers = expected_headers - actual_headers
        
        if missing_headers:
            raise ValidationError(
                f"CSV is missing required headers: {', '.join(sorted(missing_headers))}"
            )
        
        # Parse and validate each row
        products = []
        errors = []
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
            try:
                # Convert empty strings to None for optional fields
                # Strip whitespace and treat whitespace-only strings as empty
                description = row['description'].strip() if row['description'].strip() else None
                barcode = row['barcode'].strip() if row['barcode'].strip() else None
                
                # For required string fields, ensure they're not empty after stripping
                sku = row['sku'].strip()
                name = row['name'].strip()
                gender = row['gender'].strip()
                brand = row['brand'].strip()
                reference = row['reference'].strip()
                size = row['size'].strip()
                
                # If any required field is empty after stripping, it's invalid
                if not sku or not name or not gender or not brand or not reference or not size:
                    errors.append(f"Row {row_num}: Required fields cannot be empty")
                    continue
                
                # Create ProductCreate object (validates data)
                product_data = ProductCreate(
                    sku=sku,
                    name=name,
                    description=description,
                    gender=gender,
                    brand=brand,
                    reference=reference,
                    size=size,
                    quantity=int(row['quantity']),
                    price=Decimal(row['price']),
                    barcode=barcode,
                    min_stock=int(row['min_stock']) if row['min_stock'].strip() else 5
                )
                
                # Convert to Product (for round-trip testing without DB)
                product = Product(
                    sku=product_data.sku,
                    name=product_data.name,
                    description=product_data.description,
                    gender=product_data.gender,
                    brand=product_data.brand,
                    reference=product_data.reference,
                    size=product_data.size,
                    quantity=product_data.quantity,
                    price=product_data.price,
                    barcode=product_data.barcode,
                    min_stock=product_data.min_stock
                )
                
                products.append(product)
                
            except (ValueError, KeyError) as e:
                errors.append(f"Row {row_num}: {str(e)}")
            except Exception as e:
                errors.append(f"Row {row_num}: Validation error - {str(e)}")
        
        # If there are validation errors, report all of them
        if errors:
            error_message = "CSV validation failed:\n" + "\n".join(errors)
            raise ValidationError(error_message)
        
        return products

    def export_to_csv(self, data: List[Dict[str, Any]], filepath: str) -> bool:
        """
        Export data to CSV file.
        
        Args:
            data: List of dictionaries to export
            filepath: Path to output CSV file
            
        Returns:
            True if export succeeded, False if data is empty
            
        Validates: Requirements 13.2
        """
        if not data:
            return False
        
        # Create parent directories if they don't exist
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV with UTF-8 BOM for Excel compatibility
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            if not data:
                return False
            
            # Get headers from first row
            headers = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            
            for row in data:
                # Convert complex types to strings
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, (Decimal, dict, list)):
                        clean_row[key] = str(value)
                    else:
                        clean_row[key] = value
                writer.writerow(clean_row)
        
        return True
    
    def import_from_csv(self, filepath: str) -> tuple[bool, List[Dict[str, Any]], List[str]]:
        """
        Import data from CSV file.
        
        Args:
            filepath: Path to CSV file to import
            
        Returns:
            Tuple of (success, data, errors)
            - success: True if import succeeded
            - data: List of dictionaries with imported data
            - errors: List of error messages
            
        Validates: Requirements 13.1
        """
        errors = []
        
        # Check if file exists
        if not Path(filepath).exists():
            errors.append(f"File not found: {filepath}")
            return False, [], errors
        
        # Read CSV file
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                
                if not content.strip():
                    errors.append("CSV file is empty")
                    return False, [], errors
                
                # Parse CSV
                input_stream = io.StringIO(content)
                reader = csv.DictReader(input_stream)
                
                if not reader.fieldnames:
                    errors.append("CSV has no headers")
                    return False, [], errors
                
                # Read all rows and strip whitespace
                data = []
                for row in reader:
                    clean_row = {key: value.strip() if isinstance(value, str) else value 
                                for key, value in row.items()}
                    data.append(clean_row)
                
                # Check if there's any data after headers
                if not data:
                    errors.append("CSV has no data rows")
                    return False, [], errors
                
                return True, data, []
                
        except Exception as e:
            errors.append(f"Error reading CSV: {str(e)}")
            return False, [], errors
    
    def validate_product_data(self, data: List[Dict[str, Any]]) -> tuple[List[Product], List[str]]:
        """
        Validate product data from CSV and convert to Product objects.
        
        Args:
            data: List of dictionaries with product data
            
        Returns:
            Tuple of (valid_products, errors)
            - valid_products: List of valid Product objects
            - errors: List of validation error messages
            
        Validates: Requirements 13.3
        """
        valid_products = []
        errors = []
        
        # Required columns
        required_columns = {'sku', 'name', 'price', 'quantity'}
        
        # Check if data has required columns
        if data:
            actual_columns = set(data[0].keys())
            missing_columns = required_columns - actual_columns
            if missing_columns:
                errors.append(f"Missing required columns: {', '.join(sorted(missing_columns))}")
                return [], errors
        
        # Validate each row
        for row_num, row in enumerate(data, start=2):  # Start at 2 (after header)
            row_errors = []
            
            # Validate SKU
            sku = row.get('sku', '').strip()
            if not sku:
                row_errors.append("SKU is required")
            elif len(sku) > 50:
                row_errors.append("SKU is too long (max 50 characters)")
            
            # Validate name
            name = row.get('name', '').strip()
            if not name:
                row_errors.append("Name is required")
            
            # Validate price
            price = None
            try:
                price_str = row.get('price', '0').strip()
                if not price_str:
                    row_errors.append("Price is required")
                else:
                    price = Decimal(price_str)
                    if price <= 0:
                        row_errors.append("Price must be greater than 0")
            except (ValueError, TypeError, Exception):
                row_errors.append("Invalid price")
            
            # Validate quantity
            quantity = None
            try:
                quantity_str = row.get('quantity', '0').strip()
                if not quantity_str:
                    row_errors.append("Quantity is required")
                else:
                    quantity = int(quantity_str)
                    if quantity < 0:
                        row_errors.append("Quantity cannot be negative")
            except (ValueError, TypeError):
                row_errors.append("Invalid quantity")
            
            # Validate gender (if present)
            gender = row.get('gender', 'U').strip().upper() or 'U'
            if gender and gender not in ['M', 'F', 'U']:
                row_errors.append("Gender must be M, F, or U")
            
            # If there are errors for this row, add them to the error list
            if row_errors:
                for error in row_errors:
                    errors.append(f"Row {row_num}: {error}")
            else:
                # Apply defaults for optional fields
                min_stock = int(row.get('min_stock', '5').strip() or '5')
                description = row.get('description', '').strip() or None
                barcode = row.get('barcode', '').strip() or None
                brand = row.get('brand', '').strip() or 'Unknown'
                reference = row.get('reference', '').strip() or sku  # Default to SKU
                size = row.get('size', '').strip() or 'U'  # Default to U (unisex)
                
                # Create Product object
                product = Product(
                    sku=sku,
                    name=name,
                    description=description,
                    gender=gender,
                    brand=brand,
                    reference=reference,
                    size=size,
                    quantity=quantity,
                    price=price,
                    barcode=barcode,
                    min_stock=min_stock
                )
                
                valid_products.append(product)
        
        return valid_products, errors
    
    def preview_import(self, filepath: str, num_rows: int = 10) -> tuple[bool, List[Dict[str, Any]], List[str]]:
        """
        Preview first N rows of CSV file without full validation.
        
        Args:
            filepath: Path to CSV file
            num_rows: Number of rows to preview (default: 10)
            
        Returns:
            Tuple of (success, preview_data, errors)
            
        Validates: Requirements 13.1
        """
        success, data, errors = self.import_from_csv(filepath)
        
        if not success:
            return False, [], errors
        
        # Return only first N rows
        preview_data = data[:num_rows]
        return True, preview_data, []
