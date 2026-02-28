"""
Módulo de Códigos de Barras e QR Codes

Este módulo fornece funcionalidades para:
- Validação de códigos de barras EAN-13
- Busca de produtos por código de barras
- Geração de QR codes com informações de produtos
"""

import qrcode
from io import BytesIO
from typing import Optional
import database
from logging_config import registrar_erro, registrar_info


def validar_codigo_barras(codigo: str) -> bool:
    """
    Valida formato de código de barras EAN-13.
    
    EAN-13 é um código de 13 dígitos com dígito verificador calculado
    usando o algoritmo de módulo 10.
    
    Args:
        codigo: String contendo o código de barras
        
    Returns:
        True se o código é válido, False caso contrário
        
    Exemplos:
        >>> validar_codigo_barras("7891234567890")
        True
        >>> validar_codigo_barras("123")
        False
        >>> validar_codigo_barras("7891234567891")  # dígito verificador errado
        False
    """
    # Verificar se é string
    if not isinstance(codigo, str):
        return False
    
    # Remover espaços em branco
    codigo = codigo.strip()
    
    # Verificar se tem exatamente 13 dígitos
    if len(codigo) != 13:
        return False
    
    # Verificar se todos são dígitos
    if not codigo.isdigit():
        return False
    
    # Calcular dígito verificador
    # Algoritmo EAN-13:
    # 1. Somar dígitos nas posições ímpares (1, 3, 5, 7, 9, 11) multiplicados por 1
    # 2. Somar dígitos nas posições pares (2, 4, 6, 8, 10, 12) multiplicados por 3
    # 3. Somar os dois resultados
    # 4. Calcular o resto da divisão por 10
    # 5. Se resto = 0, dígito verificador = 0, senão dígito verificador = 10 - resto
    
    soma = 0
    for i in range(12):
        digito = int(codigo[i])
        if i % 2 == 0:
            # Posições ímpares (índice par: 0, 2, 4, 6, 8, 10)
            soma += digito
        else:
            # Posições pares (índice ímpar: 1, 3, 5, 7, 9, 11)
            soma += digito * 3
    
    resto = soma % 10
    digito_verificador_calculado = 0 if resto == 0 else 10 - resto
    digito_verificador_fornecido = int(codigo[12])
    
    valido = digito_verificador_calculado == digito_verificador_fornecido
    
    if not valido:
        registrar_info(
            "barcode",
            "validar_codigo_barras",
            f"Código de barras inválido: {codigo} (dígito verificador incorreto)"
        )
    
    return valido


def buscar_por_codigo(codigo: str) -> Optional[dict]:
    """
    Busca produto por código de barras.
    
    Args:
        codigo: Código de barras do produto
        
    Returns:
        Dicionário com dados do produto se encontrado, None caso contrário
        
    Exemplos:
        >>> produto = buscar_por_codigo("7891234567890")
        >>> if produto:
        ...     print(produto['descricao'])
    """
    try:
        # Validar formato do código antes de buscar
        if not validar_codigo_barras(codigo):
            registrar_info(
                "barcode",
                "buscar_por_codigo",
                f"Tentativa de busca com código inválido: {codigo}"
            )
            return None
        
        # Buscar produto no banco de dados
        response = database.supabase.table("produtos").select("*").eq("codigo_barras", codigo).execute()
        
        if response.data and len(response.data) > 0:
            produto = response.data[0]
            registrar_info(
                "barcode",
                "buscar_por_codigo",
                f"Produto encontrado: {produto.get('descricao')} (ID: {produto.get('id')})"
            )
            return produto
        else:
            registrar_info(
                "barcode",
                "buscar_por_codigo",
                f"Nenhum produto encontrado com código: {codigo}"
            )
            return None
            
    except Exception as e:
        registrar_erro(
            "barcode",
            "buscar_por_codigo",
            f"Erro ao buscar produto por código de barras: {codigo}",
            {"erro": str(e)},
            exc_info=True
        )
        return None


def gerar_qrcode(produto_id: int) -> Optional[bytes]:
    """
    Gera QR code com informações do produto.
    
    O QR code contém informações básicas do produto em formato JSON:
    - id
    - descricao
    - referencia
    - preco
    
    Args:
        produto_id: ID do produto
        
    Returns:
        Imagem do QR code em bytes (formato PNG), ou None se produto não encontrado
        
    Exemplos:
        >>> qr_bytes = gerar_qrcode(123)
        >>> if qr_bytes:
        ...     with open('qrcode.png', 'wb') as f:
        ...         f.write(qr_bytes)
    """
    try:
        # Buscar produto no banco de dados
        response = database.supabase.table("produtos").select("*").eq("id", produto_id).execute()
        
        if not response.data or len(response.data) == 0:
            registrar_info(
                "barcode",
                "gerar_qrcode",
                f"Produto não encontrado: ID {produto_id}"
            )
            return None
        
        produto = response.data[0]
        
        # Criar dados para o QR code em formato JSON
        import json
        qr_data = json.dumps({
            "id": produto.get("id"),
            "descricao": produto.get("descricao"),
            "referencia": produto.get("referencia"),
            "preco": float(produto.get("preco", 0))
        }, ensure_ascii=False)
        
        # Gerar QR code
        qr = qrcode.QRCode(
            version=1,  # Tamanho do QR code (1 é o menor)
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Criar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_bytes = buffer.getvalue()
        
        registrar_info(
            "barcode",
            "gerar_qrcode",
            f"QR code gerado para produto: {produto.get('descricao')} (ID: {produto_id})"
        )
        
        return qr_bytes
        
    except Exception as e:
        registrar_erro(
            "barcode",
            "gerar_qrcode",
            f"Erro ao gerar QR code para produto ID {produto_id}",
            {"erro": str(e)},
            exc_info=True
        )
        return None
