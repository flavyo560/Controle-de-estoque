"""Property-based tests for domain model validation.

**Validates: Requirements 2.2, 17.1, 19.1**

These tests verify that Pydantic domain models enforce validation rules
correctly across all possible inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from decimal import Decimal
from pydantic import ValidationError

from src.domain.product import Product, ProductCreate, ProductUpdate
from src.domain.sale import Sale, SaleItem, SaleCreate


# Hypothesis strategies for generating test data
@st.composite
def decimal_strategy(draw, min_value=0.01, max_value=99999.99, places=2):
    """Generate Decimal values with specific precision."""
    value = draw(st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False
    ))
    return Decimal(str(value)).quantize(Decimal('0.01'))


@st.composite
def price_with_precision_strategy(draw, max_places=5):
    """Generate prices with varying decimal places (0 to max_places)."""
    # Generate a float and convert to Decimal with specific precision
    value = draw(st.floats(
        min_value=0.01,
        max_value=99999.99,
        allow_nan=False,
        allow_infinity=False
    ))
    places = draw(st.integers(min_value=0, max_value=max_places))
    
    # Create format string for the desired precision
    if places == 0:
        quantizer = Decimal('1')
    else:
        quantizer = Decimal('0.' + '0' * places)
    
    return Decimal(str(value)).quantize(quantizer)


class TestDomainValidation:
    """Property-based tests for domain model validation."""
    
    @given(price=decimal_strategy(places=2))
    @settings(max_examples=100)
    def test_price_precision_valid_two_decimals(self, price: Decimal):
        """
        Property 2: Price precision invariant (valid case).
        
        **Validates: Requirements 2.2, 17.1**
        
        Test that prices with exactly 2 decimal places are always accepted.
        """
        # Create product with 2-decimal price
        product_data = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            gender="U",
            brand="Test Brand",
            reference="REF-001",
            size="M",
            quantity=10,
            price=price,
            min_stock=5
        )
        
        # Should not raise validation error
        assert product_data.price == price
        assert product_data.price.as_tuple().exponent >= -2
    
    @given(
        base_price=st.floats(min_value=0.01, max_value=99999.99, allow_nan=False, allow_infinity=False),
        extra_decimals=st.integers(min_value=3, max_value=10)
    )
    @settings(max_examples=100)
    def test_price_precision_invalid_more_than_two_decimals(
        self,
        base_price: float,
        extra_decimals: int
    ):
        """
        Property 2: Price precision invariant (invalid case).
        
        **Validates: Requirements 2.2, 17.1**
        
        Test that prices with more than 2 decimal places are rejected.
        """
        # Create a price with more than 2 decimal places
        quantizer = Decimal('0.' + '0' * extra_decimals)
        price_with_extra_decimals = Decimal(str(base_price)).quantize(quantizer)
        
        # Only test if the price actually has more than 2 decimal places
        assume(price_with_extra_decimals.as_tuple().exponent < -2)
        
        # Should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                gender="U",
                brand="Test Brand",
                reference="REF-001",
                size="M",
                quantity=10,
                price=price_with_extra_decimals,
                min_stock=5
            )
        
        # Verify error message mentions decimal places
        assert "decimal places" in str(exc_info.value).lower()
    
    @given(
        total_amount=decimal_strategy(min_value=0, max_value=10000),
        discount_amount=decimal_strategy(min_value=0, max_value=10000)
    )
    @settings(max_examples=100)
    def test_sale_amount_consistency(
        self,
        total_amount: Decimal,
        discount_amount: Decimal
    ):
        """
        Property 3: Sale amount consistency.
        
        **Validates: Requirements 19.1**
        
        Test that final_amount = total_amount - discount_amount for all sales.
        This property must hold for any valid combination of amounts.
        """
        # Ensure discount doesn't exceed total
        assume(discount_amount <= total_amount)
        
        # Calculate expected final amount
        expected_final = total_amount - discount_amount
        
        # Create sale with these amounts
        sale = Sale(
            id=1,
            customer_id=None,
            user_id=1,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=expected_final,
            status="completed"
        )
        
        # Verify the consistency property
        assert sale.final_amount == sale.total_amount - sale.discount_amount
        assert sale.final_amount == expected_final
    
    @given(
        total_amount=decimal_strategy(min_value=0, max_value=10000),
        discount_amount=decimal_strategy(min_value=0, max_value=10000),
        wrong_final=decimal_strategy(min_value=0, max_value=10000)
    )
    @settings(max_examples=100)
    def test_sale_amount_inconsistency_rejected(
        self,
        total_amount: Decimal,
        discount_amount: Decimal,
        wrong_final: Decimal
    ):
        """
        Property 3: Sale amount consistency (rejection case).
        
        **Validates: Requirements 19.1**
        
        Test that sales with inconsistent amounts are rejected.
        If final_amount != total_amount - discount_amount, validation should fail.
        """
        # Ensure discount doesn't exceed total
        assume(discount_amount <= total_amount)
        
        # Calculate correct final amount
        correct_final = total_amount - discount_amount
        
        # Ensure wrong_final is actually wrong
        assume(wrong_final != correct_final)
        
        # Attempting to create sale with wrong final amount should fail
        # Note: This depends on having a validator in the Sale model
        # If the model doesn't have this validator yet, this test documents
        # the expected behavior
        try:
            sale = Sale(
                id=1,
                customer_id=None,
                user_id=1,
                total_amount=total_amount,
                discount_amount=discount_amount,
                final_amount=wrong_final,
                status="completed"
            )
            
            # If no validator exists, manually check the property
            # This documents what SHOULD be validated
            calculated_final = sale.total_amount - sale.discount_amount
            assert sale.final_amount == calculated_final, (
                f"Sale amount inconsistency detected! "
                f"final_amount={sale.final_amount} but "
                f"total_amount - discount_amount = {calculated_final}"
            )
        except ValidationError:
            # Good! Validation caught the inconsistency
            pass
    
    @given(
        quantity=st.integers(min_value=-1000, max_value=-1)
    )
    @settings(max_examples=50)
    def test_quantity_non_negative_validation(self, quantity: int):
        """
        Property: Quantity must be non-negative.
        
        **Validates: Requirements 2.2, 17.1**
        
        Test that negative quantities are always rejected by domain model validation.
        """
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                gender="U",
                brand="Test Brand",
                reference="REF-001",
                size="M",
                quantity=quantity,  # Negative quantity
                price=Decimal("10.00"),
                min_stock=5
            )
        
        # Verify error mentions quantity
        assert "quantity" in str(exc_info.value).lower()
    
    @given(
        gender=st.text(min_size=1, max_size=5).filter(lambda x: x not in ['M', 'F', 'U', 'm', 'f', 'u'])
    )
    @settings(max_examples=50)
    def test_gender_validation(self, gender: str):
        """
        Property: Gender must be M, F, or U.
        
        **Validates: Requirements 2.2, 17.1**
        
        Test that invalid gender values are rejected.
        """
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                gender=gender,  # Invalid gender
                brand="Test Brand",
                reference="REF-001",
                size="M",
                quantity=10,
                price=Decimal("10.00"),
                min_stock=5
            )
        
        # Verify error mentions gender
        assert "gender" in str(exc_info.value).lower()
    
    @given(
        sku=st.text(min_size=1, max_size=50),
        name=st.text(min_size=1, max_size=200),
        brand=st.text(min_size=1, max_size=100),
        reference=st.text(min_size=1, max_size=50),
        size=st.text(min_size=1, max_size=20),
        quantity=st.integers(min_value=0, max_value=10000),
        price=decimal_strategy(),
        gender=st.sampled_from(['M', 'F', 'U'])
    )
    @settings(max_examples=100)
    def test_valid_product_always_accepted(
        self,
        sku: str,
        name: str,
        brand: str,
        reference: str,
        size: str,
        quantity: int,
        price: Decimal,
        gender: str
    ):
        """
        Property: All valid products are accepted.
        
        **Validates: Requirements 2.2, 17.1**
        
        Test that any product meeting all validation rules is accepted.
        """
        product_data = ProductCreate(
            sku=sku,
            name=name,
            gender=gender,
            brand=brand,
            reference=reference,
            size=size,
            quantity=quantity,
            price=price,
            min_stock=5
        )
        
        # Should not raise validation error
        assert product_data.sku == sku
        assert product_data.name == name
        assert product_data.quantity >= 0
        assert product_data.price > 0
        assert product_data.price.as_tuple().exponent >= -2
        assert product_data.gender in ['M', 'F', 'U']
    
    @given(
        price=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("99999.99"),
            places=2
        )
    )
    @settings(max_examples=100)
    def test_price_update_precision(self, price: Decimal):
        """
        Property: Price updates maintain precision invariant.
        
        **Validates: Requirements 2.2, 17.1**
        
        Test that updating product price also enforces 2 decimal places.
        """
        update_data = ProductUpdate(price=price)
        
        # Should not raise validation error
        assert update_data.price == price
        if update_data.price is not None:
            assert update_data.price.as_tuple().exponent >= -2
    
    @given(
        item_quantity=st.integers(min_value=1, max_value=100),
        unit_price=decimal_strategy(min_value=0.01, max_value=1000)
    )
    @settings(max_examples=100)
    def test_sale_item_subtotal_consistency(
        self,
        item_quantity: int,
        unit_price: Decimal
    ):
        """
        Property: Sale item subtotal = quantity * unit_price.
        
        **Validates: Requirements 19.1**
        
        Test that sale item subtotals are calculated correctly.
        """
        expected_subtotal = Decimal(item_quantity) * unit_price
        
        sale_item = SaleItem(
            id=1,
            sale_id=1,
            product_id=1,
            product_snapshot={},
            quantity=item_quantity,
            unit_price=unit_price,
            subtotal=expected_subtotal
        )
        
        # Verify the consistency property
        assert sale_item.subtotal == Decimal(sale_item.quantity) * sale_item.unit_price
        assert sale_item.subtotal == expected_subtotal


class TestPriceRoundingBehavior:
    """Tests for price rounding and precision edge cases."""
    
    @given(
        value=st.floats(min_value=0.01, max_value=99999.99, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_price_rounding_to_two_decimals(self, value: float):
        """
        Property: Prices are correctly rounded to 2 decimal places.
        
        **Validates: Requirements 2.2, 17.1**
        
        Test that when a price is quantized to 2 decimal places,
        it's always accepted by validation.
        """
        # Round to 2 decimal places
        price = Decimal(str(value)).quantize(Decimal('0.01'))
        
        product_data = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            gender="U",
            brand="Test Brand",
            reference="REF-001",
            size="M",
            quantity=10,
            price=price,
            min_stock=5
        )
        
        # Should be accepted
        assert product_data.price == price
        assert product_data.price.as_tuple().exponent == -2
    
    def test_price_precision_edge_cases(self):
        """
        Test specific edge cases for price precision.
        
        **Validates: Requirements 2.2, 17.1**
        """
        # Test cases: (price_string, should_pass)
        test_cases = [
            ("10.00", True),      # Exactly 2 decimals
            ("10.0", True),       # 1 decimal (will be normalized)
            ("10", True),         # No decimals (will be normalized)
            ("10.99", True),      # Exactly 2 decimals
            ("10.999", False),    # 3 decimals - should fail
            ("10.9999", False),   # 4 decimals - should fail
            ("0.01", True),       # Minimum valid price
            ("99999.99", True),   # Large valid price
        ]
        
        for price_str, should_pass in test_cases:
            price = Decimal(price_str)
            
            if should_pass:
                # Should not raise error
                product = ProductCreate(
                    sku=f"TEST-{price_str}",
                    name="Test Product",
                    gender="U",
                    brand="Test Brand",
                    reference="REF-001",
                    size="M",
                    quantity=10,
                    price=price,
                    min_stock=5
                )
                assert product.price.as_tuple().exponent >= -2
            else:
                # Should raise validation error
                with pytest.raises(ValidationError):
                    ProductCreate(
                        sku=f"TEST-{price_str}",
                        name="Test Product",
                        gender="U",
                        brand="Test Brand",
                        reference="REF-001",
                        size="M",
                        quantity=10,
                        price=price,
                        min_stock=5
                    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
