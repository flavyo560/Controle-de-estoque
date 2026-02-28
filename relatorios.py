"""
Módulo de Relatórios - Sistema de Vendas DEKIDS

Este módulo gera relatórios gerenciais de vendas, produtos e vendedores.
"""

import csv
from typing import List, Dict, Optional
from database import supabase


def relatorio_vendas_periodo(
    data_inicio: str,
    data_fim: str,
    usuario_id: Optional[int] = None,
    forma_pagamento: Optional[str] = None
) -> Dict:
    """
    Gera relatório de vendas por período.
    
    Args:
        data_inicio: Data inicial (formato ISO)
        data_fim: Data final (formato ISO)
        usuario_id: Filtro opcional por vendedor
        forma_pagamento: Filtro opcional por forma de pagamento
        
    Returns:
        Dict com métricas e lista de vendas
    
    Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9
    """
    try:
        # Normalizar datas para incluir timestamp completo
        # Se data_inicio não tem hora, adicionar 00:00:00
        if 'T' not in data_inicio:
            data_inicio = f"{data_inicio}T00:00:00"
        # Se data_fim não tem hora, adicionar 23:59:59
        if 'T' not in data_fim:
            data_fim = f"{data_fim}T23:59:59"
        
        # Construir query base para vendas
        query = supabase.table('vendas').select(
            'id, data_hora, valor_total, desconto_valor, desconto_percentual, valor_final, '
            'status, cliente_id, usuario_id, '
            'clientes(nome, cpf), '
            'usuarios!vendas_usuario_id_fkey(username)'
        ).gte('data_hora', data_inicio).lte('data_hora', data_fim)
        
        # Aplicar filtro por vendedor se fornecido
        if usuario_id is not None:
            query = query.eq('usuario_id', usuario_id)
        
        # Executar query
        response = query.execute()
        vendas = response.data if response.data else []
        
        # Buscar pagamentos para todas as vendas
        venda_ids = [v['id'] for v in vendas]
        pagamentos_data = []
        
        if venda_ids:
            pagamentos_response = supabase.table('pagamentos').select(
                'venda_id, forma_pagamento, valor, numero_parcelas'
            ).in_('venda_id', venda_ids).execute()
            pagamentos_data = pagamentos_response.data if pagamentos_response.data else []
        
        # Criar mapa de pagamentos por venda_id
        pagamentos_por_venda = {}
        for pag in pagamentos_data:
            venda_id = pag['venda_id']
            if venda_id not in pagamentos_por_venda:
                pagamentos_por_venda[venda_id] = []
            pagamentos_por_venda[venda_id].append(pag)
        
        # Filtrar por forma de pagamento se fornecido
        if forma_pagamento:
            vendas_filtradas = []
            for venda in vendas:
                pagamentos_venda = pagamentos_por_venda.get(venda['id'], [])
                if any(p['forma_pagamento'] == forma_pagamento for p in pagamentos_venda):
                    vendas_filtradas.append(venda)
            vendas = vendas_filtradas
        
        # Separar vendas canceladas das não canceladas
        vendas_nao_canceladas = [v for v in vendas if v['status'] != 'cancelada']
        
        # Calcular métricas (excluindo vendas canceladas)
        faturamento_total = sum(v['valor_final'] for v in vendas_nao_canceladas)
        numero_vendas = len(vendas_nao_canceladas)
        ticket_medio = faturamento_total / numero_vendas if numero_vendas > 0 else 0.0
        
        # Calcular distribuição por forma de pagamento
        distribuicao_pagamento = {}
        for venda in vendas_nao_canceladas:
            pagamentos_venda = pagamentos_por_venda.get(venda['id'], [])
            for pag in pagamentos_venda:
                forma = pag['forma_pagamento']
                if forma not in distribuicao_pagamento:
                    distribuicao_pagamento[forma] = 0.0
                distribuicao_pagamento[forma] += pag['valor']
        
        # Converter para lista com percentuais
        distribuicao_lista = []
        for forma, valor in distribuicao_pagamento.items():
            percentual = (valor / faturamento_total * 100) if faturamento_total > 0 else 0.0
            distribuicao_lista.append({
                'forma_pagamento': forma,
                'valor': float(valor),
                'percentual': float(percentual)
            })
        
        # Preparar lista de vendas com detalhes
        vendas_detalhadas = []
        for venda in vendas:
            pagamentos_venda = pagamentos_por_venda.get(venda['id'], [])
            
            # Extrair nome do cliente
            cliente_nome = None
            if venda.get('clientes') and isinstance(venda['clientes'], dict):
                cliente_nome = venda['clientes'].get('nome')
            
            # Extrair nome do vendedor
            vendedor_nome = None
            if venda.get('usuarios') and isinstance(venda['usuarios'], dict):
                vendedor_nome = venda['usuarios'].get('username')
            
            vendas_detalhadas.append({
                'id': venda['id'],
                'data_hora': venda['data_hora'],
                'valor_total': float(venda['valor_total']),
                'desconto_valor': float(venda.get('desconto_valor', 0)),
                'desconto_percentual': float(venda.get('desconto_percentual', 0)),
                'valor_final': float(venda['valor_final']),
                'status': venda['status'],
                'cliente_nome': cliente_nome,
                'vendedor_nome': vendedor_nome,
                'pagamentos': pagamentos_venda
            })
        
        return {
            'faturamento_total': float(faturamento_total),
            'numero_vendas': numero_vendas,
            'ticket_medio': float(ticket_medio),
            'distribuicao_pagamento': distribuicao_lista,
            'vendas': vendas_detalhadas
        }
        
    except Exception as e:
        from logging_config import registrar_erro
        registrar_erro(
            mensagem="Erro ao gerar relatório de vendas por período",
            modulo="relatorios",
            funcao="relatorio_vendas_periodo",
            detalhes={
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "usuario_id": usuario_id,
                "forma_pagamento": forma_pagamento,
                "erro": str(e)
            },
            exc_info=True
        )
        raise


