"""
Tela de Relatórios - Sistema de Vendas DEKIDS

Interface completa de relatórios gerenciais com:
- Relatório de vendas por período
- Relatório de produtos mais vendidos
- Relatório de vendas por vendedor
"""

import flet as ft
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from relatorios import (
    relatorio_vendas_periodo,
    relatorio_produtos_mais_vendidos,
    relatorio_vendas_por_vendedor,
    exportar_relatorio_csv
)


class TelaRelatorios:
    """
    Classe principal da tela de relatórios.
    
    Gerencia toda a interface de relatórios gerenciais com abas
    para cada tipo de relatório.
    """
    
    def __init__(self, page: ft.Page, usuario_id: int, usuario_nome: str):
        """
        Inicializa a tela de relatórios.
        
        Args:
            page: Instância da página Flet
            usuario_id: ID do usuário autenticado
            usuario_nome: Nome do usuário autenticado
        """
        self.page = page
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        
        # Dados dos relatórios
        self.dados_relatorio_vendas: Optional[Dict] = None
        self.dados_relatorio_produtos: Optional[List[Dict]] = None
        self.dados_relatorio_vendedores: Optional[List[Dict]] = None
        
        # Criar componentes da interface
        self._criar_componentes()
    
    def _criar_componentes(self):
        """Cria todos os componentes da interface."""
        # Criar abas para cada tipo de relatório
        self._criar_aba_vendas_periodo()
        self._criar_aba_produtos_mais_vendidos()
        self._criar_aba_vendas_por_vendedor()
        
        # Criar tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Vendas por Período",
                    icon=ft.icons.CALENDAR_MONTH,
                    content=self.aba_vendas_periodo
                ),
                ft.Tab(
                    text="Produtos Mais Vendidos",
                    icon=ft.icons.SHOPPING_BAG,
                    content=self.aba_produtos_mais_vendidos
                ),
                ft.Tab(
                    text="Vendas por Vendedor",
                    icon=ft.icons.PEOPLE,
                    content=self.aba_vendas_por_vendedor
                ),
            ],
            expand=1,
        )
    
    def _criar_aba_vendas_periodo(self):
        """Cria a aba de relatório de vendas por período."""
        # Filtros
        hoje = datetime.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        
        self.vendas_data_inicio = ft.TextField(
            label="Data Início",
            hint_text="YYYY-MM-DD",
            value=str(primeiro_dia_mes),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.vendas_data_fim = ft.TextField(
            label="Data Fim",
            hint_text="YYYY-MM-DD",
            value=str(hoje),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.vendas_filtro_vendedor = ft.Dropdown(
            label="Vendedor (opcional)",
            hint_text="Todos os vendedores",
            options=[],
            width=200
        )
        
        self.vendas_filtro_pagamento = ft.Dropdown(
            label="Forma de Pagamento (opcional)",
            hint_text="Todas as formas",
            options=[
                ft.dropdown.Option("", "Todas"),
                ft.dropdown.Option("dinheiro", "Dinheiro"),
                ft.dropdown.Option("cartao_credito", "Cartão de Crédito"),
                ft.dropdown.Option("cartao_debito", "Cartão de Débito"),
                ft.dropdown.Option("pix", "PIX"),
            ],
            width=200
        )
        
        self.btn_gerar_vendas = ft.ElevatedButton(
            "Gerar Relatório",
            icon=ft.icons.ANALYTICS,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._gerar_relatorio_vendas()
        )
        
        self.btn_exportar_vendas = ft.ElevatedButton(
            "Exportar CSV",
            icon=ft.icons.DOWNLOAD,
            bgcolor="green",
            color="white",
            disabled=True,
            on_click=lambda e: self._exportar_vendas_csv()
        )
        
        # Métricas
        self.vendas_faturamento = ft.Text("R$ 0,00", size=24, weight="bold", color="green")
        self.vendas_num_vendas = ft.Text("0", size=24, weight="bold", color="#0070C0")
        self.vendas_ticket_medio = ft.Text("R$ 0,00", size=24, weight="bold", color="purple")
        
        # Tabela de vendas
        self.tabela_vendas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nº", weight="bold")),
                ft.DataColumn(ft.Text("Data/Hora", weight="bold")),
                ft.DataColumn(ft.Text("Cliente", weight="bold")),
                ft.DataColumn(ft.Text("Vendedor", weight="bold")),
                ft.DataColumn(ft.Text("Valor", weight="bold")),
                ft.DataColumn(ft.Text("Status", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        # Container de distribuição por forma de pagamento
        self.vendas_distribuicao_pagamento = ft.Column([], spacing=5)
        
        # Layout da aba
        self.aba_vendas_periodo = ft.Container(
            content=ft.Column([
                # Filtros
                ft.Container(
                    content=ft.Column([
                        ft.Text("📊 Filtros", size=16, weight="bold", color="#0070C0"),
                        ft.Row([
                            self.vendas_data_inicio,
                            self.vendas_data_fim,
                            self.vendas_filtro_vendedor,
                            self.vendas_filtro_pagamento,
                        ], spacing=10),
                        ft.Row([
                            self.btn_gerar_vendas,
                            self.btn_exportar_vendas,
                        ], spacing=10),
                    ], spacing=10),
                    bgcolor="#F0F8FF",
                    padding=15,
                    border_radius=5,
                    border=ft.border.all(1, "#0070C0")
                ),
                ft.Divider(height=20),
                # Métricas
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("💰 Faturamento Total", size=14, weight="bold"),
                            self.vendas_faturamento,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#E8F5E9",
                        padding=15,
                        border_radius=5,
                        expand=1
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("🛍️ Número de Vendas", size=14, weight="bold"),
                            self.vendas_num_vendas,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#E3F2FD",
                        padding=15,
                        border_radius=5,
                        expand=1
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📈 Ticket Médio", size=14, weight="bold"),
                            self.vendas_ticket_medio,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#F3E5F5",
                        padding=15,
                        border_radius=5,
                        expand=1
                    ),
                ], spacing=10),
                ft.Divider(height=20),
                # Distribuição por forma de pagamento
                ft.Container(
                    content=ft.Column([
                        ft.Text("💳 Distribuição por Forma de Pagamento", size=14, weight="bold", color="#0070C0"),
                        self.vendas_distribuicao_pagamento,
                    ], spacing=10),
                    bgcolor="#FFF9C4",
                    padding=15,
                    border_radius=5,
                    height=150
                ),
                ft.Divider(height=20),
                # Tabela de vendas
                ft.Text("📋 Lista de Vendas", size=14, weight="bold", color="#0070C0"),
                ft.Container(
                    content=ft.Column([self.tabela_vendas], scroll=ft.ScrollMode.ALWAYS),
                    height=300,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=15,
            expand=True
        )
    
    def _criar_aba_produtos_mais_vendidos(self):
        """Cria a aba de relatório de produtos mais vendidos."""
        # Filtros
        hoje = datetime.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        
        self.produtos_data_inicio = ft.TextField(
            label="Data Início",
            hint_text="YYYY-MM-DD",
            value=str(primeiro_dia_mes),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.produtos_data_fim = ft.TextField(
            label="Data Fim",
            hint_text="YYYY-MM-DD",
            value=str(hoje),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.produtos_filtro_genero = ft.Dropdown(
            label="Gênero (opcional)",
            hint_text="Todos",
            options=[
                ft.dropdown.Option("", "Todos"),
                ft.dropdown.Option("masculino", "Masculino"),
                ft.dropdown.Option("feminino", "Feminino"),
                ft.dropdown.Option("unissex", "Unissex"),
            ],
            width=150
        )
        
        self.produtos_filtro_marca = ft.TextField(
            label="Marca (opcional)",
            hint_text="Todas",
            width=150
        )
        
        self.produtos_top_n = ft.TextField(
            label="Top N Produtos",
            hint_text="Ex: 10",
            value="10",
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.btn_gerar_produtos = ft.ElevatedButton(
            "Gerar Relatório",
            icon=ft.icons.ANALYTICS,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._gerar_relatorio_produtos()
        )
        
        self.btn_exportar_produtos = ft.ElevatedButton(
            "Exportar CSV",
            icon=ft.icons.DOWNLOAD,
            bgcolor="green",
            color="white",
            disabled=True,
            on_click=lambda e: self._exportar_produtos_csv()
        )
        
        # Tabela de produtos
        self.tabela_produtos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Pos", weight="bold")),
                ft.DataColumn(ft.Text("Descrição", weight="bold")),
                ft.DataColumn(ft.Text("Marca", weight="bold")),
                ft.DataColumn(ft.Text("Ref", weight="bold")),
                ft.DataColumn(ft.Text("Qtd Vendida", weight="bold")),
                ft.DataColumn(ft.Text("Faturamento", weight="bold")),
                ft.DataColumn(ft.Text("% Part.", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        # Gráfico de barras (visual simples com containers)
        self.produtos_grafico = ft.Column([], spacing=5)
        
        # Layout da aba
        self.aba_produtos_mais_vendidos = ft.Container(
            content=ft.Column([
                # Filtros
                ft.Container(
                    content=ft.Column([
                        ft.Text("📊 Filtros", size=16, weight="bold", color="#0070C0"),
                        ft.Row([
                            self.produtos_data_inicio,
                            self.produtos_data_fim,
                            self.produtos_filtro_genero,
                            self.produtos_filtro_marca,
                            self.produtos_top_n,
                        ], spacing=10),
                        ft.Row([
                            self.btn_gerar_produtos,
                            self.btn_exportar_produtos,
                        ], spacing=10),
                    ], spacing=10),
                    bgcolor="#F0F8FF",
                    padding=15,
                    border_radius=5,
                    border=ft.border.all(1, "#0070C0")
                ),
                ft.Divider(height=20),
                # Tabela de produtos
                ft.Text("📋 Produtos Mais Vendidos", size=14, weight="bold", color="#0070C0"),
                ft.Container(
                    content=ft.Column([self.tabela_produtos], scroll=ft.ScrollMode.ALWAYS),
                    height=350,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
                ft.Divider(height=20),
                # Gráfico
                ft.Text("📊 Top 5 Produtos", size=14, weight="bold", color="#0070C0"),
                ft.Container(
                    content=ft.Column([self.produtos_grafico], scroll=ft.ScrollMode.AUTO),
                    height=200,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=15,
            expand=True
        )
    
    def _criar_aba_vendas_por_vendedor(self):
        """Cria a aba de relatório de vendas por vendedor."""
        # Filtros
        hoje = datetime.now().date()
        primeiro_dia_mes = hoje.replace(day=1)
        
        self.vendedores_data_inicio = ft.TextField(
            label="Data Início",
            hint_text="YYYY-MM-DD",
            value=str(primeiro_dia_mes),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.vendedores_data_fim = ft.TextField(
            label="Data Fim",
            hint_text="YYYY-MM-DD",
            value=str(hoje),
            width=150,
            prefix_icon=ft.icons.CALENDAR_TODAY
        )
        
        self.btn_gerar_vendedores = ft.ElevatedButton(
            "Gerar Relatório",
            icon=ft.icons.ANALYTICS,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._gerar_relatorio_vendedores()
        )
        
        self.btn_exportar_vendedores = ft.ElevatedButton(
            "Exportar CSV",
            icon=ft.icons.DOWNLOAD,
            bgcolor="green",
            color="white",
            disabled=True,
            on_click=lambda e: self._exportar_vendedores_csv()
        )
        
        # Tabela de vendedores
        self.tabela_vendedores = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Pos", weight="bold")),
                ft.DataColumn(ft.Text("Vendedor", weight="bold")),
                ft.DataColumn(ft.Text("Nº Vendas", weight="bold")),
                ft.DataColumn(ft.Text("Faturamento", weight="bold")),
                ft.DataColumn(ft.Text("Ticket Médio", weight="bold")),
                ft.DataColumn(ft.Text("% Part.", weight="bold")),
                ft.DataColumn(ft.Text("Ação", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        # Gráfico comparativo (visual simples com containers)
        self.vendedores_grafico = ft.Column([], spacing=5)
        
        # Layout da aba
        self.aba_vendas_por_vendedor = ft.Container(
            content=ft.Column([
                # Filtros
                ft.Container(
                    content=ft.Column([
                        ft.Text("📊 Filtros", size=16, weight="bold", color="#0070C0"),
                        ft.Row([
                            self.vendedores_data_inicio,
                            self.vendedores_data_fim,
                        ], spacing=10),
                        ft.Row([
                            self.btn_gerar_vendedores,
                            self.btn_exportar_vendedores,
                        ], spacing=10),
                    ], spacing=10),
                    bgcolor="#F0F8FF",
                    padding=15,
                    border_radius=5,
                    border=ft.border.all(1, "#0070C0")
                ),
                ft.Divider(height=20),
                # Tabela de vendedores
                ft.Text("📋 Desempenho por Vendedor", size=14, weight="bold", color="#0070C0"),
                ft.Container(
                    content=ft.Column([self.tabela_vendedores], scroll=ft.ScrollMode.ALWAYS),
                    height=350,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
                ft.Divider(height=20),
                # Gráfico
                ft.Text("📊 Comparativo de Faturamento", size=14, weight="bold", color="#0070C0"),
                ft.Container(
                    content=ft.Column([self.vendedores_grafico], scroll=ft.ScrollMode.AUTO),
                    height=200,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=15,
            expand=True
        )
    
    def build(self) -> ft.Container:
        """
        Constrói e retorna o layout completo da tela de relatórios.
        
        Returns:
            Container com o layout completo com abas
        """
        layout = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Container(
                    content=ft.Row([
                        ft.Text("📊 Relatórios Gerenciais", size=24, weight="bold", color="white"),
                        ft.Text(f"Usuário: {self.usuario_nome}", size=14, color="white", italic=True),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#0070C0",
                    padding=15,
                    border_radius=10
                ),
                # Abas
                self.tabs,
            ], spacing=10, expand=True),
            padding=20,
            expand=True
        )
        
        return layout
    
    # ========== MÉTODOS DE RELATÓRIO DE VENDAS ==========
    
    def _gerar_relatorio_vendas(self):
        """Gera o relatório de vendas por período."""
        # Validar datas
        data_inicio = self.vendas_data_inicio.value
        data_fim = self.vendas_data_fim.value
        
        if not data_inicio or not data_fim:
            self._mostrar_snackbar("❌ Preencha as datas de início e fim", "red")
            return
        
        try:
            # Preparar filtros opcionais
            usuario_id = None
            if self.vendas_filtro_vendedor.value:
                usuario_id = int(self.vendas_filtro_vendedor.value)
            
            forma_pagamento = None
            if self.vendas_filtro_pagamento.value:
                forma_pagamento = self.vendas_filtro_pagamento.value
            
            # Gerar relatório
            self.dados_relatorio_vendas = relatorio_vendas_periodo(
                data_inicio=data_inicio,
                data_fim=data_fim,
                usuario_id=usuario_id,
                forma_pagamento=forma_pagamento
            )
            
            # Atualizar métricas
            self.vendas_faturamento.value = f"R$ {self.dados_relatorio_vendas['faturamento_total']:.2f}"
            self.vendas_num_vendas.value = str(self.dados_relatorio_vendas['numero_vendas'])
            self.vendas_ticket_medio.value = f"R$ {self.dados_relatorio_vendas['ticket_medio']:.2f}"
            
            # Atualizar distribuição por forma de pagamento
            self.vendas_distribuicao_pagamento.controls.clear()
            
            if self.dados_relatorio_vendas['distribuicao_pagamento']:
                for dist in self.dados_relatorio_vendas['distribuicao_pagamento']:
                    forma_texto = {
                        'dinheiro': '💵 Dinheiro',
                        'cartao_credito': '💳 Cartão Crédito',
                        'cartao_debito': '💳 Cartão Débito',
                        'pix': '📱 PIX'
                    }.get(dist['forma_pagamento'], dist['forma_pagamento'])
                    
                    # Criar barra visual proporcional ao percentual
                    largura_barra = int(dist['percentual'] * 3)  # Escala para visualização
                    
                    self.vendas_distribuicao_pagamento.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(forma_texto, size=12, width=120),
                                ft.Container(
                                    content=ft.Text(
                                        f"R$ {dist['valor']:.2f} ({dist['percentual']:.1f}%)",
                                        size=12,
                                        color="white",
                                        weight="bold"
                                    ),
                                    bgcolor="#0070C0",
                                    padding=5,
                                    border_radius=3,
                                    width=largura_barra if largura_barra > 80 else 80
                                ),
                            ], spacing=10),
                            padding=5
                        )
                    )
            else:
                self.vendas_distribuicao_pagamento.controls.append(
                    ft.Text("Nenhuma venda no período", italic=True, color="gray")
                )
            
            # Atualizar tabela de vendas
            self.tabela_vendas.rows.clear()
            
            for venda in self.dados_relatorio_vendas['vendas']:
                status_cor = "green" if venda['status'] == 'finalizada' else "red"
                status_texto = "Finalizada" if venda['status'] == 'finalizada' else "Cancelada"
                
                cliente_texto = venda.get('cliente_nome', 'Venda Avulsa') or 'Venda Avulsa'
                vendedor_texto = venda.get('vendedor_nome', '-') or '-'
                
                self.tabela_vendas.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"#{venda['id']}")),
                            ft.DataCell(ft.Text(self._formatar_data(venda['data_hora']))),
                            ft.DataCell(ft.Text(cliente_texto[:20])),
                            ft.DataCell(ft.Text(vendedor_texto[:15])),
                            ft.DataCell(ft.Text(f"R$ {venda['valor_final']:.2f}", weight="bold")),
                            ft.DataCell(ft.Text(status_texto, color=status_cor)),
                        ]
                    )
                )
            
            # Habilitar botão de exportação
            self.btn_exportar_vendas.disabled = False
            
            self._mostrar_snackbar(f"✅ Relatório gerado: {self.dados_relatorio_vendas['numero_vendas']} vendas", "green")
            self.page.update()
            
        except Exception as e:
            self._mostrar_snackbar(f"❌ Erro ao gerar relatório: {str(e)}", "red")
    
    def _exportar_vendas_csv(self):
        """Exporta o relatório de vendas para CSV."""
        if not self.dados_relatorio_vendas:
            self._mostrar_snackbar("❌ Gere o relatório antes de exportar", "orange")
            return
        
        try:
            import os
            from datetime import datetime
            
            # Criar diretório de relatórios se não existir
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = f"relatorios/vendas_periodo_{timestamp}.csv"
            
            # Preparar dados para exportação
            dados_exportacao = []
            for venda in self.dados_relatorio_vendas['vendas']:
                dados_exportacao.append({
                    'Numero_Venda': venda['id'],
                    'Data_Hora': venda['data_hora'],
                    'Cliente': venda.get('cliente_nome', 'Venda Avulsa') or 'Venda Avulsa',
                    'Vendedor': venda.get('vendedor_nome', '-') or '-',
                    'Valor_Total': venda['valor_total'],
                    'Desconto': venda['desconto_valor'],
                    'Valor_Final': venda['valor_final'],
                    'Status': venda['status']
                })
            
            # Exportar CSV
            sucesso = exportar_relatorio_csv(dados_exportacao, caminho)
            
            if sucesso:
                self._mostrar_snackbar(f"✅ CSV exportado: {caminho}", "green")
            else:
                self._mostrar_snackbar("❌ Erro ao exportar CSV", "red")
                
        except Exception as e:
            self._mostrar_snackbar(f"❌ Erro ao exportar: {str(e)}", "red")
    
    # ========== MÉTODOS DE RELATÓRIO DE PRODUTOS ==========
    
    def _gerar_relatorio_produtos(self):
        """Gera o relatório de produtos mais vendidos."""
        # Validar datas
        data_inicio = self.produtos_data_inicio.value
        data_fim = self.produtos_data_fim.value
        
        if not data_inicio or not data_fim:
            self._mostrar_snackbar("❌ Preencha as datas de início e fim", "red")
            return
        
        try:
            # Preparar filtros opcionais
            filtros = {}
            
            if self.produtos_filtro_genero.value:
                filtros['genero'] = self.produtos_filtro_genero.value
            
            if self.produtos_filtro_marca.value and self.produtos_filtro_marca.value.strip():
                filtros['marca'] = self.produtos_filtro_marca.value.strip()
            
            # Obter limite de produtos
            limit = None
            if self.produtos_top_n.value:
                try:
                    limit = int(self.produtos_top_n.value)
                except ValueError:
                    limit = 10
            
            # Gerar relatório
            self.dados_relatorio_produtos = relatorio_produtos_mais_vendidos(
                data_inicio=data_inicio,
                data_fim=data_fim,
                filtros=filtros if filtros else None,
                limit=limit
            )
            
            # Atualizar tabela de produtos
            self.tabela_produtos.rows.clear()
            
            for i, produto in enumerate(self.dados_relatorio_produtos, 1):
                self.tabela_produtos.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{i}º", weight="bold")),
                            ft.DataCell(ft.Text(produto['descricao'][:25])),
                            ft.DataCell(ft.Text(produto.get('marca', '-')[:15])),
                            ft.DataCell(ft.Text(produto.get('referencia', '-')[:10])),
                            ft.DataCell(ft.Text(str(produto['quantidade_vendida']), weight="bold", color="#0070C0")),
                            ft.DataCell(ft.Text(f"R$ {produto['faturamento_gerado']:.2f}", weight="bold", color="green")),
                            ft.DataCell(ft.Text(f"{produto['percentual_participacao']:.1f}%", color="purple")),
                        ]
                    )
                )
            
            # Atualizar gráfico (top 5)
            self.produtos_grafico.controls.clear()
            
            if self.dados_relatorio_produtos:
                # Pegar top 5 para o gráfico
                top_5 = self.dados_relatorio_produtos[:5]
                
                # Encontrar o maior valor para escala
                max_qtd = max(p['quantidade_vendida'] for p in top_5) if top_5 else 1
                
                for i, produto in enumerate(top_5, 1):
                    # Calcular largura da barra proporcional
                    largura_barra = int((produto['quantidade_vendida'] / max_qtd) * 400)
                    
                    self.produtos_grafico.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"{i}º - {produto['descricao'][:30]}", size=12, weight="bold"),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text(
                                            f"{produto['quantidade_vendida']} un. | R$ {produto['faturamento_gerado']:.2f}",
                                            size=11,
                                            color="white",
                                            weight="bold"
                                        ),
                                        bgcolor="#0070C0",
                                        padding=8,
                                        border_radius=3,
                                        width=largura_barra if largura_barra > 100 else 100
                                    ),
                                ], spacing=5),
                            ], spacing=5),
                            padding=5
                        )
                    )
            else:
                self.produtos_grafico.controls.append(
                    ft.Text("Nenhum produto vendido no período", italic=True, color="gray")
                )
            
            # Habilitar botão de exportação
            self.btn_exportar_produtos.disabled = False
            
            self._mostrar_snackbar(f"✅ Relatório gerado: {len(self.dados_relatorio_produtos)} produtos", "green")
            self.page.update()
            
        except Exception as e:
            self._mostrar_snackbar(f"❌ Erro ao gerar relatório: {str(e)}", "red")
    
    def _exportar_produtos_csv(self):
        """Exporta o relatório de produtos para CSV."""
        if not self.dados_relatorio_produtos:
            self._mostrar_snackbar("❌ Gere o relatório antes de exportar", "orange")
            return
        
        try:
            import os
            from datetime import datetime
            
            # Criar diretório de relatórios se não existir
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = f"relatorios/produtos_mais_vendidos_{timestamp}.csv"
            
            # Preparar dados para exportação
            dados_exportacao = []
            for i, produto in enumerate(self.dados_relatorio_produtos, 1):
                dados_exportacao.append({
                    'Posicao': i,
                    'Descricao': produto['descricao'],
                    'Marca': produto.get('marca', '-'),
                    'Referencia': produto.get('referencia', '-'),
                    'Tamanho': produto.get('tamanho', '-'),
                    'Quantidade_Vendida': produto['quantidade_vendida'],
                    'Faturamento_Gerado': produto['faturamento_gerado'],
                    'Percentual_Participacao': produto['percentual_participacao']
                })
            
            # Exportar CSV
            sucesso = exportar_relatorio_csv(dados_exportacao, caminho)
            
            if sucesso:
                self._mostrar_snackbar(f"✅ CSV exportado: {caminho}", "green")
            else:
                self._mostrar_snackbar("❌ Erro ao exportar CSV", "red")
                
        except Exception as e:
            self._mostrar_snackbar(f"❌ Erro ao exportar: {str(e)}", "red")
    
    # ========== MÉTODOS DE RELATÓRIO DE VENDEDORES ==========
    
    def _gerar_relatorio_vendedores(self):
        """Gera o relatório de vendas por vendedor."""
        # Validar datas
        data_inicio = self.vendedores_data_inicio.value
        data_fim = self.vendedores_data_fim.value
        
        if not data_inicio or not data_fim:
            self._mostrar_snackbar("❌ Preencha as datas de início e fim", "red")
            return
        
        try:
            # Gerar relatório
            self.dados_relatorio_vendedores = relatorio_vendas_por_vendedor(
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            # Atualizar tabela de vendedores
            self.tabela_vendedores.rows.clear()
            
            for i, vendedor in enumerate(self.dados_relatorio_vendedores, 1):
                self.tabela_vendedores.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{i}º", weight="bold")),
                            ft.DataCell(ft.Text(vendedor['nome_vendedor'][:20])),
                            ft.DataCell(ft.Text(str(vendedor['numero_vendas']), weight="bold", color="#0070C0")),
                            ft.DataCell(ft.Text(f"R$ {vendedor['faturamento_total']:.2f}", weight="bold", color="green")),
                            ft.DataCell(ft.Text(f"R$ {vendedor['ticket_medio']:.2f}", color="purple")),
                            ft.DataCell(ft.Text(f"{vendedor['percentual_participacao']:.1f}%", color="orange")),
                            ft.DataCell(
                                ft.IconButton(
                                    icon=ft.icons.VISIBILITY,
                                    icon_color="#0070C0",
                                    tooltip="Ver detalhes das vendas",
                                    on_click=lambda e, v=vendedor: self._ver_detalhes_vendedor(v)
                                )
                            ),
                        ]
                    )
                )
            
            # Atualizar gráfico comparativo
            self.vendedores_grafico.controls.clear()
            
            if self.dados_relatorio_vendedores:
                # Encontrar o maior faturamento para escala
                max_faturamento = max(v['faturamento_total'] for v in self.dados_relatorio_vendedores) if self.dados_relatorio_vendedores else 1
                
                for i, vendedor in enumerate(self.dados_relatorio_vendedores, 1):
                    # Calcular largura da barra proporcional
                    largura_barra = int((vendedor['faturamento_total'] / max_faturamento) * 400)
                    
                    # Escolher cor baseada na posição
                    cor_barra = "#FFD700" if i == 1 else "#C0C0C0" if i == 2 else "#CD7F32" if i == 3 else "#0070C0"
                    
                    self.vendedores_grafico.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"{i}º - {vendedor['nome_vendedor'][:25]}", size=12, weight="bold"),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text(
                                            f"R$ {vendedor['faturamento_total']:.2f} | {vendedor['numero_vendas']} vendas",
                                            size=11,
                                            color="white",
                                            weight="bold"
                                        ),
                                        bgcolor=cor_barra,
                                        padding=8,
                                        border_radius=3,
                                        width=largura_barra if largura_barra > 100 else 100
                                    ),
                                ], spacing=5),
                            ], spacing=5),
                            padding=5
                        )
                    )
            else:
                self.vendedores_grafico.controls.append(
                    ft.Text("Nenhuma venda no período", italic=True, color="gray")
                )
            
            # Habilitar botão de exportação
            self.btn_exportar_vendedores.disabled = False
            
            self._mostrar_snackbar(f"✅ Relatório gerado: {len(self.dados_relatorio_vendedores)} vendedores", "green")
            self.page.update()
            
        except Exception as e:
            self._mostrar_snackbar(f"❌ Erro ao gerar relatório: {str(e)}", "red")
    
    def _exportar_vendedores_csv(self):
        """Exporta o relatório de vendedores para CSV."""
        if not self.dados_relatorio_vendedores:
            self._mostrar_snackbar("❌ Gere o relatório antes de exportar", "orange")
            return
        
        try:
            import os
            from datetime import datetime
            
            # Criar diretório de relatórios se não existir
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            caminho = f"relatorios/vendas_por_vendedor_{timestamp}.csv"
            
            # Preparar dados para exportação
            dados_exportacao = []
            for i, vendedor in enumerate(self.dados_relatorio_vendedores, 1):
                dados_exportacao.append({
                    'Posicao': i,
                    'Vendedor': vendedor['nome_vendedor'],
                    'Numero_Vendas': vendedor['numero_vendas'],
                    'Faturamento_Total': vendedor['faturamento_total'],
                    'Ticket_Medio': vendedor['ticket_medio'],
                    'Percentual_Participacao': vendedor['percentual_participacao']
                })
            
            # Exportar CSV
            sucesso = exportar_relatorio_csv(dados_exportacao, caminho)
            
            if sucesso:
                self._mostrar_snackbar(f"✅ CSV exportado: {caminho}", "green")
            else:
                self._mostrar_snackbar("❌ Erro ao exportar CSV", "red")
                
        except Exception as e:
            self._mostrar_snackbar(f"❌ Erro ao exportar: {str(e)}", "red")
    
    def _ver_detalhes_vendedor(self, vendedor: Dict):
        """Exibe detalhes das vendas de um vendedor específico."""
        # Gerar relatório de vendas filtrado por este vendedor
        data_inicio = self.vendedores_data_inicio.value
        data_fim = self.vendedores_data_fim.value
        
        try:
            # Buscar vendas do vendedor
            relatorio_vendedor = relatorio_vendas_periodo(
                data_inicio=data_inicio,
                data_fim=data_fim,
                usuario_id=vendedor['usuario_id']
            )
            
            # Mudar para a aba de vendas e aplicar o filtro
            self.tabs.selected_index = 0
            self.vendas_data_inicio.value = data_inicio
            self.vendas_data_fim.value = data_fim
            self.vendas_filtro_vendedor.value = str(vendedor['usuario_id'])
            
            # Atualizar dados e interface
            self.dados_relatorio_vendas = relatorio_vendedor
            
            # Atualizar métricas
            self.vendas_faturamento.value = f"R$ {relatorio_vendedor['faturamento_total']:.2f}"
            self.vendas_num_vendas.value = str(relatorio_vendedor['numero_vendas'])
            self.vendas_ticket_medio.value = f"R$ {relatorio_vendedor['ticket_medio']:.2f}"
            
            # Atualizar tabela
            self.tabela_vendas.rows.clear()
            for venda in relatorio_vendedor['vendas']:
                status_cor = "green" if venda['status'] == 'finalizada' else "red"
                status_texto = "Finalizada" if venda['status'] == 'finalizada' else "Cancelada"
                cliente_texto = venda.get('cliente_nome', 'Venda Avulsa') or 'Venda Avulsa'
                
                self.tabela_vendas.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"#{venda['id']}")),
                            ft.DataCell(ft.Text(self._formatar_data(venda['data_hora']))),
                            ft.DataCell(ft.Text(cliente_texto[:20])),
                            ft.DataCell(ft.Text(vendedor['nome_vendedor'][:15])),
                            ft.DataCell(ft.Text(f"R$ {venda['valor_final']:.2f}", weight="bold")),
                            ft.DataCell(ft.Text(status_texto, color=status_cor)),
                        ]
                    )
                )
            
            # Atualizar distribuição de pagamento
            self.vendas_distribuicao_pagamento.controls.clear()
            if relatorio_vendedor['distribuicao_pagamento']:
                for dist in relatorio_vendedor['distribuicao_pagamento']:
                    forma_texto = {
                        'dinheiro': '💵 Dinheiro',
                        'cartao_credito': '💳 Cartão Crédito',
                        'cartao_debito': '💳 Cartão Débito',
                        'pix': '📱 PIX'
                    }.get(dist['forma_pagamento'], dist['forma_pagamento'])
                    
                    largura_barra = int(dist['percentual'] * 3)
                    
                    self.vendas_distribuicao_pagamento.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(forma_texto, size=12, width=120),
                                ft.Container(
                                    content=ft.Text(
                                        f"R$ {dist['valor']:.2f} ({dist['percentual']:.1f}%)",
                                        size=12,
                                        color="white",
                                        weight="bold"
                                    ),
                                    bgcolor="#0070C0",
                                    padding=5,
                                    border_radius=3,
                                    width=largura_barra if largura_barra > 80 else 80
                                ),
                            ], spacing=10),
                            padding=5
                        )
                    )
            
            self._mostrar_snackbar(f"📊 Exibindo vendas de {vendedor['nome_vendedor']}", "#0070C0")
            self.page.update()
            
        except Exception as e:
            self._mostrar_snackbar(f"❌ Erro ao buscar detalhes: {str(e)}", "red")
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _formatar_data(self, data_str: str) -> str:
        """Formata data para exibição (DD/MM/YYYY HH:MM)."""
        try:
            if 'T' in data_str:
                data = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
            else:
                data = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
            return data.strftime("%d/%m/%Y %H:%M")
        except:
            return data_str
    
    def _mostrar_snackbar(self, mensagem: str, cor: str):
        """Exibe uma mensagem SnackBar."""
        snackbar = ft.SnackBar(
            content=ft.Text(mensagem),
            bgcolor=cor
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
