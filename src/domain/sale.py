"""Sale domain models with Pydantic validation."""

from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any


class SaleItem(BaseModel):
    """Sale item domain model."""
    
    id: Optional[int] = None
    sale_id: Optional[int] = None
    product_id: int
    product_snapshot: Dict[str, Any]  # Store product details at time of sale
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    subtotal: Decimal = Field(ge=0)
    created_at: Optional[datetime] = None
    
    @field_validator('unit_price', 'subtotal')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Price must have at most 2 decimal places')
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v
    
    @model_validator(mode='after')
    def validate_subtotal(self) -> 'SaleItem':
        """Validate subtotal equals quantity * unit_price."""
        expected_subtotal = Decimal(str(self.quantity)) * self.unit_price
        # Round to 2 decimal places for comparison
        expected_subtotal = expected_subtotal.quantize(Decimal('0.01'))
        actual_subtotal = self.subtotal.quantize(Decimal('0.01'))
        
        if actual_subtotal != expected_subtotal:
            raise ValueError(
                f'Subtotal {actual_subtotal} does not match quantity * unit_price = {expected_subtotal}'
            )
        return self


class Payment(BaseModel):
    """Payment domain model."""
    
    id: Optional[int] = None
    sale_id: Optional[int] = None
    payment_method: str = Field(pattern="^(cash|credit_card|debit_card|pix)$")
    amount: Decimal = Field(gt=0)
    created_at: Optional[datetime] = None
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount must have at most 2 decimal places')
        return v
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        """Validate payment method is valid."""
        if v not in ('cash', 'credit_card', 'debit_card', 'pix'):
            raise ValueError('Payment method must be cash, credit_card, debit_card, or pix')
        return v.lower()


class Sale(BaseModel):
    """Sale domain model with validation."""
    
    id: Optional[int] = None
    customer_id: Optional[int] = None
    user_id: int
    total_amount: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    final_amount: Decimal = Field(ge=0)
    status: str = Field(default='completed', pattern="^(completed|cancelled|em_aberto)$")
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[int] = None
    version: int = Field(default=1, ge=1)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Related entities (not stored in database, loaded separately)
    items: List[SaleItem] = Field(default_factory=list)
    payments: List[Payment] = Field(default_factory=list)
    
    @field_validator('total_amount', 'discount_amount', 'final_amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount must have at most 2 decimal places')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status is valid."""
        if v not in ('completed', 'cancelled'):
            raise ValueError('Status must be completed or cancelled')
        return v.lower()
    
    @model_validator(mode='after')
    def validate_final_amount(self) -> 'Sale':
        """Validate final_amount equals total_amount - discount_amount."""
        expected_final = self.total_amount - self.discount_amount
        # Round to 2 decimal places for comparison
        expected_final = expected_final.quantize(Decimal('0.01'))
        actual_final = self.final_amount.quantize(Decimal('0.01'))
        
        if actual_final != expected_final:
            raise ValueError(
                f'Final amount {actual_final} does not match total_amount - discount_amount = {expected_final}'
            )
        return self
    
    @model_validator(mode='after')
    def validate_cancellation(self) -> 'Sale':
        """Validate cancellation fields are consistent."""
        if self.status == 'cancelled':
            if not self.cancelled_at:
                raise ValueError('Cancelled sales must have cancelled_at timestamp')
            if not self.cancellation_reason:
                raise ValueError('Cancelled sales must have cancellation_reason')
            if not self.cancelled_by:
                raise ValueError('Cancelled sales must have cancelled_by user_id')
        else:
            if self.cancelled_at or self.cancellation_reason or self.cancelled_by:
                raise ValueError('Non-cancelled sales cannot have cancellation fields set')
        return self


class SaleItemCreate(BaseModel):
    """DTO for creating sale items."""
    
    product_id: int
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    
    @field_validator('unit_price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Price must have at most 2 decimal places')
        return v
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class PaymentCreate(BaseModel):
    """DTO for creating payments."""
    
    payment_method: str = Field(pattern="^(cash|credit_card|debit_card|pix)$")
    amount: Decimal = Field(gt=0)
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate amount has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount must have at most 2 decimal places')
        return v
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        """Validate payment method is valid."""
        if v not in ('cash', 'credit_card', 'debit_card', 'pix'):
            raise ValueError('Payment method must be cash, credit_card, debit_card, or pix')
        return v.lower()


class SaleCreate(BaseModel):
    """DTO for creating sales."""
    
    customer_id: Optional[int] = None
    user_id: int
    discount_amount: Decimal = Field(default=Decimal('0.00'), ge=0)
    items: List[SaleItemCreate] = Field(min_length=1)
    payments: List[PaymentCreate] = Field(min_length=1)
    
    @field_validator('discount_amount')
    @classmethod
    def validate_discount(cls, v: Decimal) -> Decimal:
        """Validate discount has at most 2 decimal places."""
        if v.as_tuple().exponent < -2:
            raise ValueError('Discount must have at most 2 decimal places')
        return v
    
    @model_validator(mode='after')
    def validate_amounts(self) -> 'SaleCreate':
        """Validate total payment matches sale total."""
        # Calculate total from items
        total_amount = sum(
            Decimal(str(item.quantity)) * item.unit_price
            for item in self.items
        )
        
        # Calculate final amount after discount
        final_amount = total_amount - self.discount_amount
        
        # Calculate total payments
        total_payments = sum(payment.amount for payment in self.payments)
        
        # Round to 2 decimal places for comparison
        final_amount = final_amount.quantize(Decimal('0.01'))
        total_payments = total_payments.quantize(Decimal('0.01'))
        
        if total_payments != final_amount:
            raise ValueError(
                f'Total payments {total_payments} does not match final amount {final_amount}'
            )
        
        return self


class InventoryMovement(BaseModel):
    """Inventory movement domain model."""
    
    id: Optional[int] = None
    product_id: int
    movement_type: str = Field(pattern="^(sale|purchase|adjustment|return)$")
    quantity_change: int
    quantity_before: int = Field(ge=0)
    quantity_after: int = Field(ge=0)
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    user_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @field_validator('movement_type')
    @classmethod
    def validate_movement_type(cls, v: str) -> str:
        """Validate movement type is valid."""
        if v not in ('sale', 'purchase', 'adjustment', 'return'):
            raise ValueError('Movement type must be sale, purchase, adjustment, or return')
        return v.lower()
    
    @model_validator(mode='after')
    def validate_quantity_change(self) -> 'InventoryMovement':
        """Validate quantity_after equals quantity_before + quantity_change."""
        expected_after = self.quantity_before + self.quantity_change
        if self.quantity_after != expected_after:
            raise ValueError(
                f'Quantity after {self.quantity_after} does not match '
                f'quantity_before + quantity_change = {expected_after}'
            )
        return self
