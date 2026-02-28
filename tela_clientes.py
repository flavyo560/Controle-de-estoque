"""
Tela de Gestão de Clientes - Sistema de Vendas DEKIDS

Interface completa de gestão de clientes com:
- Busca e listagem de clientes
- Cadastro e edição de clientes
- Visualização de histórico de compras
- Métricas do cliente
"""

import flet as ft
from typing import Optional, Dict, List
from clientes import buscar_clientes, cadastrar_cliente, editar_cliente, obter_cliente, obter_historico_compras
from datetime import datetime


class TelaClientes:
    """
    Classe principal da tela de gestão de clientes.
    
    Gerencia toda a interface de clientes incluindo busca, cadastro,
    edição e visualização de histórico de compras.
    """
    
    def __init__(self, page: ft.Page, usuario_id: int, usuario_nome: str):
        """
        Inicializa a tela de gestão de clientes.
        
        Args:
            page: Instância da página Flet
            usuario_id: ID do usuário autenticado
            usuario_nome: Nome do usuário autenticado
        """
        self.page = page
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        
        # Cliente selecionado para edição
        self.cliente_selecionado: Optional[Dict] = None
        
        # Modo do formulário: 'cadastro' ou 'edicao'
        self.modo_formulario = 'cadastro'
        
        # Criar componentes da interface
        self._criar_componentes()
    
    def _criar_componentes(self):
        """Cria todos os componentes da interface."""
        # ========== COMPONENTES DE BUSCA ==========
        self.txt_busca = ft.TextField(
            label="Buscar Cliente",
            hint_text="Digite CPF, nome ou telefone",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_submit=lambda e: self._buscar_clientes()
        )
        
        self.btn_buscar = ft.ElevatedButton(
            "Buscar",
            icon=ft.icons.SEARCH,
            bgcolor="#0070C0",
            color="white",
            on_click=lambda e: self._buscar_clientes()
        )
        
        self.btn_limpar_busca = ft.IconButton(
            icon=ft.icons.CLEAR,
            icon_color="orange",
            tooltip="Limpar busca",
            on_click=lambda e: self._limpar_busca()
        )
        
        # Tabela de clientes
        self.tabela_clientes = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome", weight="bold")),
                ft.DataColumn(ft.Text("CPF", weight="bold")),
                ft.DataColumn(ft.Text("Telefone", weight="bold")),
                ft.DataColumn(ft.Text("Email", weight="bold")),
                ft.DataColumn(ft.Text("Ações", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        # ========== COMPONENTES DO FORMULÁRIO ==========
        self.txt_nome = ft.TextField(
            label="Nome Completo *",
            hint_text="Nome do cliente",
            prefix_icon=ft.icons.PERSON
        )
        
        self.txt_cpf = ft.TextField(
            label="CPF *",
            hint_text="000.000.000-00",
            prefix_icon=ft.icons.BADGE,
            max_length=14,
            on_change=lambda e: self._validar_cpf_tempo_real()
        )
        
        self.txt_telefone = ft.TextField(
            label="Telefone",
            hint_text="(00) 00000-0000",
            prefix_icon=ft.icons.PHONE
        )
        
        self.txt_email = ft.TextField(
            label="Email",
            hint_text="email@exemplo.com",
            prefix_icon=ft.icons.EMAIL,
            on_change=lambda e: self._validar_email_tempo_real()
        )
        
        # Campos de endereço
        self.txt_endereco_rua = ft.TextField(
            label="Logradouro",
            hint_text="Rua, Avenida...",
            prefix_icon=ft.icons.HOME
        )
        
        self.txt_endereco_numero = ft.TextField(
            label="Número",
            hint_text="123",
            width=100
        )
        
        self.txt_endereco_complemento = ft.TextField(
            label="Complemento",
            hint_text="Apto, Bloco...",
            width=200
        )
        
        self.txt_endereco_bairro = ft.TextField(
            label="Bairro",
            hint_text="Nome do bairro"
        )
        
        self.txt_endereco_cidade = ft.TextField(
            label="Cidade",
            hint_text="Nome da cidade"
        )
        
        self.txt_endereco_estado = ft.TextField(
            label="Estado",
            hint_text="UF",
            max_length=2,
            width=80
        )
        
        self.txt_endereco_cep = ft.TextField(
            label="CEP",
            hint_text="00000-000",
            max_length=9,
            width=120
        )
        
        # Mensagens de validação
        self.msg_validacao_cpf = ft.Text("", size=12, color="red", visible=False)
        self.msg_validacao_email = ft.Text("", size=12, color="red", visible=False)
        
        # Botões do formulário
        self.btn_salvar = ft.ElevatedButton(
            "Salvar Cliente",
            icon=ft.icons.SAVE,
            bgcolor="green",
            color="white",
            on_click=lambda e: self._salvar_cliente()
        )
        
        self.btn_limpar = ft.ElevatedButton(
            "Limpar Formulário",
            icon=ft.icons.CLEAR_ALL,
            bgcolor="orange",
            color="white",
            on_click=lambda e: self._limpar_formulario()
        )
        
        self.btn_cancelar_edicao = ft.ElevatedButton(
            "Cancelar Edição",
            icon=ft.icons.CANCEL,
            bgcolor="red",
            color="white",
            visible=False,
            on_click=lambda e: self._cancelar_edicao()
        )
        
        # Título do formulário
        self.titulo_formulario = ft.Text(
            "📝 Cadastrar Novo Cliente",
            size=18,
            weight="bold",
            color="#0070C0"
        )
        
        # ========== MODAL DE HISTÓRICO ==========
        self._criar_modal_historico()
    
    def _criar_modal_historico(self):
        """Cria o modal de histórico de compras."""
        self.historico_nome_cliente = ft.Text("", size=18, weight="bold")
        
        # Métricas do cliente
        self.historico_total_gasto = ft.Text("", size=16, weight="bold", color="green")
        self.historico_num_compras = ft.Text("", size=16, weight="bold", color="#0070C0")
        self.historico_ultima_compra = ft.Text("", size=14, italic=True)
        
        # Tabela de vendas
        self.tabela_historico_vendas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nº Venda", weight="bold")),
                ft.DataColumn(ft.Text("Data", weight="bold")),
                ft.DataColumn(ft.Text("Valor", weight="bold")),
                ft.DataColumn(ft.Text("Status", weight="bold")),
                ft.DataColumn(ft.Text("Ação", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5,
        )
        
        # Lista de produtos mais comprados
        self.lista_produtos_mais_comprados = ft.Column([], spacing=5)
        
        self.modal_historico = ft.AlertDialog(
            title=self.historico_nome_cliente,
            content=ft.Container(
                content=ft.Column([
                    # Métricas
                    ft.Container(
                        content=ft.Column([
                            ft.Text("📊 Métricas do Cliente", size=16, weight="bold", color="#0070C0"),
                            ft.Divider(),
                            self.historico_total_gasto,
                            self.historico_num_compras,
                            self.historico_ultima_compra,
                        ], spacing=5),
                        bgcolor="#F0F8FF",
                        padding=15,
                        border_radius=5,
                        border=ft.border.all(1, "#0070C0")
                    ),
                    ft.Divider(height=20),
                    # Histórico de vendas
                    ft.Text("🛍️ Histórico de Compras", size=16, weight="bold", color="#0070C0"),
                    ft.Container(
                        content=ft.Column([self.tabela_historico_vendas], scroll=ft.ScrollMode.AUTO),
                        height=200,
                        border=ft.border.all(1, "#EEEEEE"),
                        border_radius=5,
                        padding=10
                    ),
                    ft.Divider(height=20),
                    # Produtos mais comprados
                    ft.Text("⭐ Produtos Mais Comprados", size=16, weight="bold", color="#0070C0"),
                    ft.Container(
                        content=ft.Column([self.lista_produtos_mais_comprados], scroll=ft.ScrollMode.AUTO),
                        height=150,
                        border=ft.border.all(1, "#EEEEEE"),
                        border_radius=5,
                        padding=10
                    ),
                ], scroll=ft.ScrollMode.AUTO, spacing=10),
                width=700,
                height=700
            ),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: self._fechar_modal_historico()),
            ],
        )
        self.page.overlay.append(self.modal_historico)
    
    def build(self) -> ft.Container:
        """
        Constrói e retorna o layout completo da tela de clientes.
        
        Returns:
            Container com o layout completo em 2 colunas
        """
        # Coluna 1: Busca e Lista de Clientes
        coluna_busca = ft.Container(
            content=ft.Column([
                ft.Text("🔍 Buscar Clientes", size=18, weight="bold", color="#0070C0"),
                ft.Divider(),
                ft.Row([
                    self.txt_busca,
                    self.btn_buscar,
                    self.btn_limpar_busca
                ], spacing=5),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([self.tabela_clientes], scroll=ft.ScrollMode.ALWAYS),
                    height=600,
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
        
        # Coluna 2: Formulário de Cadastro/Edição
        coluna_formulario = ft.Container(
            content=ft.Column([
                self.titulo_formulario,
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        # Dados básicos
                        ft.Text("Dados Básicos", weight="bold", size=14),
                        self.txt_nome,
                        self.txt_cpf,
                        self.msg_validacao_cpf,
                        self.txt_telefone,
                        self.txt_email,
                        self.msg_validacao_email,
                        ft.Divider(height=20),
                        # Endereço
                        ft.Text("Endereço (opcional)", weight="bold", size=14),
                        self.txt_endereco_rua,
                        ft.Row([
                            self.txt_endereco_numero,
                            self.txt_endereco_complemento
                        ], spacing=10),
                        self.txt_endereco_bairro,
                        ft.Row([
                            self.txt_endereco_cidade,
                            self.txt_endereco_estado
                        ], spacing=10),
                        self.txt_endereco_cep,
                    ], spacing=10, scroll=ft.ScrollMode.AUTO),
                    height=550,
                ),
                ft.Divider(),
                # Botões
                ft.Row([
                    self.btn_salvar,
                    self.btn_limpar,
                    self.btn_cancelar_edicao
                ], spacing=10),
            ], spacing=10),
            padding=15,
            bgcolor="white",
            border_radius=10,
            expand=1
        )
        
        # Layout principal com 2 colunas
        layout = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Container(
                    content=ft.Row([
                        ft.Text("👥 Gestão de Clientes", size=24, weight="bold", color="white"),
                        ft.Text(f"Usuário: {self.usuario_nome}", size=14, color="white", italic=True),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#0070C0",
                    padding=15,
                    border_radius=10
                ),
                # Conteúdo em 2 colunas
                ft.Row([
                    coluna_busca,
                    coluna_formulario,
                ], spacing=10, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
            ], spacing=10, expand=True),
            padding=20,
            expand=True
        )
        
        return layout

    
    # ========== MÉTODOS DE BUSCA ==========
    
    def _buscar_clientes(self):
        """Busca clientes e exibe na tabela."""
        termo = self.txt_busca.value
        
        if not termo or not termo.strip():
            self._mostrar_snackbar("Digite um termo de busca", "orange")
            return
        
        # Buscar clientes
        clientes = buscar_clientes(termo)
        
        # Limpar tabela
        self.tabela_clientes.rows.clear()
        
        if not clientes:
            self._mostrar_snackbar("Nenhum cliente encontrado", "orange")
            self.page.update()
            return
        
        # Preencher tabela com clientes encontrados
        for cliente in clientes:
            self.tabela_clientes.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(cliente['nome'][:30])),
                        ft.DataCell(ft.Text(self._formatar_cpf(cliente['cpf']))),
                        ft.DataCell(ft.Text(cliente.get('telefone', '-')[:15])),
                        ft.DataCell(ft.Text(cliente.get('email', '-')[:25])),
                        ft.DataCell(
                            ft.Row([
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    icon_color="blue",
                                    tooltip="Editar cliente",
                                    on_click=lambda e, c=cliente: self._editar_cliente(c)
                                ),
                                ft.IconButton(
                                    icon=ft.icons.HISTORY,
                                    icon_color="purple",
                                    tooltip="Ver histórico",
                                    on_click=lambda e, c=cliente: self._abrir_historico(c)
                                ),
                            ], spacing=0)
                        ),
                    ]
                )
            )
        
        self._mostrar_snackbar(f"{len(clientes)} cliente(s) encontrado(s)", "green")
        self.page.update()
    
    def _limpar_busca(self):
        """Limpa a busca e a tabela de clientes."""
        self.txt_busca.value = ""
        self.tabela_clientes.rows.clear()
        self.page.update()
    
    # ========== MÉTODOS DO FORMULÁRIO ==========
    
    def _validar_cpf_tempo_real(self):
        """Valida CPF em tempo real enquanto o usuário digita."""
        from validacao_vendas import validar_cpf
        
        cpf = self.txt_cpf.value
        
        if not cpf or len(cpf) < 11:
            self.msg_validacao_cpf.visible = False
            self.page.update()
            return
        
        valido, mensagem = validar_cpf(cpf)
        
        if not valido:
            self.msg_validacao_cpf.value = f"❌ {mensagem}"
            self.msg_validacao_cpf.visible = True
        else:
            self.msg_validacao_cpf.value = "✅ CPF válido"
            self.msg_validacao_cpf.color = "green"
            self.msg_validacao_cpf.visible = True
        
        self.page.update()
    
    def _validar_email_tempo_real(self):
        """Valida email em tempo real enquanto o usuário digita."""
        from validacao_vendas import validar_email
        
        email = self.txt_email.value
        
        if not email or len(email) < 3:
            self.msg_validacao_email.visible = False
            self.page.update()
            return
        
        valido, mensagem = validar_email(email)
        
        if not valido:
            self.msg_validacao_email.value = f"❌ {mensagem}"
            self.msg_validacao_email.visible = True
        else:
            self.msg_validacao_email.value = "✅ Email válido"
            self.msg_validacao_email.color = "green"
            self.msg_validacao_email.visible = True
        
        self.page.update()
    
    def _salvar_cliente(self):
        """Salva um novo cliente ou edita um existente."""
        # Validar campos obrigatórios
        if not self.txt_nome.value or not self.txt_nome.value.strip():
            self._mostrar_snackbar("❌ Nome é obrigatório", "red")
            return
        
        if not self.txt_cpf.value or not self.txt_cpf.value.strip():
            self._mostrar_snackbar("❌ CPF é obrigatório", "red")
            return
        
        # Preparar dados do cliente
        dados_cliente = {
            'nome': self.txt_nome.value.strip(),
            'cpf': self.txt_cpf.value.strip(),
            'telefone': self.txt_telefone.value.strip() if self.txt_telefone.value else None,
            'email': self.txt_email.value.strip() if self.txt_email.value else None,
            'endereco_logradouro': self.txt_endereco_rua.value.strip() if self.txt_endereco_rua.value else None,
            'endereco_numero': self.txt_endereco_numero.value.strip() if self.txt_endereco_numero.value else None,
            'endereco_complemento': self.txt_endereco_complemento.value.strip() if self.txt_endereco_complemento.value else None,
            'endereco_bairro': self.txt_endereco_bairro.value.strip() if self.txt_endereco_bairro.value else None,
            'endereco_cidade': self.txt_endereco_cidade.value.strip() if self.txt_endereco_cidade.value else None,
            'endereco_estado': self.txt_endereco_estado.value.strip().upper() if self.txt_endereco_estado.value else None,
            'endereco_cep': self.txt_endereco_cep.value.strip() if self.txt_endereco_cep.value else None,
        }
        
        if self.modo_formulario == 'cadastro':
            # Cadastrar novo cliente
            sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
            
            if sucesso:
                self._mostrar_snackbar(f"✅ {mensagem}", "green")
                self._limpar_formulario()
                # Atualizar busca se houver termo
                if self.txt_busca.value:
                    self._buscar_clientes()
            else:
                self._mostrar_snackbar(f"❌ {mensagem}", "red")
        
        else:  # modo_formulario == 'edicao'
            # Editar cliente existente
            sucesso, mensagem = editar_cliente(self.cliente_selecionado['id'], dados_cliente)
            
            if sucesso:
                self._mostrar_snackbar(f"✅ {mensagem}", "green")
                self._cancelar_edicao()
                # Atualizar busca se houver termo
                if self.txt_busca.value:
                    self._buscar_clientes()
            else:
                self._mostrar_snackbar(f"❌ {mensagem}", "red")
    
    def _limpar_formulario(self):
        """Limpa todos os campos do formulário."""
        self.txt_nome.value = ""
        self.txt_cpf.value = ""
        self.txt_telefone.value = ""
        self.txt_email.value = ""
        self.txt_endereco_rua.value = ""
        self.txt_endereco_numero.value = ""
        self.txt_endereco_complemento.value = ""
        self.txt_endereco_bairro.value = ""
        self.txt_endereco_cidade.value = ""
        self.txt_endereco_estado.value = ""
        self.txt_endereco_cep.value = ""
        
        self.msg_validacao_cpf.visible = False
        self.msg_validacao_email.visible = False
        
        # Resetar para modo cadastro
        self.modo_formulario = 'cadastro'
        self.cliente_selecionado = None
        self.titulo_formulario.value = "📝 Cadastrar Novo Cliente"
        self.btn_salvar.text = "Salvar Cliente"
        self.btn_cancelar_edicao.visible = False
        
        self.page.update()
    
    def _editar_cliente(self, cliente: Dict):
        """Carrega dados do cliente no formulário para edição."""
        self.cliente_selecionado = cliente
        self.modo_formulario = 'edicao'
        
        # Preencher campos com dados do cliente
        self.txt_nome.value = cliente.get('nome', '')
        self.txt_cpf.value = self._formatar_cpf(cliente.get('cpf', ''))
        self.txt_telefone.value = cliente.get('telefone', '')
        self.txt_email.value = cliente.get('email', '')
        self.txt_endereco_rua.value = cliente.get('endereco_rua', '') or cliente.get('endereco_logradouro', '')
        self.txt_endereco_numero.value = cliente.get('endereco_numero', '')
        self.txt_endereco_complemento.value = cliente.get('endereco_complemento', '')
        self.txt_endereco_bairro.value = cliente.get('endereco_bairro', '')
        self.txt_endereco_cidade.value = cliente.get('endereco_cidade', '')
        self.txt_endereco_estado.value = cliente.get('endereco_estado', '')
        self.txt_endereco_cep.value = cliente.get('endereco_cep', '')
        
        # Atualizar interface
        self.titulo_formulario.value = f"✏️ Editar Cliente: {cliente.get('nome', '')}"
        self.btn_salvar.text = "Salvar Alterações"
        self.btn_cancelar_edicao.visible = True
        
        self.msg_validacao_cpf.visible = False
        self.msg_validacao_email.visible = False
        
        self._mostrar_snackbar(f"Editando cliente: {cliente.get('nome', '')}", "#0070C0")
        self.page.update()
    
    def _cancelar_edicao(self):
        """Cancela a edição e volta para modo cadastro."""
        self._limpar_formulario()
        self._mostrar_snackbar("Edição cancelada", "black")
    
    # ========== MÉTODOS DE HISTÓRICO ==========
    
    def _abrir_historico(self, cliente: Dict):
        """Abre o modal de histórico de compras do cliente."""
        # Obter histórico completo
        historico = obter_historico_compras(cliente['id'])
        
        # Atualizar nome do cliente
        self.historico_nome_cliente.value = f"👤 {cliente['nome']}"
        
        # Atualizar métricas
        self.historico_total_gasto.value = f"💰 Total Gasto: R$ {historico['valor_total_gasto']:.2f}"
        self.historico_num_compras.value = f"🛍️ Número de Compras: {historico['numero_compras']}"
        
        if historico['data_ultima_compra']:
            data_formatada = self._formatar_data(historico['data_ultima_compra'])
            self.historico_ultima_compra.value = f"📅 Última Compra: {data_formatada}"
        else:
            self.historico_ultima_compra.value = "📅 Nenhuma compra realizada"
        
        # Limpar e preencher tabela de vendas
        self.tabela_historico_vendas.rows.clear()
        
        for venda in historico['vendas']:
            status_cor = "green" if venda['status'] == 'finalizada' else "red"
            status_texto = "Finalizada" if venda['status'] == 'finalizada' else "Cancelada"
            
            self.tabela_historico_vendas.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"#{venda['id']}")),
                        ft.DataCell(ft.Text(self._formatar_data(venda['data_hora']))),
                        ft.DataCell(ft.Text(f"R$ {venda['valor_final']:.2f}", weight="bold")),
                        ft.DataCell(ft.Text(status_texto, color=status_cor)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.icons.VISIBILITY,
                                icon_color="#0070C0",
                                tooltip="Ver detalhes",
                                on_click=lambda e, v=venda: self._ver_detalhes_venda(v)
                            )
                        ),
                    ]
                )
            )
        
        # Limpar e preencher produtos mais comprados
        self.lista_produtos_mais_comprados.controls.clear()
        
        if historico['produtos_mais_comprados']:
            for i, produto in enumerate(historico['produtos_mais_comprados'][:5], 1):  # Top 5
                self.lista_produtos_mais_comprados.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"{i}.", weight="bold", size=14),
                            ft.Column([
                                ft.Text(produto['descricao'][:40], size=14, weight="bold"),
                                ft.Text(f"Ref: {produto['referencia']} | Quantidade: {produto['quantidade_total']}", size=12, color="gray"),
                            ], spacing=2, expand=True),
                        ], spacing=10),
                        padding=10,
                        bgcolor="#F5F5F5",
                        border_radius=5,
                        border=ft.border.all(1, "#EEEEEE")
                    )
                )
        else:
            self.lista_produtos_mais_comprados.controls.append(
                ft.Text("Nenhum produto comprado ainda", italic=True, color="gray")
            )
        
        # Abrir modal
        self.modal_historico.open = True
        self.page.update()
    
    def _fechar_modal_historico(self):
        """Fecha o modal de histórico."""
        self.modal_historico.open = False
        self.page.update()
    
    def _ver_detalhes_venda(self, venda: Dict):
        """Exibe detalhes de uma venda específica."""
        # TODO: Implementar visualização de detalhes da venda
        # Por enquanto, apenas mostra uma mensagem
        self._mostrar_snackbar(f"Detalhes da venda #{venda['id']}", "#0070C0")
    
    # ========== MÉTODOS AUXILIARES ==========
    
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
    
    def _formatar_data(self, data_str: str) -> str:
        """Formata data para exibição (DD/MM/YYYY HH:MM)."""
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
    
    def _mostrar_snackbar(self, mensagem: str, cor: str):
        """Exibe uma mensagem SnackBar."""
        snackbar = ft.SnackBar(
            content=ft.Text(mensagem),
            bgcolor=cor
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
