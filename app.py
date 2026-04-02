import flet as ft
import os
import time
from datetime import datetime
import database as db

# Importar a função main do sistema principal
from main import main as main_sistema

def main(page: ft.Page):
    '''Aplicação unificada: Login -> Sistema Principal'''
    
    # ADICIONE ESTA LINHA PARA HABILITAR SCROLL GLOBAL
    page.scroll = ft.ScrollMode.ADAPTIVE

    page.title = "DEKIDS - Sistema de Gestão"
    page.bgcolor = "white"
    page.vertical_alignment = "start"
    page.horizontal_alignment = "start"
    
    # Variável para armazenar sessão
    sessao_atual = {"token": None, "usuario": None}
    
    def mostrar_login():
        '''Mostra a tela de login'''
        page.clean()
        
        # Campos de login
        txt_usuario = ft.TextField(label="Usuário", width=300, autofocus=True)
        txt_senha = ft.TextField(label="Senha", password=True, width=300, on_submit=lambda e: logar())
        lbl_erro = ft.Text("", color="red")
        
        def logar():
            '''Realiza login e abre sistema principal'''
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
                    
                    # Abrir sistema principal
                    abrir_sistema_principal()
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
        
        def mostrar_alterar_senha():
            '''Mostra tela de alteração de senha'''
            page.clean()
            
            txt_usuario_senha = ft.TextField(label="Usuário", width=300)
            txt_senha_antiga = ft.TextField(label="Senha Antiga", password=True, width=300)
            txt_senha_nova = ft.TextField(label="Senha Nova", password=True, width=300)
            txt_senha_confirma = ft.TextField(label="Confirmar Senha Nova", password=True, width=300)
            lbl_erro_senha = ft.Text("", color="red")
            lbl_sucesso_senha = ft.Text("", color="green")
            
            def alterar_senha():
                usuario = txt_usuario_senha.value
                senha_antiga = txt_senha_antiga.value
                senha_nova = txt_senha_nova.value
                senha_confirma = txt_senha_confirma.value
                
                lbl_erro_senha.value = ""
                lbl_sucesso_senha.value = ""
                
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
                
                sucesso_auth, msg_auth, dados_usuario = db.autenticar_usuario(usuario, senha_antiga)
                
                if not sucesso_auth:
                    lbl_erro_senha.value = "Usuário ou senha antiga incorretos"
                    page.update()
                    return
                
                sucesso, mensagem = db.alterar_senha(dados_usuario["id"], senha_antiga, senha_nova)
                
                if sucesso:
                    lbl_sucesso_senha.value = "✅ Senha alterada com sucesso!"
                    txt_usuario_senha.value = ""
                    txt_senha_antiga.value = ""
                    txt_senha_nova.value = ""
                    txt_senha_confirma.value = ""
                else:
                    lbl_erro_senha.value = mensagem
                
                page.update()
            
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("🔐 ALTERAR SENHA", size=24, weight="bold", color="#0070C0"),
                        ft.Divider(),
                        txt_usuario_senha,
                        txt_senha_antiga,
                        txt_senha_nova,
                        txt_senha_confirma,
                        lbl_erro_senha,
                        lbl_sucesso_senha,
                        ft.ElevatedButton("ALTERAR SENHA", on_click=lambda e: alterar_senha(), bgcolor="#0070C0", color="white"),
                        ft.TextButton("Voltar ao Login", on_click=lambda e: mostrar_login()),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                    padding=50,
                    alignment=ft.alignment.center
                )
            )
        
        # Montar tela de login
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("🧸 DEKIDS", size=32, weight="bold", color="#0070C0"),
                    ft.Text("Sistema de Gestão", size=18, color="#666"),
                    ft.Divider(height=30),
                    ft.Text("ACESSO RESTRITO", size=20, weight="bold"),
                    txt_usuario,
                    txt_senha,
                    lbl_erro,
                    ft.ElevatedButton("ENTRAR", on_click=lambda e: logar(), bgcolor="#0070C0", color="white", width=300),
                    ft.TextButton("Alterar Senha", on_click=lambda e: mostrar_alterar_senha()),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                padding=50,
                alignment=ft.alignment.center
            )
        )
    
    def abrir_sistema_principal():
        '''Abre o sistema principal após login bem-sucedido'''
        # Limpar página e chamar o main do sistema
        page.clean()
        
        # Chamar a função main do sistema principal passando a page e a sessão
        main_sistema(page, sessao_atual)
    
    # Verificar se já existe sessão ativa
    sucesso, mensagem, sessao = db.obter_sessao_ativa()
    
    if sucesso and sessao:
        # Já tem sessão ativa, ir direto para o sistema
        sessao_atual["token"] = sessao["token"]
        sessao_atual["usuario"] = sessao["usuario"]
        abrir_sistema_principal()
    else:
        # Não tem sessão, mostrar login
        mostrar_login()

if __name__ == "__main__":
    import webbrowser
    import threading
    
    port = int(os.getenv("PORT", 8000))
    print(f"\n{'='*70}")
    print(f"🧸 DEKIDS - Sistema de Gestão")
    print(f"{'='*70}")
    print(f"\n✅ Servidor iniciado com sucesso!")
    print(f"\n🌐 Acesse o sistema em seu navegador:")
    print(f"   http://localhost:{port}")
    print(f"   ou")
    print(f"   http://0.0.0.0:{port}")
    print(f"\n⚠️  Pressione CTRL+C para parar o servidor")
    print(f"{'='*70}\n")
    
    # Função para abrir o navegador após 2 segundos
    def abrir_navegador():
        time.sleep(2)
        webbrowser.open(f"http://localhost:{port}")
        print(f"🌐 Abrindo navegador em http://localhost:{port}...")
    
    # Iniciar thread para abrir navegador
    threading.Thread(target=abrir_navegador, daemon=True).start()
    
    # Iniciar servidor Flet
    ft.app(target=main, port=port, host="0.0.0.0", view=ft.AppView.WEB_BROWSER)
