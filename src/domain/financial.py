"""Financial domain models with Pydantic validation."""

from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List


class FinancialCategory(BaseModel):
    """Financial category domain model."""
    id: Optional[int] = None
    nome: str = Field(min_length=2, max_length=50)
    tipo: str = Field(pattern="^(receita|despesa)$")
    descricao: Optional[str] = None
    created_at: Optional[datetime] = None


class AccountPayable(BaseModel):
    """Accounts payable domain model."""
    id: Optional[int] = None
    descricao: str = Field(min_length=3)
    valor: Decimal = Field(gt=0)
    data_vencimento: date
    data_pagamento: Optional[date] = None
    categoria_id: Optional[int] = None
    status: str = Field(default='pendente', pattern="^(pendente|pago|atrasado|cancelado)$")
    fornecedor_id: Optional[int] = None
    observacao: Optional[str] = None
    usuario_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AccountReceivable(BaseModel):
    """Accounts receivable domain model."""
    id: Optional[int] = None
    descricao: str = Field(min_length=3)
    valor: Decimal = Field(gt=0)
    data_vencimento: date
    data_recebimento: Optional[date] = None
    venda_id: Optional[int] = None
    cliente_id: Optional[int] = None
    categoria_id: Optional[int] = None
    status: str = Field(default='pendente', pattern="^(pendente|recebido|atrasado|cancelado)$")
    forma_recebimento: Optional[str] = None
    observacao: Optional[str] = None
    usuario_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CashFlowMovement(BaseModel):
    """Cash flow movement domain model."""
    id: Optional[int] = None
    data_movimento: datetime = Field(default_factory=datetime.now)
    tipo: str = Field(pattern="^(entrada|saida)$")
    valor: Decimal = Field(gt=0)
    descricao: str
    categoria_id: Optional[int] = None
    origem_id: Optional[int] = None
    origem_tipo: Optional[str] = None
    usuario_id: int
    created_at: Optional[datetime] = None
