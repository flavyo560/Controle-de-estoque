"""
Tela de Financeiro - Sistema de Vendas DEKIDS

Interface para gestão financeira:
- Fluxo de Caixa
- Contas a Pagar
- Contas a Receber
- Categorias Financeiras
"""

import flet as ft
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any

# Nota: Assumindo que o FinancialService será injetado ou instanciado
# Para simplificar agora, usaremos chamadas diretas ou mocks se necessário
# mas idealmente seguiria o padrão do projeto.

class TelaFinanceiro:
    def __init__(self, page: ft.Page, usuario_id: int):
        self.page = page
        self.usuario_id = usuario_id
        
        # Estado local
        self.categorias = []
        self.movimentacoes = []
        
        self._criar_componentes()
        self.carregar_dados()

    def carregar_dados(self):
        """Carrega dados iniciais do banco."""
        try:
            from database import supabase
            res = supabase.table("financeiro_categorias").select("*").execute()
            self.categorias = res.data or []
            self._atualizar_lista_categorias()
        except Exception as e:
            print(f"Erro ao carregar dados financeiro: {e}")

    def _atualizar_lista_categorias(self):
        """Atualiza a exibição das categorias."""
        self.lista_categorias.controls.clear()
        for cat in self.categorias:
            cor = "green" if cat['tipo'] == 'receita' else "red"
            self.lista_categorias.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.CATEGORY, color=cor),
                    title=ft.Text(cat['nome']),
                    subtitle=ft.Text(f"Tipo: {cat['tipo'].capitalize()} | {cat.get('descricao') or ''}"),
                    trailing=ft.IconButton(ft.icons.DELETE, icon_color="red", on_click=lambda e, cid=cat['id']: self._deletar_categoria(cid))
                )
            )
        self.page.update()

    async def _deletar_categoria(self, categoria_id):
        # Implementar deleção se necessário
        pass

    def _criar_componentes(self):
        # Tabs para organizar as seções
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Fluxo de Caixa", icon=ft.icons.ACCOUNT_BALANCE_WALLET),
                ft.Tab(text="Contas a Pagar", icon=ft.icons.MONEY_OFF),
                ft.Tab(text="Contas a Receber", icon=ft.icons.ATTACH_MONEY),
                ft.Tab(text="Categorias", icon=ft.icons.CATEGORY),
            ],
            expand=1,
            on_change=self._mudar_tab
        )

        # Conteúdo do Fluxo de Caixa
        self.txt_periodo = ft.Text("Período: Últimos 30 dias", size=16, weight="bold")
        self.card_entrada = self._criar_card_financeiro("Entradas", "R$ 0,00", "green", ft.icons.ARROW_UPWARD)
        self.card_saida = self._criar_card_financeiro("Saídas", "R$ 0,00", "red", ft.icons.ARROW_DOWNWARD)
        self.card_saldo = self._criar_card_financeiro("Saldo", "R$ 0,00", "blue", ft.icons.ACCOUNT_BALANCE)

        self.lista_fluxo = ft.ListView(expand=1, spacing=10, padding=20)
        
        self.view_fluxo = ft.Column([
            ft.Row([self.card_entrada, self.card_saida, self.card_saldo], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            ft.Row([
                ft.Text("Histórico de Movimentações", size=18, weight="bold"),
                ft.ElevatedButton("Nova Movimentação", icon=ft.icons.ADD, on_click=lambda _: self._abrir_modal_movimentacao())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.lista_fluxo
        ], visible=True)

        # Conteúdo de Contas a Pagar
        self.lista_pagar = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Vencimento")),
                ft.DataColumn(ft.Text("Valor")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[]
        )
        
        self.view_pagar = ft.Column([
            ft.Row([
                ft.Text("Contas a Pagar", size=18, weight="bold"),
                ft.ElevatedButton("Nova Conta", icon=ft.icons.ADD, on_click=lambda _: self._abrir_modal_conta("pagar"))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(content=self.lista_pagar, scroll=ft.ScrollMode.AUTO)
        ], visible=False)

        # Conteúdo de Contas a Receber
        self.lista_receber = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Vencimento")),
                ft.DataColumn(ft.Text("Valor")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[]
        )
        
        self.view_receber = ft.Column([
            ft.Row([
                ft.Text("Contas a Receber", size=18, weight="bold"),
                ft.ElevatedButton("Novo Recebimento", icon=ft.icons.ADD, on_click=lambda _: self._abrir_modal_conta("receber"))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(content=self.lista_receber, scroll=ft.ScrollMode.AUTO)
        ], visible=False)

        # Conteúdo de Categorias
        self.lista_categorias = ft.Column(spacing=10)
        self.view_categorias = ft.Column([
            ft.Row([
                ft.Text("Categorias Financeiras", size=18, weight="bold"),
                ft.ElevatedButton("Nova Categoria", icon=ft.icons.ADD, on_click=lambda _: self._abrir_modal_categoria())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.lista_categorias
        ], visible=False)

    def _criar_card_financeiro(self, titulo, valor, cor, icone):
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(icone, color=cor, size=30),
                        title=ft.Text(titulo, size=14, color="grey"),
                        subtitle=ft.Text(valor, size=20, weight="bold", color=cor),
                    )
                ]),
                width=250,
                padding=10
            )
        )

    def _mudar_tab(self, e):
        idx = self.tabs.selected_index
        self.view_fluxo.visible = (idx == 0)
        self.view_pagar.visible = (idx == 1)
        self.view_receber.visible = (idx == 2)
        self.view_categorias.visible = (idx == 3)
        self.page.update()

    def build(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Text("💰 Gestão Financeira", size=24, weight="bold", color="white"),
                    ]),
                    bgcolor="#0070C0",
                    padding=15,
                    border_radius=10
                ),
                self.tabs,
                ft.Container(
                    content=ft.Column([
                        self.view_fluxo,
                        self.view_pagar,
                        self.view_receber,
                        self.view_categorias
                    ], expand=True),
                    padding=20,
                    expand=True
                )
            ], expand=True),
            padding=20,
            expand=True
        )

    def _abrir_modal_movimentacao(self):
        self._mostrar_aviso("Funcionalidade de Nova Movimentação em desenvolvimento")

    def _abrir_modal_conta(self, tipo):
        self._mostrar_aviso(f"Funcionalidade de Contas a {tipo.capitalize()} em desenvolvimento")

    def _abrir_modal_categoria(self):
        self._mostrar_aviso("Funcionalidade de Categorias em desenvolvimento")

    def _mostrar_aviso(self, msg):
        snack = ft.SnackBar(ft.Text(msg))
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()
