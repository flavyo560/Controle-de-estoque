"""
Testes de integração para verificar que registrar_entrada e registrar_saida
usam registrar_movimentacao internamente.

Feature: sistema-estoque-melhorado
Requisitos: 3.1
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock das variáveis de ambiente antes de importar database
with patch.dict('os.environ', {'SUPABASE_URL': 'http://test.supabase.co', 'SUPABASE_KEY': 'test-key'}):
    import database


class TestIntegracaoRegistrarEntrada:
    """Testes para verificar integração de registrar_entrada com registrar_movimentacao"""
    
    @patch('database.registrar_movimentacao')
    def test_registrar_entrada_chama_registrar_movimentacao(self, mock_registrar_mov):
        """Testa que registrar_entrada chama registrar_movimentacao com parâmetros corretos"""
        # Arrange
        mock_registrar_mov.return_value = True
        produto_id = 10
        qtd_atual = 5
        
        # Act
        resultado = database.registrar_entrada(produto_id, qtd_atual)
        
        # Assert
        assert resultado is True
        mock_registrar_mov.assert_called_once_with(
            produto_id=produto_id,
            tipo='entrada',
            quantidade=1,
            observacao='Entrada unitária via interface'
        )
    
    @patch('database.registrar_movimentacao')
    def test_registrar_entrada_retorna_false_quando_movimentacao_falha(self, mock_registrar_mov):
        """Testa que registrar_entrada retorna False quando registrar_movimentacao falha"""
        # Arrange
        mock_registrar_mov.return_value = False
        produto_id = 10
        qtd_atual = 5
        
        # Act
        resultado = database.registrar_entrada(produto_id, qtd_atual)
        
        # Assert
        assert resultado is False
    
    @patch('database.registrar_movimentacao')
    def test_registrar_entrada_trata_excecao(self, mock_registrar_mov):
        """Testa que registrar_entrada trata exceções adequadamente"""
        # Arrange
        mock_registrar_mov.side_effect = Exception("Erro de teste")
        produto_id = 10
        qtd_atual = 5
        
        # Act
        resultado = database.registrar_entrada(produto_id, qtd_atual)
        
        # Assert
        assert resultado is False


class TestIntegracaoRegistrarSaida:
    """Testes para verificar integração de registrar_saida com registrar_movimentacao"""
    
    @patch('database.registrar_movimentacao')
    def test_registrar_saida_chama_registrar_movimentacao(self, mock_registrar_mov):
        """Testa que registrar_saida chama registrar_movimentacao com parâmetros corretos"""
        # Arrange
        mock_registrar_mov.return_value = True
        produto_id = 15
        qtd_atual = 10
        
        # Act
        resultado = database.registrar_saida(produto_id, qtd_atual)
        
        # Assert
        assert resultado is True
        mock_registrar_mov.assert_called_once_with(
            produto_id=produto_id,
            tipo='saida',
            quantidade=1,
            observacao='Saída unitária via interface'
        )
    
    @patch('database.registrar_movimentacao')
    def test_registrar_saida_retorna_false_quando_estoque_zero(self, mock_registrar_mov):
        """Testa que registrar_saida retorna False quando estoque está zerado"""
        # Arrange
        produto_id = 15
        qtd_atual = 0
        
        # Act
        resultado = database.registrar_saida(produto_id, qtd_atual)
        
        # Assert
        assert resultado is False
        # Não deve chamar registrar_movimentacao quando estoque está zerado
        mock_registrar_mov.assert_not_called()
    
    @patch('database.registrar_movimentacao')
    def test_registrar_saida_retorna_false_quando_movimentacao_falha(self, mock_registrar_mov):
        """Testa que registrar_saida retorna False quando registrar_movimentacao falha"""
        # Arrange
        mock_registrar_mov.return_value = False
        produto_id = 15
        qtd_atual = 5
        
        # Act
        resultado = database.registrar_saida(produto_id, qtd_atual)
        
        # Assert
        assert resultado is False
    
    @patch('database.registrar_movimentacao')
    def test_registrar_saida_trata_excecao(self, mock_registrar_mov):
        """Testa que registrar_saida trata exceções adequadamente"""
        # Arrange
        mock_registrar_mov.side_effect = Exception("Erro de teste")
        produto_id = 15
        qtd_atual = 5
        
        # Act
        resultado = database.registrar_saida(produto_id, qtd_atual)
        
        # Assert
        assert resultado is False


class TestCompatibilidadeRetroativa:
    """Testes para garantir compatibilidade com código existente"""
    
    @patch('database.supabase')
    @patch('database.registrar_movimentacao')
    def test_registrar_entrada_mantem_interface_original(self, mock_registrar_mov, mock_supabase):
        """Testa que registrar_entrada mantém a mesma interface (assinatura)"""
        # Arrange
        mock_registrar_mov.return_value = True
        
        # Act - chamada com parâmetros posicionais (interface original)
        resultado = database.registrar_entrada(10, 5)
        
        # Assert
        assert resultado is True
        assert mock_registrar_mov.called
    
    @patch('database.supabase')
    @patch('database.registrar_movimentacao')
    def test_registrar_saida_mantem_interface_original(self, mock_registrar_mov, mock_supabase):
        """Testa que registrar_saida mantém a mesma interface (assinatura)"""
        # Arrange
        mock_registrar_mov.return_value = True
        
        # Act - chamada com parâmetros posicionais (interface original)
        resultado = database.registrar_saida(10, 5)
        
        # Assert
        assert resultado is True
        assert mock_registrar_mov.called
    
    @patch('database.registrar_movimentacao')
    def test_registrar_entrada_retorna_booleano(self, mock_registrar_mov):
        """Testa que registrar_entrada retorna booleano (compatibilidade)"""
        # Arrange
        mock_registrar_mov.return_value = True
        
        # Act
        resultado = database.registrar_entrada(10, 5)
        
        # Assert
        assert isinstance(resultado, bool)
    
    @patch('database.registrar_movimentacao')
    def test_registrar_saida_retorna_booleano(self, mock_registrar_mov):
        """Testa que registrar_saida retorna booleano (compatibilidade)"""
        # Arrange
        mock_registrar_mov.return_value = True
        
        # Act
        resultado = database.registrar_saida(10, 5)
        
        # Assert
        assert isinstance(resultado, bool)
