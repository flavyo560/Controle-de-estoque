"""
Testes unitários para validação de pagamento
"""

import pytest
from validacao_vendas import validar_pagamento


def test_validar_pagamento_dinheiro_valido():
    """Testa pagamento em dinheiro válido"""
    valido, msg = validar_pagamento('dinheiro', 100.0)
    assert valido is True
    assert msg == "Pagamento válido"


def test_validar_pagamento_cartao_credito_valido():
    """Testa pagamento com cartão de crédito válido"""
    valido, msg = validar_pagamento('cartao_credito', 100.0, numero_parcelas=3)
    assert valido is True
    assert msg == "Pagamento válido"


def test_validar_pagamento_cartao_debito_valido():
    """Testa pagamento com cartão de débito válido"""
    valido, msg = validar_pagamento('cartao_debito', 100.0)
    assert valido is True
    assert msg == "Pagamento válido"


def test_validar_pagamento_pix_valido():
    """Testa pagamento via PIX válido"""
    valido, msg = validar_pagamento('pix', 100.0)
    assert valido is True
    assert msg == "Pagamento válido"


def test_validar_pagamento_forma_invalida():
    """Testa forma de pagamento inválida"""
    valido, msg = validar_pagamento('boleto', 100.0)
    assert valido is False
    assert "Forma de pagamento inválida" in msg


def test_validar_pagamento_valor_zero():
    """Testa pagamento com valor zero"""
    valido, msg = validar_pagamento('dinheiro', 0)
    assert valido is False
    assert "maior que zero" in msg


def test_validar_pagamento_valor_negativo():
    """Testa pagamento com valor negativo"""
    valido, msg = validar_pagamento('dinheiro', -50.0)
    assert valido is False
    assert "maior que zero" in msg


def test_validar_pagamento_cartao_credito_sem_parcelas():
    """Testa cartão de crédito sem número de parcelas"""
    valido, msg = validar_pagamento('cartao_credito', 100.0)
    assert valido is False
    assert "obrigatório" in msg


def test_validar_pagamento_cartao_credito_parcelas_invalidas():
    """Testa cartão de crédito com número de parcelas inválido"""
    # Parcelas = 0
    valido, msg = validar_pagamento('cartao_credito', 100.0, numero_parcelas=0)
    assert valido is False
    assert "entre 1 e 12" in msg
    
    # Parcelas = 13
    valido, msg = validar_pagamento('cartao_credito', 100.0, numero_parcelas=13)
    assert valido is False
    assert "entre 1 e 12" in msg
    
    # Parcelas = -1
    valido, msg = validar_pagamento('cartao_credito', 100.0, numero_parcelas=-1)
    assert valido is False
    assert "entre 1 e 12" in msg


def test_validar_pagamento_cartao_credito_parcelas_limites():
    """Testa cartão de crédito com parcelas nos limites (1 e 12)"""
    # Parcelas = 1
    valido, msg = validar_pagamento('cartao_credito', 100.0, numero_parcelas=1)
    assert valido is True
    
    # Parcelas = 12
    valido, msg = validar_pagamento('cartao_credito', 100.0, numero_parcelas=12)
    assert valido is True


def test_validar_pagamento_dinheiro_com_parcelas():
    """Testa pagamento em dinheiro com parcelas (não permitido)"""
    valido, msg = validar_pagamento('dinheiro', 100.0, numero_parcelas=2)
    assert valido is False
    assert "não é permitido" in msg


def test_validar_pagamento_cartao_debito_com_parcelas():
    """Testa pagamento com cartão de débito com parcelas (não permitido)"""
    valido, msg = validar_pagamento('cartao_debito', 100.0, numero_parcelas=2)
    assert valido is False
    assert "não é permitido" in msg


def test_validar_pagamento_pix_com_parcelas():
    """Testa pagamento via PIX com parcelas (não permitido)"""
    valido, msg = validar_pagamento('pix', 100.0, numero_parcelas=2)
    assert valido is False
    assert "não é permitido" in msg


# Testes para validar_pagamentos_venda

from validacao_vendas import validar_pagamentos_venda


def test_validar_pagamentos_venda_unico_pagamento_valido():
    """Testa venda com um único pagamento válido"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 100.0}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is True
    assert msg == "Pagamentos válidos"


def test_validar_pagamentos_venda_multiplos_pagamentos_validos():
    """Testa venda com múltiplos pagamentos válidos (pagamento misto)"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 50.0},
        {'forma_pagamento': 'cartao_debito', 'valor': 30.0},
        {'forma_pagamento': 'pix', 'valor': 20.0}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is True
    assert msg == "Pagamentos válidos"


def test_validar_pagamentos_venda_com_cartao_credito():
    """Testa venda com cartão de crédito parcelado"""
    pagamentos = [
        {'forma_pagamento': 'cartao_credito', 'valor': 100.0, 'numero_parcelas': 3}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is True
    assert msg == "Pagamentos válidos"


def test_validar_pagamentos_venda_soma_incorreta_maior():
    """Testa venda onde soma dos pagamentos é maior que o total"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 60.0},
        {'forma_pagamento': 'pix', 'valor': 50.0}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is False
    assert "não corresponde ao total da venda" in msg
    assert "110.00" in msg  # Soma dos pagamentos
    assert "100.00" in msg  # Total da venda


def test_validar_pagamentos_venda_soma_incorreta_menor():
    """Testa venda onde soma dos pagamentos é menor que o total"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 40.0},
        {'forma_pagamento': 'pix', 'valor': 30.0}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is False
    assert "não corresponde ao total da venda" in msg
    assert "70.00" in msg  # Soma dos pagamentos
    assert "100.00" in msg  # Total da venda


def test_validar_pagamentos_venda_lista_vazia():
    """Testa venda sem nenhum pagamento"""
    pagamentos = []
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is False
    assert "pelo menos uma forma de pagamento" in msg


def test_validar_pagamentos_venda_pagamento_individual_invalido():
    """Testa venda com um pagamento individual inválido"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 50.0},
        {'forma_pagamento': 'cartao_credito', 'valor': 50.0}  # Sem numero_parcelas
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is False
    assert "Pagamento 2" in msg
    assert "obrigatório" in msg


def test_validar_pagamentos_venda_forma_pagamento_invalida():
    """Testa venda com forma de pagamento inválida"""
    pagamentos = [
        {'forma_pagamento': 'boleto', 'valor': 100.0}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is False
    assert "Pagamento 1" in msg
    assert "Forma de pagamento inválida" in msg


def test_validar_pagamentos_venda_valor_negativo():
    """Testa venda com valor de pagamento negativo"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': -50.0}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is False
    assert "Pagamento 1" in msg
    assert "maior que zero" in msg


def test_validar_pagamentos_venda_tolerancia_ponto_flutuante():
    """Testa venda com diferença mínima devido a ponto flutuante (dentro da tolerância)"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 33.33},
        {'forma_pagamento': 'pix', 'valor': 33.33},
        {'forma_pagamento': 'cartao_debito', 'valor': 33.34}
    ]
    # Soma = 100.00, mas pode haver pequenas diferenças de arredondamento
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is True
    assert msg == "Pagamentos válidos"


def test_validar_pagamentos_venda_multiplos_pagamentos_com_credito():
    """Testa venda mista com cartão de crédito parcelado"""
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 50.0},
        {'forma_pagamento': 'cartao_credito', 'valor': 50.0, 'numero_parcelas': 2}
    ]
    valido, msg = validar_pagamentos_venda(pagamentos, 100.0)
    assert valido is True
    assert msg == "Pagamentos válidos"
