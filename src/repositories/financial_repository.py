"""Financial repository for database operations."""

from typing import List, Optional, Dict, Any
from datetime import date
from src.repositories.base import BaseRepository
from src.domain.financial import AccountPayable, AccountReceivable, CashFlowMovement, FinancialCategory


class FinancialRepository(BaseRepository):
    """Repository for financial operations."""
    
    async def create_category(self, category: FinancialCategory) -> FinancialCategory:
        """Create a new financial category."""
        data = category.model_dump(exclude={'id', 'created_at'})
        result = await self.db.insert("financeiro_categorias", data)
        return FinancialCategory(**result[0])

    async def list_categories(self, tipo: Optional[str] = None) -> List[FinancialCategory]:
        """List financial categories."""
        query = self.db.table("financeiro_categorias").select("*")
        if tipo:
            query = query.eq("tipo", tipo)
        result = await query.execute()
        return [FinancialCategory(**item) for item in result.data]

    async def create_account_payable(self, payable: AccountPayable) -> AccountPayable:
        """Create a new account payable."""
        data = payable.model_dump(exclude={'id', 'created_at', 'updated_at'})
        result = await self.db.insert("contas_pagar", data)
        return AccountPayable(**result[0])

    async def update_account_payable(self, id: int, data: Dict[str, Any]) -> Optional[AccountPayable]:
        """Update an account payable."""
        result = await self.db.update("contas_pagar", id, data)
        return AccountPayable(**result[0]) if result else None

    async def create_account_receivable(self, receivable: AccountReceivable) -> AccountReceivable:
        """Create a new account receivable."""
        data = receivable.model_dump(exclude={'id', 'created_at', 'updated_at'})
        result = await self.db.insert("contas_receber", data)
        return AccountReceivable(**result[0])

    async def update_account_receivable(self, id: int, data: Dict[str, Any]) -> Optional[AccountReceivable]:
        """Update an account receivable."""
        result = await self.db.update("contas_receber", id, data)
        return AccountReceivable(**result[0]) if result else None

    async def register_cash_movement(self, movement: CashFlowMovement) -> CashFlowMovement:
        """Register a movement in cash flow."""
        data = movement.model_dump(exclude={'id', 'created_at'})
        result = await self.db.insert("fluxo_caixa", data)
        return CashFlowMovement(**result[0])

    async def get_cash_flow_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get summary of cash flow for a period."""
        query = f"""
            SELECT 
                tipo, 
                SUM(valor) as total
            FROM fluxo_caixa
            WHERE data_movimento >= $1 AND data_movimento <= $2
            GROUP BY tipo
        """
        result = await self.db.execute(query, start_date, end_date)
        
        summary = {"entrada": 0, "saida": 0, "saldo": 0}
        for row in result:
            if row['tipo'] == 'entrada':
                summary['entrada'] = row['total']
            else:
                summary['saida'] = row['total']
        
        summary['saldo'] = summary['entrada'] - summary['saida']
        return summary
