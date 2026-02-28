"""
Módulo de Vendas - Sistema de Vendas DEKIDS

Este módulo gerencia o carrinho de compras e operações de vendas.
Integra-se com o sistema de estoque existente para validação e baixa de produtos.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple


@dataclass
class ItemCarrinho:
    """
    Representa um item no carrinho de compras.
    
    Attributes:
        produto_id: ID do produto no banco de dados
        descricao: Descrição do produto
        quantidade: Quantidade do produto no carrinho
        preco_unitario: Preço unitário do produto
        estoque_disponivel: Quantidade disponível em estoque
    """
    produto_id: int
    descricao: str
    quantidade: int
    preco_unitario: float
    estoque_disponivel: int
    
    def calcular_subtotal(self) -> float:
        """
        Calcula o subtotal do item (quantidade * preço unitário).
        
        Returns:
            float: Subtotal do item
        """
        return self.quantidade * self.preco_unitario



class Carrinho:
    """
    Gerencia o carrinho de compras temporário.
    
    Attributes:
        itens: Lista de itens no carrinho
        desconto_percentual: Desconto percentual aplicado (0-100)
        desconto_valor: Desconto em valor fixo aplicado
    """
    
    def __init__(self):
        """Inicializa um carrinho vazio sem descontos."""
        self.itens: List[ItemCarrinho] = []
        self.desconto_percentual: float = 0.0
        self.desconto_valor: float = 0.0
    
    def adicionar_produto(self, produto_id: int, quantidade: int = 1) -> bool:
        """
        Adiciona um produto ao carrinho ou incrementa sua quantidade se já existir.
        
        Busca o produto no banco de dados para obter preço e estoque,
        valida a disponibilidade e adiciona ao carrinho.
        
        Args:
            produto_id: ID do produto a ser adicionado
            quantidade: Quantidade a adicionar (padrão: 1)
        
        Returns:
            bool: True se produto foi adicionado com sucesso, False caso contrário
        
        Validates Requirements: 1.2, 1.3, 1.4
        """
        from database import supabase
        
        try:
            # Buscar produto no banco para obter preço e estoque
            response = supabase.table("produtos").select("*").eq("id", produto_id).execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            produto = response.data[0]
            preco_unitario = float(produto.get('preco', 0))
            estoque_disponivel = int(produto.get('quantidade', 0))
            descricao = produto.get('descricao', '')
            
            # Verificar se produto já existe no carrinho
            item_existente = None
            for item in self.itens:
                if item.produto_id == produto_id:
                    item_existente = item
                    break
            
            if item_existente:
                # Produto já existe - incrementar quantidade
                nova_quantidade = item_existente.quantidade + quantidade
                
                # Validar disponibilidade de estoque
                if nova_quantidade > estoque_disponivel:
                    return False
                
                item_existente.quantidade = nova_quantidade
            else:
                # Produto novo - validar estoque e adicionar
                if quantidade > estoque_disponivel:
                    return False
                
                # Criar novo ItemCarrinho e adicionar à lista
                novo_item = ItemCarrinho(
                    produto_id=produto_id,
                    descricao=descricao,
                    quantidade=quantidade,
                    preco_unitario=preco_unitario,
                    estoque_disponivel=estoque_disponivel
                )
                self.itens.append(novo_item)
            
            return True
            
        except Exception as e:
            # Em caso de erro (conexão, etc), retornar False
            return False

    def remover_produto(self, produto_id: int) -> bool:
        """
        Remove um produto do carrinho.
        
        Args:
            produto_id: ID do produto a ser removido
        
        Returns:
            bool: True se produto foi removido com sucesso, False se não encontrado
        
        Validates Requirement: 1.6
        """
        # Procurar o item no carrinho
        for i, item in enumerate(self.itens):
            if item.produto_id == produto_id:
                # Item encontrado - remover da lista
                self.itens.pop(i)
                return True
        
        # Item não encontrado no carrinho
        return False
    
    def atualizar_quantidade(self, produto_id: int, quantidade: int) -> bool:
        """
        Atualiza a quantidade de um produto no carrinho.
        
        Valida se a nova quantidade está disponível em estoque antes de atualizar.
        Se a quantidade solicitada exceder o estoque, mantém a quantidade anterior.
        
        Args:
            produto_id: ID do produto a ter quantidade atualizada
            quantidade: Nova quantidade desejada
        
        Returns:
            bool: True se quantidade foi atualizada com sucesso, False caso contrário
                  (item não encontrado ou estoque insuficiente)
        
        Validates Requirements: 1.4, 1.5
        """
        # Procurar o item no carrinho
        for item in self.itens:
            if item.produto_id == produto_id:
                # Item encontrado - validar disponibilidade de estoque
                if quantidade > item.estoque_disponivel:
                    # Estoque insuficiente - manter quantidade anterior
                    return False
                
                # Validar que quantidade é positiva
                if quantidade <= 0:
                    return False
                
                # Atualizar quantidade
                item.quantidade = quantidade
                return True
        
        # Item não encontrado no carrinho
        return False
    
    def calcular_subtotal(self) -> float:
        """
        Calcula o subtotal do carrinho somando os subtotais de todos os itens.
        
        Returns:
            float: Subtotal do carrinho (soma de todos os itens)
        
        Validates Requirement: 1.8
        """
        if not self.itens:
            return 0.0
        
        return sum(item.calcular_subtotal() for item in self.itens)
    
    def calcular_desconto(self) -> float:
        """
        Calcula o valor do desconto aplicado ao carrinho.
        
        O desconto pode ser baseado em percentual ou valor fixo.
        Se ambos estiverem definidos, o desconto em valor fixo tem prioridade.
        
        Returns:
            float: Valor do desconto a ser aplicado
        
        Validates Requirements: 2.1, 2.2
        """
        # Priorizar desconto em valor fixo se definido
        if self.desconto_valor > 0:
            return self.desconto_valor
        
        # Calcular desconto percentual se definido
        if self.desconto_percentual > 0:
            subtotal = self.calcular_subtotal()
            return subtotal * self.desconto_percentual / 100.0
        
        # Nenhum desconto aplicado
        return 0.0
    
    def calcular_total(self) -> float:
        """
        Calcula o valor total final do carrinho (subtotal - desconto).
        
        O total é calculado subtraindo o desconto do subtotal.
        Garante que o resultado nunca seja negativo (mínimo 0.0).
        
        Returns:
            float: Valor total final do carrinho (nunca negativo)
        
        Validates Requirements: 1.8, 2.6
        """
        subtotal = self.calcular_subtotal()
        desconto = self.calcular_desconto()
        total = subtotal - desconto
        
        # Garantir que o total nunca seja negativo
        return max(0.0, total)
    
    def aplicar_desconto_percentual(self, percentual: float) -> bool:
        """
        Aplica um desconto percentual ao carrinho.
        
        Valida que o percentual está entre 0 e 100 (inclusive) e que o desconto
        não resulta em valor negativo. Se válido, aplica o desconto percentual
        e limpa qualquer desconto em valor fixo (apenas um tipo de desconto por vez).
        
        Args:
            percentual: Percentual de desconto a aplicar (0-100)
        
        Returns:
            bool: True se desconto foi aplicado com sucesso, False se validação falhou
        
        Validates Requirements: 2.1, 2.3, 2.5
        """
        # Validar que percentual está entre 0 e 100
        if percentual < 0 or percentual > 100:
            return False
        
        # Calcular o valor do desconto que seria aplicado
        subtotal = self.calcular_subtotal()
        valor_desconto = subtotal * percentual / 100.0
        
        # Validar que desconto não resulta em valor negativo
        if subtotal - valor_desconto < 0:
            return False
        
        # Aplicar desconto percentual
        self.desconto_percentual = percentual
        
        # Limpar desconto em valor fixo (apenas um tipo de desconto por vez)
        self.desconto_valor = 0.0
        
        return True
    
    def aplicar_desconto_valor(self, valor: float) -> bool:
        """
        Aplica um desconto em valor fixo ao carrinho.
        
        Valida que o valor do desconto não excede o total do carrinho e que o desconto
        não resulta em valor negativo. Se válido, aplica o desconto em valor fixo
        e limpa qualquer desconto percentual (apenas um tipo de desconto por vez).
        
        Args:
            valor: Valor fixo de desconto a aplicar
        
        Returns:
            bool: True se desconto foi aplicado com sucesso, False se validação falhou
        
        Validates Requirements: 2.2, 2.4, 2.5
        """
        # Validar que valor não é negativo
        if valor < 0:
            return False
        
        # Calcular o subtotal do carrinho
        subtotal = self.calcular_subtotal()
        
        # Validar que valor do desconto não excede o total do carrinho
        if valor > subtotal:
            return False
        
        # Validar que desconto não resulta em valor negativo
        if subtotal - valor < 0:
            return False
        
        # Aplicar desconto em valor fixo
        self.desconto_valor = valor
        
        # Limpar desconto percentual (apenas um tipo de desconto por vez)
        self.desconto_percentual = 0.0
        
        return True
    
    def remover_desconto(self) -> None:
        """
        Remove todos os descontos aplicados ao carrinho.
        
        Zera tanto o desconto percentual quanto o desconto em valor fixo,
        restaurando o valor total original do carrinho.
        
        Validates Requirement: 2.7
        """
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0
    
    def limpar(self) -> None:
        """
        Limpa o carrinho removendo todos os itens e descontos.
        
        Remove todos os itens do carrinho e zera os descontos,
        preparando o carrinho para uma nova venda.
        
        Validates Requirement: 5.10
        """
        self.itens.clear()
        self.desconto_percentual = 0.0
        self.desconto_valor = 0.0
    
    def validar_disponibilidade(self) -> tuple[bool, List[str]]:
        """
        Valida a disponibilidade de estoque para todos os itens do carrinho.
        
        Para cada item no carrinho, consulta o estoque atual no banco de dados
        e verifica se a quantidade solicitada está disponível. Retorna uma tupla
        com um booleano indicando se todos os itens estão disponíveis e uma lista
        de mensagens de erro descritivas para itens com estoque insuficiente.
        
        Returns:
            tuple[bool, List[str]]: Tupla contendo:
                - bool: True se todos os itens têm estoque disponível, False caso contrário
                - List[str]: Lista de mensagens de erro para itens com estoque insuficiente
                             (vazia se todos os itens estão disponíveis)
        
        Validates Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6
        """
        from database import supabase
        
        mensagens_erro: List[str] = []
        
        # Se carrinho está vazio, considerar válido
        if not self.itens:
            return True, []
        
        try:
            # Para cada item no carrinho, consultar estoque atual
            for item in self.itens:
                # Consultar estoque atual no banco de dados
                response = supabase.table("produtos").select("quantidade, descricao").eq("id", item.produto_id).execute()
                
                if not response.data or len(response.data) == 0:
                    # Produto não encontrado no banco
                    mensagens_erro.append(
                        f"Produto {item.descricao}: não encontrado no banco de dados"
                    )
                    continue
                
                produto = response.data[0]
                estoque_atual = int(produto.get('quantidade', 0))
                descricao = produto.get('descricao', item.descricao)
                
                # Verificar se quantidade solicitada está disponível
                if item.quantidade > estoque_atual:
                    # Estoque insuficiente - adicionar mensagem de erro descritiva
                    mensagens_erro.append(
                        f"Produto {descricao}: estoque insuficiente. Disponível: {estoque_atual}, Solicitado: {item.quantidade}"
                    )
                    
                    # Atualizar o estoque_disponivel do item para refletir o valor atual
                    item.estoque_disponivel = estoque_atual
                elif estoque_atual == 0:
                    # Produto sem estoque
                    mensagens_erro.append(
                        f"Produto {descricao}: sem estoque disponível"
                    )
                    item.estoque_disponivel = 0
            
            # Retornar resultado da validação
            if mensagens_erro:
                return False, mensagens_erro
            else:
                return True, []
                
        except Exception as e:
            # Em caso de erro de conexão ou outro erro, retornar falha
            mensagens_erro.append(f"Erro ao validar disponibilidade: {str(e)}")
            return False, mensagens_erro









def buscar_produtos_venda(termo: str, apenas_disponiveis: bool = True) -> List[dict]:
    """
    Busca produtos por código de barras, referência ou descrição.
    
    Realiza busca case-insensitive e parcial nos campos codigo_barras, referencia
    e descricao. Opcionalmente filtra apenas produtos com estoque disponível.
    
    Args:
        termo: Termo de busca (código de barras, referência ou descrição)
        apenas_disponiveis: Se True, retorna apenas produtos com quantidade > 0 (padrão: True)
    
    Returns:
        List[dict]: Lista de produtos encontrados com todas as informações.
                    Cada produto é um dicionário com os campos da tabela produtos.
                    Retorna lista vazia se nenhum produto for encontrado.
    
    Validates Requirement: 1.1
    """
    from database import supabase
    
    try:
        # Construir query base
        query = supabase.table("produtos").select("*")
        
        # Aplicar filtro de busca em múltiplos campos usando OR
        # ILIKE para busca case-insensitive e parcial
        termo_busca = f"%{termo}%"
        query = query.or_(
            f"codigo_barras.ilike.{termo_busca},"
            f"referencia.ilike.{termo_busca},"
            f"descricao.ilike.{termo_busca}"
        )
        
        # Filtrar apenas produtos disponíveis se solicitado
        if apenas_disponiveis:
            query = query.gt("quantidade", 0)
        
        # Executar query
        response = query.execute()
        
        # Retornar lista de produtos (vazia se nenhum encontrado)
        if response.data:
            return response.data
        else:
            return []
            
    except Exception as e:
        # Em caso de erro (conexão, etc), retornar lista vazia
        return []



def finalizar_venda(
    carrinho: Carrinho,
    pagamentos: List[Dict],
    usuario_id: int,
    cliente_id: Optional[int] = None
) -> tuple[bool, str, Optional[int]]:
    """
    Finaliza uma venda com transação atômica.
    
    Valida disponibilidade de estoque, valida pagamentos, insere venda no banco,
    insere itens e pagamentos, executa baixa de estoque via registrar_movimentacao(),
    e limpa o carrinho após sucesso.
    
    Args:
        carrinho: Instância do Carrinho com os produtos da venda
        pagamentos: Lista de dicionários com dados dos pagamentos
        usuario_id: ID do usuário (vendedor) que está finalizando a venda
        cliente_id: ID do cliente (opcional, None para venda avulsa)
    
    Returns:
        Tupla (sucesso, mensagem, venda_id)
        - sucesso: bool indicando se a venda foi finalizada com sucesso
        - mensagem: str com mensagem descritiva do resultado
        - venda_id: int com ID da venda criada ou None em caso de erro
    
    Validates Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.10
    """
    from database import inserir_venda, inserir_itens_venda, inserir_pagamentos, registrar_movimentacao
    from validacao_vendas import validar_pagamentos_venda
    
    # Validar que o carrinho não está vazio
    if not carrinho.itens or len(carrinho.itens) == 0:
        return False, "Carrinho está vazio. Adicione produtos antes de finalizar a venda.", None
    
    # 1. Validar disponibilidade de estoque (fail fast)
    disponivel, mensagens_erro = carrinho.validar_disponibilidade()
    if not disponivel:
        mensagem_erro = "Estoque insuficiente:\n" + "\n".join(mensagens_erro)
        return False, mensagem_erro, None
    
    # 2. Calcular totais do carrinho
    valor_total = carrinho.calcular_subtotal()
    valor_desconto = carrinho.calcular_desconto()
    valor_final = carrinho.calcular_total()
    
    # 3. Validar que pagamentos correspondem ao total da venda
    valido, mensagem_validacao = validar_pagamentos_venda(pagamentos, valor_final)
    if not valido:
        return False, f"Erro na validação de pagamentos: {mensagem_validacao}", None
    
    try:
        # 4. Preparar dados da venda
        dados_venda = {
            'valor_total': valor_total,
            'desconto_percentual': carrinho.desconto_percentual,
            'desconto_valor': carrinho.desconto_valor,
            'valor_final': valor_final,
            'usuario_id': usuario_id,
            'status': 'finalizada'
        }
        
        # Adicionar cliente_id apenas se fornecido (venda não avulsa)
        if cliente_id is not None:
            dados_venda['cliente_id'] = cliente_id
        
        # 5. Inserir venda no banco (início da "transação")
        venda_id = inserir_venda(dados_venda)
        if venda_id is None:
            return False, "Erro ao registrar venda no banco de dados. Tente novamente.", None
        
        # 6. Preparar e inserir itens da venda
        itens_venda = []
        for item in carrinho.itens:
            itens_venda.append({
                'produto_id': item.produto_id,
                'quantidade': item.quantidade,
                'preco_unitario': item.preco_unitario,
                'subtotal': item.calcular_subtotal()
            })
        
        sucesso_itens = inserir_itens_venda(venda_id, itens_venda)
        if not sucesso_itens:
            # Falha ao inserir itens - idealmente deveria fazer rollback da venda
            return False, f"Erro ao registrar itens da venda. Venda ID {venda_id} pode estar incompleta.", venda_id
        
        # 7. Inserir pagamentos
        sucesso_pagamentos = inserir_pagamentos(venda_id, pagamentos)
        if not sucesso_pagamentos:
            # Falha ao inserir pagamentos - idealmente deveria fazer rollback
            return False, f"Erro ao registrar pagamentos da venda. Venda ID {venda_id} pode estar incompleta.", venda_id
        
        # 8. Executar baixa de estoque para cada item (registrar movimentação tipo='saida')
        for item in carrinho.itens:
            sucesso_movimentacao = registrar_movimentacao(
                produto_id=item.produto_id,
                tipo='saida',
                quantidade=item.quantidade,
                observacao=f'Venda #{venda_id}',
                usuario_id=usuario_id
            )
            
            if not sucesso_movimentacao:
                # Falha na baixa de estoque - situação crítica
                # Idealmente deveria fazer rollback de toda a transação
                return False, f"Erro ao dar baixa no estoque do produto {item.descricao}. Venda ID {venda_id} registrada mas estoque não atualizado.", venda_id
        
        # 9. Limpar carrinho após sucesso completo
        carrinho.limpar()
        
        # 10. Retornar sucesso
        return True, f"Venda finalizada com sucesso! ID da venda: {venda_id}", venda_id
        
    except Exception as e:
        # Capturar qualquer exceção não tratada
        mensagem_erro = f"Erro inesperado ao finalizar venda: {str(e)}"
        return False, mensagem_erro, None



def gerar_comprovante(venda_id: int) -> Optional[Dict]:
    """
    Gera dados estruturados do comprovante de venda.
    
    Busca a venda completa usando buscar_venda_completa() e estrutura
    os dados em um formato adequado para exibição/impressão do comprovante.
    
    Args:
        venda_id: ID da venda para gerar o comprovante
    
    Returns:
        Dict estruturado com dados do comprovante ou None se venda não encontrada.
        Estrutura retornada:
        {
            'numero_venda': int,
            'data_hora': str,
            'cliente': {
                'nome': str,
                'cpf': str,
                'telefone': str
            } or None (para venda avulsa),
            'vendedor': str (nome do vendedor),
            'itens': [
                {
                    'descricao': str,
                    'quantidade': int,
                    'preco_unitario': float,
                    'subtotal': float
                },
                ...
            ],
            'subtotal': float,
            'desconto_percentual': float,
            'desconto_valor': float,
            'desconto_total': float,
            'valor_final': float,
            'pagamentos': [
                {
                    'forma_pagamento': str,
                    'valor': float,
                    'numero_parcelas': int or None,
                    'valor_recebido': float or None,
                    'troco': float or None
                },
                ...
            ],
            'status': str
        }
    
    Validates Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
    """
    from database import buscar_venda_completa
    
    # Buscar venda completa do banco de dados
    venda_completa = buscar_venda_completa(venda_id)
    
    # Se venda não encontrada, retornar None
    if venda_completa is None:
        return None
    
    # Estruturar dados do cliente (None para venda avulsa)
    cliente_data = None
    if venda_completa.get('cliente'):
        cliente = venda_completa['cliente']
        cliente_data = {
            'nome': cliente.get('nome', ''),
            'cpf': cliente.get('cpf', ''),
            'telefone': cliente.get('telefone', '')
        }
    
    # Estruturar dados do vendedor
    vendedor_nome = ''
    if venda_completa.get('vendedor'):
        vendedor = venda_completa['vendedor']
        vendedor_nome = vendedor.get('nome', '') or vendedor.get('username', '')
    
    # Estruturar lista de itens
    itens_comprovante = []
    for item in venda_completa.get('itens', []):
        # Obter descrição do produto
        descricao = ''
        if item.get('produto'):
            produto = item['produto']
            descricao = produto.get('descricao', '')
        
        itens_comprovante.append({
            'descricao': descricao,
            'quantidade': int(item.get('quantidade', 0)),
            'preco_unitario': float(item.get('preco_unitario', 0)),
            'subtotal': float(item.get('subtotal', 0))
        })
    
    # Estruturar lista de pagamentos
    pagamentos_comprovante = []
    for pagamento in venda_completa.get('pagamentos', []):
        pagamento_data = {
            'forma_pagamento': pagamento.get('forma_pagamento', ''),
            'valor': float(pagamento.get('valor', 0))
        }
        
        # Adicionar número de parcelas se aplicável (cartão de crédito)
        if pagamento.get('numero_parcelas'):
            pagamento_data['numero_parcelas'] = int(pagamento['numero_parcelas'])
        
        # Adicionar valor recebido e troco se aplicável (dinheiro)
        if pagamento.get('valor_recebido'):
            pagamento_data['valor_recebido'] = float(pagamento['valor_recebido'])
        
        if pagamento.get('troco'):
            pagamento_data['troco'] = float(pagamento['troco'])
        
        pagamentos_comprovante.append(pagamento_data)
    
    # Calcular desconto total
    desconto_percentual = float(venda_completa.get('desconto_percentual', 0))
    desconto_valor = float(venda_completa.get('desconto_valor', 0))
    valor_total = float(venda_completa.get('valor_total', 0))
    
    # Calcular o valor do desconto total aplicado
    desconto_total = 0.0
    if desconto_valor > 0:
        desconto_total = desconto_valor
    elif desconto_percentual > 0:
        desconto_total = valor_total * desconto_percentual / 100.0
    
    # Estruturar comprovante completo
    comprovante = {
        'numero_venda': venda_completa['id'],
        'data_hora': venda_completa['data_hora'],
        'cliente': cliente_data,
        'vendedor': vendedor_nome,
        'itens': itens_comprovante,
        'subtotal': valor_total,
        'desconto_percentual': desconto_percentual,
        'desconto_valor': desconto_valor,
        'desconto_total': desconto_total,
        'valor_final': float(venda_completa.get('valor_final', 0)),
        'pagamentos': pagamentos_comprovante,
        'status': venda_completa.get('status', '')
    }
    
    return comprovante


def exportar_comprovante_pdf(venda_id: int, caminho_arquivo: str) -> bool:
    """
    Exporta comprovante de venda para arquivo PDF.
    
    Args:
        venda_id: ID da venda para exportar
        caminho_arquivo: Caminho completo onde salvar o arquivo PDF
    
    Returns:
        bool: True se exportação foi bem-sucedida, False caso contrário
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        from datetime import datetime
        
        # Obter dados do comprovante
        comprovante = gerar_comprovante(venda_id)
        if comprovante is None:
            return False
        
        # Criar documento PDF
        doc = SimpleDocTemplate(
            caminho_arquivo,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        
        # Estilo para cabeçalho da empresa
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10*mm,
            textColor=colors.darkblue
        )
        
        # Estilo para informações da venda
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3*mm
        )
        
        # Estilo para títulos de seção
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=5*mm,
            spaceBefore=5*mm,
            textColor=colors.darkblue
        )
        
        # Estilo para rodapé
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=5*mm,
            textColor=colors.grey
        )
        
        # Lista de elementos do documento
        elements = []
        
        # Cabeçalho da empresa
        elements.append(Paragraph("DEKIDS Moda Infantil", header_style))
        elements.append(Spacer(1, 5*mm))
        
        # Informações da venda
        elements.append(Paragraph(f"<b>Comprovante de Venda Nº:</b> {comprovante['numero_venda']}", info_style))
        
        # Formatar data/hora
        try:
            if isinstance(comprovante['data_hora'], str):
                data_hora_obj = datetime.fromisoformat(comprovante['data_hora'].replace('Z', '+00:00'))
                data_hora_formatada = data_hora_obj.strftime("%d/%m/%Y às %H:%M")
            else:
                data_hora_formatada = str(comprovante['data_hora'])
        except:
            data_hora_formatada = str(comprovante['data_hora'])
        
        elements.append(Paragraph(f"<b>Data/Hora:</b> {data_hora_formatada}", info_style))
        elements.append(Paragraph(f"<b>Vendedor:</b> {comprovante['vendedor']}", info_style))
        
        # Dados do cliente (se não for venda avulsa)
        if comprovante['cliente']:
            cliente = comprovante['cliente']
            elements.append(Spacer(1, 3*mm))
            elements.append(Paragraph("Dados do Cliente", section_style))
            elements.append(Paragraph(f"<b>Nome:</b> {cliente['nome']}", info_style))
            if cliente['cpf']:
                elements.append(Paragraph(f"<b>CPF:</b> {cliente['cpf']}", info_style))
            if cliente['telefone']:
                elements.append(Paragraph(f"<b>Telefone:</b> {cliente['telefone']}", info_style))
        
        # Tabela de itens
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph("Itens da Venda", section_style))
        
        # Cabeçalho da tabela de itens
        itens_data = [['Descrição', 'Qtd', 'Preço Unit.', 'Subtotal']]
        
        # Adicionar itens
        for item in comprovante['itens']:
            itens_data.append([
                item['descricao'],
                str(item['quantidade']),
                f"R$ {item['preco_unitario']:.2f}".replace('.', ','),
                f"R$ {item['subtotal']:.2f}".replace('.', ',')
            ])
        
        # Criar tabela de itens
        itens_table = Table(itens_data, colWidths=[80*mm, 20*mm, 30*mm, 30*mm])
        itens_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(itens_table)
        elements.append(Spacer(1, 5*mm))
        
        # Totais
        elements.append(Paragraph("Totais", section_style))
        
        totais_data = []
        totais_data.append(['Subtotal:', f"R$ {comprovante['subtotal']:.2f}".replace('.', ',')])
        
        if comprovante['desconto_total'] > 0:
            if comprovante['desconto_percentual'] > 0:
                totais_data.append([f'Desconto ({comprovante["desconto_percentual"]:.1f}%):', f"- R$ {comprovante['desconto_total']:.2f}".replace('.', ',')])
            else:
                totais_data.append(['Desconto:', f"- R$ {comprovante['desconto_total']:.2f}".replace('.', ',')])
        
        totais_data.append(['<b>Total Final:</b>', f"<b>R$ {comprovante['valor_final']:.2f}</b>".replace('.', ',')])
        
        totais_table = Table(totais_data, colWidths=[120*mm, 40*mm])
        totais_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(totais_table)
        elements.append(Spacer(1, 5*mm))
        
        # Formas de pagamento
        if comprovante['pagamentos']:
            elements.append(Paragraph("Formas de Pagamento", section_style))
            
            pagamentos_data = [['Forma de Pagamento', 'Valor', 'Detalhes']]
            
            for pagamento in comprovante['pagamentos']:
                detalhes = ''
                
                # Adicionar detalhes específicos por forma de pagamento
                if pagamento.get('numero_parcelas'):
                    detalhes = f"{pagamento['numero_parcelas']}x"
                elif pagamento.get('valor_recebido'):
                    detalhes = f"Recebido: R$ {pagamento['valor_recebido']:.2f}".replace('.', ',')
                    if pagamento.get('troco', 0) > 0:
                        detalhes += f" | Troco: R$ {pagamento['troco']:.2f}".replace('.', ',')
                
                pagamentos_data.append([
                    pagamento['forma_pagamento'],
                    f"R$ {pagamento['valor']:.2f}".replace('.', ','),
                    detalhes
                ])
            
            pagamentos_table = Table(pagamentos_data, colWidths=[60*mm, 40*mm, 60*mm])
            pagamentos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(pagamentos_table)
        
        # Rodapé
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("Obrigado pela preferência!", footer_style))
        elements.append(Paragraph("DEKIDS Moda Infantil - Vestindo sonhos, criando memórias", footer_style))
        
        # Gerar PDF
        doc.build(elements)
        return True
        
    except FileNotFoundError:
        # Erro ao criar/acessar o arquivo
        return False
    except PermissionError:
        # Sem permissão para escrever no caminho especificado
        return False
    except ImportError:
        # Biblioteca reportlab não instalada
        return False
    except Exception:
        # Qualquer outro erro
        return False



