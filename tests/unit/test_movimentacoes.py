"""
Testes unitários para funções de movimentação de estoque.
Feature: sistema-estoque-melhorado
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

# Configurar variáveis de ambiente antes de importar database
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_KEY'] = 'test-key'

# Mock do supabase antes de importar database
with patch('database.create_client'):
    import database


class TestRegistrarMovimentacao:
    """Testes para a função registrar_movimentacao()"""
    
    @patch('database.supabase')
    def test_registrar_entrada_sucesso(self, mock_supabase):
        """Testa registro de entrada com sucesso"""
        # Configurar mock para retornar produto com quantidade 10
        mock_produto_response = Mock()
        mock_produto_response.data = [{"quantidade": 10}]
        
        mock_update_response = Mock()
        mock_insert_response = Mock()
        
        # Configurar cadeia de chamadas do mock
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_produto_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        
        # Executar função
        resultado = database.registrar_movimentacao(
            produto_id=1,
            tipo='entrada',
            quantidade=5,
            observacao='Teste de entrada'
        )
        
        # Verificar resultado
        assert resultado is True
    
    @patch('database.supabase')
    def test_registrar_saida_sucesso(self, mock_supabase):
        """Testa registro de saída com sucesso"""
        # Configurar mock para retornar produto com quantidade 10
        mock_produto_response = Mock()
        mock_produto_response.data = [{"quantidade": 10}]
        
        mock_update_response = Mock()
        mock_insert_response = Mock()
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_produto_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        
        # Executar função
        resultado = database.registrar_movimentacao(
            produto_id=1,
            tipo='saida',
            quantidade=3
        )
        
        # Verificar resultado
        assert resultado is True
    
    @patch('database.supabase')
    def test_tipo_invalido(self, mock_supabase):
        """Testa rejeição de tipo de movimentação inválido"""
        resultado = database.registrar_movimentacao(
            produto_id=1,
            tipo='invalido',
            quantidade=5
        )
        
        assert resultado is False
    
    @patch('database.supabase')
    def test_quantidade_invalida(self, mock_supabase):
        """Testa rejeição de quantidade inválida (zero ou negativa)"""
        resultado = database.registrar_movimentacao(
            produto_id=1,
            tipo='entrada',
            quantidade=0
        )
        
        assert resultado is False
        
        resultado = database.registrar_movimentacao(
            produto_id=1,
            tipo='entrada',
            quantidade=-5
        )
        
        assert resultado is False
    
    @patch('database.supabase')
    def test_produto_nao_encontrado(self, mock_supabase):
        """Testa comportamento quando produto não existe"""
        # Configurar mock para retornar lista vazia
        mock_produto_response = Mock()
        mock_produto_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_produto_response
        
        resultado = database.registrar_movimentacao(
            produto_id=999,
            tipo='entrada',
            quantidade=5
        )
        
        assert resultado is False
    
    @patch('database.supabase')
    def test_movimentacao_em_lote(self, mock_supabase):
        """Testa movimentação em lote com quantidade > 1 (Requisito 7.1)"""
        # Configurar mock para retornar produto com quantidade 10
        mock_produto_response = Mock()
        mock_produto_response.data = [{"quantidade": 10}]
        
        mock_update_response = Mock()
        mock_insert_response = Mock()
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_produto_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        
        # Executar função com quantidade em lote (15 unidades)
        resultado = database.registrar_movimentacao(
            produto_id=1,
            tipo='entrada',
            quantidade=15,
            observacao='Movimentação em lote'
        )
        
        # Verificar resultado
        assert resultado is True
    
    @patch('database.supabase')
    def test_saida_maior_que_estoque(self, mock_supabase):
        """Testa saída maior que estoque disponível (Requisito 7.3)"""
        # Configurar mock para retornar produto com quantidade 5
        mock_produto_response = Mock()
        mock_produto_response.data = [{"quantidade": 5}]
        
        mock_update_response = Mock()
        mock_insert_response = Mock()
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_produto_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        
        # Executar função com saída maior que estoque (10 > 5)
        # A função deve permitir mas registrar aviso
        resultado = database.registrar_movimentacao(
            produto_id=1,
            tipo='saida',
            quantidade=10,
            observacao='Saída maior que estoque'
        )
        
        # Verificar que a operação é permitida (com aviso)
        assert resultado is True


class TestListarMovimentacoes:
    """Testes para a função listar_movimentacoes()"""
    
    @patch('database.supabase')
    def test_listar_todas_movimentacoes(self, mock_supabase):
        """Testa listagem de todas as movimentações"""
        # Configurar mock para retornar lista de movimentações
        mock_response = Mock()
        mock_response.data = [
            {"id": 1, "produto_id": 1, "tipo": "entrada", "quantidade": 5},
            {"id": 2, "produto_id": 2, "tipo": "saida", "quantidade": 3}
        ]
        
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value = mock_response
        
        resultado = database.listar_movimentacoes()
        
        assert len(resultado) == 2
        assert resultado[0]["id"] == 1
    
    @patch('database.supabase')
    def test_listar_por_produto(self, mock_supabase):
        """Testa listagem filtrada por produto"""
        mock_response = Mock()
        mock_response.data = [
            {"id": 1, "produto_id": 1, "tipo": "entrada", "quantidade": 5}
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response
        
        resultado = database.listar_movimentacoes(produto_id=1)
        
        assert len(resultado) == 1
        assert resultado[0]["produto_id"] == 1
    
    @patch('database.supabase')
    def test_listar_por_periodo(self, mock_supabase):
        """Testa listagem filtrada por período"""
        mock_response = Mock()
        mock_response.data = []
        
        # Criar mock chain para múltiplos filtros
        mock_chain = Mock()
        mock_chain.gte.return_value = mock_chain
        mock_chain.lte.return_value = mock_chain
        mock_chain.order.return_value = mock_chain
        mock_chain.execute.return_value = mock_response
        
        mock_supabase.table.return_value.select.return_value = mock_chain
        
        resultado = database.listar_movimentacoes(
            data_inicio='2024-01-01',
            data_fim='2024-01-31'
        )
        
        assert isinstance(resultado, list)


class TestDesfazerUltimaMovimentacao:
    """Testes para a função desfazer_ultima_movimentacao()"""
    
    @patch('database.supabase')
    def test_desfazer_sucesso(self, mock_supabase):
        """Testa desfazer movimentação com sucesso"""
        # Configurar mock para retornar última movimentação
        mock_mov_response = Mock()
        mock_mov_response.data = [{
            "id": 1,
            "produto_id": 1,
            "tipo": "entrada",
            "quantidade": 5,
            "quantidade_anterior": 10,
            "quantidade_nova": 15
        }]
        
        mock_update_response = Mock()
        mock_delete_response = Mock()
        
        # Configurar cadeia de chamadas
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_mov_response
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_delete_response
        
        resultado = database.desfazer_ultima_movimentacao(produto_id=1)
        
        assert resultado is True
    
    @patch('database.supabase')
    def test_desfazer_sem_movimentacao(self, mock_supabase):
        """Testa desfazer quando não há movimentação"""
        # Configurar mock para retornar lista vazia
        mock_mov_response = Mock()
        mock_mov_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_mov_response
        
        resultado = database.desfazer_ultima_movimentacao(produto_id=999)
        
        assert resultado is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
