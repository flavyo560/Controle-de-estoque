"""
Testes unitários para gerenciamento de sessões
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os

# Configurar variáveis de ambiente antes de importar database
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_KEY'] = 'test_key'

import database as db


class TestCriarSessao:
    """Testes para criar_sessao()"""
    
    @patch('database.supabase')
    def test_criar_sessao_sucesso(self, mock_supabase):
        """Testa criação de sessão com sucesso"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = [{"id": 1, "token": "abc123", "usuario_id": 1}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Executar
        sucesso, mensagem, token = db.criar_sessao(1)
        
        # Verificar
        assert sucesso is True
        assert "sucesso" in mensagem.lower()
        assert token is not None
        assert len(token) > 20  # Token deve ser longo
    
    @patch('database.supabase')
    def test_criar_sessao_sem_dados(self, mock_supabase):
        """Testa criação de sessão quando banco não retorna dados"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response
        
        # Executar
        sucesso, mensagem, token = db.criar_sessao(1)
        
        # Verificar
        assert sucesso is False
        assert token is None


class TestValidarSessao:
    """Testes para validar_sessao()"""
    
    @patch('database.supabase')
    def test_validar_sessao_valida(self, mock_supabase):
        """Testa validação de sessão válida"""
        # Configurar mock com sessão válida (expira em 1 hora)
        expira_em = datetime.now() + timedelta(hours=1)
        mock_response = Mock()
        mock_response.data = [{
            "id": 1,
            "token": "abc123",
            "usuario_id": 1,
            "expira_em": expira_em.isoformat(),
            "usuarios": {
                "id": 1,
                "username": "admin",
                "ativo": True
            }
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Executar
        valida, mensagem, usuario = db.validar_sessao("abc123")
        
        # Verificar
        assert valida is True
        assert "válida" in mensagem.lower()
        assert usuario is not None
        assert usuario["username"] == "admin"
    
    @patch('database.supabase')
    def test_validar_sessao_expirada(self, mock_supabase):
        """Testa validação de sessão expirada"""
        # Configurar mock com sessão expirada (expirou há 1 hora)
        expira_em = datetime.now() - timedelta(hours=1)
        mock_response = Mock()
        mock_response.data = [{
            "id": 1,
            "token": "abc123",
            "usuario_id": 1,
            "expira_em": expira_em.isoformat(),
            "usuarios": {
                "id": 1,
                "username": "admin",
                "ativo": True
            }
        }]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Executar
        valida, mensagem, usuario = db.validar_sessao("abc123")
        
        # Verificar
        assert valida is False
        assert "expirada" in mensagem.lower()
        assert usuario is None
    
    @patch('database.supabase')
    def test_validar_sessao_nao_encontrada(self, mock_supabase):
        """Testa validação de sessão não encontrada"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        # Executar
        valida, mensagem, usuario = db.validar_sessao("token_invalido")
        
        # Verificar
        assert valida is False
        assert "não encontrada" in mensagem.lower()
        assert usuario is None


class TestLimparSessoesExpiradas:
    """Testes para limpar_sessoes_expiradas()"""
    
    @patch('database.supabase')
    def test_limpar_sessoes_sucesso(self, mock_supabase):
        """Testa limpeza de sessões expiradas com sucesso"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.delete.return_value.lt.return_value.execute.return_value = mock_response
        
        # Executar
        sucesso, mensagem = db.limpar_sessoes_expiradas()
        
        # Verificar
        assert sucesso is True
        assert "removidas" in mensagem.lower() or "limpas" in mensagem.lower()


class TestEncerrarSessao:
    """Testes para encerrar_sessao()"""
    
    @patch('database.supabase')
    def test_encerrar_sessao_sucesso(self, mock_supabase):
        """Testa encerramento de sessão com sucesso"""
        # Configurar mock
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_response
        
        # Executar
        sucesso, mensagem = db.encerrar_sessao("abc123")
        
        # Verificar
        assert sucesso is True
        assert "encerrada" in mensagem.lower()
