import flet as ft
import os
from database import cadastrar_produto, listar_estoque, excluir_produto, registrar_saida, registrar_entrada, registrar_estorno

def main(page: ft.Page):
    # --- CONFIGURAÇÃO DA PÁGINA ---
    page.title = "DEKIDS Moda Infantil"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "white"
    page.padding = 20
    # Alinhamento no canto superior esquerdo (topo)
    page.vertical_alignment = "start"
    page.horizontal_alignment = "start"
    page.scroll = "adaptive"

    # --- CAMPOS DE ENTRADA DO SEU PROJETO ---
    txt_descricao = ft.TextField(label="Descrição da Peça", hint_text="Ex: Conjunto Moletom")
    txt_genero = ft.Dropdown(
        label="Gênero",
        options=[ft.dropdown.Option("Masculino"), ft.dropdown.Option("Feminino"), ft.dropdown.Option("Unissex")]
    )
    txt_marca = ft.TextField(label="Marca")
    txt_referencia = ft.TextField(label="Referência")
    txt_tamanho = ft.TextField(label="Tamanho")
    txt_qtd = ft.TextField(label="Quantidade", value="0")
    txt_preco = ft.TextField(label="Preço", prefix=ft.Text("R$ "))

    txt_busca = ft.TextField(
        label="Pesquisar produto...",
        prefix_icon="search",
        on_change=lambda e: atualizar_lista_visual(e.control.value)
    )

    lista_produtos = ft.Column(spacing=10)

    # Funções de ação do estoque
    def acao_estoque(func, id_p, qtd_p, msg, cor):
        if func(id_p, qtd_p):
            atualizar_lista_visual(txt_busca.value)
            snack = ft.SnackBar(ft.Text(msg), bgcolor=cor)
            page.overlay.append(snack)
            snack.open = True
            page.update()

    def deletar_item(id_p):
        excluir_produto(id_p)
        atualizar_lista_visual(txt_busca.value)
        snack = ft.SnackBar(ft.Text("Produto removido!"), bgcolor="black")
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def atualizar_lista_visual(filtro=""):
        lista_produtos.controls.clear()
        try:
            produtos = listar_estoque()
            if produtos:
                produtos_filtrados = [p for p in produtos if filtro.lower() in p['descricao'].lower()]
                for p in produtos_filtrados:
                    lista_produtos.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(f"{p['descricao']}".upper(), weight="bold", size=16),
                                    ft.Text(f"Ref: {p['referencia']} | Tam: {p['tamanho']}", size=13),
                                    ft.Text(f"Qtd: {p['quantidade']} | R$ {p['preco']}", color="#0070C0", weight="bold"),
                                ], expand=True, spacing=2),
                                ft.Row([
                                    ft.ElevatedButton("+", bgcolor="green", color="white", on_click=lambda _, id=p['id'], q=p['quantidade']: acao_estoque(registrar_entrada, id, q, "Entrada +1", "green")),
                                    ft.ElevatedButton("-", bgcolor="blue", color="white", on_click=lambda _, id=p['id'], q=p['quantidade']: acao_estoque(registrar_saida, id, q, "Saída -1", "blue")),
                                    ft.ElevatedButton("🗑️", bgcolor="red", color="white", on_click=lambda _, id=p['id']: deletar_item(id)),
                                ], spacing=5)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=15, border=ft.Border.all(1, "#EEEEEE"), border_radius=10, bgcolor="white"
                        )
                    )
            else:
                lista_produtos.controls.append(ft.Text("Nenhum produto encontrado."))
        except Exception as ex:
            print(f"Erro Visual: {ex}")
        page.update()

    def salvar_clicado(e):
        try:
            cadastrar_produto(
                txt_descricao.value, txt_genero.value, txt_marca.value,
                txt_referencia.value, txt_tamanho.value, 
                int(txt_qtd.value), float(txt_preco.value.replace(",", "."))
            )
            for f in [txt_descricao, txt_marca, txt_referencia, txt_tamanho, txt_preco]: f.value = ""
            txt_qtd.value = "0"
            atualizar_lista_visual()
            page.update()
        except:
            pass

    # Conteúdos das abas
    container_cadastro = ft.Column([
        ft.Text("Cadastrar Novo Item", size=20, weight="bold", color="#E91E63"),
        txt_descricao,
        ft.Row([txt_genero, txt_tamanho]),
        ft.Row([txt_marca, txt_referencia]),
        ft.Row([txt_qtd, txt_preco]),
        ft.ElevatedButton("SALVAR PRODUTO", on_click=salvar_clicado, bgcolor="#0070C0", color="white", width=400),
    ], visible=True)

    container_estoque = ft.Column([
        ft.Text("Estoque Atual", size=20, weight="bold", color="#E91E63"),
        txt_busca,
        ft.Divider(color="#FFC000"),
        lista_produtos
    ], visible=False)

    def navegar(mostra_cadastro):
        container_cadastro.visible = mostra_cadastro
        container_estoque.visible = not mostra_cadastro
        if not mostra_cadastro: atualizar_lista_visual()
        page.update()

    # Adiciona os elementos do sistema na página diretamente
    page.add(
        ft.Text("🧸 DEKIDS SISTEMA", size=32, weight="bold", color="#0070C0"),
        ft.Row([
            ft.ElevatedButton("NOVO PRODUTO", on_click=lambda _: navegar(True), bgcolor="#0070C0", color="white"),
            ft.ElevatedButton("VER ESTOQUE", on_click=lambda _: navegar(False), bgcolor="#E91E63", color="white"),
        ]),
        ft.Divider(color="#FFC000", height=20),
        container_cadastro,
        container_estoque
    )
    
    # Carrega a lista inicial
    atualizar_lista_visual()

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)