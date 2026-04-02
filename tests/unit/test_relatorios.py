"""
Testes unitários para o módulo de relatórios
"""

import pytest
from datetime import datetime, timedelta
from relatorios import relatorio_vendas_periodo
from vendas import Carrinho, finalizar_venda
from clientes import cadastrar_cliente
from database import supabase


@pytest.fixture
def limpar_dados_teste():
    """Limpa dados de teste antes e depois dos testes"""
    # Limpar antes
    supabase.table('pagamentos').delete().neq('id', 0).execute()
    supabase.table('itens_venda').delete().neq('id', 0).execute()
    supabase.table('vendas').delete().neq('id', 0).execute()
    
    yield
    
    # Limpar depois
    supabase.table('pagamentos').delete().neq('id', 0).execute()
    supabase.table('itens_venda').delete().neq('id', 0).execute()
    supabase.table('vendas').delete().neq('id', 0).execute()


def test_relatorio_vendas_periodo_vazio(limpar_dados_teste):
    """Testa relatório com período sem vendas"""
    data_inicio = '2025-01-01'
    data_fim = '2025-01-31'
    
    resultado = relatorio_vendas_periodo(data_inicio, data_fim)
    
    assert resultado['faturamento_total'] == 0.0
    assert resultado['numero_vendas'] == 0
    assert resultado['ticket_medio'] == 0.0
    assert resultado['distribuicao_pagamento'] == []
    assert resultado['vendas'] == []


def test_relatorio_vendas_periodo_com_vendas(limpar_dados_teste, criar_produto_teste, criar_usuario_teste):
    """Testa relatório com vendas no período"""
    # Criar produto e usuário
    produto = criar_produto_teste(preco=100.0, quantidade=10)
    usuario = criar_usuario_teste()
    
    # Criar carrinho e finalizar venda
    carrinho = Carrinho()
    carrinho.adicionar_produto(produto['id'], 2)
    
    pagamentos = [
        {'forma_pagamento': 'dinheiro', 'valor': 200.0, 'valor_recebido': 200.0, 'troco': 0.0}
    ]
    
    sucesso, msg, venda_id = finalizar_venda(
        carrinho=carrinho,
        pagamentos=pagamentos,
        usuario_id=usuario['id'],
        cliente_id=None
    )
    
    assert sucesso, f"Falha ao finalizar venda: {msg}"
    
    # Gerar relatório
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_vendas_periodo(data_inicio, data_fim)
    
    # Verificar métricas
    assert resultado['faturamento_total'] == 200.0
    assert resultado['numero_vendas'] == 1
    assert resultado['ticket_medio'] == 200.0
    
    # Verificar distribuição de pagamento
    assert len(resultado['distribuicao_pagamento']) == 1
    assert resultado['distribuicao_pagamento'][0]['forma_pagamento'] == 'dinheiro'
    assert resultado['distribuicao_pagamento'][0]['valor'] == 200.0
    assert resultado['distribuicao_pagamento'][0]['percentual'] == 100.0
    
    # Verificar lista de vendas
    assert len(resultado['vendas']) == 1
    assert resultado['vendas'][0]['id'] == venda_id
    assert resultado['vendas'][0]['valor_final'] == 200.0


def test_relatorio_vendas_periodo_exclui_canceladas(limpar_dados_teste, criar_produto_teste, criar_usuario_teste):
    """Testa que vendas canceladas são excluídas do faturamento"""
    from vendas import cancelar_venda
    
    # Criar produto e usuário
    produto = criar_produto_teste(preco=100.0, quantidade=10)
    usuario = criar_usuario_teste()
    
    # Criar e finalizar venda
    carrinho = Carrinho()
    carrinho.adicionar_produto(produto['id'], 1)
    
    pagamentos = [
        {'forma_pagamento': 'pix', 'valor': 100.0}
    ]
    
    sucesso, msg, venda_id = finalizar_venda(
        carrinho=carrinho,
        pagamentos=pagamentos,
        usuario_id=usuario['id'],
        cliente_id=None
    )
    
    assert sucesso
    
    # Cancelar venda
    sucesso_cancelamento, msg_cancelamento = cancelar_venda(
        venda_id=venda_id,
        motivo="Teste de cancelamento",
        usuario_id=usuario['id']
    )
    
    assert sucesso_cancelamento, f"Falha ao cancelar venda: {msg_cancelamento}"
    
    # Gerar relatório
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_vendas_periodo(data_inicio, data_fim)
    
    # Verificar que venda cancelada não conta no faturamento
    assert resultado['faturamento_total'] == 0.0
    assert resultado['numero_vendas'] == 0
    assert resultado['ticket_medio'] == 0.0
    
    # Mas a venda ainda aparece na lista (com status cancelada)
    assert len(resultado['vendas']) == 1
    assert resultado['vendas'][0]['status'] == 'cancelada'


