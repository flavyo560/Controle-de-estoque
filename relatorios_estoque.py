"""
Módulo de Relatórios de Estoque - Sistema DEKIDS

Este módulo gera relatórios gerenciais de estoque e movimentações.
"""

import csv
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from database import supabase
from logging_config import registrar_erro, registrar_info


def gerar_relatorio_estoque_baixo() -> List[Dict]:
    """
    Gera relatório de produtos com estoque abaixo do mínimo.
    
    Returns:
        Lista de dicionários contendo produtos com estoque baixo:
        - id: ID do produto
        - descricao: Descrição do produto
        - marca: Marca do produto
        - referencia: Referência do produto
        - tamanho: Tamanho do produto
        - quantidade: Quantidade atual em estoque
        - estoque_minimo: Estoque mínimo configurado
        - diferenca: Diferença entre estoque atual e mínimo
    """
    try:
        # Buscar todos os produtos
        response = supabase.table("produtos").select("*").execute()
        produtos = response.data if response.data else []
        
        # Filtrar produtos com estoque baixo
        produtos_estoque_baixo = []
        
        for produto in produtos:
            estoque_minimo = produto.get('estoque_minimo', 5)
            quantidade_atual = produto.get('quantidade', 0)
            
            # Verificar se está abaixo do mínimo
            if quantidade_atual <= estoque_minimo:
                produtos_estoque_baixo.append({
                    'id': produto['id'],
                    'descricao': produto['descricao'],
                    'marca': produto.get('marca', ''),
                    'referencia': produto.get('referencia', ''),
                    'tamanho': produto.get('tamanho', ''),
                    'quantidade': quantidade_atual,
                    'estoque_minimo': estoque_minimo,
                    'diferenca': estoque_minimo - quantidade_atual
                })
        
        registrar_info(
            mensagem=f"Relatório de estoque baixo gerado: {len(produtos_estoque_baixo)} produtos",
            modulo="relatorios_estoque",
            funcao="gerar_relatorio_estoque_baixo"
        )
        
        return produtos_estoque_baixo
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao gerar relatório de estoque baixo",
            modulo="relatorios_estoque",
            funcao="gerar_relatorio_estoque_baixo",
            detalhes={"erro": str(e)},
            exc_info=True
        )
        return []


def gerar_relatorio_movimentacoes(data_inicio: str, data_fim: str) -> List[Dict]:
    """
    Gera relatório de movimentações de estoque no período.
    
    Args:
        data_inicio: Data inicial no formato 'YYYY-MM-DD' ou 'YYYY-MM-DDTHH:MM:SS'
        data_fim: Data final no formato 'YYYY-MM-DD' ou 'YYYY-MM-DDTHH:MM:SS'
    
    Returns:
        Lista de dicionários contendo movimentações:
        - id: ID da movimentação
        - produto_id: ID do produto
        - produto_descricao: Descrição do produto
        - tipo: Tipo de movimentação (entrada/saida/ajuste)
        - quantidade: Quantidade movimentada
        - quantidade_anterior: Quantidade antes da movimentação
        - quantidade_nova: Quantidade após a movimentação
        - data_hora: Data e hora da movimentação
        - observacao: Observação da movimentação
        - usuario_id: ID do usuário que realizou a movimentação
    """
    try:
        # Normalizar datas para incluir timestamp completo
        if 'T' not in data_inicio:
            data_inicio = f"{data_inicio}T00:00:00"
        if 'T' not in data_fim:
            data_fim = f"{data_fim}T23:59:59"
        
        # Buscar movimentações no período com informações do produto
        response = supabase.table("movimentacoes").select(
            "id, produto_id, tipo, quantidade, quantidade_anterior, quantidade_nova, "
            "data_hora, observacao, usuario_id, "
            "produtos(descricao, marca, referencia, tamanho)"
        ).gte('data_hora', data_inicio).lte('data_hora', data_fim).order('data_hora', desc=True).execute()
        
        movimentacoes = response.data if response.data else []
        
        # Formatar dados para o relatório
        relatorio = []
        for mov in movimentacoes:
            produto = mov.get('produtos', {})
            if isinstance(produto, dict):
                produto_descricao = produto.get('descricao', 'Produto não encontrado')
            else:
                produto_descricao = 'Produto não encontrado'
            
            relatorio.append({
                'id': mov['id'],
                'produto_id': mov['produto_id'],
                'produto_descricao': produto_descricao,
                'tipo': mov['tipo'],
                'quantidade': mov['quantidade'],
                'quantidade_anterior': mov['quantidade_anterior'],
                'quantidade_nova': mov['quantidade_nova'],
                'data_hora': mov['data_hora'],
                'observacao': mov.get('observacao', ''),
                'usuario_id': mov.get('usuario_id')
            })
        
        registrar_info(
            mensagem=f"Relatório de movimentações gerado: {len(relatorio)} registros",
            modulo="relatorios_estoque",
            funcao="gerar_relatorio_movimentacoes",
            detalhes={"data_inicio": data_inicio, "data_fim": data_fim}
        )
        
        return relatorio
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao gerar relatório de movimentações",
            modulo="relatorios_estoque",
            funcao="gerar_relatorio_movimentacoes",
            detalhes={
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "erro": str(e)
            },
            exc_info=True
        )
        return []


