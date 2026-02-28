"""
Tela de Vendas (PDV) - Sistema de Vendas DEKIDS

Interface completa de Ponto de Venda (PDV) com:
- Busca e adição de produtos
- Gerenciamento do carrinho
- Seleção de cliente
- Processamento de pagamentos
- Finalização de venda
- Geração de comprovante
"""

import flet as ft
from typing import Optional, List, Dict
from vendas import Carrinho, buscar_produtos_venda, finalizar_venda, gerar_comprovante, exportar_comprovante_pdf
from clientes import buscar_clientes, cadastrar_cliente
from validacao_vendas import validar_pagamentos_venda


class TelaPDV:
    """
    Classe principal da tela de PDV (Ponto de Venda).
    
    Gerencia toda a interface de vendas incluindo busca de produtos,
    carrinho, seleção de cliente, pagamentos e finalização.
    """
    
    def __init__(self, page: ft.Page, usuario_id: int, usuario_nome: str):
        """
        Inicializa a tela de PDV.
        
        Args:
            page: Instância da página Flet
            usuario_id: ID do usuário autenticado (vendedor)
            usuario_nome: Nome do usuário autenticado
        """
        self.page = page
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        
        # Instância do carrinho
        self.carrinho = Carrinho()
        
        # Cliente selecionado (None para venda avulsa)
        self.cliente_selecionado: Optional[Dict] = None
        
        # Lista de pagamentos adicionados
        self.pagamentos: List[Dict] = []
        
        # Criar componentes da interface
        self._criar_componentes()

    
    def _criar_componentes(self):
        """Cria todos os componentes da interface."""
        # Componentes de busca de produtos
        self.txt_busca_produto = ft.TextField(
            label="Buscar Produto",
            hint_text="Digite código de barras, referência ou descrição",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_submit=lambda e: self._buscar_produtos()
        )
        
        self.btn_buscar = ft.ElevatedButton(
            "Buscar",
            icon=ft.icons.SEARCH,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._buscar_produtos()
        )
        
        self.tabela_produtos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Descrição", weight="bold"), numeric=False),
                ft.DataColumn(ft.Text("Ref", weight="bold"), numeric=False),
                ft.DataColumn(ft.Text("Preço", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Estoque", weight="bold"), numeric=True),
                ft.DataColumn(ft.Text("Ação", weight="bold"), numeric=False),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
            column_spacing=5,
        )
        
        # Componentes do carrinho
        self.tabela_carrinho = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Descrição", weight="bold")),
                ft.DataColumn(ft.Text("Qtd", weight="bold")),
                ft.DataColumn(ft.Text("Preço Unit.", weight="bold")),
                ft.DataColumn(ft.Text("Subtotal", weight="bold")),
                ft.DataColumn(ft.Text("Ações", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        self.txt_desconto = ft.TextField(
            label="Desconto",
            hint_text="Ex: 10% ou 50.00",
            width=150,
            on_submit=lambda e: self._aplicar_desconto()
        )
        
        self.btn_aplicar_desconto = ft.ElevatedButton(
            "Aplicar",
            bgcolor="green",
            color="white",
            on_click=lambda e: self._aplicar_desconto()
        )
        
        self.btn_remover_desconto = ft.ElevatedButton(
            "Remover",
            bgcolor="orange",
            color="white",
            on_click=lambda e: self._remover_desconto()
        )
        
        self.txt_subtotal = ft.Text("Subtotal: R$ 0,00", size=16, weight="bold")
        self.txt_desconto_aplicado = ft.Text("Desconto: R$ 0,00", size=14, color="green")
        self.txt_total = ft.Text("TOTAL: R$ 0,00", size=20, weight="bold", color="#0070C0")

        
        # Componentes de cliente
        self.dropdown_cliente = ft.Dropdown(
            label="Cliente",
            hint_text="Selecione um cliente ou deixe em branco para venda avulsa",
            options=[],
            width=300,
            on_change=lambda e: self._selecionar_cliente()
        )
        
        self.txt_busca_cliente = ft.TextField(
            label="Buscar Cliente",
            hint_text="CPF, nome ou telefone",
            width=250,
            on_submit=lambda e: self._buscar_clientes()
        )
        
        self.btn_buscar_cliente = ft.IconButton(
            icon=ft.icons.SEARCH,
            icon_color="#0070C0",
            tooltip="Buscar cliente",
            on_click=lambda e: self._buscar_clientes()
        )
        
        self.btn_novo_cliente = ft.ElevatedButton(
            "Novo Cliente",
            icon=ft.icons.PERSON_ADD,
            bgcolor="green",
            color="white",
            on_click=lambda e: self._abrir_modal_novo_cliente()
        )
        
        self.txt_cliente_selecionado = ft.Text("Venda Avulsa", size=14, italic=True)
        
        # Componentes de pagamento
        self.dropdown_forma_pagamento = ft.Dropdown(
            label="Forma de Pagamento",
            options=[
                ft.dropdown.Option("dinheiro", "Dinheiro"),
                ft.dropdown.Option("cartao_credito", "Cartão de Crédito"),
                ft.dropdown.Option("cartao_debito", "Cartão de Débito"),
                ft.dropdown.Option("pix", "PIX"),
            ],
            width=200,
            on_change=lambda e: self._atualizar_campos_pagamento()
        )
        
        self.txt_valor_pagamento = ft.TextField(
            label="Valor",
            hint_text="0.00",
            prefix=ft.Text("R$ "),
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.txt_parcelas = ft.TextField(
            label="Parcelas",
            hint_text="1-12",
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False
        )
        
        self.txt_valor_recebido = ft.TextField(
            label="Valor Recebido",
            hint_text="0.00",
            prefix=ft.Text("R$ "),
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            visible=False,
            on_change=lambda e: self._calcular_troco()
        )
        
        self.txt_troco = ft.Text("Troco: R$ 0,00", size=14, color="green", visible=False)

        
        self.btn_adicionar_pagamento = ft.ElevatedButton(
            "Adicionar Pagamento",
            icon=ft.icons.ADD,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._adicionar_pagamento()
        )
        
        self.tabela_pagamentos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Forma", weight="bold")),
                ft.DataColumn(ft.Text("Valor", weight="bold")),
                ft.DataColumn(ft.Text("Parcelas", weight="bold")),
                ft.DataColumn(ft.Text("Ação", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        self.txt_total_pagamentos = ft.Text("Total Pago: R$ 0,00", size=16, weight="bold")
        self.txt_restante = ft.Text("Restante: R$ 0,00", size=16, weight="bold", color="red")
        
        self.btn_finalizar_venda = ft.ElevatedButton(
            "FINALIZAR VENDA",
            icon=ft.icons.CHECK_CIRCLE,
            bgcolor="green",
            color="white",
            height=50,
            disabled=True,
            on_click=lambda e: self._finalizar_venda()
        )
        
        # Modal de novo cliente
        self._criar_modal_novo_cliente()
        
        # Modal de comprovante
        self._criar_modal_comprovante()
    
    def _criar_modal_novo_cliente(self):
        """Cria o modal de cadastro de novo cliente."""
        self.modal_nome = ft.TextField(label="Nome *", hint_text="Nome completo")
        self.modal_cpf = ft.TextField(label="CPF *", hint_text="000.000.000-00", max_length=14)
        self.modal_telefone = ft.TextField(label="Telefone", hint_text="(00) 00000-0000")
        self.modal_email = ft.TextField(label="Email", hint_text="email@exemplo.com")
        self.modal_endereco_rua = ft.TextField(label="Logradouro", hint_text="Rua, Avenida...")
        self.modal_endereco_numero = ft.TextField(label="Número", width=100)
        self.modal_endereco_complemento = ft.TextField(label="Complemento", hint_text="Apto, Bloco...")
        self.modal_endereco_bairro = ft.TextField(label="Bairro")
        self.modal_endereco_cidade = ft.TextField(label="Cidade")
        self.modal_endereco_estado = ft.TextField(label="Estado", hint_text="UF", max_length=2, width=80)
        self.modal_endereco_cep = ft.TextField(label="CEP", hint_text="00000-000", max_length=9)
        
        self.modal_novo_cliente = ft.AlertDialog(
            title=ft.Text("Cadastrar Novo Cliente"),
            content=ft.Container(
                content=ft.Column([
                    self.modal_nome,
                    self.modal_cpf,
                    self.modal_telefone,
                    self.modal_email,
                    ft.Divider(),
                    ft.Text("Endereço (opcional)", weight="bold"),
                    self.modal_endereco_rua,
                    ft.Row([self.modal_endereco_numero, self.modal_endereco_complemento]),
                    self.modal_endereco_bairro,
                    ft.Row([self.modal_endereco_cidade, self.modal_endereco_estado]),
                    self.modal_endereco_cep,
                ], tight=True, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=600
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._fechar_modal_novo_cliente()),
                ft.ElevatedButton("Salvar", bgcolor="green", color="white", on_click=lambda e: self._salvar_novo_cliente()),
            ],
        )
        self.page.overlay.append(self.modal_novo_cliente)

    
    def _criar_modal_comprovante(self):
        """Cria o modal de exibição do comprovante."""
        self.comprovante_conteudo = ft.Column([], scroll=ft.ScrollMode.AUTO)
        
        self.modal_comprovante = ft.AlertDialog(
            title=ft.Text("Comprovante de Venda", size=20, weight="bold"),
            content=ft.Container(
                content=self.comprovante_conteudo,
                width=600,
                height=700
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: self._fechar_modal_comprovante()),
                ft.ElevatedButton("Exportar PDF", icon=ft.icons.PICTURE_AS_PDF, bgcolor="#0070C0", color="white", on_click=lambda e: self._exportar_pdf()),
            ],
        )
        self.page.overlay.append(self.modal_comprovante)
    
    def build(self) -> ft.Container:
        """
        Constrói e retorna o layout completo da tela de PDV.
        
        Returns:
            Container com o layout completo em 3 colunas
        """
        # Coluna 1: Busca de Produtos
        coluna_produtos = ft.Container(
            content=ft.Column([
                ft.Text("🔍 Buscar Produtos", size=18, weight="bold", color="#0070C0"),
                ft.Divider(),
                ft.Row([self.txt_busca_produto, self.btn_buscar]),
                ft.Container(
                    content=ft.Column([self.tabela_produtos], scroll=ft.ScrollMode.ALWAYS),
                    height=500,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
            ], spacing=10),
            padding=15,
            bgcolor="white",
            border_radius=10,
            expand=1
        )
        
        # Coluna 2: Carrinho
        coluna_carrinho = ft.Container(
            content=ft.Column([
                ft.Text("🛒 Carrinho", size=18, weight="bold", color="#0070C0"),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([self.tabela_carrinho], scroll=ft.ScrollMode.ALWAYS),
                    height=300,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        ft.Text("💰 Desconto", weight="bold", size=14),
                        ft.Row([
                            self.txt_desconto,
                            self.btn_aplicar_desconto,
                            self.btn_remover_desconto
                        ], spacing=5),
                    ], spacing=5),
                    bgcolor="#F0F8FF",
                    padding=10,
                    border_radius=5,
                    border=ft.border.all(1, "#0070C0")
                ),
                ft.Divider(),
                self.txt_subtotal,
                self.txt_desconto_aplicado,
                self.txt_total,
            ], spacing=10),
            padding=15,
            bgcolor="white",
            border_radius=10,
            expand=1
        )

        
        # Coluna 3: Cliente e Pagamento
        coluna_pagamento = ft.Container(
            content=ft.Column([
                ft.Text("👤 Cliente", size=18, weight="bold", color="#0070C0"),
                ft.Divider(),
                ft.Row([
                    self.txt_busca_cliente,
                    self.btn_buscar_cliente,
                ]),
                self.dropdown_cliente,
                self.btn_novo_cliente,
                self.txt_cliente_selecionado,
                ft.Divider(height=20),
                ft.Text("💳 Pagamento", size=18, weight="bold", color="#0070C0"),
                ft.Divider(),
                self.dropdown_forma_pagamento,
                self.txt_valor_pagamento,
                self.txt_parcelas,
                self.txt_valor_recebido,
                self.txt_troco,
                self.btn_adicionar_pagamento,
                ft.Divider(),
                ft.Container(
                    content=ft.Column([self.tabela_pagamentos], scroll=ft.ScrollMode.AUTO),
                    height=150,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5,
                    padding=10
                ),
                self.txt_total_pagamentos,
                self.txt_restante,
                ft.Divider(),
                self.btn_finalizar_venda,
            ], spacing=10, scroll=ft.ScrollMode.AUTO),
            padding=15,
            bgcolor="white",
            border_radius=10,
            expand=1
        )
        
        # Layout principal com 3 colunas
        layout = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Container(
                    content=ft.Row([
                        ft.Text("🏪 PDV - Ponto de Venda", size=24, weight="bold", color="white"),
                        ft.Text(f"Vendedor: {self.usuario_nome}", size=14, color="white", italic=True),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#0070C0",
                    padding=15,
                    border_radius=10
                ),
                # Conteúdo em 3 colunas
                ft.Row([
                    coluna_produtos,
                    coluna_carrinho,
                    coluna_pagamento,
                ], spacing=10, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            ], spacing=10, expand=True),
            padding=20,
            expand=True
        )
        
        return layout

    
    # ========== MÉTODOS DE BUSCA DE PRODUTOS ==========
    
    def _buscar_produtos(self):
        """Busca produtos e exibe na tabela."""
        termo = self.txt_busca_produto.value
        
        if not termo or not termo.strip():
            self._mostrar_snackbar("Digite um termo de busca", "orange")
            return
        
        # Buscar produtos
        produtos = buscar_produtos_venda(termo, apenas_disponiveis=True)
        
        # Limpar tabela
        self.tabela_produtos.rows.clear()
        
        if not produtos:
            self._mostrar_snackbar("Nenhum produto encontrado", "orange")
            self.page.update()
            return
        
        # Preencher tabela com produtos encontrados
        for produto in produtos:
            self.tabela_produtos.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(produto['descricao'][:20])),
                        ft.DataCell(ft.Text(produto['referencia'][:10])),
                        ft.DataCell(ft.Text(f"R$ {produto['preco']:.2f}")),
                        ft.DataCell(ft.Text(str(produto['quantidade']))),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.ADD_SHOPPING_CART,
                                icon_color="white",
                                bgcolor="green",
                                tooltip="Adicionar ao carrinho",
                                on_click=lambda e, p=produto: self._adicionar_ao_carrinho(p)
                            )
                        ),
                    ]
                )
            )
        
        self._mostrar_snackbar(f"{len(produtos)} produto(s) encontrado(s)", "green")
        self.page.update()
    
    def _adicionar_ao_carrinho(self, produto: Dict):
        """Adiciona um produto ao carrinho."""
        sucesso = self.carrinho.adicionar_produto(produto['id'], quantidade=1)
        
        if sucesso:
            self._mostrar_snackbar(f"✅ {produto['descricao']} adicionado ao carrinho", "green")
            self._atualizar_carrinho()
        else:
            self._mostrar_snackbar(f"❌ Estoque insuficiente para {produto['descricao']}", "red")
        
        self.page.update()

    
    # ========== MÉTODOS DO CARRINHO ==========
    
    def _atualizar_carrinho(self):
        """Atualiza a exibição do carrinho."""
        # Limpar tabela
        self.tabela_carrinho.rows.clear()
        
        # Preencher tabela com itens do carrinho
        for item in self.carrinho.itens:
            self.tabela_carrinho.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item.descricao[:25])),
                        ft.DataCell(ft.Text(str(item.quantidade))),
                        ft.DataCell(ft.Text(f"R$ {item.preco_unitario:.2f}")),
                        ft.DataCell(ft.Text(f"R$ {item.calcular_subtotal():.2f}", weight="bold")),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.ADD,
                                    icon_color="green",
                                    tooltip="Aumentar quantidade",
                                    on_click=lambda e, item=item: self._aumentar_quantidade(item)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.REMOVE,
                                    icon_color="orange",
                                    tooltip="Diminuir quantidade",
                                    on_click=lambda e, item=item: self._diminuir_quantidade(item)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    icon_color="red",
                                    tooltip="Remover item",
                                    on_click=lambda e, item=item: self._remover_do_carrinho(item)
                                ),
                            ], spacing=0)
                        ),
                    ]
                )
            )
        
        # Atualizar totais
        subtotal = self.carrinho.calcular_subtotal()
        desconto = self.carrinho.calcular_desconto()
        total = self.carrinho.calcular_total()
        
        self.txt_subtotal.value = f"Subtotal: R$ {subtotal:.2f}"
        self.txt_desconto_aplicado.value = f"Desconto: R$ {desconto:.2f}"
        self.txt_total.value = f"TOTAL: R$ {total:.2f}"
        
        # Atualizar valor restante e botão finalizar
        self._atualizar_pagamentos()
        
        self.page.update()
    
    def _aumentar_quantidade(self, item):
        """Aumenta a quantidade de um item no carrinho."""
        nova_quantidade = item.quantidade + 1
        sucesso = self.carrinho.atualizar_quantidade(item.produto_id, nova_quantidade)
        
        if sucesso:
            self._atualizar_carrinho()
        else:
            self._mostrar_snackbar(f"❌ Estoque insuficiente. Disponível: {item.estoque_disponivel}", "red")
    
    def _diminuir_quantidade(self, item):
        """Diminui a quantidade de um item no carrinho."""
        if item.quantidade > 1:
            nova_quantidade = item.quantidade - 1
            self.carrinho.atualizar_quantidade(item.produto_id, nova_quantidade)
            self._atualizar_carrinho()
        else:
            self._remover_do_carrinho(item)
    
    def _remover_do_carrinho(self, item):
        """Remove um item do carrinho."""
        self.carrinho.remover_produto(item.produto_id)
        self._mostrar_snackbar(f"🗑️ {item.descricao} removido do carrinho", "black")
        self._atualizar_carrinho()

    
    def _aplicar_desconto(self):
        """Aplica desconto ao carrinho."""
        valor_desconto = self.txt_desconto.value
        
        if not valor_desconto or not valor_desconto.strip():
            self._mostrar_snackbar("Digite um valor de desconto", "orange")
            return
        
        # Verificar se é percentual (contém %) ou valor fixo
        if '%' in valor_desconto:
            # Desconto percentual
            try:
                percentual = float(valor_desconto.replace('%', '').replace(',', '.').strip())
                sucesso = self.carrinho.aplicar_desconto_percentual(percentual)
                
                if sucesso:
                    self._mostrar_snackbar(f"✅ Desconto de {percentual}% aplicado", "green")
                    self._atualizar_carrinho()
                else:
                    self._mostrar_snackbar("❌ Desconto inválido. Deve estar entre 0 e 100%", "red")
            except ValueError:
                self._mostrar_snackbar("❌ Valor de desconto inválido", "red")
        else:
            # Desconto em valor fixo
            try:
                valor = float(valor_desconto.replace(',', '.').strip())
                sucesso = self.carrinho.aplicar_desconto_valor(valor)
                
                if sucesso:
                    self._mostrar_snackbar(f"✅ Desconto de R$ {valor:.2f} aplicado", "green")
                    self._atualizar_carrinho()
                else:
                    self._mostrar_snackbar("❌ Desconto inválido. Não pode exceder o total do carrinho", "red")
            except ValueError:
                self._mostrar_snackbar("❌ Valor de desconto inválido", "red")
    
    def _remover_desconto(self):
        """Remove o desconto aplicado."""
        self.carrinho.remover_desconto()
        self.txt_desconto.value = ""
        self._mostrar_snackbar("Desconto removido", "black")
        self._atualizar_carrinho()

    
    # ========== MÉTODOS DE CLIENTE ==========
    
    def _buscar_clientes(self):
        """Busca clientes e preenche o dropdown."""
        termo = self.txt_busca_cliente.value
        
        if not termo or not termo.strip():
            self._mostrar_snackbar("Digite um termo de busca", "orange")
            return
        
        # Buscar clientes
        clientes = buscar_clientes(termo)
        
        # Limpar dropdown
        self.dropdown_cliente.options.clear()
        
        # Adicionar opção de venda avulsa
        self.dropdown_cliente.options.append(
            ft.dropdown.Option(key="0", text="Venda Avulsa (sem cliente)")
        )
        
        if not clientes:
            self._mostrar_snackbar("Nenhum cliente encontrado", "orange")
            self.page.update()
            return
        
        # Preencher dropdown com clientes encontrados
        for cliente in clientes:
            nome = cliente['nome']
            cpf = cliente['cpf']
            self.dropdown_cliente.options.append(
                ft.dropdown.Option(
                    key=str(cliente['id']),
                    text=f"{nome} - CPF: {cpf}"
                )
            )
        
        self._mostrar_snackbar(f"{len(clientes)} cliente(s) encontrado(s)", "green")
        self.page.update()
    
    def _selecionar_cliente(self):
        """Seleciona um cliente do dropdown."""
        if not self.dropdown_cliente.value or self.dropdown_cliente.value == "0":
            # Venda avulsa
            self.cliente_selecionado = None
            self.txt_cliente_selecionado.value = "Venda Avulsa"
        else:
            # Cliente selecionado
            cliente_id = int(self.dropdown_cliente.value)
            # Buscar dados completos do cliente
            from clientes import obter_cliente
            self.cliente_selecionado = obter_cliente(cliente_id)
            
            if self.cliente_selecionado:
                self.txt_cliente_selecionado.value = f"Cliente: {self.cliente_selecionado['nome']}"
            else:
                self.txt_cliente_selecionado.value = "Erro ao carregar cliente"
        
        self.page.update()
    
    def _abrir_modal_novo_cliente(self):
        """Abre o modal de cadastro de novo cliente."""
        # Limpar campos
        self.modal_nome.value = ""
        self.modal_cpf.value = ""
        self.modal_telefone.value = ""
        self.modal_email.value = ""
        self.modal_endereco_rua.value = ""
        self.modal_endereco_numero.value = ""
        self.modal_endereco_complemento.value = ""
        self.modal_endereco_bairro.value = ""
        self.modal_endereco_cidade.value = ""
        self.modal_endereco_estado.value = ""
        self.modal_endereco_cep.value = ""
        
        self.modal_novo_cliente.open = True
        self.page.update()
    
    def _fechar_modal_novo_cliente(self):
        """Fecha o modal de cadastro de novo cliente."""
        self.modal_novo_cliente.open = False
        self.page.update()

    
    def _salvar_novo_cliente(self):
        """Salva um novo cliente."""
        # Validar campos obrigatórios
        if not self.modal_nome.value or not self.modal_cpf.value:
            self._mostrar_snackbar("❌ Nome e CPF são obrigatórios", "red")
            return
        
        # Preparar dados do cliente
        dados_cliente = {
            'nome': self.modal_nome.value,
            'cpf': self.modal_cpf.value,
            'telefone': self.modal_telefone.value,
            'email': self.modal_email.value,
            'endereco_logradouro': self.modal_endereco_rua.value,
            'endereco_numero': self.modal_endereco_numero.value,
            'endereco_complemento': self.modal_endereco_complemento.value,
            'endereco_bairro': self.modal_endereco_bairro.value,
            'endereco_cidade': self.modal_endereco_cidade.value,
            'endereco_estado': self.modal_endereco_estado.value,
            'endereco_cep': self.modal_endereco_cep.value,
        }
        
        # Cadastrar cliente
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        
        if sucesso:
            self._mostrar_snackbar(f"✅ {mensagem}", "green")
            self._fechar_modal_novo_cliente()
            
            # Adicionar cliente ao dropdown e selecionar
            self.dropdown_cliente.options.append(
                ft.dropdown.Option(
                    key=str(cliente_id),
                    text=f"{dados_cliente['nome']} - CPF: {dados_cliente['cpf']}"
                )
            )
            self.dropdown_cliente.value = str(cliente_id)
            self._selecionar_cliente()
        else:
            self._mostrar_snackbar(f"❌ {mensagem}", "red")

    
    # ========== MÉTODOS DE PAGAMENTO ==========
    
    def _atualizar_campos_pagamento(self):
        """Atualiza a visibilidade dos campos de pagamento baseado na forma selecionada."""
        forma = self.dropdown_forma_pagamento.value
        
        if forma == "cartao_credito":
            # Mostrar campo de parcelas
            self.txt_parcelas.visible = True
            self.txt_valor_recebido.visible = False
            self.txt_troco.visible = False
        elif forma == "dinheiro":
            # Mostrar campos de valor recebido e troco
            self.txt_parcelas.visible = False
            self.txt_valor_recebido.visible = True
            self.txt_troco.visible = True
        else:
            # Ocultar campos extras
            self.txt_parcelas.visible = False
            self.txt_valor_recebido.visible = False
            self.txt_troco.visible = False
        
        self.page.update()
    
    def _calcular_troco(self):
        """Calcula o troco para pagamento em dinheiro."""
        try:
            valor_recebido = float(self.txt_valor_recebido.value.replace(',', '.'))
            total = self.carrinho.calcular_total()
            troco = valor_recebido - total
            
            if troco >= 0:
                self.txt_troco.value = f"Troco: R$ {troco:.2f}"
                self.txt_troco.color = "green"
            else:
                self.txt_troco.value = f"Falta: R$ {abs(troco):.2f}"
                self.txt_troco.color = "red"
            
            self.page.update()
        except:
            self.txt_troco.value = "Troco: R$ 0,00"
            self.page.update()
    
    def _adicionar_pagamento(self):
        """Adiciona uma forma de pagamento à lista."""
        # Validar forma de pagamento
        if not self.dropdown_forma_pagamento.value:
            self._mostrar_snackbar("❌ Selecione uma forma de pagamento", "red")
            return
        
        # Validar valor
        if not self.txt_valor_pagamento.value:
            self._mostrar_snackbar("❌ Digite o valor do pagamento", "red")
            return
        
        try:
            valor = float(self.txt_valor_pagamento.value.replace(',', '.'))
            if valor <= 0:
                self._mostrar_snackbar("❌ Valor deve ser maior que zero", "red")
                return
        except ValueError:
            self._mostrar_snackbar("❌ Valor inválido", "red")
            return
        
        forma = self.dropdown_forma_pagamento.value
        
        # Preparar dados do pagamento
        pagamento = {
            'forma_pagamento': forma,
            'valor': valor
        }
        
        # Adicionar campos específicos por forma de pagamento
        if forma == "cartao_credito":
            if not self.txt_parcelas.value:
                self._mostrar_snackbar("❌ Digite o número de parcelas", "red")
                return
            
            try:
                parcelas = int(self.txt_parcelas.value)
                if parcelas < 1 or parcelas > 12:
                    self._mostrar_snackbar("❌ Número de parcelas deve ser entre 1 e 12", "red")
                    return
                pagamento['numero_parcelas'] = parcelas
            except ValueError:
                self._mostrar_snackbar("❌ Número de parcelas inválido", "red")
                return
        
        elif forma == "dinheiro":
            if not self.txt_valor_recebido.value:
                self._mostrar_snackbar("❌ Digite o valor recebido", "red")
                return
            
            try:
                valor_recebido = float(self.txt_valor_recebido.value.replace(',', '.'))
                if valor_recebido < valor:
                    self._mostrar_snackbar("❌ Valor recebido deve ser maior ou igual ao valor do pagamento", "red")
                    return
                
                troco = valor_recebido - valor
                pagamento['valor_recebido'] = valor_recebido
                pagamento['troco'] = troco
            except ValueError:
                self._mostrar_snackbar("❌ Valor recebido inválido", "red")
                return
        
        # Adicionar pagamento à lista
        self.pagamentos.append(pagamento)
        
        # Limpar campos
        self.txt_valor_pagamento.value = ""
        self.txt_parcelas.value = ""
        self.txt_valor_recebido.value = ""
        self.txt_troco.value = "Troco: R$ 0,00"
        
        self._mostrar_snackbar("✅ Pagamento adicionado", "green")
        self._atualizar_pagamentos()

    
    def _atualizar_pagamentos(self):
        """Atualiza a exibição da tabela de pagamentos e totais."""
        # Limpar tabela
        self.tabela_pagamentos.rows.clear()
        
        # Preencher tabela com pagamentos
        for i, pagamento in enumerate(self.pagamentos):
            forma_texto = {
                'dinheiro': 'Dinheiro',
                'cartao_credito': 'Cartão Crédito',
                'cartao_debito': 'Cartão Débito',
                'pix': 'PIX'
            }.get(pagamento['forma_pagamento'], pagamento['forma_pagamento'])
            
            parcelas_texto = ""
            if pagamento.get('numero_parcelas'):
                parcelas_texto = f"{pagamento['numero_parcelas']}x"
            
            self.tabela_pagamentos.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(forma_texto)),
                        ft.DataCell(ft.Text(f"R$ {pagamento['valor']:.2f}")),
                        ft.DataCell(ft.Text(parcelas_texto)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_color="red",
                                tooltip="Remover pagamento",
                                on_click=lambda e, idx=i: self._remover_pagamento(idx)
                            )
                        ),
                    ]
                )
            )
        
        # Calcular totais
        total_pago = sum(p['valor'] for p in self.pagamentos)
        total_venda = self.carrinho.calcular_total()
        restante = total_venda - total_pago
        
        self.txt_total_pagamentos.value = f"Total Pago: R$ {total_pago:.2f}"
        self.txt_restante.value = f"Restante: R$ {restante:.2f}"
        
        # Atualizar cor do restante
        if restante > 0:
            self.txt_restante.color = "red"
        elif restante < 0:
            self.txt_restante.color = "orange"
        else:
            self.txt_restante.color = "green"
        
        # Habilitar/desabilitar botão finalizar
        # Só habilitar se carrinho não está vazio e restante é zero
        if len(self.carrinho.itens) > 0 and abs(restante) < 0.01:
            self.btn_finalizar_venda.disabled = False
            self.btn_finalizar_venda.bgcolor = "green"
        else:
            self.btn_finalizar_venda.disabled = True
            self.btn_finalizar_venda.bgcolor = "gray"
        
        self.page.update()
    
    def _remover_pagamento(self, indice: int):
        """Remove um pagamento da lista."""
        if 0 <= indice < len(self.pagamentos):
            self.pagamentos.pop(indice)
            self._mostrar_snackbar("🗑️ Pagamento removido", "black")
            self._atualizar_pagamentos()

    
    # ========== MÉTODOS DE FINALIZAÇÃO ==========
    
    def _finalizar_venda(self):
        """Finaliza a venda."""
        # Validar carrinho não vazio
        if not self.carrinho.itens or len(self.carrinho.itens) == 0:
            self._mostrar_snackbar("❌ Carrinho está vazio", "red")
            return
        
        # Validar pagamentos
        if not self.pagamentos or len(self.pagamentos) == 0:
            self._mostrar_snackbar("❌ Adicione pelo menos uma forma de pagamento", "red")
            return
        
        # Obter ID do cliente (None para venda avulsa)
        cliente_id = None
        if self.cliente_selecionado:
            cliente_id = self.cliente_selecionado['id']
        
        # Finalizar venda
        sucesso, mensagem, venda_id = finalizar_venda(
            carrinho=self.carrinho,
            pagamentos=self.pagamentos,
            usuario_id=self.usuario_id,
            cliente_id=cliente_id
        )
        
        if sucesso:
            self._mostrar_snackbar(f"✅ {mensagem}", "green")
            
            # Exibir comprovante
            self._exibir_comprovante(venda_id)
            
            # Limpar tela para nova venda
            self._limpar_tela()
        else:
            self._mostrar_snackbar(f"❌ {mensagem}", "red")
    
    def _limpar_tela(self):
        """Limpa a tela após finalização de venda."""
        # Limpar busca de produtos
        self.txt_busca_produto.value = ""
        self.tabela_produtos.rows.clear()
        
        # Carrinho já foi limpo pela função finalizar_venda
        self._atualizar_carrinho()
        
        # Limpar cliente
        self.cliente_selecionado = None
        self.txt_busca_cliente.value = ""
        self.dropdown_cliente.options.clear()
        self.dropdown_cliente.value = None
        self.txt_cliente_selecionado.value = "Venda Avulsa"
        
        # Limpar pagamentos
        self.pagamentos.clear()
        self.dropdown_forma_pagamento.value = None
        self.txt_valor_pagamento.value = ""
        self.txt_parcelas.value = ""
        self.txt_valor_recebido.value = ""
        self.txt_troco.value = "Troco: R$ 0,00"
        self._atualizar_pagamentos()
        
        # Limpar desconto
        self.txt_desconto.value = ""
        
        self.page.update()

    
    # ========== MÉTODOS DE COMPROVANTE ==========
    
    def _exibir_comprovante(self, venda_id: int):
        """Exibe o comprovante de venda no modal."""
        # Gerar comprovante
        comprovante = gerar_comprovante(venda_id)
        
        if not comprovante:
            self._mostrar_snackbar("❌ Erro ao gerar comprovante", "red")
            return
        
        # Armazenar venda_id para exportação PDF
        self.venda_id_comprovante = venda_id
        
        # Limpar conteúdo anterior
        self.comprovante_conteudo.controls.clear()
        
        # Cabeçalho
        self.comprovante_conteudo.controls.extend([
            ft.Container(
                content=ft.Column([
                    ft.Text("DEKIDS Moda Infantil", size=20, weight="bold", text_align=ft.TextAlign.CENTER),
                    ft.Text("Comprovante de Venda", size=16, text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#0070C0",
                padding=15,
                border_radius=5
            ),
            ft.Divider(height=20),
        ])
        
        # Informações da venda
        self.comprovante_conteudo.controls.extend([
            ft.Text(f"Venda Nº: {comprovante['numero_venda']}", size=16, weight="bold"),
            ft.Text(f"Data/Hora: {comprovante['data_hora']}", size=14),
            ft.Text(f"Vendedor: {comprovante['vendedor']}", size=14),
        ])
        
        # Cliente (se não for venda avulsa)
        if comprovante['cliente']:
            self.comprovante_conteudo.controls.extend([
                ft.Divider(),
                ft.Text("Cliente:", size=14, weight="bold"),
                ft.Text(f"Nome: {comprovante['cliente']['nome']}", size=14),
                ft.Text(f"CPF: {comprovante['cliente']['cpf']}", size=14),
                ft.Text(f"Telefone: {comprovante['cliente']['telefone']}", size=14),
            ])
        else:
            self.comprovante_conteudo.controls.extend([
                ft.Divider(),
                ft.Text("Venda Avulsa (sem cliente)", size=14, italic=True),
            ])
        
        # Itens
        self.comprovante_conteudo.controls.extend([
            ft.Divider(),
            ft.Text("Itens:", size=14, weight="bold"),
        ])
        
        for item in comprovante['itens']:
            self.comprovante_conteudo.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(item['descricao'], size=14, weight="bold"),
                        ft.Row([
                            ft.Text(f"{item['quantidade']} x R$ {item['preco_unitario']:.2f}", size=12),
                            ft.Text(f"R$ {item['subtotal']:.2f}", size=12, weight="bold"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ]),
                    padding=10,
                    bgcolor="#F5F5F5",
                    border_radius=5,
                    margin=ft.margin.only(bottom=5)
                )
            )
        
        # Totais
        self.comprovante_conteudo.controls.extend([
            ft.Divider(),
            ft.Row([
                ft.Text("Subtotal:", size=14),
                ft.Text(f"R$ {comprovante['subtotal']:.2f}", size=14, weight="bold"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ])
        
        if comprovante['desconto_total'] > 0:
            self.comprovante_conteudo.controls.append(
                ft.Row([
                    ft.Text("Desconto:", size=14, color="green"),
                    ft.Text(f"- R$ {comprovante['desconto_total']:.2f}", size=14, weight="bold", color="green"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )
        
        self.comprovante_conteudo.controls.extend([
            ft.Row([
                ft.Text("TOTAL:", size=18, weight="bold"),
                ft.Text(f"R$ {comprovante['valor_final']:.2f}", size=18, weight="bold", color="#0070C0"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
        ])
        
        # Pagamentos
        self.comprovante_conteudo.controls.append(
            ft.Text("Formas de Pagamento:", size=14, weight="bold")
        )
        
        for pagamento in comprovante['pagamentos']:
            forma_texto = {
                'dinheiro': 'Dinheiro',
                'cartao_credito': 'Cartão de Crédito',
                'cartao_debito': 'Cartão de Débito',
                'pix': 'PIX'
            }.get(pagamento['forma_pagamento'], pagamento['forma_pagamento'])
            
            texto_pagamento = f"{forma_texto}: R$ {pagamento['valor']:.2f}"
            
            if pagamento.get('numero_parcelas'):
                texto_pagamento += f" ({pagamento['numero_parcelas']}x de R$ {pagamento['valor'] / pagamento['numero_parcelas']:.2f})"
            
            if pagamento.get('valor_recebido'):
                texto_pagamento += f" | Recebido: R$ {pagamento['valor_recebido']:.2f}"
            
            if pagamento.get('troco'):
                texto_pagamento += f" | Troco: R$ {pagamento['troco']:.2f}"
            
            self.comprovante_conteudo.controls.append(
                ft.Text(texto_pagamento, size=14)
            )
        
        # Abrir modal
        self.modal_comprovante.open = True
        self.page.update()
    
    def _fechar_modal_comprovante(self):
        """Fecha o modal de comprovante."""
        self.modal_comprovante.open = False
        self.page.update()
    
    def _exportar_pdf(self):
        """Exporta o comprovante para PDF."""
        import os
        from datetime import datetime
        
        # Criar diretório de comprovantes se não existir
        if not os.path.exists("comprovantes"):
            os.makedirs("comprovantes")
        
        # Gerar nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho = f"comprovantes/venda_{self.venda_id_comprovante}_{timestamp}.pdf"
        
        # Exportar PDF
        sucesso = exportar_comprovante_pdf(self.venda_id_comprovante, caminho)
        
        if sucesso:
            self._mostrar_snackbar(f"✅ PDF exportado: {caminho}", "green")
        else:
            self._mostrar_snackbar("❌ Erro ao exportar PDF", "red")
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _mostrar_snackbar(self, mensagem: str, cor: str):
        """Exibe uma mensagem SnackBar."""
        snackbar = ft.SnackBar(
            content=ft.Text(mensagem),
            bgcolor=cor
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
