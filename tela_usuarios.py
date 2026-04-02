"""
Tela de Gerenciamento de Usuários
Permite cadastrar, listar, editar e excluir usuários (apenas para admin)
"""

import flet as ft
import database as db


class TelaUsuarios:
    def __init__(self, page: ft.Page, usuario_id: int, usuario_nome: str, usuario_role: str):
        self.page = page
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        self.usuario_role = usuario_role
        
        # Lista de usuários
        self.lista_usuarios = []
        
        # Campos do formulário
        self.txt_username = ft.TextField(label="Nome de Usuário", width=300)
        self.txt_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300)
        self.txt_confirmar_senha = ft.TextField(label="Confirmar Senha", password=True, can_reveal_password=True, width=300)
        self.dropdown_role = ft.Dropdown(
            label="Nível de Acesso",
            width=300,
            options=[
                ft.dropdown.Option("admin", "Admin - Acesso Total"),
                ft.dropdown.Option("manager", "Gerente - Acesso a Relatórios"),
                ft.dropdown.Option("user", "Usuário - Acesso Básico"),
            ],
            value="user"
        )
        
        self.lbl_mensagem = ft.Text("", size=14)
        self.container_lista = ft.Column([], scroll="auto")
        
    def build(self):
        """Constrói a interface da tela de usuários"""
        
        # Verificar se usuário é admin
        if self.usuario_role != "admin":
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.LOCK, size=64, color="red"),
                    ft.Text("Acesso Negado", size=24, weight="bold", color="red"),
                    ft.Text("Apenas administradores podem acessar esta área.", size=16),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=50,
                alignment=ft.alignment.center
            )
        
        return ft.Column([
            ft.Text("👥 GERENCIAMENTO DE USUÁRIOS", size=24, weight="bold", color="#0070C0"),
            ft.Divider(),
            
            # Formulário de cadastro
            ft.Container(
                content=ft.Column([
                    ft.Text("➕ Cadastrar Novo Usuário", size=18, weight="bold"),
                    self.txt_username,
                    self.txt_senha,
                    self.txt_confirmar_senha,
                    self.dropdown_role,
                    self.lbl_mensagem,
                    ft.Row([
                        ft.ElevatedButton(
                            "Cadastrar Usuário",
                            on_click=self.cadastrar_usuario,
                            bgcolor="#0070C0",
                            color="white"
                        ),
                        ft.ElevatedButton(
                            "Limpar",
                            on_click=self.limpar_formulario,
                            bgcolor="#666",
                            color="white"
                        ),
                    ]),
                ], spacing=10),
                bgcolor="#F5F5F5",
                padding=20,
                border_radius=10,
            ),
            
            ft.Divider(height=30),
            
            # Lista de usuários
            ft.Text("📋 Usuários Cadastrados", size=18, weight="bold"),
            ft.ElevatedButton(
                "🔄 Atualizar Lista",
                on_click=lambda _: self.carregar_usuarios(),
                bgcolor="#4CAF50",
                color="white"
            ),
            self.container_lista,
        ], scroll="auto", spacing=15)
    
    def limpar_formulario(self, e=None):
        """Limpa os campos do formulário"""
        self.txt_username.value = ""
        self.txt_senha.value = ""
        self.txt_confirmar_senha.value = ""
        self.dropdown_role.value = "user"
        self.lbl_mensagem.value = ""
        self.lbl_mensagem.color = "black"
        self.page.update()
    
    def cadastrar_usuario(self, e):
        """Cadastra um novo usuário"""
        username = self.txt_username.value.strip()
        senha = self.txt_senha.value
        confirmar_senha = self.txt_confirmar_senha.value
        role = self.dropdown_role.value
        
        # Validações
        if not username:
            self.lbl_mensagem.value = "❌ Nome de usuário é obrigatório"
            self.lbl_mensagem.color = "red"
            self.page.update()
            return
        
        if not senha:
            self.lbl_mensagem.value = "❌ Senha é obrigatória"
            self.lbl_mensagem.color = "red"
            self.page.update()
            return
        
        if len(senha) < 4:
            self.lbl_mensagem.value = "❌ Senha deve ter pelo menos 4 caracteres"
            self.lbl_mensagem.color = "red"
            self.page.update()
            return
        
        if senha != confirmar_senha:
            self.lbl_mensagem.value = "❌ As senhas não coincidem"
            self.lbl_mensagem.color = "red"
            self.page.update()
            return
        
        # Cadastrar usuário
        sucesso, mensagem = db.criar_usuario(username, senha, role)
        
        if sucesso:
            self.lbl_mensagem.value = f"✅ {mensagem}"
            self.lbl_mensagem.color = "green"
            self.limpar_formulario()
            self.carregar_usuarios()
        else:
            self.lbl_mensagem.value = f"❌ {mensagem}"
            self.lbl_mensagem.color = "red"
        
        self.page.update()
    
    def carregar_usuarios(self):
        """Carrega a lista de usuários"""
        self.lista_usuarios = db.listar_usuarios()
        
        # Limpar container
        self.container_lista.controls.clear()
        
        if not self.lista_usuarios:
            self.container_lista.controls.append(
                ft.Text("Nenhum usuário encontrado", color="gray", italic=True)
            )
        else:
            # Criar cards para cada usuário
            for usuario in self.lista_usuarios:
                card = self.criar_card_usuario(usuario)
                self.container_lista.controls.append(card)
        
        self.page.update()
    
    def criar_card_usuario(self, usuario):
        """Cria um card para exibir informações do usuário"""
        user_id = usuario.get('id')
        username = usuario.get('username', 'N/A')
        role = usuario.get('role', 'user')
        ativo = usuario.get('ativo', False) or usuario.get('is_active', False)
        
        # Mapear roles para nomes amigáveis
        role_map = {
            'admin': '👑 Admin',
            'manager': '📊 Gerente',
            'user': '👤 Usuário'
        }
        role_display = role_map.get(role, role)
        
        # Cor do status
        status_color = "green" if ativo else "red"
        status_text = "Ativo" if ativo else "Inativo"
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(f"🆔 {username}", size=16, weight="bold"),
                    ft.Text(f"{role_display}", size=14),
                    ft.Text(f"Status: {status_text}", size=12, color=status_color),
                ], spacing=5),
                ft.Row([
                    ft.IconButton(
                        icon=ft.icons.EDIT,
                        tooltip="Alterar Role",
                        on_click=lambda _, uid=user_id: self.alterar_role(uid),
                        icon_color="#0070C0"
                    ),
                    ft.IconButton(
                        icon=ft.icons.POWER_SETTINGS_NEW if ativo else ft.icons.CHECK_CIRCLE,
                        tooltip="Ativar/Desativar",
                        on_click=lambda _, uid=user_id, a=ativo: self.toggle_ativo(uid, a),
                        icon_color="orange"
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        tooltip="Excluir",
                        on_click=lambda _, uid=user_id, uname=username: self.confirmar_exclusao(uid, uname),
                        icon_color="red"
                    ),
                ], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor="#F5F5F5",
            padding=15,
            border_radius=10,
            border=ft.border.all(1, "#E0E0E0"),
        )
    
    def alterar_role(self, usuario_id):
        """Abre diálogo para alterar o role do usuário"""
        dropdown_novo_role = ft.Dropdown(
            label="Novo Nível de Acesso",
            width=300,
            options=[
                ft.dropdown.Option("admin", "Admin - Acesso Total"),
                ft.dropdown.Option("manager", "Gerente - Acesso a Relatórios"),
                ft.dropdown.Option("user", "Usuário - Acesso Básico"),
            ],
        )
        
        def confirmar_alteracao(e):
            novo_role = dropdown_novo_role.value
            if not novo_role:
                return
            
            sucesso, mensagem = db.atualizar_role_usuario(usuario_id, novo_role)
            
            if sucesso:
                self.page.dialog.open = False
                self.carregar_usuarios()
                self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {mensagem}"), bgcolor="green")
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"❌ {mensagem}"), bgcolor="red")
                self.page.snack_bar.open = True
            
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Alterar Nível de Acesso"),
            content=dropdown_novo_role,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.fechar_dialog()),
                ft.ElevatedButton("Confirmar", on_click=confirmar_alteracao, bgcolor="#0070C0", color="white"),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def toggle_ativo(self, usuario_id, ativo_atual):
        """Ativa ou desativa um usuário"""
        novo_status = not ativo_atual
        sucesso, mensagem = db.ativar_desativar_usuario(usuario_id, novo_status)
        
        if sucesso:
            self.carregar_usuarios()
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {mensagem}"), bgcolor="green")
        else:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"❌ {mensagem}"), bgcolor="red")
        
        self.page.snack_bar.open = True
        self.page.update()
    
    def confirmar_exclusao(self, usuario_id, username):
        """Abre diálogo de confirmação para excluir usuário"""
        def executar_exclusao(e):
            sucesso, mensagem = db.excluir_usuario(usuario_id)
            
            if sucesso:
                self.page.dialog.open = False
                self.carregar_usuarios()
                self.page.snack_bar = ft.SnackBar(ft.Text(f"✅ {mensagem}"), bgcolor="green")
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"❌ {mensagem}"), bgcolor="red")
                self.page.snack_bar.open = True
            
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("⚠️ Confirmar Exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir o usuário '{username}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.fechar_dialog()),
                ft.ElevatedButton("Excluir", on_click=executar_exclusao, bgcolor="red", color="white"),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def fechar_dialog(self):
        """Fecha o diálogo aberto"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()
