"""
Módulo de Validação de Vendas - Sistema de Vendas DEKIDS

Este módulo contém funções de validação para CPF, email, pagamentos e descontos.
"""

import re
from typing import Tuple, List, Dict, Optional


def validar_cpf(cpf: str) -> Tuple[bool, str]:
    """
    Valida formato e dígitos verificadores do CPF.
    
    Args:
        cpf: String contendo o CPF (apenas números)
    
    Returns:
        Tupla (valido, mensagem)
        - valido: bool indicando se o CPF é válido
        - mensagem: str com mensagem de erro ou sucesso
    
    Requisitos: 3.2
    """
    # Remove caracteres não numéricos
    cpf_numeros = re.sub(r'\D', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf_numeros) != 11:
        return False, "CPF deve conter exatamente 11 dígitos"
    
    # Verifica se todos os dígitos são iguais (CPF inválido)
    if cpf_numeros == cpf_numeros[0] * 11:
        return False, "CPF inválido"
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf_numeros[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_numeros[9]) != digito1:
        return False, "CPF inválido"
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf_numeros[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_numeros[10]) != digito2:
        return False, "CPF inválido"
    
    return True, "CPF válido"


def validar_email(email: str) -> Tuple[bool, str]:
    """
    Valida formato de email.
    
    Args:
        email: String contendo o email
    
    Returns:
        Tupla (valido, mensagem)
        - valido: bool indicando se o email é válido
        - mensagem: str com mensagem de erro ou sucesso
    
    Requisitos: 3.4
    """
    # Padrão regex para validação de email
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email or not email.strip():
        return False, "Email não pode ser vazio"
    
    if re.match(padrao, email.strip()):
        return True, "Email válido"
    else:
        return False, "Formato de email inválido"


def validar_pagamento(
    forma_pagamento: str,
    valor: float,
    numero_parcelas: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Valida dados de um pagamento individual.
    
    Args:
        forma_pagamento: Tipo de pagamento (dinheiro, cartao_credito, cartao_debito, pix)
        valor: Valor do pagamento
        numero_parcelas: Número de parcelas (apenas para cartão de crédito)
    
    Returns:
        Tupla (valido, mensagem)
        - valido: bool indicando se o pagamento é válido
        - mensagem: str com mensagem de erro ou sucesso
    
    Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Validar forma de pagamento
    formas_validas = ['dinheiro', 'cartao_credito', 'cartao_debito', 'pix']
    if forma_pagamento not in formas_validas:
        return False, f"Forma de pagamento inválida. Deve ser uma de: {', '.join(formas_validas)}"
    
    # Validar valor
    if valor <= 0:
        return False, "Valor do pagamento deve ser maior que zero"
    
    # Validar número de parcelas para cartão de crédito
    if forma_pagamento == 'cartao_credito':
        if numero_parcelas is None:
            return False, "Número de parcelas é obrigatório para pagamento com cartão de crédito"
        if not isinstance(numero_parcelas, int) or numero_parcelas < 1 or numero_parcelas > 12:
            return False, "Número de parcelas deve ser entre 1 e 12"
    else:
        # Para outras formas de pagamento, numero_parcelas deve ser None
        if numero_parcelas is not None:
            return False, f"Número de parcelas não é permitido para pagamento com {forma_pagamento}"
    
    return True, "Pagamento válido"


def validar_pagamentos_venda(
    pagamentos: List[Dict],
    valor_total: float
) -> Tuple[bool, str]:
    """
    Valida que a soma dos pagamentos corresponde ao total da venda.
    
    Args:
        pagamentos: Lista de dicionários com dados dos pagamentos
        valor_total: Valor total da venda
    
    Returns:
        Tupla (valido, mensagem)
        - valido: bool indicando se os pagamentos são válidos
        - mensagem: str com mensagem de erro ou sucesso
    
    Requisitos: 4.7, 4.8
    """
    # Validar que há pelo menos um pagamento
    if not pagamentos or len(pagamentos) == 0:
        return False, "Deve haver pelo menos uma forma de pagamento"
    
    # Validar cada pagamento individualmente
    for i, pagamento in enumerate(pagamentos):
        forma_pagamento = pagamento.get('forma_pagamento')
        valor = pagamento.get('valor')
        numero_parcelas = pagamento.get('numero_parcelas')
        
        valido, mensagem = validar_pagamento(forma_pagamento, valor, numero_parcelas)
        if not valido:
            return False, f"Pagamento {i+1}: {mensagem}"
    
    # Calcular soma dos valores dos pagamentos
    soma_pagamentos = sum(pagamento.get('valor', 0) for pagamento in pagamentos)
    
    # Validar que a soma corresponde ao valor total (com tolerância para precisão de ponto flutuante)
    tolerancia = 0.01
    diferenca = abs(soma_pagamentos - valor_total)
    
    if diferenca > tolerancia:
        return False, f"Soma dos pagamentos (R$ {soma_pagamentos:.2f}) não corresponde ao total da venda (R$ {valor_total:.2f})"
    
    return True, "Pagamentos válidos"


def validar_desconto(
    tipo: str,
    valor: float,
    total_carrinho: float
) -> Tuple[bool, str]:
    """
    Valida desconto percentual ou em valor fixo.
    
    Args:
        tipo: Tipo de desconto ('percentual' ou 'valor')
        valor: Valor do desconto (percentual 0-100 ou valor em reais)
        total_carrinho: Valor total do carrinho antes do desconto
    
    Returns:
        Tupla (valido, mensagem)
        - valido: bool indicando se o desconto é válido
        - mensagem: str com mensagem de erro ou sucesso
    
    Requisitos: 2.3, 2.4
    """
    # Validar tipo de desconto
    if tipo not in ['percentual', 'valor']:
        return False, f"Tipo de desconto inválido: {tipo}. Use 'percentual' ou 'valor'"
    
    # Validar desconto percentual
    if tipo == 'percentual':
        # Percentual deve estar entre 0 e 100
        if valor < 0 or valor > 100:
            return False, "Desconto percentual deve estar entre 0 e 100"
        
        # Calcular valor do desconto
        desconto_calculado = total_carrinho * valor / 100
        
        # Validar que desconto não resulta em valor negativo
        if total_carrinho - desconto_calculado < 0:
            return False, "Desconto resulta em valor negativo"
        
        return True, "Desconto percentual válido"
    
    # Validar desconto em valor fixo
    elif tipo == 'valor':
        # Valor não pode ser negativo
        if valor < 0:
            return False, "Desconto não pode ser negativo"
        
        # Valor não pode exceder total do carrinho
        if valor > total_carrinho:
            return False, "Desconto não pode exceder o total do carrinho"
        
        # Validar que desconto não resulta em valor negativo
        if total_carrinho - valor < 0:
            return False, "Desconto resulta em valor negativo"
        
        return True, "Desconto em valor válido"