def test_relatorio_vendas_periodo_filtro_usuario(limpar_dados_teste, criar_produto_teste, criar_usuario_teste):
    """Testa filtro por vendedor"""
    # Criar produto e dois usuários
    produto = criar_produto_teste(preco=50.0, quantidade=20)
    usuario1 = criar_usuario_teste(username="vendedor1")
    usuario2 = criar_usuario_teste(username="vendedor2")
    
    # Criar venda para usuário 1
    carrinho1 = Carrinho()
    carrinho1.adicionar_produto(produto['id'], 1)
    pagamentos1 = [{'forma_pagamento': 'dinheiro', 'valor': 50.0, 'valor_recebido': 50.0, 'troco': 0.0}]
    sucesso1, _, venda_id1 = finalizar_venda(carrinho1, pagamentos1, usuario1['id'], None)
    assert sucesso1
    
    # Criar venda para usuário 2
    carrinho2 = Carrinho()
    carrinho2.adicionar_produto(produto['id'], 2)
    pagamentos2 = [{'forma_pagamento': 'pix', 'valor': 100.0}]
    sucesso2, _, venda_id2 = finalizar_venda(carrinho2, pagamentos2, usuario2['id'], None)
    assert sucesso2
    
    # Gerar relatório filtrado por usuário 1
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_vendas_periodo(data_inicio, data_fim, usuario_id=usuario1['id'])
    
    # Verificar que apenas venda do usuário 1 aparece
    assert resultado['numero_vendas'] == 1
    assert resultado['faturamento_total'] == 50.0
    assert len(resultado['vendas']) == 1
    assert resultado['vendas'][0]['id'] == venda_id1


def test_relatorio_vendas_periodo_filtro_forma_pagamento(limpar_dados_teste, criar_produto_teste, criar_usuario_teste):
    """Testa filtro por forma de pagamento"""
    # Criar produto e usuário
    produto = criar_produto_teste(preco=50.0, quantidade=20)
    usuario = criar_usuario_teste()
    
    # Criar venda com dinheiro
    carrinho1 = Carrinho()
    carrinho1.adicionar_produto(produto['id'], 1)
    pagamentos1 = [{'forma_pagamento': 'dinheiro', 'valor': 50.0, 'valor_recebido': 50.0, 'troco': 0.0}]
    sucesso1, _, venda_id1 = finalizar_venda(carrinho1, pagamentos1, usuario['id'], None)
    assert sucesso1
    
    # Criar venda com PIX
    carrinho2 = Carrinho()
    carrinho2.adicionar_produto(produto['id'], 2)
    pagamentos2 = [{'forma_pagamento': 'pix', 'valor': 100.0}]
    sucesso2, _, venda_id2 = finalizar_venda(carrinho2, pagamentos2, usuario['id'], None)
    assert sucesso2
    
    # Gerar relatório filtrado por PIX
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_vendas_periodo(data_inicio, data_fim, forma_pagamento='pix')
    
    # Verificar que apenas venda com PIX aparece
    assert resultado['numero_vendas'] == 1
    assert resultado['faturamento_total'] == 100.0
    assert len(resultado['vendas']) == 1
    assert resultado['vendas'][0]['id'] == venda_id2


