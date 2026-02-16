import flet as ft
# Importamos a função do seu outro arquivo
from main import main as abrir_sistema_principal 

def main(page: ft.Page):
    page.title = "DEKIDS - Login"
    page.bgcolor = "white"
    
    # Mantendo suas configurações de alinhamento padrão que deram certo
    page.vertical_alignment = "start"
    page.horizontal_alignment = "start"
    
    txt_senha = ft.TextField(label="Senha", password=True, width=300)
    lbl_erro = ft.Text("", color="red")
    
    def logar(e):
        if txt_senha.value == "1234":
            page.clean()
            # Chama a função do seu arquivo main.py passando a página atual
            abrir_sistema_principal(page)
        else:
            lbl_erro.value = "Senha Errada"
            page.update()

    page.add(
        ft.Text("ACESSO RESTRITO", size=20, weight="bold"),
        txt_senha,
        lbl_erro,
        ft.ElevatedButton("ENTRAR", on_click=logar)
    )

if __name__ == "__main__":
    # Mantendo a abertura no navegador para evitar a tela cinza
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)