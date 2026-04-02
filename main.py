import flet as ft
import os
import time
import base64
from datetime import datetime, timedelta
# Adicione 'editar_produto' na importação abaixo
from database import cadastrar_produto, listar_estoque, excluir_produto, registrar_saida, registrar_entrada, registrar_estorno, editar_produto, registrar_movimentacao, buscar_produtos_avancado, gerar_sugestoes, atualizar_estoque_minimo, listar_movimentacoes, desfazer_ultima_movimentacao, contar_produtos_avancado
from barcode import gerar_qrcode, validar_codigo_barras
from relatorios_estoque import gerar_relatorio_estoque_baixo, gerar_relatorio_movimentacoes, gerar_relatorio_produtos_sem_movimentacao, exportar_csv
from estoque import calcular_valor_total_estoque

# Importar telas de vendas
from tela_vendas import TelaPDV
from tela_clientes import TelaClientes
from tela_relatorios import TelaRelatorios
from tela_cancelamento import TelaCancelamento
from tela_usuarios import TelaUsuarios
from tela_financeiro import TelaFinanceiro

# Importar funções de autenticação
from database import obter_sessao_ativa
from login import encerrar_sessao_atual

def main(page: ft.Page, sessao_inicial: dict = None):
    # --- CONFIGURAÇÃO DA PÁGINA ---
    page.title = "DEKIDS Moda Infantil"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "white"
    page.padding = 0  # Removido padding para NavigationRail
    page.vertical_alignment = "start"
    page.horizontal_alignment = "start"
    page.scroll = None  # Desativado para permitir que o layout preencha a tela e use scroll interno

    # --- VALIDAÇÃO DE SESSÃO ---
    # Se uma sessão foi passada por argumento (ex: vindo do app.py), usá-la
    if sessao_inicial and sessao_inicial.get("token") and sessao_inicial.get("usuario"):
        sessao = sessao_inicial
        sucesso = True
        print(f"DEBUG: Usando sessão inicial do app.py para {sessao['usuario']['username']}")
    else:
        # Senão, tentar obter sessão ativa do banco de dados
        sucesso, mensagem, sessao = obter_sessao_ativa()
        print(f"DEBUG: obter_sessao_ativa() - sucesso={sucesso}, mensagem={mensagem}")
    
    # Se não conseguiu obter sessão, sessao será None
    if not sucesso:
        sessao = None
    
    # Verificar se há sessão ativa
    if not sessao or not sessao.get("token") or not sessao.get("usuario"):
        # Não há sessão ativa - redirecionar para login
        page.clean()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚠️ Sessão Inválida", size=24, weight="bold", color="red"),
                    ft.Text("Você precisa fazer login para acessar o sistema.", size=16),
                    ft.ElevatedButton(
                        "Ir para Login",
                        on_click=lambda _: page.window_close(),
                        bgcolor="#0070C0",
                        color="white"
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=50,
                alignment=ft.alignment.center
            )
        )
        page.update()
        return
    
    # Extrair dados do usuário da sessão
    usuario_id = sessao["usuario"]["id"]
    usuario_nome = sessao["usuario"]["username"]
    usuario_role = sessao["usuario"].get("role", "user")  # Capturar role do usuário
    print(f"DEBUG: Usuario carregado - ID={usuario_id}, Nome={usuario_nome}, Role={usuario_role}")

    print("DEBUG: Iniciando criação da interface...")
    # --- ESTADO DE NAVEGAÇÃO ---
    # Estado para controlar qual tela está ativa
    estado_navegacao = {"view_atual": "estoque"}

    # --- ESTADO DA SESSÃO (persistência de filtros e paginação) ---
    filtros_sessao = {
        "termo": "",
        "genero": None,
        "marca": None,
        "preco_min": None,
        "preco_max": None,
        "order_by": None,
        "order_direction": "asc",
        "pagina_atual": 1,
        "itens_por_pagina": 50,
        "total_produtos": 0
    }
    
    # Timer para debounce da busca
    debounce_timer = {"timer": None}
    
    # --- INDICADOR DE CARREGAMENTO ---
    loading_indicator = ft.ProgressRing(visible=False, width=30, height=30)
    
    # --- CONTADOR DE ESTOQUE BAIXO ---
    contador_estoque_baixo = ft.Container(
        content=ft.Row([
            ft.Text("0 produtos com estoque baixo", size=14, weight="bold", color="orange")
        ], spacing=5),
        padding=10,
        bgcolor="#FFF3E0",
        border_radius=5,
        visible=False
    )

    # --- CAMPOS DE ENTRADA ---
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
    txt_codigo_barras = ft.TextField(
        label="Código de Barras (EAN-13)",
        hint_text="13 dígitos",
        max_length=13,
        keyboard_type=ft.KeyboardType.NUMBER
    )
    txt_estoque_minimo = ft.TextField(
        label="Estoque Mínimo",
        hint_text="5",
        value="5",
        keyboard_type=ft.KeyboardType.NUMBER
    )

    # --- CAMPOS DE BUSCA E FILTROS ---
    def aplicar_busca_com_debounce(e):
        """Aplica busca com debounce de 300ms"""
        # Cancelar timer anterior se existir
        if debounce_timer["timer"] is not None:
            debounce_timer["timer"] = None
        
        # Criar novo timer
        def executar_busca():
            time.sleep(0.3)  # 300ms de debounce
            if debounce_timer["timer"] == "executar":
                filtros_sessao["termo"] = txt_busca.value
                atualizar_lista_visual()
        
        debounce_timer["timer"] = "executar"
        import threading
        threading.Thread(target=executar_busca, daemon=True).start()
    
    txt_busca = ft.TextField(
        label="Pesquisar produto...",
        hint_text="Buscar por descrição, marca ou referência",
        prefix_icon="search",
        on_change=aplicar_busca_com_debounce,
        expand=True
    )
    
    # Filtros
    filtro_genero = ft.Dropdown(
        label="Gênero",
        hint_text="Todos",
        options=[
            ft.dropdown.Option(""),
            ft.dropdown.Option("Masculino"),
            ft.dropdown.Option("Feminino"),
            ft.dropdown.Option("Unissex")
        ],
        width=150,
        # on_change removido temporariamente
    )
    
    filtro_marca = ft.TextField(
        label="Marca",
        hint_text="Filtrar por marca",
        width=150,
        # on_change removido temporariamente
    )
    
    filtro_preco_min = ft.TextField(
        label="Preço Mín",
        hint_text="0.00",
        width=120,
        keyboard_type=ft.KeyboardType.NUMBER,
        # on_change removido temporariamente
    )
    
    filtro_preco_max = ft.TextField(
        label="Preço Máx",
        hint_text="9999.99",
        width=120,
        keyboard_type=ft.KeyboardType.NUMBER,
        # on_change removido temporariamente
    )
    
    filtro_ordenacao = ft.Dropdown(
        label="Ordenar por",
        hint_text="Padrão",
        options=[
            ft.dropdown.Option(""),
            ft.dropdown.Option("nome", "Nome"),
            ft.dropdown.Option("preco", "Preço"),
            ft.dropdown.Option("quantidade", "Quantidade")
        ],
        width=150,
        # on_change removido temporariamente
    )
    
    def limpar_filtros():
        """Limpa todos os filtros e restaura listagem completa"""
        filtros_sessao["termo"] = ""
        filtros_sessao["genero"] = None
        filtros_sessao["marca"] = None
        filtros_sessao["preco_min"] = None
        filtros_sessao["preco_max"] = None
        filtros_sessao["order_by"] = None
        filtros_sessao["pagina_atual"] = 1  # Resetar para primeira página
        
        txt_busca.value = ""
        filtro_genero.value = ""
        filtro_marca.value = ""
        filtro_preco_min.value = ""
        filtro_preco_max.value = ""
        filtro_ordenacao.value = ""
        
        atualizar_lista_visual()
    
    def aplicar_filtros():
        """Aplica filtros e atualiza a listagem"""
        # Atualizar filtros da sessão
        filtros_sessao["genero"] = filtro_genero.value if filtro_genero.value else None
        filtros_sessao["marca"] = filtro_marca.value if filtro_marca.value else None
        filtros_sessao["pagina_atual"] = 1  # Resetar para primeira página ao aplicar filtros
        
        try:
            filtros_sessao["preco_min"] = float(filtro_preco_min.value.replace(",", ".")) if filtro_preco_min.value else None
        except:
            filtros_sessao["preco_min"] = None
        
        try:
            filtros_sessao["preco_max"] = float(filtro_preco_max.value.replace(",", ".")) if filtro_preco_max.value else None
        except:
            filtros_sessao["preco_max"] = None
        
        filtros_sessao["order_by"] = filtro_ordenacao.value if filtro_ordenacao.value else None
        
        atualizar_lista_visual()

    lista_produtos = ft.Column(spacing=10)
    
    # --- CONTROLES DE PAGINAÇÃO ---
    info_paginacao = ft.Text("", size=14, color="#0070C0", weight="bold")
    
    def ir_para_pagina(pagina):
        """Navega para uma página específica"""
        filtros_sessao["pagina_atual"] = pagina
        atualizar_lista_visual()
    
    def pagina_anterior(e):
        """Vai para a página anterior"""
        if filtros_sessao["pagina_atual"] > 1:
            ir_para_pagina(filtros_sessao["pagina_atual"] - 1)
    
    def pagina_proxima(e):
        """Vai para a próxima página"""
        total_paginas = (filtros_sessao["total_produtos"] + filtros_sessao["itens_por_pagina"] - 1) // filtros_sessao["itens_por_pagina"]
        if filtros_sessao["pagina_atual"] < total_paginas:
            ir_para_pagina(filtros_sessao["pagina_atual"] + 1)
    
    def primeira_pagina(e):
        """Vai para a primeira página"""
        ir_para_pagina(1)
    
    def ultima_pagina(e):
        """Vai para a última página"""
        total_paginas = (filtros_sessao["total_produtos"] + filtros_sessao["itens_por_pagina"] - 1) // filtros_sessao["itens_por_pagina"]
        ir_para_pagina(total_paginas)
    
    controles_paginacao = ft.Row([
        ft.IconButton(
            icon=ft.icons.CHEVRON_LEFT,
            tooltip="Página anterior",
            on_click=pagina_anterior
        ),
        info_paginacao,
        ft.IconButton(
            icon=ft.icons.CHEVRON_RIGHT,
            tooltip="Próxima página",
            on_click=pagina_proxima
        ),
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)

    # --- CAMPOS DO MODAL DE EDIÇÃO ---
    edit_id = ft.Text(visible=False)
    edit_descricao = ft.TextField(label="Descrição")
    edit_referencia = ft.TextField(label="Referência")
    edit_tamanho = ft.TextField(label="Tamanho")
    edit_preco = ft.TextField(label="Preço", prefix=ft.Text("R$ "))
    edit_estoque_minimo = ft.TextField(
        label="Estoque Mínimo",
        hint_text="5",
        value="5",
        keyboard_type=ft.KeyboardType.NUMBER
    )

    def fechar_modal(e):
        modal_editar.open = False
        page.update()

    def salvar_edicao(e):
        try:
            novos_dados = {
                "descricao": edit_descricao.value,
                "referencia": edit_referencia.value,
                "tamanho": edit_tamanho.value,
                "preco": float(edit_preco.value.replace(",", "."))
            }
            
            # Atualizar dados básicos do produto
            editar_produto(edit_id.value, novos_dados)
            
            # Atualizar estoque mínimo separadamente
            estoque_minimo = int(edit_estoque_minimo.value) if edit_estoque_minimo.value else 5
            atualizar_estoque_minimo(int(edit_id.value), estoque_minimo)
            
            modal_editar.open = False
            atualizar_lista_visual(txt_busca.value)
            
            snack = ft.SnackBar(
                ft.Row([
                    ft.Text("✅ Produto atualizado com sucesso!")
                ]),
                bgcolor="green"
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except Exception as ex:
            snack = ft.SnackBar(
                ft.Row([
                    ft.Text(f"❌ Erro ao salvar: {str(ex)}")
                ]),
                bgcolor="red"
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()

    modal_editar = ft.AlertDialog(
        title=ft.Text("Editar Produto"),
        content=ft.Column([
            edit_descricao,
            edit_referencia,
            edit_tamanho,
            edit_preco,
            edit_estoque_minimo,
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal),
            ft.ElevatedButton("Salvar Alterações", bgcolor="#0070C0", color="white", on_click=salvar_edicao),
        ],
    )
    page.overlay.append(modal_editar)

    # --- MODAL DE MOVIMENTAÇÃO EM LOTE ---
    mov_produto_id = ft.Text(visible=False)
    mov_produto_nome = ft.Text(visible=False)
    mov_estoque_atual = ft.Text(visible=False)
    mov_tipo = ft.Text(visible=False)  # 'entrada' ou 'saida'
    mov_quantidade = ft.TextField(
        label="Quantidade",
        value="1",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=200
    )
    mov_observacao = ft.TextField(
        label="Observação (opcional)",
        multiline=True,
        max_lines=3
    )
    mov_aviso = ft.Container(
        content=ft.Row([
            ft.Text("", color="orange", weight="bold")
        ]),
        visible=False,
        padding=10,
        bgcolor="#FFF3E0",
        border_radius=5
    )

    def fechar_modal_movimentacao(e):
        modal_movimentacao.open = False
        mov_quantidade.value = "1"
        mov_observacao.value = ""
        mov_aviso.visible = False
        page.update()

    def confirmar_movimentacao(e):
        # Mostrar indicador de carregamento
        loading_indicator.visible = True
        page.update()
        
        try:
            quantidade = int(mov_quantidade.value)
            if quantidade <= 0:
                loading_indicator.visible = False
                return
            
            produto_id = int(mov_produto_id.value)
            tipo = mov_tipo.value
            observacao = mov_observacao.value if mov_observacao.value else None
            
            # Registrar movimentação usando a função do database.py
            sucesso = registrar_movimentacao(produto_id, tipo, quantidade, observacao)
            
            loading_indicator.visible = False
            
            if sucesso:
                modal_movimentacao.open = False
                mov_quantidade.value = "1"
                mov_observacao.value = ""
                mov_aviso.visible = False
                atualizar_lista_visual(txt_busca.value)
                
                msg = f"✅ {'Entrada' if tipo == 'entrada' else 'Saída'} de {quantidade} unidade(s) registrada com sucesso!"
                cor = "green" if tipo == 'entrada' else "blue"
                icone = ft.icons.CHECK_CIRCLE if tipo == 'entrada' else ft.icons.CHECK_CIRCLE
                
                snack = ft.SnackBar(
                    ft.Row([
                        ft.Text(msg)
                    ]),
                    bgcolor=cor
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
            else:
                snack = ft.SnackBar(
                    ft.Row([
                        ft.Text("❌ Erro ao registrar movimentação")
                    ]),
                    bgcolor="red"
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
        except ValueError:
            loading_indicator.visible = False
            snack = ft.SnackBar(
                ft.Row([
                    ft.Text("⚠️ Quantidade inválida")
                ]),
                bgcolor="orange"
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()

    def atualizar_aviso_estoque(e):
        try:
            quantidade = int(mov_quantidade.value)
            estoque_atual = int(mov_estoque_atual.value)
            tipo = mov_tipo.value
            
            # Mostrar aviso se saída for maior que estoque
            if tipo == 'saida' and quantidade > estoque_atual:
                mov_aviso.visible = True
                mov_aviso.content.controls[1].value = f"⚠️ Atenção: Saída de {quantidade} unidades é maior que o estoque atual ({estoque_atual}). Confirme para prosseguir."
            # Mostrar confirmação para movimentações em lote (quantidade > 1)
            elif quantidade > 1:
                mov_aviso.visible = True
                mov_aviso.bgcolor = "#E3F2FD"
                mov_aviso.content.controls[0].color = "blue"
                mov_aviso.content.controls[1].color = "blue"
                mov_aviso.content.controls[1].value = f"ℹ️ Movimentação em lote: {quantidade} unidades. Confirme para prosseguir."
            else:
                mov_aviso.visible = False
            
            page.update()
        except ValueError:
            mov_aviso.visible = False
            page.update()

    mov_quantidade.on_change = atualizar_aviso_estoque

    modal_movimentacao = ft.AlertDialog(
        title=ft.Text("Movimentação de Estoque"),
        content=ft.Column([
            ft.Text("", size=16, weight="bold"),  # Nome do produto
            ft.Text("", size=14),  # Estoque atual
            ft.Divider(),
            mov_quantidade,
            mov_observacao,
            mov_aviso,
        ], tight=True, height=300),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal_movimentacao),
            ft.ElevatedButton("Confirmar", bgcolor="#0070C0", color="white", on_click=confirmar_movimentacao),
        ],
    )
    page.overlay.append(modal_movimentacao)

    def abrir_modal_editar(p):
        edit_id.value = p['id']
        edit_descricao.value = p['descricao']
        edit_referencia.value = p['referencia']
        edit_tamanho.value = p['tamanho']
        edit_preco.value = str(p['preco']).replace(".", ",")
        edit_estoque_minimo.value = str(p.get('estoque_minimo', 5))
        modal_editar.open = True
        page.update()

    def abrir_modal_movimentacao(p, tipo):
        """Abre modal de movimentação em lote"""
        mov_produto_id.value = str(p['id'])
        mov_produto_nome.value = p['descricao']
        mov_estoque_atual.value = str(p['quantidade'])
        mov_tipo.value = tipo
        mov_quantidade.value = "1"
        mov_observacao.value = ""
        mov_aviso.visible = False
        
        # Atualizar título e informações do modal
        modal_movimentacao.title.value = f"{'Entrada' if tipo == 'entrada' else 'Saída'} de Estoque"
        modal_movimentacao.content.controls[0].value = p['descricao']
        modal_movimentacao.content.controls[1].value = f"Estoque atual: {p['quantidade']} unidade(s)"
        
        # Mudar cor do botão confirmar
        cor = "green" if tipo == 'entrada' else "blue"
        modal_movimentacao.actions[1].bgcolor = cor
        
        modal_movimentacao.open = True
        page.update()

    # --- MODAL DE QR CODE ---
    qr_image = ft.Image(src=chr(34)+chr(34), width=300, height=300)
    qr_produto_nome = ft.Text("", size=16, weight="bold")
    
    def fechar_modal_qrcode(e):
        modal_qrcode.open = False
        page.update()
    
    def abrir_modal_qrcode(p):
        """Gera e exibe QR code do produto"""
        try:
            qr_bytes = gerar_qrcode(p['id'])
            if qr_bytes:
                # Converter bytes para base64 para exibir no Flet
                import base64
                qr_base64 = base64.b64encode(qr_bytes).decode()
                qr_image.src_base64 = qr_base64
                qr_produto_nome.value = f"QR Code: {p['descricao']}"
                modal_qrcode.open = True
                page.update()
            else:
                snack = ft.SnackBar(ft.Text("Erro ao gerar QR code"), bgcolor="red")
                page.overlay.append(snack)
                snack.open = True
                page.update()
        except Exception as e:
            print(f"Erro ao gerar QR code: {e}")
            snack = ft.SnackBar(ft.Text("Erro ao gerar QR code"), bgcolor="red")
            page.overlay.append(snack)
            snack.open = True
            page.update()
    
    modal_qrcode = ft.AlertDialog(
        title=qr_produto_nome,
        content=ft.Container(
            content=qr_image,
            alignment=ft.alignment.center,
            width=320,
            height=320
        ),
        actions=[
            ft.TextButton("Fechar", on_click=fechar_modal_qrcode),
        ],
    )
    page.overlay.append(modal_qrcode)

    # --- FUNÇÕES DE AÇÃO ---
    def acao_estoque(func, id_p, qtd_p, msg, cor):
        if func(id_p, qtd_p):
            atualizar_lista_visual()
            snack = ft.SnackBar(ft.Text(msg), bgcolor=cor)
            page.overlay.append(snack)
            snack.open = True
            page.update()

    # --- MODAL DE CONFIRMAÇÃO DE EXCLUSÃO ---
    confirmar_exclusao_produto_id = ft.Text(visible=False)
    confirmar_exclusao_produto_nome = ft.Text("", size=16)
    
    def fechar_modal_confirmar_exclusao(e):
        modal_confirmar_exclusao.open = False
        page.update()
    
    def executar_exclusao(e):
        produto_id = int(confirmar_exclusao_produto_id.value)
        excluir_produto(produto_id)
        modal_confirmar_exclusao.open = False
        atualizar_lista_visual()
        
        snack = ft.SnackBar(
            ft.Row([
                ft.Text("🗑️ Produto removido com sucesso!")
            ]),
            bgcolor="black"
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    
    modal_confirmar_exclusao = ft.AlertDialog(
        title=ft.Text("⚠️ Confirmar Exclusão", color="red", weight="bold"),
        content=ft.Column([
            ft.Text("Tem certeza que deseja excluir este produto?", size=14),
            confirmar_exclusao_produto_nome,
            ft.Divider(),
            ft.Text("⚠️ Esta ação não pode ser desfeita!", size=12, color="red", italic=True),
        ], tight=True, height=150),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_modal_confirmar_exclusao),
            ft.ElevatedButton(
                "Excluir",
                bgcolor="red",
                color="white",
                on_click=executar_exclusao
            ),
        ],
    )
    page.overlay.append(modal_confirmar_exclusao)

    def deletar_item(id_p, nome_produto=""):
        """Abre modal de confirmação antes de excluir"""
        confirmar_exclusao_produto_id.value = str(id_p)
        confirmar_exclusao_produto_nome.value = f"Produto: {nome_produto}"
        modal_confirmar_exclusao.open = True
        page.update()

    def atualizar_lista_visual():
        """Atualiza a lista de produtos usando busca avançada com filtros da sessão e paginação"""
        # Mostrar indicador de carregamento
        loading_indicator.visible = True
        page.update()
        
        lista_produtos.controls.clear()
        try:
            # Preparar filtros para busca avançada
            filtros = {}
            
            if filtros_sessao["termo"]:
                filtros["termo"] = filtros_sessao["termo"]
            if filtros_sessao["genero"]:
                filtros["genero"] = filtros_sessao["genero"]
            if filtros_sessao["marca"]:
                filtros["marca"] = filtros_sessao["marca"]
            if filtros_sessao["preco_min"] is not None:
                filtros["preco_min"] = filtros_sessao["preco_min"]
            if filtros_sessao["preco_max"] is not None:
                filtros["preco_max"] = filtros_sessao["preco_max"]
            if filtros_sessao["order_by"]:
                filtros["order_by"] = filtros_sessao["order_by"]
                filtros["order_direction"] = filtros_sessao["order_direction"]
            
            # Adicionar paginação (50 itens por página)
            filtros["limit"] = filtros_sessao["itens_por_pagina"]
            filtros["offset"] = (filtros_sessao["pagina_atual"] - 1) * filtros_sessao["itens_por_pagina"]
            
            # Contar total de produtos (sem paginação) para calcular páginas
            filtros_count = {k: v for k, v in filtros.items() if k not in ['limit', 'offset']}
            if filtros_count:
                # Buscar todos para contar (otimização futura: usar COUNT do banco)
                todos_produtos = buscar_produtos_avancado(filtros_count)
                filtros_sessao["total_produtos"] = len(todos_produtos)
            else:
                todos_produtos = listar_estoque()
                filtros_sessao["total_produtos"] = len(todos_produtos)
            
            # Buscar produtos da página atual
            if filtros:
                produtos = buscar_produtos_avancado(filtros)
            else:
                # Se não há filtros, aplicar paginação manualmente
                offset = filtros["offset"]
                limit = filtros["limit"]
                produtos = todos_produtos[offset:offset + limit]
            
            # Calcular informações de paginação
            total_paginas = (filtros_sessao["total_produtos"] + filtros_sessao["itens_por_pagina"] - 1) // filtros_sessao["itens_por_pagina"]
            if total_paginas == 0:
                total_paginas = 1
            
            # Atualizar info de paginação
            info_paginacao.value = f"Página {filtros_sessao['pagina_atual']} de {total_paginas} ({filtros_sessao['total_produtos']} produtos)"
            
            # Contar produtos com estoque baixo
            produtos_estoque_baixo = 0
            
            print(f"DEBUG: Renderizando {len(produtos)} produtos")
            if produtos:
                for p in produtos:
                    # Verificar se estoque está baixo
                    estoque_minimo = p.get('estoque_minimo', 5)
                    estoque_baixo = p['quantidade'] <= estoque_minimo
                    
                    if estoque_baixo:
                        produtos_estoque_baixo += 1
                    
                    # Criar linha de ações com botões
                    acoes = ft.Row([
                        ft.IconButton(
                            icon=ft.icons.HISTORY,
                            icon_color="purple",
                            tooltip="Histórico",
                            on_click=lambda _, p=p: abrir_historico_produto(p)
                        ),
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            icon_color="blue",
                            tooltip="Editar",
                            on_click=lambda _, p=p: abrir_modal_editar(p)
                        ),
                        ft.IconButton(
                            icon=ft.icons.QR_CODE,
                            icon_color="purple",
                            tooltip="Gerar QR Code",
                            on_click=lambda _, p=p: abrir_modal_qrcode(p)
                        ),
                        ft.ElevatedButton(
                            "+",
                            bgcolor="green",
                            color="white",
                            tooltip="Entrada",
                            on_click=lambda _, p=p: abrir_modal_movimentacao(p, 'entrada')
                        ),
                        ft.ElevatedButton(
                            "-",
                            bgcolor="blue",
                            color="white",
                            tooltip="Saída",
                            on_click=lambda _, p=p: abrir_modal_movimentacao(p, 'saida')
                        ),
                        ft.ElevatedButton(
                            "🗑️",
                            bgcolor="red",
                            color="white",
                            tooltip="Excluir",
                            on_click=lambda _, id=p['id'], nome=p['descricao']: deletar_item(id, nome)
                        ),
                    ], spacing=5)
                    
                    # Informações do produto com indicador de estoque baixo
                    info_controls = [
                        ft.Row([
                            ft.Text(f"{p['descricao']}".upper(), weight="bold", size=16),
                        ], spacing=5),
                        ft.Text(f"Ref: {p['referencia']} | Tam: {p['tamanho']}", size=13),
                        ft.Text(f"Qtd: {p['quantidade']} | R$ {p['preco']}", color="#0070C0", weight="bold"),
                    ]
                    
                    # Adicionar estoque mínimo se estoque baixo
                    if estoque_baixo:
                        info_controls.append(
                            ft.Text(f"⚠️ Estoque mínimo: {estoque_minimo}", size=12, color="orange", weight="bold")
                        )
                    
                    info_produto = ft.Column(info_controls, expand=True, spacing=2)
                    
                    # Adicionar código de barras se existir
                    if p.get('codigo_barras'):
                        info_produto.controls.append(
                            ft.Text(f"Código: {p['codigo_barras']}", size=12, color="gray")
                        )
                    
                    # Definir cor de fundo baseado no estoque
                    bgcolor = "#FFEBEE" if estoque_baixo else "white"
                    border_color = "#FF5252" if estoque_baixo else "#EEEEEE"
                    
                    lista_produtos.controls.append(
                        ft.Container(
                            content=ft.Row([
                                info_produto,
                                acoes
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=15,
                            border=ft.border.all(2 if estoque_baixo else 1, border_color),
                            border_radius=10,
                            bgcolor=bgcolor
                        )
                    )
                
                # Adicionar contador de resultados
                lista_produtos.controls.insert(0,
                    ft.Text(f"📦 {len(produtos)} produto(s) encontrado(s)", 
                           size=14, weight="bold", color="#0070C0")
                )
                
                # Atualizar contador de estoque baixo
                if produtos_estoque_baixo > 0:
                    contador_estoque_baixo.content.controls[0].value = f"{produtos_estoque_baixo} produto(s) com estoque baixo"
                    contador_estoque_baixo.visible = True
                else:
                    contador_estoque_baixo.visible = False
            else:
                lista_produtos.controls.append(ft.Text("Nenhum produto encontrado."))
                contador_estoque_baixo.visible = False
                
                # Gerar sugestões se houver termo de busca
                if filtros_sessao["termo"]:
                    sugestoes = gerar_sugestoes(filtros_sessao["termo"])
                    if sugestoes:
                        lista_produtos.controls.append(
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("💡 Você quis dizer:", weight="bold"),
                                    ft.Text(", ".join(sugestoes), color="blue")
                                ]),
                                padding=10,
                                bgcolor="#E3F2FD",
                                border_radius=5
                            )
                        )
        except Exception as ex:
            print(f"Erro Visual: {ex}")
            lista_produtos.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Erro ao carregar produtos", size=16, weight="bold", color="red")
                        ], spacing=10),
                        ft.Text(str(ex), size=12, color="gray")
                    ]),
                    padding=15,
                    bgcolor="#FFEBEE",
                    border_radius=5,
                    border=ft.border.all(1, "red")
                )
            )
            contador_estoque_baixo.visible = False
        finally:
            # Esconder indicador de carregamento
            loading_indicator.visible = False
            print(f"[DEBUG] lista_produtos tem {len(lista_produtos.controls)} controles")
            lista_produtos.update()  # Explicit update for the Column
            page.update()

    def salvar_clicado(e):
        # Mostrar indicador de carregamento
        loading_indicator.visible = True
        page.update()
        
        try:
            # Validar código de barras se fornecido
            codigo_barras = txt_codigo_barras.value.strip() if txt_codigo_barras.value else None
            if codigo_barras and not validar_codigo_barras(codigo_barras):
                loading_indicator.visible = False
                snack = ft.SnackBar(
                    ft.Row([
                        ft.Text("Código de barras inválido! Use formato EAN-13 (13 dígitos)")
                    ]),
                    bgcolor="red"
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
                return
            
            # Cadastrar produto (a função cadastrar_produto precisa ser atualizada para aceitar codigo_barras)
            estoque_minimo = int(txt_estoque_minimo.value) if txt_estoque_minimo.value else 5
            sucesso = cadastrar_produto(
                txt_descricao.value, txt_genero.value, txt_marca.value,
                txt_referencia.value, txt_tamanho.value, 
                int(txt_qtd.value), float(txt_preco.value.replace(",", ".")),
                codigo_barras=codigo_barras,
                estoque_minimo=estoque_minimo
            )
            
            loading_indicator.visible = False
            
            if sucesso:
                # Limpar campos
                for f in [txt_descricao, txt_marca, txt_referencia, txt_tamanho, txt_preco, txt_codigo_barras]:
                    f.value = ""
                txt_qtd.value = "0"
                txt_estoque_minimo.value = "5"
                txt_genero.value = None
                
                snack = ft.SnackBar(
                    ft.Row([
                        ft.Text("✅ Produto cadastrado com sucesso!")
                    ]),
                    bgcolor="green"
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
            else:
                snack = ft.SnackBar(
                    ft.Row([
                        ft.Text("❌ Erro ao cadastrar produto")
                    ]),
                    bgcolor="red"
                )
                page.overlay.append(snack)
                snack.open = True
                page.update()
        except ValueError as ve:
            loading_indicator.visible = False
            snack = ft.SnackBar(
                ft.Row([
                    ft.Text(f"⚠️ Erro de validação: {ve}")
                ]),
                bgcolor="orange"
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
        except Exception as ex:
            loading_indicator.visible = False
            print(f"Erro ao salvar: {ex}")
            snack = ft.SnackBar(
                ft.Row([
                    ft.Text(f"❌ Erro ao salvar produto: {str(ex)}")
                ]),
                bgcolor="red"
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()

    # --- INTERFACE ---
    container_cadastro = ft.Column([
        ft.Text("Cadastrar Novo Item", size=20, weight="bold", color="#E91E63"),
        txt_descricao,
        ft.Row([txt_genero, txt_tamanho]),
        ft.Row([txt_marca, txt_referencia]),
        ft.Row([txt_qtd, txt_preco]),
        ft.Row([txt_codigo_barras, txt_estoque_minimo]),
        ft.ElevatedButton("SALVAR PRODUTO", on_click=salvar_clicado, bgcolor="#0070C0", color="white", width=400),
    ], visible=True)

    container_estoque = ft.Column([
        ft.Text("Estoque Atual", size=20, weight="bold", color="#E91E63"),
        contador_estoque_baixo,  # Contador de estoque baixo
        ft.Row([txt_busca, loading_indicator]),  # Adicionar loading indicator
        ft.Divider(height=5, color="transparent"),
        ft.Text("🔍 Filtros Avançados", size=14, weight="bold", color="#0070C0"),
        ft.Row([
            filtro_genero,
            filtro_marca,
            filtro_preco_min,
            filtro_preco_max,
            filtro_ordenacao,
        ], wrap=True, spacing=10),
        ft.Row([
            ft.ElevatedButton(
                "Limpar Filtros",
                on_click=lambda _: limpar_filtros(),
                bgcolor="#FFC000",
                color="white"
            ),
        ]),
        ft.Divider(color="#FFC000"),
        controles_paginacao,  # Controles de paginação
        lista_produtos,
        ft.Divider(height=10, color="transparent"),
        controles_paginacao,  # Controles de paginação no final também
    ], visible=False)

    # --- INTERFACE DE RELATÓRIOS ---
    
    # Seleção de tipo de relatório
    tipo_relatorio = ft.Dropdown(
        label="Tipo de Relatório",
        hint_text="Selecione o tipo de relatório",
        options=[
            ft.dropdown.Option("estoque_baixo", "Produtos com Estoque Baixo"),
            ft.dropdown.Option("movimentacoes", "Movimentações por Período"),
            ft.dropdown.Option("sem_movimentacao", "Produtos sem Movimentação"),
            ft.dropdown.Option("valor_total", "Valor Total do Estoque"),
        ],
        width=300,
        on_change=lambda e: atualizar_campos_relatorio()
    )
    
    # Seletores de data
    data_inicio = ft.TextField(
        label="Data Início",
        hint_text="YYYY-MM-DD",
        value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        width=200,
        visible=False
    )
    
    data_fim = ft.TextField(
        label="Data Fim",
        hint_text="YYYY-MM-DD",
        value=datetime.now().strftime("%Y-%m-%d"),
        width=200,
        visible=False
    )
    
    dias_sem_mov = ft.TextField(
        label="Dias sem Movimentação",
        hint_text="30",
        value="30",
        width=200,
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False
    )
    
    # Container para exibir relatório
    tabela_relatorio = ft.Column(spacing=10, scroll="auto")
    
    # Informações do relatório gerado
    info_relatorio = ft.Container(
        content=ft.Column([
            ft.Text("", size=16, weight="bold"),
            ft.Text("", size=14, color="gray"),
        ]),
        visible=False,
        padding=10,
        bgcolor="#E3F2FD",
        border_radius=5
    )
    
    def atualizar_campos_relatorio():
        """Atualiza visibilidade dos campos baseado no tipo de relatório selecionado"""
        tipo = tipo_relatorio.value
        
        # Esconder todos os campos primeiro
        data_inicio.visible = False
        data_fim.visible = False
        dias_sem_mov.visible = False
        
        # Mostrar campos relevantes
        if tipo == "movimentacoes":
            data_inicio.visible = True
            data_fim.visible = True
        elif tipo == "sem_movimentacao":
            dias_sem_mov.visible = True
        
        # Limpar relatório anterior
        tabela_relatorio.controls.clear()
        info_relatorio.visible = False
        
        page.update()
    
    def gerar_relatorio_clicado(e):
        """Gera o relatório selecionado"""
        tipo = tipo_relatorio.value
        
        if not tipo:
            snack = ft.SnackBar(ft.Text("Selecione um tipo de relatório"), bgcolor="orange")
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        
        try:
            # Limpar relatório anterior
            tabela_relatorio.controls.clear()
            info_relatorio.visible = False
            
            # Gerar relatório baseado no tipo
            if tipo == "estoque_baixo":
                dados = gerar_relatorio_estoque_baixo()
                exibir_relatorio_estoque_baixo(dados)
                
            elif tipo == "movimentacoes":
                inicio = data_inicio.value
                fim = data_fim.value
                dados = gerar_relatorio_movimentacoes(inicio, fim)
                exibir_relatorio_movimentacoes(dados)
                
            elif tipo == "sem_movimentacao":
                dias = int(dias_sem_mov.value) if dias_sem_mov.value else 30
                dados = gerar_relatorio_produtos_sem_movimentacao(dias)
                exibir_relatorio_sem_movimentacao(dados)
                
            elif tipo == "valor_total":
                valor_total = calcular_valor_total_estoque()
                exibir_relatorio_valor_total(valor_total)
            
            page.update()
            
        except Exception as ex:
            print(f"Erro ao gerar relatório: {ex}")
            snack = ft.SnackBar(ft.Text(f"Erro ao gerar relatório: {ex}"), bgcolor="red")
            page.overlay.append(snack)
            snack.open = True
            page.update()
    
    def exibir_relatorio_estoque_baixo(dados):
        """Exibe relatório de estoque baixo em tabela formatada"""
        if not dados:
            tabela_relatorio.controls.append(
                ft.Text("Nenhum produto com estoque baixo encontrado! 🎉", size=16, color="green")
            )
            return
        
        # Informações do relatório
        info_relatorio.content.controls[0].value = f"📊 Relatório de Estoque Baixo"
        info_relatorio.content.controls[1].value = f"{len(dados)} produto(s) com estoque baixo"
        info_relatorio.visible = True
        
        # Cabeçalho da tabela
        tabela_relatorio.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("Produto", weight="bold", size=14, expand=3),
                    ft.Text("Ref/Tam", weight="bold", size=14, expand=2),
                    ft.Text("Qtd", weight="bold", size=14, expand=1),
                    ft.Text("Mín", weight="bold", size=14, expand=1),
                    ft.Text("Status", weight="bold", size=14, expand=2),
                ]),
                bgcolor="#0070C0",
                padding=10,
                border_radius=5
            )
        )
        
        # Linhas da tabela
        for item in dados:
            # Definir cor baseado no status
            if "CRÍTICO" in item["status"]:
                cor_status = "red"
            elif "URGENTE" in item["status"]:
                cor_status = "orange"
            else:
                cor_status = "blue"
            
            tabela_relatorio.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(item["descricao"], size=13, weight="bold"),
                            ft.Text(item["marca"], size=11, color="gray"),
                        ], expand=3, spacing=2),
                        ft.Text(f"{item['referencia']}/{item['tamanho']}", size=12, expand=2),
                        ft.Text(str(item["quantidade"]), size=13, weight="bold", expand=1),
                        ft.Text(str(item["estoque_minimo"]), size=12, expand=1),
                        ft.Text(item["status"], size=11, color=cor_status, weight="bold", expand=2),
                    ]),
                    padding=10,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5
                )
            )
    
    def exibir_relatorio_movimentacoes(dados):
        """Exibe relatório de movimentações em tabela formatada"""
        if not dados:
            tabela_relatorio.controls.append(
                ft.Text("Nenhuma movimentação encontrada no período selecionado.", size=16)
            )
            return
        
        # Informações do relatório
        info_relatorio.content.controls[0].value = f"📊 Relatório de Movimentações"
        info_relatorio.content.controls[1].value = f"{len(dados)} movimentação(ões) no período"
        info_relatorio.visible = True
        
        # Cabeçalho da tabela
        tabela_relatorio.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("Data/Hora", weight="bold", size=14, expand=2),
                    ft.Text("Produto", weight="bold", size=14, expand=3),
                    ft.Text("Tipo", weight="bold", size=14, expand=1),
                    ft.Text("Qtd", weight="bold", size=14, expand=1),
                    ft.Text("Anterior→Nova", weight="bold", size=14, expand=2),
                ]),
                bgcolor="#0070C0",
                padding=10,
                border_radius=5
            )
        )
        
        # Linhas da tabela
        for item in dados:
            # Definir cor baseado no tipo
            if item["tipo"] == "entrada":
                cor_tipo = "green"
                icone_tipo = "⬆️"
            elif item["tipo"] == "saida":
                cor_tipo = "blue"
                icone_tipo = "⬇️"
            else:
                cor_tipo = "orange"
                icone_tipo = "🔄"
            
            tabela_relatorio.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(item["data_formatada"], size=12, expand=2),
                            ft.Column([
                                ft.Text(item["descricao"], size=12, weight="bold"),
                                ft.Text(f"{item['referencia']}/{item['tamanho']}", size=10, color="gray"),
                            ], expand=3, spacing=2),
                            ft.Text(f"{icone_tipo} {item['tipo'].upper()}", size=11, color=cor_tipo, weight="bold", expand=1),
                            ft.Text(str(item["quantidade"]), size=12, weight="bold", expand=1),
                            ft.Text(f"{item['quantidade_anterior']}→{item['quantidade_nova']}", size=11, expand=2),
                        ]),
                        ft.Text(item["observacao"], size=10, color="gray", italic=True) if item["observacao"] else ft.Container(height=0),
                    ], spacing=5),
                    padding=10,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5
                )
            )
    
    def exibir_relatorio_sem_movimentacao(dados):
        """Exibe relatório de produtos sem movimentação em tabela formatada"""
        if not dados:
            tabela_relatorio.controls.append(
                ft.Text("Todos os produtos tiveram movimentação recente! 🎉", size=16, color="green")
            )
            return
        
        # Informações do relatório
        info_relatorio.content.controls[0].value = f"📊 Relatório de Produtos sem Movimentação"
        info_relatorio.content.controls[1].value = f"{len(dados)} produto(s) sem movimentação"
        info_relatorio.visible = True
        
        # Cabeçalho da tabela
        tabela_relatorio.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text("Produto", weight="bold", size=14, expand=3),
                    ft.Text("Ref/Tam", weight="bold", size=14, expand=2),
                    ft.Text("Qtd", weight="bold", size=14, expand=1),
                    ft.Text("Valor", weight="bold", size=14, expand=1),
                    ft.Text("Status", weight="bold", size=14, expand=2),
                ]),
                bgcolor="#0070C0",
                padding=10,
                border_radius=5
            )
        )
        
        # Linhas da tabela
        for item in dados:
            # Definir cor baseado no status
            if "CRÍTICO" in item["status"]:
                cor_status = "red"
            elif "NUNCA" in item["status"]:
                cor_status = "purple"
            else:
                cor_status = "orange"
            
            tabela_relatorio.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(item["descricao"], size=13, weight="bold"),
                            ft.Text(item["marca"], size=11, color="gray"),
                        ], expand=3, spacing=2),
                        ft.Text(f"{item['referencia']}/{item['tamanho']}", size=12, expand=2),
                        ft.Text(str(item["quantidade"]), size=12, expand=1),
                        ft.Text(f"R$ {item['valor_total']:.2f}", size=12, expand=1),
                        ft.Column([
                            ft.Text(item["status"], size=10, color=cor_status, weight="bold"),
                            ft.Text(item["dias_sem_movimentacao"], size=9, color="gray"),
                        ], expand=2, spacing=2),
                    ]),
                    padding=10,
                    border=ft.border.all(1, "#EEEEEE"),
                    border_radius=5
                )
            )
    
    def exibir_relatorio_valor_total(valor_total):
        """Exibe relatório de valor total do estoque"""
        # Informações do relatório
        info_relatorio.content.controls[0].value = f"📊 Valor Total do Estoque"
        info_relatorio.content.controls[1].value = f"Calculado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        info_relatorio.visible = True
        
        # Exibir valor total em destaque
        tabela_relatorio.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("💰 VALOR TOTAL DO ESTOQUE", size=20, weight="bold", color="#0070C0"),
                    ft.Text(f"R$ {valor_total:,.2f}", size=32, weight="bold", color="green"),
                    ft.Divider(),
                    ft.Text("Este valor representa a soma de (quantidade × preço) de todos os produtos em estoque.", 
                           size=12, color="gray", italic=True),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=30,
                bgcolor="#E8F5E9",
                border_radius=10,
                alignment=ft.alignment.center
            )
        )
    
    def exportar_relatorio_clicado(e):
        """Exporta o relatório atual para CSV"""
        tipo = tipo_relatorio.value
        
        if not tipo:
            snack = ft.SnackBar(ft.Text("Gere um relatório antes de exportar"), bgcolor="orange")
            page.overlay.append(snack)
            snack.open = True
            page.update()
            return
        
        try:
            # Gerar dados do relatório novamente
            if tipo == "estoque_baixo":
                dados = gerar_relatorio_estoque_baixo()
                nome_arquivo = "relatorio_estoque_baixo"
                
            elif tipo == "movimentacoes":
                inicio = data_inicio.value
                fim = data_fim.value
                dados = gerar_relatorio_movimentacoes(inicio, fim)
                nome_arquivo = f"relatorio_movimentacoes_{inicio}_a_{fim}"
                
            elif tipo == "sem_movimentacao":
                dias = int(dias_sem_mov.value) if dias_sem_mov.value else 30
                dados = gerar_relatorio_produtos_sem_movimentacao(dias)
                nome_arquivo = f"relatorio_sem_movimentacao_{dias}dias"
                
            elif tipo == "valor_total":
                # Valor total não pode ser exportado como CSV (é um único valor)
                snack = ft.SnackBar(ft.Text("Relatório de valor total não pode ser exportado para CSV"), bgcolor="orange")
                page.overlay.append(snack)
                snack.open = True
                page.update()
                return
            
            if not dados:
                snack = ft.SnackBar(ft.Text("Nenhum dado para exportar"), bgcolor="orange")
                page.overlay.append(snack)
                snack.open = True
                page.update()
                return
            
            # Exportar para CSV
            caminho_arquivo = exportar_csv(dados, nome_arquivo)
            
            snack = ft.SnackBar(
                ft.Text(f"✅ Relatório exportado com sucesso!\n{caminho_arquivo}"),
                bgcolor="green"
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
            
        except Exception as ex:
            print(f"Erro ao exportar relatório: {ex}")
            snack = ft.SnackBar(ft.Text(f"Erro ao exportar relatório: {ex}"), bgcolor="red")
            page.overlay.append(snack)
            snack.open = True
            page.update()
    
    container_relatorios = ft.Column([
        ft.Text("Relatórios de Estoque", size=20, weight="bold", color="#E91E63"),
        ft.Divider(height=5, color="transparent"),
        
        # Seleção de relatório e filtros
        ft.Container(
            content=ft.Column([
                ft.Text("📋 Configuração do Relatório", size=16, weight="bold", color="#0070C0"),
                tipo_relatorio,
                ft.Row([data_inicio, data_fim], spacing=10),
                dias_sem_mov,
                ft.Row([
                    ft.ElevatedButton(
                        "Gerar Relatório",
                        on_click=gerar_relatorio_clicado,
                        bgcolor="#0070C0",
                        color="white"
                    ),
                    ft.ElevatedButton(
                        "Exportar CSV",
                        on_click=exportar_relatorio_clicado,
                        bgcolor="#4CAF50",
                        color="white"
                    ),
                ], spacing=10),
            ], spacing=10),
            padding=15,
            border=ft.border.all(2, "#0070C0"),
            border_radius=10,
            bgcolor="#F5F5F5"
        ),
        
        ft.Divider(color="#FFC000"),
        
        # Informações do relatório
        info_relatorio,
        
        # Tabela de resultados
        ft.Container(
            content=tabela_relatorio,
            padding=10,
            height=500,
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5
        ),
    ], visible=False, scroll="auto")

    # --- INTERFACE DE HISTÓRICO DE MOVIMENTAÇÕES ---
    
    # Estado do histórico com lazy loading
    historico_produto_id = ft.Text(visible=False)
    historico_produto_nome = ft.Text("", size=20, weight="bold", color="#E91E63")
    historico_state = {
        "offset": 0,
        "limit": 20,  # Carregar 20 movimentações por vez
        "total_carregado": 0,
        "tem_mais": True
    }
    
    # Filtros de data para histórico
    hist_data_inicio = ft.TextField(
        label="Data Início",
        hint_text="YYYY-MM-DD",
        value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        width=200
    )
    
    hist_data_fim = ft.TextField(
        label="Data Fim",
        hint_text="YYYY-MM-DD",
        value=datetime.now().strftime("%Y-%m-%d"),
        width=200
    )
    
    # Lista de movimentações
    lista_historico = ft.Column(spacing=10, scroll="auto")
    
    # Informações do histórico
    info_historico = ft.Container(
        content=ft.Row([
            ft.Text("", size=14, color="blue")
        ], spacing=5),
        visible=False,
        padding=10,
        bgcolor="#E3F2FD",
        border_radius=5
    )
    
    def carregar_historico(limpar=True):
        """Carrega e exibe o histórico de movimentações do produto com lazy loading"""
        loading_indicator.visible = True
        page.update()
        
        try:
            produto_id = int(historico_produto_id.value)
            data_inicio_val = hist_data_inicio.value if hist_data_inicio.value else None
            data_fim_val = hist_data_fim.value if hist_data_fim.value else None
            
            # Se limpar=True, resetar estado e limpar lista
            if limpar:
                historico_state["offset"] = 0
                historico_state["total_carregado"] = 0
                historico_state["tem_mais"] = True
                lista_historico.controls.clear()
            
            # Buscar movimentações com paginação (lazy loading)
            movimentacoes = listar_movimentacoes(
                produto_id, 
                data_inicio_val, 
                data_fim_val,
                limit=historico_state["limit"],
                offset=historico_state["offset"]
            )
            
            # Atualizar estado
            if movimentacoes:
                historico_state["offset"] += len(movimentacoes)
                historico_state["total_carregado"] += len(movimentacoes)
                historico_state["tem_mais"] = len(movimentacoes) == historico_state["limit"]
                
                # Atualizar informações (apenas na primeira carga)
                if limpar:
                    info_historico.content.controls[1].value = f"{historico_state['total_carregado']} movimentação(ões) carregada(s)"
                    info_historico.visible = True
                else:
                    info_historico.content.controls[1].value = f"{historico_state['total_carregado']} movimentação(ões) carregada(s)"
                
                # Exibir cada movimentação
                for mov in movimentacoes:
                    # Formatar data
                    data_mov = datetime.fromisoformat(mov['created_at'].replace('Z', '+00:00'))
                    data_formatada = data_mov.strftime("%d/%m/%Y %H:%M:%S")
                    
                    # Definir cor e ícone baseado no tipo
                    if mov['tipo'] == 'entrada':
                        cor_tipo = "green"
                        icone_tipo = "⬆️"
                        tipo_texto = "ENTRADA"
                    elif mov['tipo'] == 'saida':
                        cor_tipo = "blue"
                        icone_tipo = "⬇️"
                        tipo_texto = "SAÍDA"
                    else:
                        cor_tipo = "orange"
                        icone_tipo = "🔄"
                        tipo_texto = "AJUSTE"
                    
                    # Criar card de movimentação
                    mov_card = ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Row([
                                        ft.Text(data_formatada, size=13, weight="bold"),
                                    ], spacing=5),
                                    ft.Row([
                                        ft.Text(f"{icone_tipo} {tipo_texto}", size=14, color=cor_tipo, weight="bold"),
                                        ft.Text(f"Quantidade: {mov['quantidade']}", size=13),
                                    ], spacing=10),
                                    ft.Row([
                                        ft.Text(f"Anterior: {mov['quantidade_anterior']}", size=12, color="gray"),
                                        ft.Text(f"Nova: {mov['quantidade_nova']}", size=12, color="gray"),
                                    ], spacing=5),
                                ], expand=True, spacing=5),
                            ]),
                            ft.Container(
                                content=ft.Text(f"Obs: {mov['observacao']}", size=11, color="gray", italic=True),
                                visible=bool(mov.get('observacao'))
                            ),
                        ], spacing=5),
                        padding=15,
                        border=ft.border.all(1, "#EEEEEE"),
                        border_radius=10,
                        bgcolor="white"
                    )
                    
                    lista_historico.controls.append(mov_card)
                
                # Adicionar botão "Carregar mais" se houver mais movimentações
                if historico_state["tem_mais"]:
                    # Remover botão anterior se existir
                    if lista_historico.controls and isinstance(lista_historico.controls[-1], ft.Container):
                        last_control = lista_historico.controls[-1]
                        if hasattr(last_control, 'content') and isinstance(last_control.content, ft.ElevatedButton):
                            lista_historico.controls.pop()
                    
                    btn_carregar_mais = ft.Container(
                        content=ft.ElevatedButton(
                            "Carregar mais movimentações",
                            on_click=lambda _: carregar_historico(limpar=False),
                            bgcolor="#0070C0",
                            color="white"
                        ),
                        alignment=ft.alignment.center,
                        padding=10
                    )
                    lista_historico.controls.append(btn_carregar_mais)
            else:
                if limpar:
                    info_historico.visible = False
                    lista_historico.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Nenhuma movimentação encontrada", size=16, color="gray"),
                                ft.Text("Tente ajustar os filtros de data", size=12, color="gray"),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                            padding=30,
                            alignment=ft.alignment.center
                        )
                    )
                else:
                    # Não há mais movimentações para carregar
                    historico_state["tem_mais"] = False
                    # Remover botão "Carregar mais"
                    if lista_historico.controls and isinstance(lista_historico.controls[-1], ft.Container):
                        last_control = lista_historico.controls[-1]
                        if hasattr(last_control, 'content') and isinstance(last_control.content, ft.ElevatedButton):
                            lista_historico.controls.pop()
                    
                    lista_historico.controls.append(
                        ft.Container(
                            content=ft.Text("✓ Todas as movimentações foram carregadas", size=14, color="green", weight="bold"),
                            alignment=ft.alignment.center,
                            padding=10
                        )
                    )
            
        except Exception as ex:
            print(f"Erro ao carregar histórico: {ex}")
            if limpar:
                lista_historico.controls.clear()
            lista_historico.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Erro ao carregar histórico", size=16, weight="bold", color="red")
                        ], spacing=10),
                        ft.Text(str(ex), size=12, color="gray")
                    ]),
                    padding=15,
                    bgcolor="#FFEBEE",
                    border_radius=5,
                    border=ft.border.all(1, "red")
                )
            )
            if limpar:
                info_historico.visible = False
        finally:
            loading_indicator.visible = False
            page.update()
    
    def aplicar_filtros_historico(e):
        """Aplica filtros de data e recarrega histórico"""
        carregar_historico()
    
    def desfazer_ultima_mov_clicado(e):
        """Desfaz a última movimentação do produto"""
        try:
            produto_id = int(historico_produto_id.value)
            
            # Confirmar ação
            def confirmar_desfazer(e):
                modal_confirmar_desfazer.open = False
                page.update()
                
                loading_indicator.visible = True
                page.update()
                
                sucesso = desfazer_ultima_movimentacao(produto_id)
                
                loading_indicator.visible = False
                
                if sucesso:
                    # Recarregar histórico
                    carregar_historico()
                    
                    snack = ft.SnackBar(
                        ft.Row([
                            ft.Text("✅ Última movimentação desfeita com sucesso!")
                        ]),
                        bgcolor="green"
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
                else:
                    snack = ft.SnackBar(
                        ft.Row([
                            ft.Text("❌ Nenhuma movimentação para desfazer ou erro ao desfazer")
                        ]),
                        bgcolor="red"
                    )
                    page.overlay.append(snack)
                    snack.open = True
                    page.update()
            
            def cancelar_desfazer(e):
                modal_confirmar_desfazer.open = False
                page.update()
            
            # Modal de confirmação
            modal_confirmar_desfazer = ft.AlertDialog(
                title=ft.Text("⚠️ Confirmar Desfazer", color="orange", weight="bold"),
                content=ft.Column([
                    ft.Text("Tem certeza que deseja desfazer a última movimentação?", size=14),
                    ft.Divider(),
                    ft.Text("⚠️ Esta ação reverterá a quantidade do produto para o valor anterior!", size=12, color="orange", italic=True),
                ], tight=True, height=120),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancelar_desfazer),
                    ft.ElevatedButton(
                        "Desfazer",
                        bgcolor="orange",
                        color="white",
                        on_click=confirmar_desfazer
                    ),
                ],
            )
            page.overlay.append(modal_confirmar_desfazer)
            modal_confirmar_desfazer.open = True
            page.update()
            
        except Exception as ex:
            print(f"Erro ao desfazer movimentação: {ex}")
            snack = ft.SnackBar(
                ft.Row([
                    ft.Text(f"❌ Erro: {str(ex)}")
                ]),
                bgcolor="red"
            )
            page.overlay.append(snack)
            snack.open = True
            page.update()
    
    def voltar_para_estoque(e):
        """Volta para a tela de estoque"""
        navegar(False)
    
    container_historico = ft.Column([
        ft.Row([
            ft.IconButton(
                icon_color="#0070C0",
                tooltip="Voltar para Estoque",
                on_click=voltar_para_estoque
            ),
            historico_produto_nome,
        ], spacing=10),
        ft.Divider(height=5, color="transparent"),
        
        # Filtros e ações
        ft.Container(
            content=ft.Column([
                ft.Text("📅 Filtros de Data", size=16, weight="bold", color="#0070C0"),
                ft.Row([hist_data_inicio, hist_data_fim], spacing=10),
                ft.Row([
                    ft.ElevatedButton(
                        "Aplicar Filtros",
                        on_click=aplicar_filtros_historico,
                        bgcolor="#0070C0",
                        color="white"
                    ),
                    ft.ElevatedButton(
                        "Desfazer Última Movimentação",
                        on_click=desfazer_ultima_mov_clicado,
                        bgcolor="orange",
                        color="white"
                    ),
                ], spacing=10),
            ], spacing=10),
            padding=15,
            border=ft.border.all(2, "#0070C0"),
            border_radius=10,
            bgcolor="#F5F5F5"
        ),
        
        ft.Divider(color="#FFC000"),
        
        # Informações do histórico
        info_historico,
        
        # Lista de movimentações
        ft.Container(
            content=lista_historico,
            padding=10,
            height=500,
            border=ft.border.all(1, "#EEEEEE"),
            border_radius=5
        ),
    ], visible=False, scroll="auto")
    
    def abrir_historico_produto(p):
        """Abre a tela de histórico para um produto específico"""
        historico_produto_id.value = str(p['id'])
        historico_produto_nome.value = f"Histórico: {p['descricao']}"
        
        # Resetar filtros de data
        hist_data_inicio.value = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        hist_data_fim.value = datetime.now().strftime("%Y-%m-%d")
        
        # Mostrar tela de histórico
        container_cadastro.visible = False
        container_estoque.visible = False
        container_relatorios.visible = False
        container_historico.visible = True
        
        # Carregar histórico
        carregar_historico()
        
        page.update()

    # --- INSTANCIAR TELAS DE VENDAS ---
    tela_vendas = TelaPDV(page, usuario_id, usuario_nome)
    tela_clientes = TelaClientes(page, usuario_id, usuario_nome)
    tela_relatorios = TelaRelatorios(page, usuario_id, usuario_nome)
    tela_cancelamento = TelaCancelamento(page, usuario_id, usuario_nome)
    tela_usuarios = TelaUsuarios(page, usuario_id, usuario_nome, usuario_role)
    tela_financeiro = TelaFinanceiro(page, usuario_id)
    
    # --- CUSTOM SIDEBAR MENU SETUP (must be before mudar_view) ---
    # Track selected menu item
    selected_menu_index = {"value": 0}
    menu_items = []  # Will be populated after functions are defined
    
    def update_menu_selection():
        """Update menu items to reflect current selection"""
        for i, item in enumerate(menu_items):
            item.bgcolor = "#E3F2FD" if i == selected_menu_index["value"] else "#F5F5F5"
        page.update()
    
    # --- FUNÇÃO DE NAVEGAÇÃO ---
    def mudar_view(destino: str):
        """Muda a view atual e atualiza a interface."""
        print(f"DEBUG: Mudando view para {destino}")
        estado_navegacao["view_atual"] = destino
        
        # Atualizar seleção do menu customizado
        destinos_menu = ["estoque", "vendas", "clientes", "relatorios", "cancelamento", "financeiro"]
        if usuario_role == "admin":
            destinos_menu.append("usuarios")
        
        for i, dest in enumerate(destinos_menu):
            if dest == destino:
                selected_menu_index["value"] = i
                if menu_items:
                    update_menu_selection()
                break
        
        # Mostrar/ocultar containers baseado na view
        try:
            container_estoque_wrapper.visible = (destino == "estoque")
            container_vendas.visible = (destino == "vendas")
            container_clientes.visible = (destino == "clientes")
            container_relatorios_vendas.visible = (destino == "relatorios")
            container_cancelamento.visible = (destino == "cancelamento")
            container_financeiro.visible = (destino == "financeiro")
            container_usuarios.visible = (destino == "usuarios")
            
            # Atualizar lista de estoque se necessário
            if destino == "estoque":
                atualizar_lista_visual()
            
            # Carregar lista de usuários se necessário
            if destino == "usuarios":
                tela_usuarios.carregar_usuarios()
        except NameError as e:
            print(f"ERRO: Container não definido na mudança de view: {e}")
        
        page.update()
    
    def on_nav_change(e):
        """Handler para mudança de navegação."""
        index = e.control.selected_index
        destinos = ["estoque", "vendas", "clientes", "relatorios", "cancelamento", "financeiro"]
        if usuario_role == "admin":
            destinos.append("usuarios")
        if 0 <= index < len(destinos):
            mudar_view(destinos[index])
    
    def fazer_logout(e):
        """Encerra a sessão e redireciona para login."""
        # Encerrar sessão no banco de dados
        sucesso_sessao, msg_sessao, sessao = obter_sessao_ativa()
        if sucesso_sessao and sessao:
            from database import encerrar_sessao
            encerrar_sessao(sessao["token"])
        
        # Limpar página e mostrar mensagem
        page.clean()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("✅ Logout realizado com sucesso!", size=24, weight="bold", color="green"),
                    ft.Text("Feche esta janela.", size=16),
                    ft.Text("Execute 'python app.py' para fazer login novamente.", size=14, color="#666"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                padding=50,
                alignment=ft.alignment.center
            )
        )
        page.update()

    def navegar(mostra_cadastro, mostra_relatorios=False):
        container_cadastro.visible = mostra_cadastro
        container_estoque.visible = not mostra_cadastro and not mostra_relatorios
        container_relatorios.visible = mostra_relatorios
        container_historico.visible = False
        print(f"[DEBUG] navegar() - container_estoque.visible = {container_estoque.visible}")
        if not mostra_cadastro and not mostra_relatorios: 
            atualizar_lista_visual()
        page.update()
    
    # --- CUSTOM TOP MENU (horizontal menu bar) ---
    def create_menu_item(icon, label, index):
        """Create a custom horizontal menu item"""
        def on_click(e):
            selected_menu_index["value"] = index
            mock_event = type('obj', (object,), {
                'control': type('obj', (object,), {'selected_index': index})()
            })()
            on_nav_change(mock_event)
            update_menu_selection()
        
        item = ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=20, color="#0070C0"),
                ft.Text(label, size=14, weight="bold", color="#333"),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            on_click=on_click,
            bgcolor="#F5F5F5" if index != selected_menu_index["value"] else "#E3F2FD",
            border_radius=8,
            ink=True,
        )
        return item
    
    # Populate menu items
    menu_items.append(create_menu_item(ft.icons.INVENTORY_2, "Estoque", 0))
    menu_items.append(create_menu_item(ft.icons.SHOPPING_CART, "Vendas", 1))
    menu_items.append(create_menu_item(ft.icons.PEOPLE, "Clientes", 2))
    menu_items.append(create_menu_item(ft.icons.BAR_CHART, "Relatórios", 3))
    menu_items.append(create_menu_item(ft.icons.CANCEL, "Cancelar", 4))
    menu_items.append(create_menu_item(ft.icons.ATTACH_MONEY, "Financeiro", 5))
    
    # Adicionar botão de usuários apenas para admin
    if usuario_role == "admin":
        menu_items.append(create_menu_item(ft.icons.ADMIN_PANEL_SETTINGS, "Usuários", 6))
    
    # Custom horizontal top menu bar
    top_menu_bar = ft.Container(
        content=ft.Row([
            ft.Text("🧸 DEKIDS", size=20, weight="bold", color="#0070C0"),
            ft.Container(width=20),
            ft.Row(menu_items, spacing=5),
            ft.Container(expand=True),
            ft.Row([
                ft.Text(f"👤 {usuario_nome}", size=14, weight="bold", color="#0070C0"),
                ft.Container(width=10),
                ft.ElevatedButton(
                    "Sair",
                    icon=ft.icons.LOGOUT,
                    on_click=fazer_logout,
                    bgcolor="red",
                    color="white",
                    height=40
                ),
            ], spacing=10),
        ], alignment=ft.MainAxisAlignment.START, spacing=10),
        bgcolor="#F5F5F5",
        padding=15,
        border=ft.border.only(bottom=ft.BorderSide(2, "#E0E0E0")),
    )
    
    # --- WRAPPER PARA ESTOQUE (mantém funcionalidade existente) ---
    container_estoque_wrapper = ft.Container(
        content=ft.Column([
            ft.Text("🧸 DEKIDS SISTEMA", size=32, weight="bold", color="#0070C0"),
            ft.Row([
                ft.ElevatedButton("NOVO PRODUTO", on_click=lambda _: navegar(True), bgcolor="#0070C0", color="white"),
                ft.ElevatedButton("VER ESTOQUE", on_click=lambda _: navegar(False), bgcolor="#E91E63", color="white"),
                ft.ElevatedButton("RELATÓRIOS", on_click=lambda _: navegar(False, True), bgcolor="#4CAF50", color="white"),
            ]),
            ft.Divider(color="#FFC000", height=20),
            container_cadastro,
            container_estoque,
            container_relatorios,
            container_historico,
        ], scroll="auto"),
        padding=20,
        visible=True,
    )
    
    # --- CONTAINERS PARA TELAS DE VENDAS ---
    container_vendas = ft.Container(
        content=tela_vendas.build(),
        padding=20,
        visible=False,
    )
    
    container_clientes = ft.Container(
        content=tela_clientes.build(),
        padding=20,
        visible=False,
    )
    
    container_relatorios_vendas = ft.Container(
        content=ft.Column([tela_relatorios.build()], scroll="auto"),
        padding=20,
        visible=False,
    )
    
    container_cancelamento = ft.Container(
        content=tela_cancelamento.build(),
        padding=20,
        visible=False,
    )
    
    container_usuarios = ft.Container(
        content=tela_usuarios.build(),
        padding=20,
        visible=False,
    )

    container_financeiro = ft.Container(
        content=tela_financeiro.build(),
        padding=20,
        visible=False,
    )
    
    print("DEBUG: Prestes a adicionar layout principal...")
    # --- LAYOUT PRINCIPAL COM NAVIGATION RAIL ---
    try:
        print("DEBUG: Criando Row com componentes...")
        # Wrap all content containers - only one visible at a time
        content_area = ft.Column([
            container_estoque_wrapper,
            container_vendas,
            container_clientes,
            container_relatorios_vendas,
            container_cancelamento,
            container_financeiro,
            container_usuarios,
        ], expand=True, spacing=0)
        
        layout_column = ft.Column([
            top_menu_bar,
            content_area,
        ], expand=True, spacing=0)
        print("DEBUG: Row criado, adicionando à página...")
        page.add(layout_column)
        print("DEBUG: Layout adicionado! Atualizando página...")
        page.update()
        print("DEBUG: Página atualizada! Chamando atualizar_lista_visual...")
    except Exception as e:
        print(f"ERRO ao adicionar layout: {e}")
        import traceback
        traceback.print_exc()
    
    atualizar_lista_visual()
    print("DEBUG: atualizar_lista_visual() concluído!")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    ft.app(target=main)