def test_relatorio_produtos_mais_vendidos_basico(limpar_dados_teste, criar_produto_teste, criar_usuario_teste):
    """Testa relatório básico de produtos mais vendidos"""
    from relatorios import relatorio_produtos_mais_vendidos
    
    # Criar produtos e usuário
    produto1 = criar_produto_teste(descricao="Produto A", preco=50.0, quantidade=20)
    produto2 = criar_produto_teste(descricao="Produto B", preco=100.0, quantidade=20)
    usuario = criar_usuario_teste()
    
    # Criar venda com produto 1 (2 unidades)
    carrinho1 = Carrinho()
    carrinho1.adicionar_produto(produto1['id'], 2)
    pagamentos1 = [{'forma_pagamento': 'dinheiro', 'valor': 100.0, 'valor_recebido': 100.0, 'troco': 0.0}]
    sucesso1, _, _ = finalizar_venda(carrinho1, pagamentos1, usuario['id'], None)
    assert sucesso1
    
    # Criar venda com produto 2 (1 unidade)
    carrinho2 = Carrinho()
    carrinho2.adicionar_produto(produto2['id'], 1)
    pagamentos2 = [{'forma_pagamento': 'pix', 'valor': 100.0}]
    sucesso2, _, _ = finalizar_venda(carrinho2, pagamentos2, usuario['id'], None)
    assert sucesso2
    
    # Criar venda com produto 1 (3 unidades) - total 5 unidades
    carrinho3 = Carrinho()
    carrinho3.adicionar_produto(produto1['id'], 3)
    pagamentos3 = [{'forma_pagamento': 'pix', 'valor': 150.0}]
    sucesso3, _, _ = finalizar_venda(carrinho3, pagamentos3, usuario['id'], None)
    assert sucesso3
    
    # Gerar relatório
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_produtos_mais_vendidos(data_inicio, data_fim)
    
    # Verificar que temos 2 produtos
    assert len(resultado) == 2
    
    # Verificar que produto 1 está em primeiro (mais vendido)
    assert resultado[0]['produto_id'] == produto1['id']
    assert resultado[0]['quantidade_vendida'] == 5
    assert resultado[0]['faturamento_gerado'] == 250.0
    
    # Verificar que produto 2 está em segundo
    assert resultado[1]['produto_id'] == produto2['id']
    assert resultado[1]['quantidade_vendida'] == 1
    assert resultado[1]['faturamento_gerado'] == 100.0
    
    # Verificar percentuais de participação
    assert abs(resultado[0]['percentual_participacao'] - (250.0 / 350.0 * 100)) < 0.01
    assert abs(resultado[1]['percentual_participacao'] - (100.0 / 350.0 * 100)) < 0.01


def test_relatorio_produtos_mais_vendidos_com_limite(limpar_dados_teste, criar_produto_teste, criar_usuario_teste):
    """Testa relatório com limite de top N produtos"""
    from relatorios import relatorio_produtos_mais_vendidos
    
    # Criar 3 produtos
    produto1 = criar_produto_teste(descricao="Produto A", preco=50.0, quantidade=20)
    produto2 = criar_produto_teste(descricao="Produto B", preco=50.0, quantidade=20)
    produto3 = criar_produto_teste(descricao="Produto C", preco=50.0, quantidade=20)
    usuario = criar_usuario_teste()
    
    # Criar vendas com quantidades diferentes
    for produto_id, qtd in [(produto1['id'], 5), (produto2['id'], 3), (produto3['id'], 1)]:
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto_id, qtd)
        pagamentos = [{'forma_pagamento': 'pix', 'valor': 50.0 * qtd}]
        sucesso, _, _ = finalizar_venda(carrinho, pagamentos, usuario['id'], None)
        assert sucesso
    
    # Gerar relatório com limite de 2 produtos
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_produtos_mais_vendidos(data_inicio, data_fim, limit=2)
    
    # Verificar que retorna apenas 2 produtos
    assert len(resultado) == 2
    assert resultado[0]['produto_id'] == produto1['id']
    assert resultado[1]['produto_id'] == produto2['id']


