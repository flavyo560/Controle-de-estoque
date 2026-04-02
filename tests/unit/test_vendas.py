"""
Testes unitários para o módulo de vendas.
"""

import pytest
from vendas import Carrinho, ItemCarrinho


class TestCarrinhoAdicionar:
    """Testes para o método adicionar_produto do Carrinho."""
    
    def test_adicionar_produto_novo(self, supabase_test, criar_produto_teste):
        """Testa adicionar um produto novo ao carrinho."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Camiseta Teste",
            preco=50.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        resultado = carrinho.adicionar_produto(produto['id'], quantidade=2)
        
        # Verificar que foi adicionado com sucesso
        assert resultado is True
        assert len(carrinho.itens) == 1
        assert carrinho.itens[0].produto_id == produto['id']
        assert carrinho.itens[0].quantidade == 2
        assert carrinho.itens[0].preco_unitario == 50.0
        assert carrinho.itens[0].descricao == "Camiseta Teste"
    
    def test_adicionar_produto_existente_incrementa_quantidade(self, supabase_test, criar_produto_teste):
        """Testa que adicionar produto existente incrementa quantidade."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Calça Teste",
            preco=80.0,
            quantidade=15
        )
        
        # Criar carrinho e adicionar produto duas vezes
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=3)
        resultado = carrinho.adicionar_produto(produto['id'], quantidade=2)
        
        # Verificar que quantidade foi incrementada, não duplicada
        assert resultado is True
        assert len(carrinho.itens) == 1
        assert carrinho.itens[0].quantidade == 5
    
    def test_adicionar_produto_estoque_insuficiente(self, supabase_test, criar_produto_teste):
        """Testa que não adiciona produto com estoque insuficiente."""
        # Criar produto com estoque limitado
        produto = criar_produto_teste(
            descricao="Produto Limitado",
            preco=30.0,
            quantidade=5
        )
        
        # Tentar adicionar quantidade maior que estoque
        carrinho = Carrinho()
        resultado = carrinho.adicionar_produto(produto['id'], quantidade=10)
        
        # Verificar que falhou
        assert resultado is False
        assert len(carrinho.itens) == 0
    
    def test_adicionar_produto_existente_excede_estoque(self, supabase_test, criar_produto_teste):
        """Testa que não incrementa se total exceder estoque."""
        # Criar produto com estoque limitado
        produto = criar_produto_teste(
            descricao="Produto Limitado 2",
            preco=40.0,
            quantidade=8
        )
        
        # Adicionar produto e tentar adicionar mais que o estoque permite
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        resultado = carrinho.adicionar_produto(produto['id'], quantidade=4)
        
        # Verificar que segunda adição falhou
        assert resultado is False
        assert carrinho.itens[0].quantidade == 5  # Quantidade não mudou
    
    def test_adicionar_produto_inexistente(self, supabase_test):
        """Testa que retorna False para produto inexistente."""
        carrinho = Carrinho()
        resultado = carrinho.adicionar_produto(produto_id=999999, quantidade=1)
        
        assert resultado is False
        assert len(carrinho.itens) == 0


class TestCarrinhoRemover:
    """Testes para o método remover_produto do Carrinho."""
    
    def test_remover_produto_existente(self, supabase_test, criar_produto_teste):
        """Testa remover um produto que existe no carrinho."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto para Remover",
            preco=60.0,
            quantidade=10
        )
        
        # Criar carrinho, adicionar e remover produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)
        resultado = carrinho.remover_produto(produto['id'])
        
        # Verificar que foi removido com sucesso
        assert resultado is True
        assert len(carrinho.itens) == 0
    
    def test_remover_produto_inexistente(self, supabase_test):
        """Testa remover um produto que não está no carrinho."""
        carrinho = Carrinho()
        resultado = carrinho.remover_produto(produto_id=999999)
        
        # Verificar que retornou False
        assert resultado is False
        assert len(carrinho.itens) == 0
    
    def test_remover_produto_com_multiplos_itens(self, supabase_test, criar_produto_teste):
        """Testa remover um produto específico quando há múltiplos itens."""
        # Criar dois produtos de teste com referências únicas
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=50.0,
            quantidade=10,
            referencia="REF-REM-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=70.0,
            quantidade=10,
            referencia="REF-REM-2"
        )
        
        # Criar carrinho e adicionar ambos produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)
        carrinho.adicionar_produto(produto2['id'], quantidade=3)
        
        # Remover apenas o primeiro produto
        resultado = carrinho.remover_produto(produto1['id'])
        
        # Verificar que apenas o primeiro foi removido
        assert resultado is True
        assert len(carrinho.itens) == 1
        assert carrinho.itens[0].produto_id == produto2['id']
        assert carrinho.itens[0].quantidade == 3


class TestCarrinhoAtualizarQuantidade:
    """Testes para o método atualizar_quantidade do Carrinho."""
    
    def test_atualizar_quantidade_sucesso(self, supabase_test, criar_produto_teste):
        """Testa atualizar quantidade de um produto no carrinho."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto para Atualizar",
            preco=45.0,
            quantidade=20
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Atualizar quantidade
        resultado = carrinho.atualizar_quantidade(produto['id'], quantidade=10)
        
        # Verificar que foi atualizado com sucesso
        assert resultado is True
        assert len(carrinho.itens) == 1
        assert carrinho.itens[0].quantidade == 10
    
    def test_atualizar_quantidade_estoque_insuficiente(self, supabase_test, criar_produto_teste):
        """Testa que não atualiza se nova quantidade exceder estoque."""
        # Criar produto com estoque limitado
        produto = criar_produto_teste(
            descricao="Produto Limitado",
            preco=35.0,
            quantidade=15
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Tentar atualizar para quantidade maior que estoque
        resultado = carrinho.atualizar_quantidade(produto['id'], quantidade=20)
        
        # Verificar que falhou e quantidade permaneceu a mesma
        assert resultado is False
        assert carrinho.itens[0].quantidade == 5
    
    def test_atualizar_quantidade_produto_inexistente(self, supabase_test):
        """Testa que retorna False para produto que não está no carrinho."""
        carrinho = Carrinho()
        resultado = carrinho.atualizar_quantidade(produto_id=999999, quantidade=5)
        
        assert resultado is False
    
    def test_atualizar_quantidade_zero(self, supabase_test, criar_produto_teste):
        """Testa que não permite atualizar quantidade para zero."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste Zero",
            preco=25.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Tentar atualizar para quantidade zero
        resultado = carrinho.atualizar_quantidade(produto['id'], quantidade=0)
        
        # Verificar que falhou e quantidade permaneceu a mesma
        assert resultado is False
        assert carrinho.itens[0].quantidade == 5
    
    def test_atualizar_quantidade_negativa(self, supabase_test, criar_produto_teste):
        """Testa que não permite atualizar quantidade para valor negativo."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste Negativo",
            preco=30.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Tentar atualizar para quantidade negativa
        resultado = carrinho.atualizar_quantidade(produto['id'], quantidade=-3)
        
        # Verificar que falhou e quantidade permaneceu a mesma
        assert resultado is False
        assert carrinho.itens[0].quantidade == 5
    
    def test_atualizar_quantidade_multiplos_produtos(self, supabase_test, criar_produto_teste):
        """Testa atualizar quantidade de um produto específico quando há múltiplos."""
        # Criar dois produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=40.0,
            quantidade=20,
            referencia="REF-ATU-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=60.0,
            quantidade=15,
            referencia="REF-ATU-2"
        )
        
        # Criar carrinho e adicionar ambos produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=5)
        carrinho.adicionar_produto(produto2['id'], quantidade=3)
        
        # Atualizar quantidade apenas do primeiro produto
        resultado = carrinho.atualizar_quantidade(produto1['id'], quantidade=8)
        
        # Verificar que apenas o primeiro foi atualizado
        assert resultado is True
        assert len(carrinho.itens) == 2
        assert carrinho.itens[0].quantidade == 8
        assert carrinho.itens[1].quantidade == 3


