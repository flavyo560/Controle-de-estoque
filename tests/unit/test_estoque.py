"""
Testes unitários para o módulo estoque.py

Feature: sistema-estoque-melhorado
Requisitos: 2.1, 2.4, 5.3, 5.5
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import estoque


class TestVerificarEstoqueBaixo:
    """Testes para a função verificar_estoque_baixo"""
    
    @patch('estoque.supabase')
    def test_verifica_produto_com_estoque_baixo(self, mock_supabase):
        """Testa identificação de produto com estoque baixo"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Camiseta",
                "quantidade": 3,
                "estoque_minimo": 5,
                "preco": 29.90
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.verificar_estoque_baixo()
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["id"] == 1
        assert resultado[0]["quantidade"] <= resultado[0]["estoque_minimo"]
    
    @patch('estoque.supabase')
    def test_nao_retorna_produto_com_estoque_adequado(self, mock_supabase):
        """Testa que produtos com estoque adequado não são retornados"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "descricao": "Camiseta",
                "quantidade": 10,
                "estoque_minimo": 5,
                "preco": 29.90
            }
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.verificar_estoque_baixo()
        
        # Assert
        assert len(resultado) == 0
    
    @patch('estoque.supabase')
    def test_verifica_produto_especifico(self, mock_supabase):
        """Testa verificação de produto específico por ID"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 5,
                "descricao": "Calça",
                "quantidade": 2,
                "estoque_minimo": 5,
                "preco": 49.90
            }
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.verificar_estoque_baixo(produto_id=5)
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["id"] == 5
    
    @patch('estoque.supabase')
    def test_retorna_lista_vazia_quando_nenhum_produto(self, mock_supabase):
        """Testa retorno de lista vazia quando não há produtos"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.verificar_estoque_baixo()
        
        # Assert
        assert resultado == []
    
    @patch('estoque.supabase')
    def test_trata_erro_de_conexao(self, mock_supabase):
        """Testa tratamento de erro de conexão"""
        # Arrange
        mock_supabase.table.return_value.select.return_value.execute.side_effect = Exception("Connection error")
        
        # Act
        resultado = estoque.verificar_estoque_baixo()
        
        # Assert
        assert resultado == []


class TestCalcularValorTotalEstoque:
    """Testes para a função calcular_valor_total_estoque"""
    
    @patch('estoque.supabase')
    def test_calcula_valor_total_corretamente(self, mock_supabase):
        """Testa cálculo correto do valor total do estoque"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {"quantidade": 10, "preco": 29.90},
            {"quantidade": 5, "preco": 49.90},
            {"quantidade": 3, "preco": 19.90}
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.calcular_valor_total_estoque()
        
        # Assert
        # 10*29.90 + 5*49.90 + 3*19.90 = 299.00 + 249.50 + 59.70 = 608.20
        assert resultado == pytest.approx(608.20, rel=0.01)
    
    @patch('estoque.supabase')
    def test_retorna_zero_quando_nenhum_produto(self, mock_supabase):
        """Testa retorno de 0.0 quando não há produtos"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.calcular_valor_total_estoque()
        
        # Assert
        assert resultado == 0.0
    
    @patch('estoque.supabase')
    def test_trata_produtos_com_quantidade_zero(self, mock_supabase):
        """Testa cálculo com produtos de quantidade zero"""
        # Arrange
        mock_response = Mock()
        mock_response.data = [
            {"quantidade": 0, "preco": 29.90},
            {"quantidade": 5, "preco": 10.00}
        ]
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.calcular_valor_total_estoque()
        
        # Assert
        assert resultado == 50.0
    
    @patch('estoque.supabase')
    def test_trata_erro_de_conexao(self, mock_supabase):
        """Testa tratamento de erro de conexão"""
        # Arrange
        mock_supabase.table.return_value.select.return_value.execute.side_effect = Exception("Connection error")
        
        # Act
        resultado = estoque.calcular_valor_total_estoque()
        
        # Assert
        assert resultado == 0.0


class TestProdutosSemMovimentacao:
    """Testes para a função produtos_sem_movimentacao"""
    
    @patch('estoque.supabase')
    def test_identifica_produto_sem_movimentacao(self, mock_supabase):
        """Testa identificação de produto sem nenhuma movimentação"""
        # Arrange
        mock_produtos = Mock()
        mock_produtos.data = [
            {"id": 1, "descricao": "Produto A", "quantidade": 10, "preco": 29.90}
        ]
        
        mock_movimentacoes = Mock()
        mock_movimentacoes.data = []
        
        # Configurar mock para retornar produtos e movimentações
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        # Primeira chamada: buscar produtos
        # Segunda chamada: buscar movimentações
        mock_table.select.side_effect = [
            Mock(execute=Mock(return_value=mock_produtos)),
            Mock(eq=Mock(return_value=Mock(order=Mock(return_value=Mock(limit=Mock(return_value=Mock(execute=Mock(return_value=mock_movimentacoes))))))))
        ]
        
        # Act
        resultado = estoque.produtos_sem_movimentacao(dias=30)
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["id"] == 1
        assert resultado[0]["ultima_movimentacao"] is None
    
    @patch('estoque.supabase')
    def test_identifica_produto_com_movimentacao_antiga(self, mock_supabase):
        """Testa identificação de produto com movimentação antiga"""
        # Arrange
        data_antiga = (datetime.now() - timedelta(days=45)).isoformat()
        
        mock_produtos = Mock()
        mock_produtos.data = [
            {"id": 2, "descricao": "Produto B", "quantidade": 5, "preco": 39.90}
        ]
        
        mock_movimentacoes = Mock()
        mock_movimentacoes.data = [
            {"created_at": data_antiga}
        ]
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        mock_table.select.side_effect = [
            Mock(execute=Mock(return_value=mock_produtos)),
            Mock(eq=Mock(return_value=Mock(order=Mock(return_value=Mock(limit=Mock(return_value=Mock(execute=Mock(return_value=mock_movimentacoes))))))))
        ]
        
        # Act
        resultado = estoque.produtos_sem_movimentacao(dias=30)
        
        # Assert
        assert len(resultado) == 1
        assert resultado[0]["id"] == 2
        assert resultado[0]["ultima_movimentacao"] == data_antiga
    
    @patch('estoque.supabase')
    def test_nao_retorna_produto_com_movimentacao_recente(self, mock_supabase):
        """Testa que produtos com movimentação recente não são retornados"""
        # Arrange
        data_recente = (datetime.now() - timedelta(days=10)).isoformat()
        
        mock_produtos = Mock()
        mock_produtos.data = [
            {"id": 3, "descricao": "Produto C", "quantidade": 8, "preco": 19.90}
        ]
        
        mock_movimentacoes = Mock()
        mock_movimentacoes.data = [
            {"created_at": data_recente}
        ]
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        mock_table.select.side_effect = [
            Mock(execute=Mock(return_value=mock_produtos)),
            Mock(eq=Mock(return_value=Mock(order=Mock(return_value=Mock(limit=Mock(return_value=Mock(execute=Mock(return_value=mock_movimentacoes))))))))
        ]
        
        # Act
        resultado = estoque.produtos_sem_movimentacao(dias=30)
        
        # Assert
        assert len(resultado) == 0
    
    @patch('estoque.supabase')
    def test_usa_parametro_dias_customizado(self, mock_supabase):
        """Testa uso de parâmetro de dias customizado"""
        # Arrange
        data_movimentacao = (datetime.now() - timedelta(days=50)).isoformat()
        
        mock_produtos = Mock()
        mock_produtos.data = [
            {"id": 4, "descricao": "Produto D", "quantidade": 3, "preco": 59.90}
        ]
        
        mock_movimentacoes = Mock()
        mock_movimentacoes.data = [
            {"created_at": data_movimentacao}
        ]
        
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        mock_table.select.side_effect = [
            Mock(execute=Mock(return_value=mock_produtos)),
            Mock(eq=Mock(return_value=Mock(order=Mock(return_value=Mock(limit=Mock(return_value=Mock(execute=Mock(return_value=mock_movimentacoes))))))))
        ]
        
        # Act - usando 60 dias, então produto com movimentação há 50 dias não deve aparecer
        resultado = estoque.produtos_sem_movimentacao(dias=60)
        
        # Assert
        assert len(resultado) == 0
    
    @patch('estoque.supabase')
    def test_retorna_lista_vazia_quando_nenhum_produto(self, mock_supabase):
        """Testa retorno de lista vazia quando não há produtos"""
        # Arrange
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.execute.return_value = mock_response
        
        # Act
        resultado = estoque.produtos_sem_movimentacao()
        
        # Assert
        assert resultado == []
    
    @patch('estoque.supabase')
    def test_trata_erro_de_conexao(self, mock_supabase):
        """Testa tratamento de erro de conexão"""
        # Arrange
        mock_supabase.table.return_value.select.return_value.execute.side_effect = Exception("Connection error")
        
        # Act
        resultado = estoque.produtos_sem_movimentacao()
        
        # Assert
        assert resultado == []