def test_relatorio_produtos_mais_vendidos_com_filtros(limpar_dados_teste, criar_usuario_teste):
    """Testa relatório com filtros de produto"""
    from relatorios import relatorio_produtos_mais_vendidos
    from database import supabase
    import uuid
    
    # Criar produtos com diferentes características usando referências únicas
    ref_suffix = str(uuid.uuid4())[:8]
    
    produto1_data = {
        'descricao': 'Camiseta Infantil',
        'genero': 'Masculino',
        'marca': 'Nike',
        'referencia': f'CAM{ref_suffix}',
        'tamanho': 'M',
        'quantidade': 20,
        'preco': 50.0,
        'estoque_minimo': 5
    }
    produto1_response = supabase.table('produtos').insert(produto1_data).execute()
    produto1 = produto1_response.data[0]
    
    produto2_data = {
        'descricao': 'Calça Infantil',
        'genero': 'Feminino',
        'marca': 'Adidas',
        'referencia': f'CAL{ref_suffix}',
        'tamanho': 'G',
        'quantidade': 20,
        'preco': 80.0,
        'estoque_minimo': 5
    }
    produto2_response = supabase.table('produtos').insert(produto2_data).execute()
    produto2 = produto2_response.data[0]
    
    usuario = criar_usuario_teste()
    
    # Criar vendas
    for produto_id, qtd in [(produto1['id'], 3), (produto2['id'], 2)]:
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto_id, qtd)
        preco = 50.0 if produto_id == produto1['id'] else 80.0
        pagamentos = [{'forma_pagamento': 'pix', 'valor': preco * qtd}]
        sucesso, _, _ = finalizar_venda(carrinho, pagamentos, usuario['id'], None)
        assert sucesso
    
    # Gerar relatório filtrado por gênero Masculino
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_produtos_mais_vendidos(
        data_inicio, 
        data_fim, 
        filtros={'genero': 'Masculino'}
    )
    
    # Verificar que retorna apenas produto masculino
    assert len(resultado) == 1
    assert resultado[0]['produto_id'] == produto1['id']
    assert resultado[0]['quantidade_vendida'] == 3
    
    # Gerar relatório filtrado por marca Adidas
    resultado2 = relatorio_produtos_mais_vendidos(
        data_inicio, 
        data_fim, 
        filtros={'marca': 'Adidas'}
    )
    
    # Verificar que retorna apenas produto Adidas
    assert len(resultado2) == 1
    assert resultado2[0]['produto_id'] == produto2['id']
    
    # Gerar relatório filtrado por faixa de preço
    resultado3 = relatorio_produtos_mais_vendidos(
        data_inicio, 
        data_fim, 
        filtros={'preco_min': 60.0, 'preco_max': 100.0}
    )
    
    # Verificar que retorna apenas produto na faixa de preço
    assert len(resultado3) == 1
    assert resultado3[0]['produto_id'] == produto2['id']


def test_relatorio_produtos_mais_vendidos_exclui_canceladas(limpar_dados_teste, criar_produto_teste, criar_usuario_teste):
    """Testa que vendas canceladas são excluídas do relatório"""
    from relatorios import relatorio_produtos_mais_vendidos
    from vendas import cancelar_venda
    
    # Criar produto e usuário
    produto = criar_produto_teste(preco=50.0, quantidade=20)
    usuario = criar_usuario_teste()
    
    # Criar venda
    carrinho = Carrinho()
    carrinho.adicionar_produto(produto['id'], 5)
    pagamentos = [{'forma_pagamento': 'pix', 'valor': 250.0}]
    sucesso, _, venda_id = finalizar_venda(carrinho, pagamentos, usuario['id'], None)
    assert sucesso
    
    # Cancelar venda
    sucesso_cancelamento, _ = cancelar_venda(venda_id, "Teste", usuario['id'])
    assert sucesso_cancelamento
    
    # Gerar relatório
    hoje = datetime.now().date()
    data_inicio = (hoje - timedelta(days=1)).isoformat()
    data_fim = (hoje + timedelta(days=1)).isoformat()
    
    resultado = relatorio_produtos_mais_vendidos(data_inicio, data_fim)
    
    # Verificar que não há produtos no relatório (venda foi cancelada)
    assert len(resultado) == 0