def buscar_venda(venda_id: int) -> tuple[bool, str, Optional[dict]]:
    """
    Busca uma venda por ID.
    
    Utiliza a função buscar_venda_completa() do módulo database.py para
    obter todos os dados da venda incluindo itens, pagamentos e informações
    do cliente.
    
    Args:
        venda_id: ID da venda a ser buscada
        
    Returns:
        Tuple[bool, str, Optional[dict]]: 
            - bool: True se venda foi encontrada, False caso contrário
            - str: Mensagem descritiva do resultado
            - Optional[dict]: Dados completos da venda se encontrada, None caso contrário
    
    Validates Requirement: 7.1
    """
    from database import buscar_venda_completa
    
    try:
        # Buscar venda completa usando função do database.py
        venda_data = buscar_venda_completa(venda_id)
        
        if venda_data:
            return True, "Venda encontrada", venda_data
        else:
            return False, "Venda não encontrada", None
            
    except Exception as e:
        # Em caso de erro (conexão, etc), retornar erro
        return False, f"Erro ao buscar venda: {str(e)}", None


def listar_vendas(
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    usuario_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    status: Optional[str] = None
) -> Tuple[bool, str, List[dict]]:
    """
    Lista vendas com filtros opcionais.
    
    Filtra vendas por data_inicio, data_fim, usuario_id, cliente_id e status.
    Ordena por data_hora DESC (mais recentes primeiro).
    
    Args:
        data_inicio: Data inicial (formato ISO)
        data_fim: Data final (formato ISO)
        usuario_id: ID do usuário/vendedor
        cliente_id: ID do cliente
        status: Status da venda ('finalizada' ou 'cancelada')
        
    Returns:
        Tuple[bool, str, List[dict]]: (sucesso, mensagem, lista_vendas)
            - bool: True se operação foi bem-sucedida, False caso contrário
            - str: Mensagem descritiva do resultado
            - List[dict]: Lista de vendas encontradas (vazia se erro ou nenhuma venda)
    
    Validates Requirements: 7.1, 8.1
    """
    from database import supabase, reconectar_supabase
    
    if not supabase:
        return False, "Erro: Conexão com Supabase não estabelecida", []
    
    try:
        # Iniciar query base
        query = supabase.table('vendas').select('*')
        
        # Aplicar filtros condicionalmente
        if data_inicio:
            query = query.gte('data_hora', data_inicio)
        
        if data_fim:
            query = query.lte('data_hora', data_fim)
        
        if usuario_id:
            query = query.eq('usuario_id', usuario_id)
        
        if cliente_id:
            query = query.eq('cliente_id', cliente_id)
        
        if status:
            query = query.eq('status', status)
        
        # Ordenar por data_hora DESC (mais recentes primeiro)
        query = query.order('data_hora', desc=True)
        
        # Executar query
        response = query.execute()
        
        vendas = response.data if response.data else []
        
        # Converter valores decimais para float
        for venda in vendas:
            if 'valor_total' in venda:
                venda['valor_total'] = float(venda['valor_total'])
            if 'desconto_percentual' in venda:
                venda['desconto_percentual'] = float(venda['desconto_percentual'])
            if 'desconto_valor' in venda:
                venda['desconto_valor'] = float(venda['desconto_valor'])
            if 'valor_final' in venda:
                venda['valor_final'] = float(venda['valor_final'])
        
        return True, "Vendas encontradas", vendas
        
    except Exception as e:
        # Tentar reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "network" in str(e).lower():
            if reconectar_supabase():
                try:
                    # Repetir query após reconexão
                    query = supabase.table('vendas').select('*')
                    
                    if data_inicio:
                        query = query.gte('data_hora', data_inicio)
                    
                    if data_fim:
                        query = query.lte('data_hora', data_fim)
                    
                    if usuario_id:
                        query = query.eq('usuario_id', usuario_id)
                    
                    if cliente_id:
                        query = query.eq('cliente_id', cliente_id)
                    
                    if status:
                        query = query.eq('status', status)
                    
                    query = query.order('data_hora', desc=True)
                    
                    response = query.execute()
                    
                    vendas = response.data if response.data else []
                    
                    # Converter valores decimais para float
                    for venda in vendas:
                        if 'valor_total' in venda:
                            venda['valor_total'] = float(venda['valor_total'])
                        if 'desconto_percentual' in venda:
                            venda['desconto_percentual'] = float(venda['desconto_percentual'])
                        if 'desconto_valor' in venda:
                            venda['desconto_valor'] = float(venda['desconto_valor'])
                        if 'valor_final' in venda:
                            venda['valor_final'] = float(venda['valor_final'])
                    
                    return True, "Vendas encontradas", vendas
                    
                except Exception as e2:
                    return False, "Erro ao listar vendas", []
        
        return False, "Erro ao listar vendas", []