def relatorio_produtos_mais_vendidos(
    data_inicio: str,
    data_fim: str,
    filtros: Optional[Dict] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Gera relatório de produtos mais vendidos.
    
    Args:
        data_inicio: Data inicial no formato 'YYYY-MM-DD'
        data_fim: Data final no formato 'YYYY-MM-DD'
        filtros: Dicionário opcional com filtros adicionais
            - genero: str
            - marca: str
            - preco_min: float
            - preco_max: float
        limit: Número máximo de produtos a retornar (top N)
    
    Returns:
        Lista de dicionários contendo:
        - produto_id: ID do produto
        - descricao: Descrição do produto
        - marca: Marca do produto
        - referencia: Referência do produto
        - tamanho: Tamanho do produto
        - quantidade_vendida: Total de unidades vendidas
        - faturamento_gerado: Total de receita gerada
        - percentual_participacao: Percentual do faturamento total
    
    Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5
    """
    try:
        # Normalizar datas para incluir timestamp completo
        if 'T' not in data_inicio:
            data_inicio = f"{data_inicio}T00:00:00"
        if 'T' not in data_fim:
            data_fim = f"{data_fim}T23:59:59"
        
        # Buscar vendas não canceladas no período
        vendas_response = supabase.table('vendas').select(
            'id, data_hora, status'
        ).gte('data_hora', data_inicio).lte('data_hora', data_fim).neq('status', 'cancelada').execute()
        
        vendas = vendas_response.data if vendas_response.data else []
        
        if not vendas:
            return []
        
        venda_ids = [v['id'] for v in vendas]
        
        # Buscar itens de venda com informações dos produtos
        itens_response = supabase.table('itens_venda').select(
            'produto_id, quantidade, subtotal, '
            'produtos(id, descricao, marca, referencia, tamanho, genero, preco)'
        ).in_('venda_id', venda_ids).execute()
        
        itens = itens_response.data if itens_response.data else []
        
        if not itens:
            return []
        
        # Aplicar filtros de produto se fornecidos
        if filtros:
            itens_filtrados = []
            for item in itens:
                produto = item.get('produtos')
                if not produto or not isinstance(produto, dict):
                    continue
                
                # Filtro por gênero
                if 'genero' in filtros and filtros['genero']:
                    if produto.get('genero') != filtros['genero']:
                        continue
                
                # Filtro por marca
                if 'marca' in filtros and filtros['marca']:
                    if produto.get('marca') != filtros['marca']:
                        continue
                
                # Filtro por preço mínimo
                if 'preco_min' in filtros and filtros['preco_min'] is not None:
                    if produto.get('preco', 0) < filtros['preco_min']:
                        continue
                
                # Filtro por preço máximo
                if 'preco_max' in filtros and filtros['preco_max'] is not None:
                    if produto.get('preco', 0) > filtros['preco_max']:
                        continue
                
                itens_filtrados.append(item)
            
            itens = itens_filtrados
        
        # Agregar dados por produto_id
        produtos_agregados = {}
        
        for item in itens:
            produto_id = item['produto_id']
            quantidade = item['quantidade']
            subtotal = item['subtotal']
            produto = item.get('produtos')
            
            if not produto or not isinstance(produto, dict):
                continue
            
            if produto_id not in produtos_agregados:
                produtos_agregados[produto_id] = {
                    'produto_id': produto_id,
                    'descricao': produto.get('descricao', ''),
                    'marca': produto.get('marca', ''),
                    'referencia': produto.get('referencia', ''),
                    'tamanho': produto.get('tamanho', ''),
                    'quantidade_vendida': 0,
                    'faturamento_gerado': 0.0
                }
            
            produtos_agregados[produto_id]['quantidade_vendida'] += quantidade
            produtos_agregados[produto_id]['faturamento_gerado'] += float(subtotal)
        
        # Converter para lista
        produtos_lista = list(produtos_agregados.values())
        
        # Calcular faturamento total para percentuais
        faturamento_total = sum(p['faturamento_gerado'] for p in produtos_lista)
        
        # Adicionar percentual de participação
        for produto in produtos_lista:
            if faturamento_total > 0:
                produto['percentual_participacao'] = (produto['faturamento_gerado'] / faturamento_total) * 100
            else:
                produto['percentual_participacao'] = 0.0
        
        # Ordenar por quantidade vendida (descendente)
        produtos_lista.sort(key=lambda x: x['quantidade_vendida'], reverse=True)
        
        # Aplicar limite se fornecido
        if limit is not None and limit > 0:
            produtos_lista = produtos_lista[:limit]
        
        return produtos_lista
        
    except Exception as e:
        from logging_config import registrar_erro
        registrar_erro(
            mensagem="Erro ao gerar relatório de produtos mais vendidos",
            modulo="relatorios",
            funcao="relatorio_produtos_mais_vendidos",
            detalhes={
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "filtros": filtros,
                "limit": limit,
                "erro": str(e)
            },
            exc_info=True
        )
        raise


def relatorio_vendas_por_vendedor(
    data_inicio: str,
    data_fim: str
) -> List[Dict]:
    """
    Gera relatório de desempenho de vendedores.
    
    Args:
        data_inicio: Data inicial no formato 'YYYY-MM-DD'
        data_fim: Data final no formato 'YYYY-MM-DD'
    
    Returns:
        Lista de dicionários contendo:
        - usuario_id: ID do vendedor
        - nome_vendedor: Nome do vendedor
        - numero_vendas: Contagem de vendas
        - faturamento_total: Soma de valor_final das vendas
        - ticket_medio: Faturamento total / número de vendas
        - percentual_participacao: Percentual do faturamento total
    
    Requisitos: 10.1, 10.2, 10.3, 10.4
    """
    try:
        # Normalizar datas para incluir timestamp completo
        if 'T' not in data_inicio:
            data_inicio = f"{data_inicio}T00:00:00"
        if 'T' not in data_fim:
            data_fim = f"{data_fim}T23:59:59"
        
        # Buscar vendas não canceladas no período com informações do vendedor
        vendas_response = supabase.table('vendas').select(
            'id, usuario_id, valor_final, status, '
            'usuarios!vendas_usuario_id_fkey(username)'
        ).gte('data_hora', data_inicio).lte('data_hora', data_fim).neq('status', 'cancelada').execute()
        
        vendas = vendas_response.data if vendas_response.data else []
        
        if not vendas:
            return []
        
        # Agregar dados por usuario_id (vendedor)
        vendedores_agregados = {}
        
        for venda in vendas:
            usuario_id = venda['usuario_id']
            valor_final = float(venda['valor_final'])
            
            # Extrair nome do vendedor
            nome_vendedor = None
            if venda.get('usuarios') and isinstance(venda['usuarios'], dict):
                nome_vendedor = venda['usuarios'].get('username')
            
            if usuario_id not in vendedores_agregados:
                vendedores_agregados[usuario_id] = {
                    'usuario_id': usuario_id,
                    'nome_vendedor': nome_vendedor or f'Usuário {usuario_id}',
                    'numero_vendas': 0,
                    'faturamento_total': 0.0
                }
            
            vendedores_agregados[usuario_id]['numero_vendas'] += 1
            vendedores_agregados[usuario_id]['faturamento_total'] += valor_final
        
        # Converter para lista
        vendedores_lista = list(vendedores_agregados.values())
        
        # Calcular faturamento total para percentuais
        faturamento_total_geral = sum(v['faturamento_total'] for v in vendedores_lista)
        
        # Calcular ticket médio e percentual de participação
        for vendedor in vendedores_lista:
            # Ticket médio = faturamento_total / numero_vendas
            if vendedor['numero_vendas'] > 0:
                vendedor['ticket_medio'] = vendedor['faturamento_total'] / vendedor['numero_vendas']
            else:
                vendedor['ticket_medio'] = 0.0
            
            # Percentual de participação
            if faturamento_total_geral > 0:
                vendedor['percentual_participacao'] = (vendedor['faturamento_total'] / faturamento_total_geral) * 100
            else:
                vendedor['percentual_participacao'] = 0.0
        
        # Ordenar por faturamento_total em ordem decrescente
        vendedores_lista.sort(key=lambda x: x['faturamento_total'], reverse=True)
        
        return vendedores_lista
        
    except Exception as e:
        from logging_config import registrar_erro
        registrar_erro(
            mensagem="Erro ao gerar relatório de vendas por vendedor",
            modulo="relatorios",
            funcao="relatorio_vendas_por_vendedor",
            detalhes={
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "erro": str(e)
            },
            exc_info=True
        )
        raise


def exportar_relatorio_csv(dados: List[Dict], caminho: str) -> bool:
    """
    Exporta relatório para formato CSV.
    
    Args:
        dados: Lista de dicionários com dados do relatório
        caminho: Caminho do arquivo CSV a ser criado
    
    Returns:
        bool indicando se a exportação foi bem-sucedida
    
    Requisitos: 8.10, 9.7, 10.7
    """
    try:
        import os
        from logging_config import registrar_erro
        
        # Validar dados de entrada
        if not dados:
            registrar_erro(
                mensagem="Tentativa de exportar CSV com dados vazios",
                modulo="relatorios",
                funcao="exportar_relatorio_csv",
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
        
        return True
        
    except Exception as e:
        from logging_config import registrar_erro
        registrar_erro(
            mensagem="Erro ao exportar relatório para CSV",
            modulo="relatorios",
            funcao="exportar_relatorio_csv",
            detalhes={
                "caminho": caminho,
                "numero_registros": len(dados) if dados else 0,
                "erro": str(e)
            },
            exc_info=True
        )
        return False