def test_exportar_relatorio_csv_basico(tmp_path):
    """Testa exportação básica de relatório para CSV"""
    from relatorios import exportar_relatorio_csv
    import csv
    
    # Dados de teste
    dados = [
        {'nome': 'Produto A', 'quantidade': 10, 'preco': 50.0},
        {'nome': 'Produto B', 'quantidade': 5, 'preco': 100.0},
        {'nome': 'Produto C', 'quantidade': 3, 'preco': 75.0}
    ]
    
    # Caminho do arquivo
    caminho = tmp_path / "relatorio_teste.csv"
    
    # Exportar
    sucesso = exportar_relatorio_csv(dados, str(caminho))
    
    # Verificar sucesso
    assert sucesso is True
    
    # Verificar que arquivo foi criado
    assert caminho.exists()
    
    # Ler arquivo e verificar conteúdo
    with open(caminho, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        linhas = list(reader)
    
    # Verificar número de linhas
    assert len(linhas) == 3
    
    # Verificar conteúdo
    assert linhas[0]['nome'] == 'Produto A'
    assert linhas[0]['quantidade'] == '10'
    assert linhas[0]['preco'] == '50.0'
    
    assert linhas[1]['nome'] == 'Produto B'
    assert linhas[2]['nome'] == 'Produto C'


def test_exportar_relatorio_csv_vazio():
    """Testa exportação com dados vazios"""
    from relatorios import exportar_relatorio_csv
    
    # Dados vazios
    dados = []
    
    # Tentar exportar
    sucesso = exportar_relatorio_csv(dados, "teste.csv")
    
    # Deve retornar False
    assert sucesso is False


def test_exportar_relatorio_csv_cria_diretorios(tmp_path):
    """Testa que a função cria diretórios pai se não existirem"""
    from relatorios import exportar_relatorio_csv
    
    # Dados de teste
    dados = [
        {'coluna1': 'valor1', 'coluna2': 'valor2'}
    ]
    
    # Caminho com diretórios que não existem
    caminho = tmp_path / "subdir1" / "subdir2" / "relatorio.csv"
    
    # Exportar
    sucesso = exportar_relatorio_csv(dados, str(caminho))
    
    # Verificar sucesso
    assert sucesso is True
    
    # Verificar que arquivo foi criado
    assert caminho.exists()


def test_exportar_relatorio_csv_com_valores_complexos(tmp_path):
    """Testa exportação com valores complexos (dicts e listas)"""
    from relatorios import exportar_relatorio_csv
    import csv
    
    # Dados com valores complexos
    dados = [
        {
            'nome': 'Produto A',
            'detalhes': {'cor': 'azul', 'tamanho': 'M'},
            'tags': ['infantil', 'verão']
        }
    ]
    
    # Caminho do arquivo
    caminho = tmp_path / "relatorio_complexo.csv"
    
    # Exportar
    sucesso = exportar_relatorio_csv(dados, str(caminho))
    
    # Verificar sucesso
    assert sucesso is True
    
    # Ler arquivo e verificar que valores complexos foram convertidos para string
    with open(caminho, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        linhas = list(reader)
    
    assert len(linhas) == 1
    assert linhas[0]['nome'] == 'Produto A'
    # Valores complexos devem estar como string
    assert 'cor' in linhas[0]['detalhes']
    assert 'infantil' in linhas[0]['tags']


def test_exportar_relatorio_csv_encoding_utf8_bom(tmp_path):
    """Testa que o arquivo é salvo com UTF-8 BOM para compatibilidade com Excel"""
    from relatorios import exportar_relatorio_csv
    
    # Dados com caracteres especiais
    dados = [
        {'nome': 'Camiseta Infantil', 'descrição': 'Tamanho único'},
        {'nome': 'Calça Jeans', 'descrição': 'Cor azul'}
    ]
    
    # Caminho do arquivo
    caminho = tmp_path / "relatorio_utf8.csv"
    
    # Exportar
    sucesso = exportar_relatorio_csv(dados, str(caminho))
    assert sucesso is True
    
    # Verificar que arquivo tem BOM UTF-8
    with open(caminho, 'rb') as f:
        primeiros_bytes = f.read(3)
        # UTF-8 BOM é EF BB BF
        assert primeiros_bytes == b'\xef\xbb\xbf'
