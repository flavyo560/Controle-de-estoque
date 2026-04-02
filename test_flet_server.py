import flet as ft

def main(page: ft.Page):
    page.title = "Teste Flet"
    page.add(
        ft.Text("✅ Servidor Flet funcionando!", size=30, color="green")
    )

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧪 TESTE DE SERVIDOR FLET")
    print("="*70)
    print("\n✅ Iniciando servidor de teste na porta 8001...")
    print("\n🌐 Acesse: http://localhost:8001")
    print("\n⚠️  Pressione CTRL+C para parar")
    print("="*70 + "\n")
    
    ft.app(target=main, port=8001, host="0.0.0.0", view=ft.AppView.WEB_BROWSER)