class TestCarrinhoCalcularSubtotal:
    """Testes para o método calcular_subtotal do Carrinho."""
    
    def test_calcular_subtotal_carrinho_vazio(self):
        """Testa que carrinho vazio retorna subtotal 0.0."""
        carrinho = Carrinho()
        subtotal = carrinho.calcular_subtotal()
        
        assert subtotal == 0.0
    
    def test_calcular_subtotal_um_item(self, supabase_test, criar_produto_teste):
        """Testa cálculo de subtotal com um item no carrinho."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=50.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=3)
        
        # Calcular subtotal
        subtotal = carrinho.calcular_subtotal()
        
        # Verificar: 3 * 50.0 = 150.0
        assert subtotal == 150.0
    
    def test_calcular_subtotal_multiplos_itens(self, supabase_test, criar_produto_teste):
        """Testa cálculo de subtotal com múltiplos itens no carrinho."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=30.0,
            quantidade=20,
            referencia="REF-SUB-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=45.0,
            quantidade=15,
            referencia="REF-SUB-2"
        )
        produto3 = criar_produto_teste(
            descricao="Produto 3",
            preco=60.0,
            quantidade=10,
            referencia="REF-SUB-3"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)  # 2 * 30.0 = 60.0
        carrinho.adicionar_produto(produto2['id'], quantidade=3)  # 3 * 45.0 = 135.0
        carrinho.adicionar_produto(produto3['id'], quantidade=1)  # 1 * 60.0 = 60.0
        
        # Calcular subtotal
        subtotal = carrinho.calcular_subtotal()
        
        # Verificar: 60.0 + 135.0 + 60.0 = 255.0
        assert subtotal == 255.0
    
    def test_calcular_subtotal_apos_remover_item(self, supabase_test, criar_produto_teste):
        """Testa que subtotal é recalculado corretamente após remover item."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=40.0,
            quantidade=10,
            referencia="REF-REM-SUB-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=50.0,
            quantidade=10,
            referencia="REF-REM-SUB-2"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)  # 2 * 40.0 = 80.0
        carrinho.adicionar_produto(produto2['id'], quantidade=3)  # 3 * 50.0 = 150.0
        
        # Verificar subtotal inicial: 80.0 + 150.0 = 230.0
        assert carrinho.calcular_subtotal() == 230.0
        
        # Remover primeiro produto
        carrinho.remover_produto(produto1['id'])
        
        # Verificar novo subtotal: apenas 150.0
        assert carrinho.calcular_subtotal() == 150.0
    
    def test_calcular_subtotal_apos_atualizar_quantidade(self, supabase_test, criar_produto_teste):
        """Testa que subtotal é recalculado corretamente após atualizar quantidade."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=25.0,
            quantidade=20
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=4)  # 4 * 25.0 = 100.0
        
        # Verificar subtotal inicial
        assert carrinho.calcular_subtotal() == 100.0
        
        # Atualizar quantidade
        carrinho.atualizar_quantidade(produto['id'], quantidade=8)  # 8 * 25.0 = 200.0
        
        # Verificar novo subtotal
        assert carrinho.calcular_subtotal() == 200.0
    
    def test_calcular_subtotal_com_precos_decimais(self, supabase_test, criar_produto_teste):
        """Testa cálculo de subtotal com preços decimais."""
        # Criar produto com preço decimal
        produto = criar_produto_teste(
            descricao="Produto Decimal",
            preco=19.99,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Calcular subtotal
        subtotal = carrinho.calcular_subtotal()
        
        # Verificar: 5 * 19.99 = 99.95
        assert subtotal == pytest.approx(99.95, rel=1e-2)


class TestCarrinhoCalcularDesconto:
    """Testes para o método calcular_desconto do Carrinho."""
    
    def test_calcular_desconto_sem_desconto(self, supabase_test, criar_produto_teste):
        """Testa que retorna 0.0 quando não há desconto aplicado."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)
        
        # Calcular desconto (sem desconto aplicado)
        desconto = carrinho.calcular_desconto()
        
        # Verificar que retorna 0.0
        assert desconto == 0.0
    
    def test_calcular_desconto_percentual(self, supabase_test, criar_produto_teste):
        """Testa cálculo de desconto baseado em percentual."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # Subtotal: 200.0
        
        # Aplicar desconto percentual de 10%
        carrinho.desconto_percentual = 10.0
        
        # Calcular desconto
        desconto = carrinho.calcular_desconto()
        
        # Verificar: 200.0 * 10 / 100 = 20.0
        assert desconto == 20.0
    
    def test_calcular_desconto_valor_fixo(self, supabase_test, criar_produto_teste):
        """Testa cálculo de desconto baseado em valor fixo."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=3)  # Subtotal: 300.0
        
        # Aplicar desconto em valor fixo de 50.0
        carrinho.desconto_valor = 50.0
        
        # Calcular desconto
        desconto = carrinho.calcular_desconto()
        
        # Verificar que retorna o valor fixo
        assert desconto == 50.0
    
    def test_calcular_desconto_prioriza_valor_fixo(self, supabase_test, criar_produto_teste):
        """Testa que desconto em valor fixo tem prioridade sobre percentual."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # Subtotal: 200.0
        
        # Aplicar ambos os descontos
        carrinho.desconto_percentual = 15.0  # Seria 30.0
        carrinho.desconto_valor = 25.0       # Deve usar este
        
        # Calcular desconto
        desconto = carrinho.calcular_desconto()
        
        # Verificar que retorna o valor fixo (prioridade)
        assert desconto == 25.0
    
    def test_calcular_desconto_percentual_multiplos_itens(self, supabase_test, criar_produto_teste):
        """Testa cálculo de desconto percentual com múltiplos itens."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=50.0,
            quantidade=10,
            referencia="REF-DESC-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=80.0,
            quantidade=10,
            referencia="REF-DESC-2"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)  # 100.0
        carrinho.adicionar_produto(produto2['id'], quantidade=3)  # 240.0
        # Subtotal: 340.0
        
        # Aplicar desconto percentual de 20%
        carrinho.desconto_percentual = 20.0
        
        # Calcular desconto
        desconto = carrinho.calcular_desconto()
        
        # Verificar: 340.0 * 20 / 100 = 68.0
        assert desconto == 68.0
    
    def test_calcular_desconto_percentual_carrinho_vazio(self):
        """Testa que desconto percentual em carrinho vazio retorna 0.0."""
        carrinho = Carrinho()
        carrinho.desconto_percentual = 10.0
        
        # Calcular desconto
        desconto = carrinho.calcular_desconto()
        
        # Verificar: subtotal é 0, então desconto é 0
        assert desconto == 0.0
    
    def test_calcular_desconto_percentual_decimal(self, supabase_test, criar_produto_teste):
        """Testa cálculo de desconto com percentual decimal."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=99.99,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)  # Subtotal: 499.95
        
        # Aplicar desconto percentual de 12.5%
        carrinho.desconto_percentual = 12.5
        
        # Calcular desconto
        desconto = carrinho.calcular_desconto()
        
        # Verificar: 499.95 * 12.5 / 100 = 62.49375
        assert desconto == pytest.approx(62.49375, rel=1e-2)


class TestCarrinhoCalcularTotal:
    """Testes para o método calcular_total do Carrinho."""
    
    def test_calcular_total_sem_desconto(self, supabase_test, criar_produto_teste):
        """Testa cálculo de total sem desconto aplicado."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # Subtotal: 200.0
        
        # Calcular total
        total = carrinho.calcular_total()
        
        # Verificar: 200.0 - 0.0 = 200.0
        assert total == 200.0
    
    def test_calcular_total_com_desconto_percentual(self, supabase_test, criar_produto_teste):
        """Testa cálculo de total com desconto percentual."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=3)  # Subtotal: 300.0
        
        # Aplicar desconto percentual de 10%
        carrinho.desconto_percentual = 10.0
        
        # Calcular total
        total = carrinho.calcular_total()
        
        # Verificar: 300.0 - 30.0 = 270.0
        assert total == 270.0
    
    def test_calcular_total_com_desconto_valor_fixo(self, supabase_test, criar_produto_teste):
        """Testa cálculo de total com desconto em valor fixo."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=80.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)  # Subtotal: 400.0
        
        # Aplicar desconto em valor fixo de 50.0
        carrinho.desconto_valor = 50.0
        
        # Calcular total
        total = carrinho.calcular_total()
        
        # Verificar: 400.0 - 50.0 = 350.0
        assert total == 350.0
    
    def test_calcular_total_nao_negativo(self, supabase_test, criar_produto_teste):
        """Testa que total nunca é negativo mesmo com desconto maior que subtotal."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=50.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=1)  # Subtotal: 50.0
        
        # Aplicar desconto maior que o subtotal
        carrinho.desconto_valor = 100.0
        
        # Calcular total
        total = carrinho.calcular_total()
        
        # Verificar que retorna 0.0 (não negativo)
        assert total == 0.0
    
    def test_calcular_total_carrinho_vazio(self):
        """Testa que carrinho vazio retorna total 0.0."""
        carrinho = Carrinho()
        total = carrinho.calcular_total()
        
        assert total == 0.0
    
    def test_calcular_total_multiplos_itens_com_desconto(self, supabase_test, criar_produto_teste):
        """Testa cálculo de total com múltiplos itens e desconto."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=60.0,
            quantidade=10,
            referencia="REF-TOT-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=40.0,
            quantidade=10,
            referencia="REF-TOT-2"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)  # 120.0
        carrinho.adicionar_produto(produto2['id'], quantidade=3)  # 120.0
        # Subtotal: 240.0
        
        # Aplicar desconto percentual de 25%
        carrinho.desconto_percentual = 25.0
        
        # Calcular total
        total = carrinho.calcular_total()
        
        # Verificar: 240.0 - 60.0 = 180.0
        assert total == 180.0
    
    def test_calcular_total_com_valores_decimais(self, supabase_test, criar_produto_teste):
        """Testa cálculo de total com valores decimais."""
        # Criar produto com preço decimal
        produto = criar_produto_teste(
            descricao="Produto Decimal",
            preco=19.99,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=3)  # Subtotal: 59.97
        
        # Aplicar desconto em valor fixo
        carrinho.desconto_valor = 9.97
        
        # Calcular total
        total = carrinho.calcular_total()
        
        # Verificar: 59.97 - 9.97 = 50.0
        assert total == pytest.approx(50.0, rel=1e-2)
    
    def test_calcular_total_desconto_percentual_100(self, supabase_test, criar_produto_teste):
        """Testa que desconto de 100% resulta em total 0.0."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=75.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=4)  # Subtotal: 300.0
        
        # Aplicar desconto de 100%
        carrinho.desconto_percentual = 100.0
        
        # Calcular total
        total = carrinho.calcular_total()
        
        # Verificar: 300.0 - 300.0 = 0.0
        assert total == 0.0



class TestCarrinhoAplicarDescontoPercentual:
    """Testes para o método aplicar_desconto_percentual do Carrinho."""
    
    def test_aplicar_desconto_percentual_valido(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto percentual válido."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # Subtotal: 200.0
        
        # Aplicar desconto percentual de 10%
        resultado = carrinho.aplicar_desconto_percentual(10.0)
        
        # Verificar que foi aplicado com sucesso
        assert resultado is True
        assert carrinho.desconto_percentual == 10.0
        assert carrinho.desconto_valor == 0.0  # Deve limpar desconto em valor
    
    def test_aplicar_desconto_percentual_zero(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto percentual de 0%."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=50.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=1)
        
        # Aplicar desconto de 0%
        resultado = carrinho.aplicar_desconto_percentual(0.0)
        
        # Verificar que foi aceito
        assert resultado is True
        assert carrinho.desconto_percentual == 0.0
    
    def test_aplicar_desconto_percentual_100(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto percentual de 100%."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=75.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=3)
        
        # Aplicar desconto de 100%
        resultado = carrinho.aplicar_desconto_percentual(100.0)
        
        # Verificar que foi aceito
        assert resultado is True
        assert carrinho.desconto_percentual == 100.0
    
    def test_aplicar_desconto_percentual_negativo(self, supabase_test, criar_produto_teste):
        """Testa que rejeita desconto percentual negativo."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=60.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)
        
        # Tentar aplicar desconto negativo
        resultado = carrinho.aplicar_desconto_percentual(-5.0)
        
        # Verificar que foi rejeitado
        assert resultado is False
        assert carrinho.desconto_percentual == 0.0
    
    def test_aplicar_desconto_percentual_maior_que_100(self, supabase_test, criar_produto_teste):
        """Testa que rejeita desconto percentual maior que 100."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=80.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=1)
        
        # Tentar aplicar desconto maior que 100%
        resultado = carrinho.aplicar_desconto_percentual(150.0)
        
        # Verificar que foi rejeitado
        assert resultado is False
        assert carrinho.desconto_percentual == 0.0
    
    def test_aplicar_desconto_percentual_limpa_desconto_valor(self, supabase_test, criar_produto_teste):
        """Testa que aplicar desconto percentual limpa desconto em valor."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)
        
        # Aplicar desconto em valor primeiro
        carrinho.desconto_valor = 30.0
        
        # Aplicar desconto percentual
        resultado = carrinho.aplicar_desconto_percentual(15.0)
        
        # Verificar que desconto em valor foi limpo
        assert resultado is True
        assert carrinho.desconto_percentual == 15.0
        assert carrinho.desconto_valor == 0.0
    
    def test_aplicar_desconto_percentual_carrinho_vazio(self):
        """Testa aplicar desconto percentual em carrinho vazio."""
        carrinho = Carrinho()
        
        # Aplicar desconto em carrinho vazio
        resultado = carrinho.aplicar_desconto_percentual(20.0)
        
        # Verificar que foi aceito (subtotal é 0, desconto também será 0)
        assert resultado is True
        assert carrinho.desconto_percentual == 20.0
    
    def test_aplicar_desconto_percentual_decimal(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto percentual com valor decimal."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=99.99,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Aplicar desconto percentual decimal
        resultado = carrinho.aplicar_desconto_percentual(12.5)
        
        # Verificar que foi aceito
        assert resultado is True
        assert carrinho.desconto_percentual == 12.5
    
    def test_aplicar_desconto_percentual_multiplos_itens(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto percentual com múltiplos itens."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=50.0,
            quantidade=10,
            referencia="REF-APLI-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=80.0,
            quantidade=10,
            referencia="REF-APLI-2"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)  # 100.0
        carrinho.adicionar_produto(produto2['id'], quantidade=3)  # 240.0
        # Subtotal: 340.0
        
        # Aplicar desconto percentual
        resultado = carrinho.aplicar_desconto_percentual(20.0)
        
        # Verificar que foi aplicado
        assert resultado is True
        assert carrinho.desconto_percentual == 20.0
        
        # Verificar que o total está correto
        total = carrinho.calcular_total()
        assert total == 272.0  # 340.0 - 68.0 (20% de 340)



class TestCarrinhoAplicarDescontoValor:
    """Testes para o método aplicar_desconto_valor do Carrinho."""
    
    def test_aplicar_desconto_valor_valido(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto em valor fixo válido."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # Subtotal: 200.0
        
        # Aplicar desconto em valor de 50.0
        resultado = carrinho.aplicar_desconto_valor(50.0)
        
        # Verificar que foi aplicado com sucesso
        assert resultado is True
        assert carrinho.desconto_valor == 50.0
        assert carrinho.desconto_percentual == 0.0  # Deve limpar desconto percentual
    
    def test_aplicar_desconto_valor_zero(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto em valor de 0."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=50.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=1)
        
        # Aplicar desconto de 0
        resultado = carrinho.aplicar_desconto_valor(0.0)
        
        # Verificar que foi aceito
        assert resultado is True
        assert carrinho.desconto_valor == 0.0
    
    def test_aplicar_desconto_valor_negativo(self, supabase_test, criar_produto_teste):
        """Testa que rejeita desconto em valor negativo."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=60.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)
        
        # Tentar aplicar desconto negativo
        resultado = carrinho.aplicar_desconto_valor(-10.0)
        
        # Verificar que foi rejeitado
        assert resultado is False
        assert carrinho.desconto_valor == 0.0
    
    def test_aplicar_desconto_valor_excede_total(self, supabase_test, criar_produto_teste):
        """Testa que rejeita desconto maior que o total do carrinho."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=80.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=1)  # Subtotal: 80.0
        
        # Tentar aplicar desconto maior que o total
        resultado = carrinho.aplicar_desconto_valor(100.0)
        
        # Verificar que foi rejeitado
        assert resultado is False
        assert carrinho.desconto_valor == 0.0
    
    def test_aplicar_desconto_valor_igual_total(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto igual ao total do carrinho."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=75.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # Subtotal: 150.0
        
        # Aplicar desconto igual ao total
        resultado = carrinho.aplicar_desconto_valor(150.0)
        
        # Verificar que foi aceito
        assert resultado is True
        assert carrinho.desconto_valor == 150.0
        
        # Verificar que o total é 0
        total = carrinho.calcular_total()
        assert total == 0.0
    
    def test_aplicar_desconto_valor_limpa_desconto_percentual(self, supabase_test, criar_produto_teste):
        """Testa que aplicar desconto em valor limpa desconto percentual."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # Subtotal: 200.0
        
        # Aplicar desconto percentual primeiro
        carrinho.desconto_percentual = 15.0
        
        # Aplicar desconto em valor
        resultado = carrinho.aplicar_desconto_valor(30.0)
        
        # Verificar que desconto percentual foi limpo
        assert resultado is True
        assert carrinho.desconto_valor == 30.0
        assert carrinho.desconto_percentual == 0.0
    
    def test_aplicar_desconto_valor_carrinho_vazio(self):
        """Testa que rejeita desconto em valor em carrinho vazio."""
        carrinho = Carrinho()
        
        # Tentar aplicar desconto em carrinho vazio (subtotal = 0)
        resultado = carrinho.aplicar_desconto_valor(10.0)
        
        # Verificar que foi rejeitado (desconto excede total)
        assert resultado is False
        assert carrinho.desconto_valor == 0.0
    
    def test_aplicar_desconto_valor_decimal(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto em valor com valor decimal."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=99.99,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)  # Subtotal: 499.95
        
        # Aplicar desconto em valor decimal
        resultado = carrinho.aplicar_desconto_valor(49.95)
        
        # Verificar que foi aceito
        assert resultado is True
        assert carrinho.desconto_valor == 49.95
        
        # Verificar que o total está correto
        total = carrinho.calcular_total()
        assert total == pytest.approx(450.0, rel=1e-2)
    
    def test_aplicar_desconto_valor_multiplos_itens(self, supabase_test, criar_produto_teste):
        """Testa aplicar desconto em valor com múltiplos itens."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=50.0,
            quantidade=10,
            referencia="REF-VALOR-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=80.0,
            quantidade=10,
            referencia="REF-VALOR-2"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)  # 100.0
        carrinho.adicionar_produto(produto2['id'], quantidade=3)  # 240.0
        # Subtotal: 340.0
        
        # Aplicar desconto em valor
        resultado = carrinho.aplicar_desconto_valor(40.0)
        
        # Verificar que foi aplicado
        assert resultado is True
        assert carrinho.desconto_valor == 40.0
        
        # Verificar que o total está correto
        total = carrinho.calcular_total()
        assert total == 300.0  # 340.0 - 40.0



class TestCarrinhoRemoverDesconto:
    """Testes para o método remover_desconto do Carrinho."""
    
    def test_remover_desconto_percentual(self, supabase_test, criar_produto_teste):
        """Testa remover desconto percentual aplicado."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=100.0,
            quantidade=10,
            referencia="REF-REM-1"
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # 200.0
        
        # Aplicar desconto percentual
        carrinho.aplicar_desconto_percentual(20.0)
        assert carrinho.desconto_percentual == 20.0
        assert carrinho.calcular_total() == 160.0  # 200.0 - 40.0
        
        # Remover desconto
        carrinho.remover_desconto()
        
        # Verificar que descontos foram zerados
        assert carrinho.desconto_percentual == 0.0
        assert carrinho.desconto_valor == 0.0
        
        # Verificar que o total voltou ao valor original
        assert carrinho.calcular_total() == 200.0
    
    def test_remover_desconto_valor(self, supabase_test, criar_produto_teste):
        """Testa remover desconto em valor fixo aplicado."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=150.0,
            quantidade=10,
            referencia="REF-REM-2"
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=3)  # 450.0
        
        # Aplicar desconto em valor
        carrinho.aplicar_desconto_valor(50.0)
        assert carrinho.desconto_valor == 50.0
        assert carrinho.calcular_total() == 400.0  # 450.0 - 50.0
        
        # Remover desconto
        carrinho.remover_desconto()
        
        # Verificar que descontos foram zerados
        assert carrinho.desconto_percentual == 0.0
        assert carrinho.desconto_valor == 0.0
        
        # Verificar que o total voltou ao valor original
        assert carrinho.calcular_total() == 450.0
    
    def test_remover_desconto_sem_desconto_aplicado(self, supabase_test, criar_produto_teste):
        """Testa remover desconto quando não há desconto aplicado."""
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=80.0,
            quantidade=10,
            referencia="REF-REM-3"
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)  # 160.0
        
        # Remover desconto (sem ter aplicado nenhum)
        carrinho.remover_desconto()
        
        # Verificar que descontos continuam zerados
        assert carrinho.desconto_percentual == 0.0
        assert carrinho.desconto_valor == 0.0
        
        # Verificar que o total permanece o mesmo
        assert carrinho.calcular_total() == 160.0
    
    def test_remover_desconto_carrinho_vazio(self):
        """Testa remover desconto em carrinho vazio."""
        carrinho = Carrinho()
        
        # Aplicar desconto percentual em carrinho vazio
        carrinho.aplicar_desconto_percentual(10.0)
        assert carrinho.desconto_percentual == 10.0
        
        # Remover desconto
        carrinho.remover_desconto()
        
        # Verificar que descontos foram zerados
        assert carrinho.desconto_percentual == 0.0
        assert carrinho.desconto_valor == 0.0
        assert carrinho.calcular_total() == 0.0
    
    def test_remover_desconto_multiplos_itens(self, supabase_test, criar_produto_teste):
        """Testa remover desconto com múltiplos itens no carrinho."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=60.0,
            quantidade=10,
            referencia="REF-REM-4"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=90.0,
            quantidade=10,
            referencia="REF-REM-5"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=2)  # 120.0
        carrinho.adicionar_produto(produto2['id'], quantidade=3)  # 270.0
        # Subtotal: 390.0
        
        # Aplicar desconto percentual
        carrinho.aplicar_desconto_percentual(15.0)
        assert carrinho.calcular_total() == 331.5  # 390.0 - 58.5
        
        # Remover desconto
        carrinho.remover_desconto()
        
        # Verificar que descontos foram zerados
        assert carrinho.desconto_percentual == 0.0
        assert carrinho.desconto_valor == 0.0
        
        # Verificar que o total voltou ao valor original
        assert carrinho.calcular_total() == 390.0


class TestCarrinhoValidarDisponibilidade:
    """Testes para o método validar_disponibilidade do Carrinho."""
    
    def test_validar_disponibilidade_carrinho_vazio(self):
        """Testa que carrinho vazio é considerado válido."""
        carrinho = Carrinho()
        valido, mensagens = carrinho.validar_disponibilidade()
        
        assert valido is True
        assert len(mensagens) == 0
    
    def test_validar_disponibilidade_estoque_suficiente(self, supabase_test, criar_produto_teste):
        """Testa validação com estoque suficiente para todos os itens."""
        # Criar produto de teste com estoque suficiente
        produto = criar_produto_teste(
            descricao="Produto com Estoque",
            preco=50.0,
            quantidade=20
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Validar disponibilidade
        valido, mensagens = carrinho.validar_disponibilidade()
        
        # Verificar que é válido
        assert valido is True
        assert len(mensagens) == 0
    
    def test_validar_disponibilidade_estoque_insuficiente(self, supabase_test, criar_produto_teste):
        """Testa validação com estoque insuficiente."""
        from database import supabase
        
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Limitado",
            preco=60.0,
            quantidade=10
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=5)
        
        # Reduzir estoque no banco para simular venda concorrente
        supabase.table("produtos").update({"quantidade": 3}).eq("id", produto['id']).execute()
        
        # Validar disponibilidade
        valido, mensagens = carrinho.validar_disponibilidade()
        
        # Verificar que não é válido
        assert valido is False
        assert len(mensagens) == 1
        assert "estoque insuficiente" in mensagens[0].lower()
        assert "Disponível: 3" in mensagens[0]
        assert "Solicitado: 5" in mensagens[0]
    
    def test_validar_disponibilidade_produto_sem_estoque(self, supabase_test, criar_produto_teste):
        """Testa validação com produto sem estoque."""
        from database import supabase
        
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Esgotado",
            preco=40.0,
            quantidade=5
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=2)
        
        # Zerar estoque no banco
        supabase.table("produtos").update({"quantidade": 0}).eq("id", produto['id']).execute()
        
        # Validar disponibilidade
        valido, mensagens = carrinho.validar_disponibilidade()
        
        # Verificar que não é válido
        assert valido is False
        assert len(mensagens) == 1
        # A mensagem pode ser "sem estoque disponível" ou "estoque insuficiente. Disponível: 0"
        assert ("sem estoque disponível" in mensagens[0].lower() or 
                ("estoque insuficiente" in mensagens[0].lower() and "disponível: 0" in mensagens[0].lower()))
    
    def test_validar_disponibilidade_multiplos_itens_todos_validos(self, supabase_test, criar_produto_teste):
        """Testa validação com múltiplos itens, todos com estoque suficiente."""
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto 1",
            preco=30.0,
            quantidade=15,
            referencia="REF-VAL-1"
        )
        produto2 = criar_produto_teste(
            descricao="Produto 2",
            preco=45.0,
            quantidade=20,
            referencia="REF-VAL-2"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=5)
        carrinho.adicionar_produto(produto2['id'], quantidade=8)
        
        # Validar disponibilidade
        valido, mensagens = carrinho.validar_disponibilidade()
        
        # Verificar que é válido
        assert valido is True
        assert len(mensagens) == 0
    
    def test_validar_disponibilidade_multiplos_itens_alguns_invalidos(self, supabase_test, criar_produto_teste):
        """Testa validação com múltiplos itens, alguns com estoque insuficiente."""
        from database import supabase
        
        # Criar produtos de teste
        produto1 = criar_produto_teste(
            descricao="Produto OK",
            preco=50.0,
            quantidade=20,
            referencia="REF-VAL-3"
        )
        produto2 = criar_produto_teste(
            descricao="Produto Limitado",
            preco=70.0,
            quantidade=10,
            referencia="REF-VAL-4"
        )
        produto3 = criar_produto_teste(
            descricao="Produto Esgotado",
            preco=35.0,
            quantidade=5,
            referencia="REF-VAL-5"
        )
        
        # Criar carrinho e adicionar produtos
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto1['id'], quantidade=5)
        carrinho.adicionar_produto(produto2['id'], quantidade=8)
        carrinho.adicionar_produto(produto3['id'], quantidade=3)
        
        # Reduzir estoque de produto2 e zerar produto3
        supabase.table("produtos").update({"quantidade": 5}).eq("id", produto2['id']).execute()
        supabase.table("produtos").update({"quantidade": 0}).eq("id", produto3['id']).execute()
        
        # Validar disponibilidade
        valido, mensagens = carrinho.validar_disponibilidade()
        
        # Verificar que não é válido
        assert valido is False
        assert len(mensagens) == 2
        
        # Verificar mensagens de erro
        mensagens_texto = " ".join(mensagens)
        assert "Produto Limitado" in mensagens_texto
        assert "Produto Esgotado" in mensagens_texto
    
    def test_validar_disponibilidade_atualiza_estoque_disponivel(self, supabase_test, criar_produto_teste):
        """Testa que validação atualiza o campo estoque_disponivel dos itens."""
        from database import supabase
        
        # Criar produto de teste
        produto = criar_produto_teste(
            descricao="Produto Teste",
            preco=55.0,
            quantidade=15
        )
        
        # Criar carrinho e adicionar produto
        carrinho = Carrinho()
        carrinho.adicionar_produto(produto['id'], quantidade=10)
        
        # Verificar estoque_disponivel inicial
        assert carrinho.itens[0].estoque_disponivel == 15
        
        # Reduzir estoque no banco
        supabase.table("produtos").update({"quantidade": 8}).eq("id", produto['id']).execute()
        
        # Validar disponibilidade
        valido, mensagens = carrinho.validar_disponibilidade()
        
        # Verificar que estoque_disponivel foi atualizado
        assert carrinho.itens[0].estoque_disponivel == 8
        assert valido is False
    
    def test_validar_disponibilidade_produto_inexistente(self, supabase_test):
        """Testa validação quando produto não existe mais no banco."""
        # Criar carrinho com item manual (simulando produto deletado)
        carrinho = Carrinho()
        item = ItemCarrinho(
            produto_id=999999,
            descricao="Produto Inexistente",
            quantidade=5,
            preco_unitario=100.0,
            estoque_disponivel=10
        )
        carrinho.itens.append(item)
        
        # Validar disponibilidade
        valido, mensagens = carrinho.validar_disponibilidade()
        
        # Verificar que não é válido
        assert valido is False
        assert len(mensagens) == 1
        assert "não encontrado no banco de dados" in mensagens[0].lower()



class TestBuscarProdutosVenda:
    """Testes para a função buscar_produtos_venda."""
    
    def test_buscar_por_codigo_barras(self, supabase_test, criar_produto_teste):
        """Testa busca por código de barras."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com código de barras específico
        produto = criar_produto_teste(
            descricao="Camiseta Azul",
            preco=50.0,
            quantidade=10,
            codigo_barras="7891234567890"
        )
        
        # Buscar por código de barras completo
        resultados = buscar_produtos_venda("7891234567890")
        
        # Verificar que encontrou o produto
        assert len(resultados) >= 1
        assert any(p['id'] == produto['id'] for p in resultados)
    
    def test_buscar_por_codigo_barras_parcial(self, supabase_test, criar_produto_teste):
        """Testa busca parcial por código de barras."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com código de barras específico
        produto = criar_produto_teste(
            descricao="Calça Jeans",
            preco=80.0,
            quantidade=5,
            codigo_barras="7899876543210"
        )
        
        # Buscar por parte do código de barras
        resultados = buscar_produtos_venda("98765")
        
        # Verificar que encontrou o produto
        assert len(resultados) >= 1
        assert any(p['id'] == produto['id'] for p in resultados)
    
    def test_buscar_por_referencia(self, supabase_test, criar_produto_teste):
        """Testa busca por referência."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com referência específica
        produto = criar_produto_teste(
            descricao="Vestido Floral",
            preco=120.0,
            quantidade=8,
            referencia="REF-12345"
        )
        
        # Buscar por referência
        resultados = buscar_produtos_venda("REF-12345")
        
        # Verificar que encontrou o produto
        assert len(resultados) >= 1
        assert any(p['id'] == produto['id'] for p in resultados)
    
    def test_buscar_por_referencia_parcial(self, supabase_test, criar_produto_teste):
        """Testa busca parcial por referência."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com referência específica
        produto = criar_produto_teste(
            descricao="Shorts Esportivo",
            preco=45.0,
            quantidade=12,
            referencia="SPORT-999"
        )
        
        # Buscar por parte da referência
        resultados = buscar_produtos_venda("SPORT")
        
        # Verificar que encontrou o produto
        assert len(resultados) >= 1
        assert any(p['id'] == produto['id'] for p in resultados)
    
    def test_buscar_por_descricao(self, supabase_test, criar_produto_teste):
        """Testa busca por descrição."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com descrição específica
        produto = criar_produto_teste(
            descricao="Jaqueta de Couro Preta",
            preco=250.0,
            quantidade=3
        )
        
        # Buscar por descrição completa
        resultados = buscar_produtos_venda("Jaqueta de Couro Preta")
        
        # Verificar que encontrou o produto
        assert len(resultados) >= 1
        assert any(p['id'] == produto['id'] for p in resultados)
    
    def test_buscar_por_descricao_parcial(self, supabase_test, criar_produto_teste):
        """Testa busca parcial por descrição."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com descrição específica
        produto = criar_produto_teste(
            descricao="Tênis Nike Air Max",
            preco=350.0,
            quantidade=6
        )
        
        # Buscar por parte da descrição
        resultados = buscar_produtos_venda("Air Max")
        
        # Verificar que encontrou o produto
        assert len(resultados) >= 1
        assert any(p['id'] == produto['id'] for p in resultados)
    
    def test_buscar_case_insensitive(self, supabase_test, criar_produto_teste):
        """Testa que busca é case-insensitive."""
        from vendas import buscar_produtos_venda
        
        # Criar produto
        produto = criar_produto_teste(
            descricao="Boné Adidas Original",
            preco=60.0,
            quantidade=15
        )
        
        # Buscar com diferentes cases
        resultados_lower = buscar_produtos_venda("adidas")
        resultados_upper = buscar_produtos_venda("ADIDAS")
        resultados_mixed = buscar_produtos_venda("AdIdAs")
        
        # Verificar que todos encontraram o produto
        assert any(p['id'] == produto['id'] for p in resultados_lower)
        assert any(p['id'] == produto['id'] for p in resultados_upper)
        assert any(p['id'] == produto['id'] for p in resultados_mixed)
    
    def test_buscar_apenas_disponiveis_true(self, supabase_test, criar_produto_teste):
        """Testa que apenas_disponiveis=True filtra produtos sem estoque."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com estoque
        produto_com_estoque = criar_produto_teste(
            descricao="Produto Com Estoque XYZ",
            referencia="REF-XYZ-COM-ESTOQUE",
            preco=100.0,
            quantidade=5
        )
        
        # Criar produto sem estoque
        produto_sem_estoque = criar_produto_teste(
            descricao="Produto Sem Estoque XYZ",
            referencia="REF-XYZ-SEM-ESTOQUE",
            preco=100.0,
            quantidade=0
        )
        
        # Buscar com apenas_disponiveis=True (padrão)
        resultados = buscar_produtos_venda("XYZ", apenas_disponiveis=True)
        
        # Verificar que retornou apenas produto com estoque
        ids_encontrados = [p['id'] for p in resultados]
        assert produto_com_estoque['id'] in ids_encontrados
        assert produto_sem_estoque['id'] not in ids_encontrados
    
    def test_buscar_apenas_disponiveis_false(self, supabase_test, criar_produto_teste):
        """Testa que apenas_disponiveis=False retorna todos os produtos."""
        from vendas import buscar_produtos_venda
        
        # Criar produto com estoque
        produto_com_estoque = criar_produto_teste(
            descricao="Produto Com Estoque ABC",
            referencia="REF-ABC-COM-ESTOQUE",
            preco=100.0,
            quantidade=5
        )
        
        # Criar produto sem estoque
        produto_sem_estoque = criar_produto_teste(
            descricao="Produto Sem Estoque ABC",
            referencia="REF-ABC-SEM-ESTOQUE",
            preco=100.0,
            quantidade=0
        )
        
        # Buscar com apenas_disponiveis=False
        resultados = buscar_produtos_venda("ABC", apenas_disponiveis=False)
        
        # Verificar que retornou ambos os produtos
        ids_encontrados = [p['id'] for p in resultados]
        assert produto_com_estoque['id'] in ids_encontrados
        assert produto_sem_estoque['id'] in ids_encontrados
    
    def test_buscar_termo_nao_encontrado(self, supabase_test):
        """Testa busca que não encontra nenhum produto."""
        from vendas import buscar_produtos_venda
        
        # Buscar termo que não existe
        resultados = buscar_produtos_venda("TERMO_INEXISTENTE_12345")
        
        # Verificar que retornou lista vazia
        assert resultados == []
    
    def test_buscar_retorna_informacoes_completas(self, supabase_test, criar_produto_teste):
        """Testa que busca retorna todas as informações do produto."""
        from vendas import buscar_produtos_venda
        
        # Criar produto
        produto = criar_produto_teste(
            descricao="Produto Completo Test",
            preco=150.0,
            quantidade=10,
            codigo_barras="1234567890123",
            referencia="REF-TEST-001"
        )
        
        # Buscar produto
        resultados = buscar_produtos_venda("Produto Completo Test")
        
        # Verificar que encontrou
        assert len(resultados) >= 1
        
        # Encontrar o produto específico
        produto_encontrado = next((p for p in resultados if p['id'] == produto['id']), None)
        assert produto_encontrado is not None
        
        # Verificar que contém campos importantes
        assert 'id' in produto_encontrado
        assert 'descricao' in produto_encontrado
        assert 'preco' in produto_encontrado
        assert 'quantidade' in produto_encontrado
        assert produto_encontrado['descricao'] == "Produto Completo Test"
        assert float(produto_encontrado['preco']) == 150.0
        assert int(produto_encontrado['quantidade']) == 10



class TestListarVendas:
    """Testes para a função listar_vendas."""
    
    def test_listar_vendas_sem_filtros(self, supabase_test):
        """Testa listar todas as vendas sem filtros."""
        from vendas import listar_vendas
        
        # Listar vendas sem filtros
        sucesso, mensagem, vendas = listar_vendas()
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        assert mensagem == "Vendas encontradas"
        assert isinstance(vendas, list)
    
    def test_listar_vendas_com_status(self, supabase_test):
        """Testa listar vendas filtradas por status."""
        from vendas import listar_vendas
        
        # Listar apenas vendas finalizadas
        sucesso, mensagem, vendas = listar_vendas(status='finalizada')
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        assert mensagem == "Vendas encontradas"
        assert isinstance(vendas, list)
        
        # Verificar que todas as vendas retornadas têm status 'finalizada'
        for venda in vendas:
            assert venda['status'] == 'finalizada'
    
    def test_listar_vendas_com_data_inicio(self, supabase_test):
        """Testa listar vendas filtradas por data inicial."""
        from vendas import listar_vendas
        
        # Listar vendas a partir de uma data
        sucesso, mensagem, vendas = listar_vendas(data_inicio='2024-01-01')
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        assert mensagem == "Vendas encontradas"
        assert isinstance(vendas, list)
    
    def test_listar_vendas_com_data_fim(self, supabase_test):
        """Testa listar vendas filtradas por data final."""
        from vendas import listar_vendas
        
        # Listar vendas até uma data
        sucesso, mensagem, vendas = listar_vendas(data_fim='2024-12-31')
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        assert mensagem == "Vendas encontradas"
        assert isinstance(vendas, list)
    
    def test_listar_vendas_com_usuario_id(self, supabase_test):
        """Testa listar vendas filtradas por usuário."""
        from vendas import listar_vendas
        
        # Listar vendas de um usuário específico
        sucesso, mensagem, vendas = listar_vendas(usuario_id=1)
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        assert mensagem == "Vendas encontradas"
        assert isinstance(vendas, list)
        
        # Verificar que todas as vendas retornadas são do usuário especificado
        for venda in vendas:
            assert venda['usuario_id'] == 1
    
    def test_listar_vendas_com_cliente_id(self, supabase_test):
        """Testa listar vendas filtradas por cliente."""
        from vendas import listar_vendas
        
        # Listar vendas de um cliente específico
        sucesso, mensagem, vendas = listar_vendas(cliente_id=1)
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        assert mensagem == "Vendas encontradas"
        assert isinstance(vendas, list)
        
        # Verificar que todas as vendas retornadas são do cliente especificado
        for venda in vendas:
            assert venda['cliente_id'] == 1
    
    def test_listar_vendas_ordenacao_desc(self, supabase_test):
        """Testa que vendas são ordenadas por data_hora DESC."""
        from vendas import listar_vendas
        
        # Listar vendas
        sucesso, mensagem, vendas = listar_vendas()
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        
        # Se houver mais de uma venda, verificar ordenação
        if len(vendas) > 1:
            for i in range(len(vendas) - 1):
                # Vendas mais recentes devem vir primeiro
                assert vendas[i]['data_hora'] >= vendas[i + 1]['data_hora']
    
    def test_listar_vendas_valores_convertidos_para_float(self, supabase_test):
        """Testa que valores decimais são convertidos para float."""
        from vendas import listar_vendas
        
        # Listar vendas
        sucesso, mensagem, vendas = listar_vendas()
        
        # Verificar que operação foi bem-sucedida
        assert sucesso is True
        
        # Se houver vendas, verificar tipos dos valores
        if len(vendas) > 0:
            venda = vendas[0]
            assert isinstance(venda['valor_total'], float)
            assert isinstance(venda['desconto_percentual'], float)
            assert isinstance(venda['desconto_valor'], float)
            assert isinstance(venda['valor_final'], float)
