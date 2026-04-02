"""Financial service with business logic for accounting and cash flow."""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal

from src.domain.financial import (
    AccountPayable, AccountReceivable, CashFlowMovement, FinancialCategory
)
from src.repositories.financial_repository import FinancialRepository
from src.repositories.audit_repository import AuditRepository
from src.infrastructure.database import DatabaseClient
from src.exceptions import NotFoundError, ValidationError


class FinancialService:
    """Service for financial management."""
    
    def __init__(
        self,
        financial_repo: FinancialRepository,
        audit_repo: AuditRepository,
        db_client: DatabaseClient
    ):
        """Initialize financial service."""
        self.financial_repo = financial_repo
        self.audit_repo = audit_repo
        self.db = db_client

    async def create_account_payable(self, payable: AccountPayable) -> AccountPayable:
        """Create a new account payable with audit trail."""
        async with self.db.transaction():
            result = await self.financial_repo.create_account_payable(payable)
            
            await self.audit_repo.log_create(
                table="contas_pagar",
                record_id=result.id,
                user_id=payable.usuario_id,
                data=payable.model_dump(mode='json')
            )
            return result

    async def pay_account(self, payable_id: int, payment_date: date, user_id: int) -> AccountPayable:
        """Mark an account payable as paid and record in cash flow."""
        async with self.db.transaction():
            payable = await self.financial_repo.update_account_payable(
                payable_id, 
                {"status": "pago", "data_pagamento": payment_date}
            )
            
            if not payable:
                raise NotFoundError(f"Account payable {payable_id} not found")

            # Register in cash flow
            movement = CashFlowMovement(
                tipo="saida",
                valor=payable.valor,
                descricao=f"Pagamento: {payable.descricao}",
                categoria_id=payable.categoria_id,
                origem_id=payable.id,
                origem_tipo="conta_pagar",
                usuario_id=user_id
            )
            await self.financial_repo.register_cash_movement(movement)
            
            await self.audit_repo.log_update(
                table="contas_pagar",
                record_id=payable_id,
                user_id=user_id,
                old_data={"status": "pendente"},
                new_data={"status": "pago", "data_pagamento": str(payment_date)}
            )
            return payable

    async def create_account_receivable(self, receivable: AccountReceivable) -> AccountReceivable:
        """Create a new account receivable."""
        async with self.db.transaction():
            result = await self.financial_repo.create_account_receivable(receivable)
            
            await self.audit_repo.log_create(
                table="contas_receber",
                record_id=result.id,
                user_id=receivable.usuario_id,
                data=receivable.model_dump(mode='json')
            )
            return result

    async def receive_account(self, receivable_id: int, receive_date: date, user_id: int, forma: str) -> AccountReceivable:
        """Mark an account receivable as received and record in cash flow."""
        async with self.db.transaction():
            receivable = await self.financial_repo.update_account_receivable(
                receivable_id, 
                {"status": "recebido", "data_recebimento": receive_date, "forma_recebimento": forma}
            )
            
            if not receivable:
                raise NotFoundError(f"Account receivable {receivable_id} not found")

            # Register in cash flow
            movement = CashFlowMovement(
                tipo="entrada",
                valor=receivable.valor,
                descricao=f"Recebimento: {receivable.descricao}",
                categoria_id=receivable.categoria_id,
                origem_id=receivable.id,
                origem_tipo="conta_receber",
                usuario_id=user_id
            )
            await self.financial_repo.register_cash_movement(movement)
            
            await self.audit_repo.log_update(
                table="contas_receber",
                record_id=receivable_id,
                user_id=user_id,
                old_data={"status": "pendente"},
                new_data={"status": "recebido", "data_recebimento": str(receive_date)}
            )
            return receivable

    async def get_cash_flow_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get summary of cash flow for a period."""
        return await self.financial_repo.get_cash_flow_summary(start_date, end_date)

    async def list_categories(self, tipo: Optional[str] = None) -> List[FinancialCategory]:
        """List financial categories."""
        return await self.financial_repo.list_categories(tipo)
