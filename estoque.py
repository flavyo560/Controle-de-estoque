"""
Módulo de Estoque - Sistema DEKIDS

Este módulo contém funções para gerenciar operações de estoque,
incluindo alertas de estoque baixo, cálculos de valor total e
identificação de produtos sem movimentação.

Requisitos: 2.1, 2.4, 5.3, 5.5
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
from logging_config import registrar_erro, registrar_info, registrar_aviso

# Carregar variáveis de ambiente
load_dotenv()

# Configurar cliente Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def verificar_estoque_baixo(produto_id: int = None) -> List[Dict[str, Any]]:
    """
    Retorna lista de produtos com estoque <= estoque_mínimo.
    
    Args:
        produto_id: ID do produto específico para verificar (opcional).
                   Se None, verifica todos os produtos.
    
    Returns:
        Lista de dicionários contendo informações dos produtos com estoque baixo.
        Cada dicionário contém: id, descricao, marca, referencia, tamanho,
        quantidade, estoque_minimo, preco.
    
    Requisitos: 2.1, 2.4
    """
    try:
        # Construir query base
        query = supabase.table("produtos").select("*")
        
        # Filtrar por produto específico se fornecido
        if produto_id is not None:
            query = query.eq("id", produto_id)
        
        # Executar query
        response = query.execute()
        
        if not response.data:
            registrar_info(
                mensagem="Nenhum produto encontrado para verificação de estoque baixo",
                modulo="estoque",
                funcao="verificar_estoque_baixo",
                detalhes={"produto_id": produto_id}
            )
            return []
        
        # Filtrar produtos com estoque baixo
        produtos_estoque_baixo = []
        for produto in response.data:
            quantidade = produto.get("quantidade", 0)
            estoque_minimo = produto.get("estoque_minimo", 5)
            
            if quantidade <= estoque_minimo:
                produtos_estoque_baixo.append(produto)
        
        registrar_info(
            mensagem=f"Verificação de estoque baixo concluída: {len(produtos_estoque_baixo)} produto(s) encontrado(s)",
            modulo="estoque",
            funcao="verificar_estoque_baixo",
            detalhes={
                "produto_id": produto_id,
                "total_produtos_baixo": len(produtos_estoque_baixo)
            }
        )
        
        return produtos_estoque_baixo
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao verificar estoque baixo",
            modulo="estoque",
            funcao="verificar_estoque_baixo",
            detalhes={"erro": str(e), "produto_id": produto_id},
            exc_info=True
        )
        print(f"Erro ao verificar estoque baixo: {e}")
        return []


def calcular_valor_total_estoque() -> float:
    """
    Calcula valor total do estoque (quantidade * preço de todos os produtos).
    
    Returns:
        Valor total do estoque em reais. Retorna 0.0 em caso de erro.
    
    Requisitos: 5.3
    """
    try:
        # Buscar todos os produtos
        response = supabase.table("produtos").select("quantidade, preco").execute()
        
        if not response.data:
            registrar_info(
                mensagem="Nenhum produto encontrado para cálculo de valor total",
                modulo="estoque",
                funcao="calcular_valor_total_estoque"
            )
            return 0.0
        
        # Calcular valor total
        valor_total = 0.0
        for produto in response.data:
            quantidade = produto.get("quantidade", 0)
            preco = produto.get("preco", 0.0)
            valor_total += quantidade * preco
        
        registrar_info(
            mensagem=f"Cálculo de valor total concluído: R$ {valor_total:.2f}",
            modulo="estoque",
            funcao="calcular_valor_total_estoque",
            detalhes={
                "valor_total": valor_total,
                "total_produtos": len(response.data)
            }
        )
        
        return valor_total
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao calcular valor total do estoque",
            modulo="estoque",
            funcao="calcular_valor_total_estoque",
            detalhes={"erro": str(e)},
            exc_info=True
        )
        print(f"Erro ao calcular valor total do estoque: {e}")
        return 0.0


def produtos_sem_movimentacao(dias: int = 30) -> List[Dict[str, Any]]:
    """
    Retorna produtos sem movimentação nos últimos N dias.
    
    Args:
        dias: Número de dias para verificar (padrão: 30)
    
    Returns:
        Lista de dicionários contendo informações dos produtos sem movimentação.
        Cada dicionário contém: id, descricao, marca, referencia, tamanho,
        quantidade, preco, ultima_movimentacao (ou None se nunca teve).
    
    Requisitos: 5.5
    """
    try:
        # Calcular data limite
        data_limite = datetime.now() - timedelta(days=dias)
        data_limite_str = data_limite.isoformat()
        
        # Buscar todos os produtos
        response_produtos = supabase.table("produtos").select("*").execute()
        
        if not response_produtos.data:
            registrar_info(
                mensagem="Nenhum produto encontrado para verificação de movimentação",
                modulo="estoque",
                funcao="produtos_sem_movimentacao",
                detalhes={"dias": dias}
            )
            return []
        
        produtos_sem_mov = []
        
        for produto in response_produtos.data:
            produto_id = produto["id"]
            
            # Buscar última movimentação do produto
            response_mov = (
                supabase.table("movimentacoes")
                .select("created_at")
                .eq("produto_id", produto_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            # Se não tem movimentação ou última movimentação é anterior à data limite
            if not response_mov.data:
                # Produto nunca teve movimentação
                produto_info = produto.copy()
                produto_info["ultima_movimentacao"] = None
                produtos_sem_mov.append(produto_info)
            else:
                ultima_mov_str = response_mov.data[0]["created_at"]
                # Converter string ISO para datetime
                ultima_mov = datetime.fromisoformat(ultima_mov_str.replace('Z', '+00:00'))
                
                if ultima_mov < data_limite:
                    # Última movimentação é anterior à data limite
                    produto_info = produto.copy()
                    produto_info["ultima_movimentacao"] = ultima_mov_str
                    produtos_sem_mov.append(produto_info)
        
        registrar_info(
            mensagem=f"Verificação de produtos sem movimentação concluída: {len(produtos_sem_mov)} produto(s) encontrado(s)",
            modulo="estoque",
            funcao="produtos_sem_movimentacao",
            detalhes={
                "dias": dias,
                "data_limite": data_limite_str,
                "total_produtos_sem_mov": len(produtos_sem_mov)
            }
        )
        
        return produtos_sem_mov
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao buscar produtos sem movimentação",
            modulo="estoque",
            funcao="produtos_sem_movimentacao",
            detalhes={"erro": str(e), "dias": dias},
            exc_info=True
        )
        print(f"Erro ao buscar produtos sem movimentação: {e}")
        return []
