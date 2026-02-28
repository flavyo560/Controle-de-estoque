import flet as ft
import os
from datetime import datetime
import database as db

# Variável global para armazenar sessão
sessao_atual = {
    "token": None,
    "usuario": None
}

def main(page: ft.Page):
    page.title = "DEKIDS - Login"
    page.bgcolor = "white"
    
    # Mantendo suas configurações de alinhamento padrão que deram certo
    page.vertical_alignment = "start"
    page.horizontal_alignment = "start"
    
    # Campos de login
    txt_usuario = ft.TextField(label="Usuário", width=300)
    txt_senha = ft.TextField(label="Senha", password=True, width=300)
    lbl_erro = ft.Text("", color="red")
    btn_entrar = ft.ElevatedButton("ENTRAR", on_click=lambda e: logar(e))
    btn_alterar_senha = ft.TextButton("Alterar Senha", on_click=lambda e: mostrar_tela_alterar_senha())
    
    # Campos de alteração de senha
    txt_usuario_senha = ft.TextField(label="Usuário", width=300)
    txt_senha_antiga = ft.TextField(label="Senha Antiga", password=True, width=300)
    txt_senha_nova = ft.TextField(label="Senha Nova", password=True, width=300)
    txt_senha_confirma = ft.TextField(label="Confirmar Senha Nova", password=True, width=300)
    lbl_erro_senha = ft.Text("", color="red")
    lbl_sucesso_senha = ft.Text("", color="green")
    
    def logar(e):
        """Realiza login com autenticação multi-usuário"""
        usuario = txt_usuario.value
        senha = txt_senha.value
        
        if not usuario or not senha:
            lbl_erro.value = "Por favor, preencha usuário e senha"
            page.update()
            return
        
        # Autenticar usuário
        sucesso, mensagem, dados_usuario = db.autenticar_usuario(usuario, senha)
        
        if sucesso:
            # Criar sessão
            sucesso_sessao, msg_sessao, token = db.criar_sessao(dados_usuario["id"])
            
            if sucesso_sessao:
                # Registrar acesso
                db.registrar_acesso(dados_usuario["id"])
                
                # Armazenar sessão
                sessao_atual["token"] = token
                sessao_atual["usuario"] = dados_usuario
                
                # Mostrar mensagem de sucesso e instruções
                page.clean()
                page.add(
                    ft.Container(
                        content=ft.Column([
                            ft.Text("✅ Login realizado com sucesso!", size=24, weight="bold", color="green"),
                            ft.Text(f"Bem-vindo, {dados_usuario['username']}!", size=18),
                            ft.Divider(),
                            ft.Text("Para acessar o sistema:", size=16, weight="bold"),
                            ft.Text("1. Feche esta janela", size=14),
                            ft.Text("2. Execute: python main.py", size=14, color="blue", weight="bold"),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                        padding=50,
                        alignment=ft.alignment.center
                    )
                )
                page.update()
            else:
                lbl_erro.value = "Erro ao criar sessão. Tente novamente."
                page.update()
        else:
            # Mensagens de erro específicas
            if "bloqueado" in mensagem.lower():
                lbl_erro.value = mensagem
            elif "credenciais inválidas" in mensagem.lower():
                lbl_erro.value = "Usuário ou senha incorretos"
            else:
                lbl_erro.value = mensagem
            page.update()
    
    def alterar_senha_usuario(e):
        """Altera a senha do usuário"""
        usuario = txt_usuario_senha.value
        senha_antiga = txt_senha_antiga.value
        senha_nova = txt_senha_nova.value
        senha_confirma = txt_senha_confirma.value
        
        # Limpar mensagens
        lbl_erro_senha.value = ""
        lbl_sucesso_senha.value = ""
        
        # Validações
        if not usuario or not senha_antiga or not senha_nova or not senha_confirma:
            lbl_erro_senha.value = "Por favor, preencha todos os campos"
            page.update()
            return
        
        if senha_nova != senha_confirma:
            lbl_erro_senha.value = "As senhas novas não coincidem"
            page.update()
            return
        
        if len(senha_nova) < 4:
            lbl_erro_senha.value = "A senha nova deve ter pelo menos 4 caracteres"
            page.update()
            return
        
        # Primeiro autenticar para obter o ID do usuário
        sucesso_auth, msg_auth, dados_usuario = db.autenticar_usuario(usuario, senha_antiga)
        
        if not sucesso_auth:
            lbl_erro_senha.value = "Usuário ou senha antiga incorretos"
            page.update()
            return
        
        # Alterar senha
        sucesso, mensagem = db.alterar_senha(dados_usuario["id"], senha_antiga, senha_nova)
        
        if sucesso:
            lbl_sucesso_senha.value = "Senha alterada com sucesso! Você pode fazer login agora."
            # Limpar campos
            txt_usuario_senha.value = ""
            txt_senha_antiga.value = ""
            txt_senha_nova.value = ""
            txt_senha_confirma.value = ""
        else:
            lbl_erro_senha.value = mensagem
        
        page.update()
    
    def mostrar_tela_login():
        """Mostra a tela de login"""
        page.clean()
        page.add(
            ft.Text("ACESSO RESTRITO", size=20, weight="bold"),
            txt_usuario,
            txt_senha,
            lbl_erro,
            btn_entrar,
            btn_alterar_senha
        )
    
    def mostrar_tela_alterar_senha():
        """Mostra a tela de alteração de senha"""
        page.clean()
        page.add(
            ft.Text("ALTERAR SENHA", size=20, weight="bold"),
            txt_usuario_senha,
            txt_senha_antiga,
            txt_senha_nova,
            txt_senha_confirma,
            lbl_erro_senha,
            lbl_sucesso_senha,
            ft.ElevatedButton("ALTERAR SENHA", on_click=alterar_senha_usuario),
            ft.TextButton("Voltar ao Login", on_click=lambda e: mostrar_tela_login())
        )
    
    # Mostrar tela de login inicial
    mostrar_tela_login()

def obter_sessao_atual():
    """Retorna a sessão atual"""
    return sessao_atual

def encerrar_sessao_atual():
    """Encerra a sessão atual"""
    if sessao_atual["token"]:
        db.encerrar_sessao(sessao_atual["token"])
        sessao_atual["token"] = None
        sessao_atual["usuario"] = None

if __name__ == "__main__":
    # Mantendo a abertura no navegador para evitar a tela cinza
    port = int(os.getenv("PORT", 8000))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port)