def gerar_relatorio_produtos_sem_movimentacao(dias: int) -> List[Dict]:
    """
    Gera relatório de produtos sem movimentação nos últimos X dias.
    
    Args:
        dias: Número de dias para verificar inatividade
    
    Returns:
        Lista de dicionários contendo produtos sem movimentação:
        - id: ID do produto
        - descricao: Descrição do produto
        - marca: Marca do produto
        - referencia: Referência do produto
        - tamanho: Tamanho do produto
        - quantidade: Quantidade atual em estoque
        - ultima_movimentacao: Data da última movimentação (ou None)
        - dias_sem_movimentacao: Dias desde a última movimentação
    """
    try:
        # Calcular data limite (X dias atrás)
        data_limite = datetime.now() - timedelta(days=dias)
        data_limite_str = data_limite.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Buscar todos os produtos
        produtos_response = supabase.table("produtos").select("*").execute()
        produtos = produtos_response.data if produtos_response.data else []
        
        # Buscar todas as movimentações recentes
        movimentacoes_response = supabase.table("movimentacoes").select(
            "produto_id, data_hora"
        ).gte('data_hora', data_limite_str).execute()
        
        movimentacoes = movimentacoes_response.data if movimentacoes_response.data else []
        
        # Criar set de produtos com movimentação recente
        produtos_com_movimentacao = set(mov['produto_id'] for mov in movimentacoes)
        
        # Filtrar produtos sem movimentação recente
        produtos_sem_movimentacao = []
        
        for produto in produtos:
            produto_id = produto['id']
            
            # Se produto não tem movimentação recente
            if produto_id not in produtos_com_movimentacao:
                # Buscar última movimentação do produto (se houver)
                ultima_mov_response = supabase.table("movimentacoes").select(
                    "data_hora"
                ).eq('produto_id', produto_id).order('data_hora', desc=True).limit(1).execute()
                
                ultima_movimentacao = None
                dias_sem_movimentacao = None
                
                if ultima_mov_response.data and len(ultima_mov_response.data) > 0:
                    ultima_movimentacao = ultima_mov_response.data[0]['data_hora']
                    # Calcular dias desde última movimentação
                    try:
                        data_ultima = datetime.fromisoformat(ultima_movimentacao.replace('Z', '+00:00'))
                        dias_sem_movimentacao = (datetime.now() - data_ultima.replace(tzinfo=None)).days
                    except:
                        dias_sem_movimentacao = None
                
                produtos_sem_movimentacao.append({
                    'id': produto_id,
                    'descricao': produto['descricao'],
                    'marca': produto.get('marca', ''),
                    'referencia': produto.get('referencia', ''),
                    'tamanho': produto.get('tamanho', ''),
                    'quantidade': produto.get('quantidade', 0),
                    'ultima_movimentacao': ultima_movimentacao,
                    'dias_sem_movimentacao': dias_sem_movimentacao if dias_sem_movimentacao else f"Mais de {dias}"
                })
        
        registrar_info(
            mensagem=f"Relatório de produtos sem movimentação gerado: {len(produtos_sem_movimentacao)} produtos",
            modulo="relatorios_estoque",
            funcao="gerar_relatorio_produtos_sem_movimentacao",
            detalhes={"dias": dias}
        )
        
        return produtos_sem_movimentacao
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao gerar relatório de produtos sem movimentação",
            modulo="relatorios_estoque",
            funcao="gerar_relatorio_produtos_sem_movimentacao",
            detalhes={"dias": dias, "erro": str(e)},
            exc_info=True
        )
        return []


def exportar_csv(dados: List[Dict], caminho: str) -> bool:
    """
    Exporta dados para arquivo CSV.
    
    Args:
        dados: Lista de dicionários com dados a exportar
        caminho: Caminho do arquivo CSV a ser criado
    
    Returns:
        bool indicando se a exportação foi bem-sucedida
    """
    try:
        import os
        
        # Validar dados de entrada
        if not dados:
            registrar_erro(
                mensagem="Tentativa de exportar CSV com dados vazios",
                modulo="relatorios_estoque",
                funcao="exportar_csv",
                detalhes={"caminho": caminho}
            )
            return False
        
        # Criar diretórios pai se não existirem
        diretorio = os.path.dirname(caminho)
        if diretorio and not os.path.exists(diretorio):
            os.makedirs(diretorio, exist_ok=True)
        
        # Obter cabeçalhos das chaves do primeiro dicionário
        headers = list(dados[0].keys())
        
        # Escrever arquivo CSV com UTF-8 BOM para compatibilidade com Excel
        with open(caminho, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # Escrever cabeçalhos
            writer.writeheader()
            
            # Escrever linhas de dados
            for linha in dados:
                # Converter valores complexos para string
                linha_processada = {}
                for key, value in linha.items():
                    if isinstance(value, (dict, list)):
                        # Converter dicts e listas para string
                        linha_processada[key] = str(value)
                    else:
                        linha_processada[key] = value
                
                writer.writerow(linha_processada)
        
        registrar_info(
            mensagem=f"CSV exportado com sucesso: {len(dados)} registros",
            modulo="relatorios_estoque",
            funcao="exportar_csv",
            detalhes={"caminho": caminho, "registros": len(dados)}
        )
        
        return True
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao exportar CSV",
            modulo="relatorios_estoque",
            funcao="exportar_csv",
            detalhes={
                "caminho": caminho,
                "numero_registros": len(dados) if dados else 0,
                "erro": str(e)
            },
            exc_info=True
        )
        return False