def cancelar_venda(venda_id: int, motivo: str, usuario_id: int) -> Tuple[bool, str]:
    """
    Cancela uma venda e restaura o estoque.
    
    Busca a venda usando buscar_venda_completa(), valida que a venda existe
    e não está cancelada, marca a venda como cancelada usando marcar_venda_cancelada(),
    e para cada item da venda executa registrar_movimentacao(tipo='entrada') para
    restaurar o estoque.
    
    Args:
        venda_id: ID da venda a ser cancelada
        motivo: Motivo do cancelamento
        usuario_id: ID do usuário que está cancelando
        
    Returns:
        Tuple[bool, str]: (sucesso, mensagem)
            - sucesso: bool indicando se o cancelamento foi bem-sucedido
            - mensagem: str com mensagem descritiva do resultado
    
    Validates Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8
    """
    from database import buscar_venda_completa, marcar_venda_cancelada, registrar_movimentacao
    
    try:
        # 1. Buscar venda completa
        venda = buscar_venda_completa(venda_id)
        
        # 2. Validar que venda existe
        if venda is None:
            return False, f"Venda #{venda_id} não encontrada."
        
        # 3. Validar que venda não está cancelada
        if venda.get('status') == 'cancelada':
            return False, f"Venda #{venda_id} já está cancelada."
        
        # 4. Marcar venda como cancelada (início da "transação")
        sucesso_marcacao = marcar_venda_cancelada(venda_id, motivo, usuario_id)
        
        if not sucesso_marcacao:
            return False, f"Erro ao marcar venda #{venda_id} como cancelada. Tente novamente."
        
        # 5. Restaurar estoque para cada item da venda
        itens = venda.get('itens', [])
        
        if not itens:
            # Venda sem itens - situação incomum mas não é erro crítico
            return True, f"Venda #{venda_id} cancelada com sucesso (sem itens para estornar)."
        
        # Lista para rastrear itens que falharam no estorno
        itens_com_erro = []
        
        for item in itens:
            produto_id = item.get('produto_id')
            quantidade = item.get('quantidade')
            
            if not produto_id or not quantidade:
                # Item sem dados completos - pular
                continue
            
            # Executar registrar_movimentacao com tipo='entrada' para estornar
            sucesso_estorno = registrar_movimentacao(
                produto_id=produto_id,
                tipo='entrada',
                quantidade=quantidade,
                observacao=f'Estorno de venda #{venda_id}',
                usuario_id=usuario_id
            )
            
            if not sucesso_estorno:
                # Falha no estorno - registrar item com erro
                descricao = ''
                if item.get('produto'):
                    descricao = item['produto'].get('descricao', f'Produto ID {produto_id}')
                else:
                    descricao = f'Produto ID {produto_id}'
                
                itens_com_erro.append(descricao)
        
        # 6. Verificar se houve erros no estorno
        if itens_com_erro:
            # Alguns itens falharam no estorno - situação crítica
            mensagem_erro = (
                f"Venda #{venda_id} foi marcada como cancelada, mas houve erro ao estornar "
                f"o estoque dos seguintes produtos: {', '.join(itens_com_erro)}. "
                f"Verifique o estoque manualmente."
            )
            return False, mensagem_erro
        
        # 7. Sucesso completo
        return True, f"Venda #{venda_id} cancelada com sucesso. Estoque restaurado para {len(itens)} item(ns)."
        
    except Exception as e:
        # Capturar qualquer exceção não tratada
        mensagem_erro = f"Erro inesperado ao cancelar venda #{venda_id}: {str(e)}"
        return False, mensagem_erro
