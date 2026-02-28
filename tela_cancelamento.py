"""
Tela de Cancelamento de Vendas - Sistema de Vendas DEKIDS

Interface completa de cancelamento de vendas com:
- Busca de vendas por número ou data
- Listagem de vendas finalizadas
- Modal de confirmação de cancelamento
- Exibição de detalhes da venda
- Registro de motivo do cancelamento
"""

import flet as ft
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from vendas import buscar_venda, listar_vendas, cancelar_venda, gerar_comprovante


class TelaCancelamento:
    """
    Classe principal da tela de cancelamento de vendas.
    
    Gerencia toda a interface de cancelamento incluindo busca de vendas,
    listagem, confirmação e processamento do cancelamento.
    """
    
    def __init__(self, page: ft.Page, usuario_id: int, usuario_nome: str):
        """
        Inicializa a tela de cancelamento.
        
        Args:
            page: Instância da página Flet
            usuario_id: ID do usuário autenticado
            usuario_nome: Nome do usuário autenticado
        """
        self.page = page
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        
        # Venda selecionada para cancelamento
        self.venda_selecionada: Optional[Dict] = None
        
        # Criar componentes da interface
        self._criar_componentes()
    
    def _criar_componentes(self):
        """Cria todos os componentes da interface."""
        # ========== COMPONENTES DE BUSCA ==========
        self.txt_busca_numero = ft.TextField(
            label="Buscar por Número da Venda",
            hint_text="Digite o número da venda",
            prefix_icon=ft.icons.SEARCH,
            width=250,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=lambda e: self._buscar_por_numero()
        )
        
        self.btn_buscar_numero = ft.ElevatedButton(
            "Buscar",
            icon=ft.icons.SEARCH,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._buscar_por_numero()
        )
        
        # Filtros de data
        hoje = datetime.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        
        self.txt_data_inicio = ft.TextField(
            label="Data Início",
            hint_text="YYYY-MM-DD",
            value=str(primeiro_dia_mes),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.txt_data_fim = ft.TextField(
            label="Data Fim",
            hint_text="YYYY-MM-DD",
            value=str(hoje),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.btn_buscar_data = ft.ElevatedButton(
            "Buscar por Data",
            icon=ft.icons.DATE_RANGE,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._buscar_por_data()
        )
        
        self.btn_limpar_busca = ft.IconButton(
            icon=ft.icons.CLEAR,
            icon_color="orange",
            tooltip="Limpar busca",
            on_click=lambda e: self._limpar_busca()
        )
        
        # Tabela de vendas
        self.tabela_vendas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nº Venda", weight="bold")),
                ft.DataColumn(ft.Text("Data/Hora", weight="bold")),
                ft.DataColumn(ft.Text("Cliente", weight="bold")),
                ft.DataColumn(ft.Text("Vendedor", weight="bold")),
                ft.DataColumn(ft.Text("Valor", weight="bold")),
                ft.DataColumn(ft.Text("Status", weight="bold")),
                ft.DataColumn(ft.Text("Ação", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        # ========== MODAL DE CONFIRMAÇÃO ==========
        self._criar_modal_confirmacao()
    
    def _criar_modal_confirmacao(self):
        """Cria o modal de confirmação de cancelamento."""
        # Conteúdo dos detalhes da venda
        self.modal_numero_venda = ft.Text("", size=20, weight="bold", color="#0070C0")
        self.modal_data_hora = ft.Text("", size=14)
        self.modal_cliente = ft.Text("", size=14)
        self.modal_vendedor = ft.Text("", size=14)
        
        # Tabela de itens da venda
        self.modal_tabela_itens = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Produto", weight="bold")),
                ft.DataColumn(ft.Text("Qtd", weight="bold")),
                ft.DataColumn(ft.Text("Preço Unit.", weight="bold")),
                ft.DataColumn(ft.Text("Subtotal", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        # Informações de pagamento
        self.modal_pagamentos = ft.Column([], spacing=5)
        
        # Totais
        self.modal_valor_total = ft.Text("", size=16, weight="bold")
        self.modal_desconto = ft.Text("", size=14, color="green")
        self.modal_valor_final = ft.Text("", size=18, weight="bold", color="#0070C0")
        
        # Campo de motivo do cancelamento
        self.txt_motivo_cancelamento = ft.TextField(
            label="Motivo do Cancelamento *",
            hint_text="Descreva o motivo do cancelamento",
            multiline=True,
            min_lines=3,
            max_lines=5,
        )
        
        # Aviso sobre restauração de estoque
        self.aviso_estoque = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.WARNING, color="orange", size=30),
                ft.Column([
                    ft.Text("⚠️ ATENÇÃO", size=14, weight="bold", color="orange"),
                    ft.Text(
                        "O estoque dos produtos será restaurado automaticamente após o cancelamento.",
                        size=12,
                        color="gray"
                    ),
                ], spacing=2, expand=True),
            ], spacing=10),
            bgcolor="#FFF9C4",
            padding=10,
            border_radius=5,
            border=ft.border.all(1, "orange")
        )
        
        # Modal
        self.modal_confirmacao = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.icons.CANCEL, color="red", size=30),
                ft.Text("Confirmar Cancelamento de Venda", size=18, weight="bold"),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    # Informações da venda
                    self.modal_numero_venda,
                    self.modal_data_hora,
                    self.modal_cliente,
                    self.modal_vendedor,
                    ft.Divider(height=20),
                    # Itens da venda
                    ft.Text("📦 Itens da Venda", size=14, weight="bold", color="#0070C0"),
                    ft.Container(
                        content=ft.Column([self.modal_tabela_itens], scroll=ft.ScrollMode.AUTO),
                        height=150,
                        border=ft.border.all(1, "#EEEEEE"),
                        border_radius=5,
                        padding=10
                    ),
                    ft.Divider(height=20),
                    # Pagamentos
                    ft.Text("💳 Formas de Pagamento", size=14, weight="bold", color="#0070C0"),
                    self.modal_pagamentos,
                    ft.Divider(height=20),
                    # Totais
                    self.modal_valor_total,
                    self.modal_desconto,
                    self.modal_valor_final,
                    ft.Divider(height=20),
                    # Motivo do cancelamento
                    self.txt_motivo_cancelamento,
                    ft.Divider(height=10),
                    # Aviso
                    self.aviso_estoque,
                ], scroll=ft.ScrollMode.AUTO, spacing=10),
                width=700,
                height=700
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._fechar_modal_confirmacao()),
                ft.ElevatedButton(
                    "Confirmar Cancelamento",
                    icon=ft.icons.CHECK_CIRCLE,
                    bgcolor="red",
                    color="white",
                    on_click=lambda e: self._confirmar_cancelamento()
                ),
            ],
        )
        self.page.overlay.append(self.modal_confirmacao)
    
    def build(self) -> ft.Container:
        """
        Constrói e retorna o layout completo da tela de cancelamento.
        
        Returns:
            Container com o layout completo em 2 colunas
        """
        # Coluna 1: Busca
        coluna_busca = ft.Container(
            content=ft.Column([
                ft.Text("🔍 Buscar Venda", size=18, weight="bold", color="#0070C0"),
                ft.Divider(),
                # Busca por número
                ft.Text("Por Número da Venda", weight="bold", size=14),
                ft.Row([
                    self.txt_busca_numero,
                    self.btn_buscar_numero,
                ], spacing=10),
                ft.Divider(height=20),
                # Busca por data
                ft.Text("Por Período", weight="bold", size=14),
                ft.Row([
                    self.txt_data_inicio,
                    self.txt_data_fim,
                ], spacing=10),
                ft.Row([
                    self.btn_buscar_data,
                    self.btn_limpar_busca,
                ], spacing=10),
            ], spacing=10),
            padding=15,
            bgcolor="white",
            border_radius=10,
            expand=1
        )
        
        # Coluna 2: Lista de Vendas
        coluna_lista = ft.Container(
            content=ft.Column([
                ft.Text("📋 Vendas Encontradas", size=18, weight="bold", color="#0070C0"),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([self.tabela_vendas], scroll=ft.ScrollMode.ALWAYS),
                    height=600,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
            ], spacing=10),
            padding=15,
            bgcolor="white",
            border_radius=10,
            expand=2
        )
        
        # Layout principal com 2 colunas
        layout = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Container(
                    content=ft.Row([
                        ft.Text("🚫 Cancelamento de Vendas", size=24, weight="bold", color="white"),
                        ft.Text(f"Usuário: {self.usuario_nome}", size=14, color="white", italic=True),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#0070C0",
                    padding=15,
                    border_radius=10
                ),
                # Conteúdo em 2 colunas
                ft.Row([
                    coluna_busca,
                    coluna_lista,
                ], spacing=10, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            ], spacing=10, expand=True),
            padding=20,
            expand=True
        )
        
        return layout
    
    # ========== MÉTODOS DE BUSCA ==========
    
    def _buscar_por_numero(self):
        """Busca uma venda específica por número."""
        numero_venda = self.txt_busca_numero.value
        
        if not numero_venda or not numero_venda.strip():
            self._mostrar_snackbar("Digite o número da venda", "orange")
            return
        
        try:
            venda_id = int(numero_venda)
        except ValueError:
            self._mostrar_snackbar("Número de venda inválido", "red")
            return
        
        # Buscar venda
        sucesso, mensagem, venda = buscar_venda(venda_id)
        
        if not sucesso or not venda:
            self._mostrar_snackbar(f"❌ {mensagem}", "red")
            return
        
        # Limpar tabela e adicionar apenas esta venda
        self.tabela_vendas.rows.clear()
        
        # Verificar se venda está finalizada (apenas vendas finalizadas podem ser canceladas)
        if venda.get('status') != 'finalizada':
            self._mostrar_snackbar(f"⚠️ Venda #{venda_id} não pode ser cancelada (status: {venda.get('status')})", "orange")
            self._adicionar_venda_tabela(venda, pode_cancelar=False)
        else:
            self._adicionar_venda_tabela(venda, pode_cancelar=True)
            self._mostrar_snackbar(f"✅ Venda #{venda_id} encontrada", "green")
        
        self.page.update()
    
    def _buscar_por_data(self):
        """Busca vendas por período de datas."""
        data_inicio = self.txt_data_inicio.value
        data_fim = self.txt_data_fim.value
        
        if not data_inicio or not data_fim:
            self._mostrar_snackbar("Preencha as datas de início e fim", "orange")
            return
        
        # Buscar vendas finalizadas no período
        sucesso, mensagem, vendas = listar_vendas(
            data_inicio=data_inicio,
            data_fim=data_fim,
            status='finalizada'  # Apenas vendas finalizadas podem ser canceladas
        )
        
        if not sucesso:
            self._mostrar_snackbar(f"❌ {mensagem}", "red")
            return
        
        # Limpar tabela
        self.tabela_vendas.rows.clear()
        
        if not vendas:
            self._mostrar_snackbar("Nenhuma venda finalizada encontrada no período", "orange")
            self.page.update()
            return
        
        # Preencher tabela com vendas encontradas
        for venda in vendas:
            self._adicionar_venda_tabela(venda, pode_cancelar=True)
        
        self._mostrar_snackbar(f"✅ {len(vendas)} venda(s) encontrada(s)", "green")
        self.page.update()
    
    def _adicionar_venda_tabela(self, venda: Dict, pode_cancelar: bool = True):
        """Adiciona uma venda à tabela."""
        # Obter dados do cliente e vendedor (podem não estar presentes)
        cliente_texto = "Venda Avulsa"
        if venda.get('cliente'):
            cliente_texto = venda['cliente'].get('nome', 'Venda Avulsa')
        elif venda.get('cliente_id'):
            # Se tem cliente_id mas não tem dados do cliente, buscar
            from clientes import obter_cliente
            cliente_data = obter_cliente(venda['cliente_id'])
            if cliente_data:
                cliente_texto = cliente_data.get('nome', 'Venda Avulsa')
        
        vendedor_texto = "-"
        if venda.get('vendedor'):
            vendedor_texto = venda['vendedor'].get('nome', '-') or venda['vendedor'].get('username', '-')
        elif venda.get('usuario_id'):
            # Se tem usuario_id mas não tem dados do vendedor, mostrar ID
            vendedor_texto = f"ID: {venda['usuario_id']}"
        
        # Determinar cor do status
        status = venda.get('status', 'finalizada')
        status_cor = "green" if status == 'finalizada' else "red"
        status_texto = "Finalizada" if status == 'finalizada' else "Cancelada"
        
        # Criar célula de ação
        if pode_cancelar and status == 'finalizada':
            celula_acao = ft.DataCell(
                ft.ElevatedButton(
                    "Cancelar Venda",
                    icon=ft.icons.CANCEL,
                    bgcolor="red",
                    color="white",
                    on_click=lambda e, v=venda: self._abrir_modal_confirmacao(v)
                )
            )
        else:
            celula_acao = ft.DataCell(
                ft.Text("-", color="gray", italic=True)
            )
        
        self.tabela_vendas.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(f"#{venda['id']}", weight="bold")),
                    ft.DataCell(ft.Text(self._formatar_data(venda.get('data_hora', '')))),
                    ft.DataCell(ft.Text(cliente_texto[:25])),
                    ft.DataCell(ft.Text(vendedor_texto[:20])),
                    ft.DataCell(ft.Text(f"R$ {float(venda.get('valor_final', 0)):.2f}", weight="bold")),
                    ft.DataCell(ft.Text(status_texto, color=status_cor)),
                    celula_acao,
                ]
            )
        )
    
    def _limpar_busca(self):
        """Limpa a busca e a tabela."""
        self.txt_busca_numero.value = ""
        self.tabela_vendas.rows.clear()
        self.page.update()
    
    # ========== MÉTODOS DO MODAL ==========
    
    def _abrir_modal_confirmacao(self, venda: Dict):
        """Abre o modal de confirmação de cancelamento."""
        # Buscar dados completos da venda
        sucesso, mensagem, venda_completa = buscar_venda(venda['id'])
        
        if not sucesso or not venda_completa:
            self._mostrar_snackbar(f"❌ Erro ao carregar detalhes da venda: {mensagem}", "red")
            return
        
        # Armazenar venda selecionada
        self.venda_selecionada = venda_completa
        
        # Preencher informações da venda
        self.modal_numero_venda.value = f"Venda #{venda_completa['id']}"
        self.modal_data_hora.value = f"📅 Data/Hora: {self._formatar_data(venda_completa.get('data_hora', ''))}"
        
        # Cliente
        if venda_completa.get('cliente'):
            cliente = venda_completa['cliente']
            self.modal_cliente.value = f"👤 Cliente: {cliente.get('nome', 'N/A')} - CPF: {self._formatar_cpf(cliente.get('cpf', ''))}"
        else:
            self.modal_cliente.value = "👤 Cliente: Venda Avulsa"
        
        # Vendedor
        if venda_completa.get('vendedor'):
            vendedor = venda_completa['vendedor']
            vendedor_nome = vendedor.get('nome', '') or vendedor.get('username', 'N/A')
            self.modal_vendedor.value = f"👨‍💼 Vendedor: {vendedor_nome}"
        else:
            self.modal_vendedor.value = "👨‍💼 Vendedor: N/A"
        
        # Limpar e preencher tabela de itens
        self.modal_tabela_itens.rows.clear()
        
        for item in venda_completa.get('itens', []):
            descricao = "Produto desconhecido"
            if item.get('produto'):
                descricao = item['produto'].get('descricao', 'Produto desconhecido')
            
            self.modal_tabela_itens.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(descricao[:30])),
                        ft.DataCell(ft.Text(str(item.get('quantidade', 0)))),
                        ft.DataCell(ft.Text(f"R$ {float(item.get('preco_unitario', 0)):.2f}")),
                        ft.DataCell(ft.Text(f"R$ {float(item.get('subtotal', 0)):.2f}", weight="bold")),
                    ]
                )
            )
        
        # Limpar e preencher pagamentos
        self.modal_pagamentos.controls.clear()
        
        for pagamento in venda_completa.get('pagamentos', []):
            forma = pagamento.get('forma_pagamento', '')
            forma_texto = {
                'dinheiro': '💵 Dinheiro',
                'cartao_credito': '💳 Cartão de Crédito',
                'cartao_debito': '💳 Cartão de Débito',
                'pix': '📱 PIX'
            }.get(forma, forma)
            
            valor = float(pagamento.get('valor', 0))
            texto_pagamento = f"{forma_texto}: R$ {valor:.2f}"
            
            # Adicionar informações extras se houver
            if pagamento.get('numero_parcelas'):
                texto_pagamento += f" ({pagamento['numero_parcelas']}x)"
            
            if pagamento.get('valor_recebido'):
                valor_recebido = float(pagamento['valor_recebido'])
                troco = float(pagamento.get('troco', 0))
                texto_pagamento += f" | Recebido: R$ {valor_recebido:.2f} | Troco: R$ {troco:.2f}"
            
            self.modal_pagamentos.controls.append(
                ft.Text(texto_pagamento, size=14)
            )
        
        # Preencher totais
        valor_total = float(venda_completa.get('valor_total', 0))
        desconto_percentual = float(venda_completa.get('desconto_percentual', 0))
        desconto_valor = float(venda_completa.get('desconto_valor', 0))
        valor_final = float(venda_completa.get('valor_final', 0))
        
        self.modal_valor_total.value = f"Subtotal: R$ {valor_total:.2f}"
        
        # Calcular desconto total
        desconto_total = 0.0
        if desconto_valor > 0:
            desconto_total = desconto_valor
        elif desconto_percentual > 0:
            desconto_total = valor_total * desconto_percentual / 100.0
        
        if desconto_total > 0:
            self.modal_desconto.value = f"Desconto: R$ {desconto_total:.2f}"
        else:
            self.modal_desconto.value = "Desconto: R$ 0,00"
        
        self.modal_valor_final.value = f"TOTAL: R$ {valor_final:.2f}"
        
        # Limpar campo de motivo
        self.txt_motivo_cancelamento.value = ""
        
        # Abrir modal
        self.modal_confirmacao.open = True
        self.page.update()
    
    def _fechar_modal_confirmacao(self):
        """Fecha o modal de confirmação."""
        self.modal_confirmacao.open = False
        self.venda_selecionada = None
        self.page.update()
    
    def _confirmar_cancelamento(self):
        """Confirma e processa o cancelamento da venda."""
        # Validar motivo
        motivo = self.txt_motivo_cancelamento.value
        
        if not motivo or not motivo.strip():
            self._mostrar_snackbar("❌ O motivo do cancelamento é obrigatório", "red")
            return
        
        if not self.venda_selecionada:
            self._mostrar_snackbar("❌ Nenhuma venda selecionada", "red")
            return
        
        venda_id = self.venda_selecionada['id']
        
        # Processar cancelamento
        sucesso, mensagem = cancelar_venda(venda_id, motivo.strip(), self.usuario_id)
        
        if sucesso:
            self._mostrar_snackbar(f"✅ {mensagem}", "green")
            self._fechar_modal_confirmacao()
            
            # Atualizar a lista de vendas se houver busca ativa
            if self.txt_busca_numero.value:
                self._buscar_por_numero()
            elif self.txt_data_inicio.value and self.txt_data_fim.value:
                self._buscar_por_data()
        else:
            self._mostrar_snackbar(f"❌ {mensagem}", "red")
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _formatar_data(self, data_str: str) -> str:
        """Formata data para exibição (DD/MM/YYYY HH:MM)."""
        if not data_str:
            return "-"
        
        try:
            # Tentar parsear diferentes formatos de data
            if 'T' in data_str:
                # Formato ISO: 2025-01-23T10:30:00
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
            else:
                # Formato padrão
                data = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
            
            return data.strftime("%d/%m/%Y %H:%M")
        except:
            # Se falhar, retornar string original
            return data_str
    
    def _formatar_cpf(self, cpf: str) -> str:
        """Formata CPF para exibição (000.000.000-00)."""
        if not cpf:
            return ""
        
        # Remover formatação existente
        cpf_limpo = cpf.replace('.', '').replace('-', '').replace(' ', '')
        
        # Aplicar formatação
        if len(cpf_limpo) == 11:
            return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        else:
            return cpf_limpo
    
    def _mostrar_snackbar(self, mensagem: str, cor: str):
        """Exibe uma mensagem SnackBar."""
        snackbar = ft.SnackBar(
            content=ft.Text(mensagem),
            bgcolor=cor
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
