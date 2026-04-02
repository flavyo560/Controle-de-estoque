"""
Testes unitários para funções de vendas em database.py

Validates: Requirement 5.3
"""

import pytest
from database import inserir_venda, supabase


class TestInserirVenda:
    """Testes para a função inserir_venda()"""
    
    def test_inserir_venda_completa_com_cliente(self):
        """
        Testa inserção de venda completa com todos os campos incluindo cliente.
        
        Validates: Requirement 5.3
        """
        # Arrange
        dados_venda = {
            'valor_total': 150.00,
            'desconto_percentual': 10.0,
            'desconto_valor': 0.0,
            'valor_final': 135.00,
            'cliente_id': 1,  # Assumindo que existe um cliente com ID 1
            'usuario_id': 1,  # Assumindo que existe um usuário com ID 1
            'status': 'finalizada'
        }
        
        # Act
        venda_id = inserir_venda(dados_venda)
        
        # Assert
        assert venda_id is not None, "Venda deveria ter sido inserida com sucesso"
        assert isinstance(venda_id, int), "ID da venda deve ser um inteiro"
        
        # Verificar se a venda foi realmente inserida no banco
        response = supabase.table('vendas').select('*').eq('id', venda_id).execute()
        assert len(response.data) == 1, "Venda deveria existir no banco"
        
        venda = response.data[0]
        assert venda['valor_total'] == 150.00
        assert venda['desconto_percentual'] == 10.0
        assert venda['desconto_valor'] == 0.0
        assert venda['valor_final'] == 135.00
        assert venda['cliente_id'] == 1
        assert venda['usuario_id'] == 1
        assert venda['status'] == 'finalizada'
        
        # Cleanup - remover venda de teste
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_venda_avulsa_sem_cliente(self):
        """
        Testa inserção de venda avulsa (sem cliente vinculado).
        
        Validates: Requirement 5.3
        """
        # Arrange
        dados_venda = {
            'valor_total': 50.00,
            'desconto_percentual': 0.0,
            'desconto_valor': 0.0,
            'valor_final': 50.00,
            'usuario_id': 1,
            'status': 'finalizada'
        }
        
        # Act
        venda_id = inserir_venda(dados_venda)
        
        # Assert
        assert venda_id is not None, "Venda avulsa deveria ter sido inserida com sucesso"
        assert isinstance(venda_id, int), "ID da venda deve ser um inteiro"
        
        # Verificar se a venda foi inserida sem cliente_id
        response = supabase.table('vendas').select('*').eq('id', venda_id).execute()
        assert len(response.data) == 1
        
        venda = response.data[0]
        assert venda['cliente_id'] is None, "Venda avulsa não deve ter cliente_id"
        assert venda['valor_final'] == 50.00
        assert venda['usuario_id'] == 1
        
        # Cleanup
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_venda_com_desconto_valor(self):
        """
        Testa inserção de venda com desconto em valor fixo.
        
        Validates: Requirement 5.3
        """
        # Arrange
        dados_venda = {
            'valor_total': 100.00,
            'desconto_percentual': 0.0,
            'desconto_valor': 15.00,
            'valor_final': 85.00,
            'usuario_id': 1,
            'status': 'finalizada'
        }
        
        # Act
        venda_id = inserir_venda(dados_venda)
        
        # Assert
        assert venda_id is not None
        
        response = supabase.table('vendas').select('*').eq('id', venda_id).execute()
        venda = response.data[0]
        
        assert venda['desconto_valor'] == 15.00
        assert venda['desconto_percentual'] == 0.0
        assert venda['valor_final'] == 85.00
        
        # Cleanup
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_venda_valores_padrao(self):
        """
        Testa que valores padrão são aplicados quando não fornecidos.
        
        Validates: Requirement 5.3
        """
        # Arrange - dados mínimos necessários
        dados_venda = {
            'valor_total': 75.00,
            'valor_final': 75.00,
            'usuario_id': 1
        }
        
        # Act
        venda_id = inserir_venda(dados_venda)
        
        # Assert
        assert venda_id is not None
        
        response = supabase.table('vendas').select('*').eq('id', venda_id).execute()
        venda = response.data[0]
        
        # Verificar valores padrão
        assert venda['desconto_percentual'] == 0.0, "Desconto percentual padrão deve ser 0"
        assert venda['desconto_valor'] == 0.0, "Desconto valor padrão deve ser 0"
        assert venda['status'] == 'finalizada', "Status padrão deve ser 'finalizada'"
        
        # Cleanup
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_venda_retorna_none_em_erro(self):
        """
        Testa que a função retorna None quando há erro (dados inválidos).
        
        Validates: Requirement 5.3
        """
        # Arrange - dados inválidos (faltando campos obrigatórios)
        dados_venda = {
            'valor_total': 100.00
            # Faltando valor_final e usuario_id obrigatórios
        }
        
        # Act
        venda_id = inserir_venda(dados_venda)
        
        # Assert
        assert venda_id is None, "Função deve retornar None quando há erro"



class TestInserirItensVenda:
    """Testes para a função inserir_itens_venda()"""
    
    def test_inserir_itens_venda_sucesso(self):
        """
        Testa inserção bem-sucedida de múltiplos itens de venda.
        
        Validates: Requirement 5.4
        """
        # Arrange - Primeiro criar uma venda
        from database import inserir_itens_venda
        
        dados_venda = {
            'valor_total': 200.00,
            'valor_final': 200.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None, "Venda deveria ter sido criada"
        
        # Preparar itens (assumindo que produtos com IDs 1 e 2 existem)
        itens = [
            {
                'produto_id': 1,
                'quantidade': 2,
                'preco_unitario': 50.00,
                'subtotal': 100.00
            },
            {
                'produto_id': 2,
                'quantidade': 1,
                'preco_unitario': 100.00,
                'subtotal': 100.00
            }
        ]
        
        # Act
        resultado = inserir_itens_venda(venda_id, itens)
        
        # Assert
        assert resultado is True, "Inserção de itens deveria ter sido bem-sucedida"
        
        # Verificar se os itens foram realmente inseridos
        response = supabase.table('itens_venda').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 2, "Deveriam existir 2 itens no banco"
        
        # Verificar dados do primeiro item
        item1 = next((i for i in response.data if i['produto_id'] == 1), None)
        assert item1 is not None
        assert item1['quantidade'] == 2
        assert item1['preco_unitario'] == 50.00
        assert item1['subtotal'] == 100.00
        
        # Verificar dados do segundo item
        item2 = next((i for i in response.data if i['produto_id'] == 2), None)
        assert item2 is not None
        assert item2['quantidade'] == 1
        assert item2['preco_unitario'] == 100.00
        assert item2['subtotal'] == 100.00
        
        # Cleanup
        supabase.table('itens_venda').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_itens_venda_lista_vazia(self):
        """
        Testa que função retorna True para lista vazia (não é erro).
        
        Validates: Requirement 5.4
        """
        # Arrange
        from database import inserir_itens_venda
        
        dados_venda = {
            'valor_total': 100.00,
            'valor_final': 100.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        # Act
        resultado = inserir_itens_venda(venda_id, [])
        
        # Assert
        assert resultado is True, "Lista vazia não deveria ser tratada como erro"
        
        # Verificar que nenhum item foi inserido
        response = supabase.table('itens_venda').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 0, "Não deveriam existir itens no banco"
        
        # Cleanup
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_itens_venda_unico_item(self):
        """
        Testa inserção de um único item de venda.
        
        Validates: Requirement 5.4
        """
        # Arrange
        from database import inserir_itens_venda
        
        dados_venda = {
            'valor_total': 75.00,
            'valor_final': 75.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        itens = [
            {
                'produto_id': 1,
                'quantidade': 3,
                'preco_unitario': 25.00,
                'subtotal': 75.00
            }
        ]
        
        # Act
        resultado = inserir_itens_venda(venda_id, itens)
        
        # Assert
        assert resultado is True
        
        response = supabase.table('itens_venda').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 1
        
        item = response.data[0]
        assert item['produto_id'] == 1
        assert item['quantidade'] == 3
        assert item['preco_unitario'] == 25.00
        assert item['subtotal'] == 75.00
        assert item['venda_id'] == venda_id
        
        # Cleanup
        supabase.table('itens_venda').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_itens_venda_retorna_false_em_erro(self):
        """
        Testa que função retorna False quando há erro (venda_id inválido).
        
        Validates: Requirement 5.4
        """
        # Arrange
        from database import inserir_itens_venda
        
        venda_id_invalido = 999999  # ID que provavelmente não existe
        itens = [
            {
                'produto_id': 1,
                'quantidade': 1,
                'preco_unitario': 50.00,
                'subtotal': 50.00
            }
        ]
        
        # Act
        resultado = inserir_itens_venda(venda_id_invalido, itens)
        
        # Assert
        assert resultado is False, "Função deveria retornar False para venda_id inválido"



class TestInserirPagamentos:
    """Testes para a função inserir_pagamentos()"""
    
    def test_inserir_pagamentos_multiplos_sucesso(self):
        """
        Testa inserção bem-sucedida de múltiplos pagamentos (pagamento misto).
        
        Validates: Requirement 5.5
        """
        # Arrange - Primeiro criar uma venda
        from database import inserir_pagamentos
        
        dados_venda = {
            'valor_total': 200.00,
            'valor_final': 200.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None, "Venda deveria ter sido criada"
        
        # Preparar pagamentos mistos
        pagamentos = [
            {
                'forma_pagamento': 'dinheiro',
                'valor': 100.00,
                'valor_recebido': 100.00,
                'troco': 0.00
            },
            {
                'forma_pagamento': 'cartao_debito',
                'valor': 100.00
            }
        ]
        
        # Act
        resultado = inserir_pagamentos(venda_id, pagamentos)
        
        # Assert
        assert resultado is True, "Inserção de pagamentos deveria ter sido bem-sucedida"
        
        # Verificar se os pagamentos foram realmente inseridos
        response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 2, "Deveriam existir 2 pagamentos no banco"
        
        # Verificar dados do pagamento em dinheiro
        pag_dinheiro = next((p for p in response.data if p['forma_pagamento'] == 'dinheiro'), None)
        assert pag_dinheiro is not None
        assert pag_dinheiro['valor'] == 100.00
        assert pag_dinheiro['valor_recebido'] == 100.00
        assert pag_dinheiro['troco'] == 0.00
        
        # Verificar dados do pagamento em cartão débito
        pag_debito = next((p for p in response.data if p['forma_pagamento'] == 'cartao_debito'), None)
        assert pag_debito is not None
        assert pag_debito['valor'] == 100.00
        assert pag_debito['numero_parcelas'] is None
        assert pag_debito['valor_recebido'] is None
        assert pag_debito['troco'] is None
        
        # Cleanup
        supabase.table('pagamentos').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_pagamento_dinheiro_com_troco(self):
        """
        Testa inserção de pagamento em dinheiro com troco.
        
        Validates: Requirement 5.5
        """
        # Arrange
        from database import inserir_pagamentos
        
        dados_venda = {
            'valor_total': 85.00,
            'valor_final': 85.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        pagamentos = [
            {
                'forma_pagamento': 'dinheiro',
                'valor': 85.00,
                'valor_recebido': 100.00,
                'troco': 15.00
            }
        ]
        
        # Act
        resultado = inserir_pagamentos(venda_id, pagamentos)
        
        # Assert
        assert resultado is True
        
        response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 1
        
        pagamento = response.data[0]
        assert pagamento['forma_pagamento'] == 'dinheiro'
        assert pagamento['valor'] == 85.00
        assert pagamento['valor_recebido'] == 100.00
        assert pagamento['troco'] == 15.00
        assert pagamento['venda_id'] == venda_id
        
        # Cleanup
        supabase.table('pagamentos').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_pagamento_cartao_credito_parcelado(self):
        """
        Testa inserção de pagamento em cartão de crédito parcelado.
        
        Validates: Requirement 5.5
        """
        # Arrange
        from database import inserir_pagamentos
        
        dados_venda = {
            'valor_total': 600.00,
            'valor_final': 600.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        pagamentos = [
            {
                'forma_pagamento': 'cartao_credito',
                'valor': 600.00,
                'numero_parcelas': 6
            }
        ]
        
        # Act
        resultado = inserir_pagamentos(venda_id, pagamentos)
        
        # Assert
        assert resultado is True
        
        response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 1
        
        pagamento = response.data[0]
        assert pagamento['forma_pagamento'] == 'cartao_credito'
        assert pagamento['valor'] == 600.00
        assert pagamento['numero_parcelas'] == 6
        assert pagamento['valor_recebido'] is None
        assert pagamento['troco'] is None
        
        # Cleanup
        supabase.table('pagamentos').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_pagamento_pix(self):
        """
        Testa inserção de pagamento via PIX.
        
        Validates: Requirement 5.5
        """
        # Arrange
        from database import inserir_pagamentos
        
        dados_venda = {
            'valor_total': 150.00,
            'valor_final': 150.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        pagamentos = [
            {
                'forma_pagamento': 'pix',
                'valor': 150.00
            }
        ]
        
        # Act
        resultado = inserir_pagamentos(venda_id, pagamentos)
        
        # Assert
        assert resultado is True
        
        response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 1
        
        pagamento = response.data[0]
        assert pagamento['forma_pagamento'] == 'pix'
        assert pagamento['valor'] == 150.00
        assert pagamento['numero_parcelas'] is None
        assert pagamento['valor_recebido'] is None
        assert pagamento['troco'] is None
        
        # Cleanup
        supabase.table('pagamentos').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_pagamentos_lista_vazia(self):
        """
        Testa que função retorna True para lista vazia (não é erro).
        
        Validates: Requirement 5.5
        """
        # Arrange
        from database import inserir_pagamentos
        
        dados_venda = {
            'valor_total': 100.00,
            'valor_final': 100.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        # Act
        resultado = inserir_pagamentos(venda_id, [])
        
        # Assert
        assert resultado is True, "Lista vazia não deveria ser tratada como erro"
        
        # Verificar que nenhum pagamento foi inserido
        response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 0, "Não deveriam existir pagamentos no banco"
        
        # Cleanup
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_inserir_pagamentos_retorna_false_em_erro(self):
        """
        Testa que função retorna False quando há erro (venda_id inválido).
        
        Validates: Requirement 5.5
        """
        # Arrange
        from database import inserir_pagamentos
        
        venda_id_invalido = 999999  # ID que provavelmente não existe
        pagamentos = [
            {
                'forma_pagamento': 'dinheiro',
                'valor': 50.00,
                'valor_recebido': 50.00,
                'troco': 0.00
            }
        ]
        
        # Act
        resultado = inserir_pagamentos(venda_id_invalido, pagamentos)
        
        # Assert
        assert resultado is False, "Função deveria retornar False para venda_id inválido"
    
    def test_inserir_pagamentos_campos_opcionais_omitidos(self):
        """
        Testa que campos opcionais podem ser omitidos sem causar erro.
        
        Validates: Requirement 5.5
        """
        # Arrange
        from database import inserir_pagamentos
        
        dados_venda = {
            'valor_total': 75.00,
            'valor_final': 75.00,
            'usuario_id': 1
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        # Pagamento mínimo - apenas campos obrigatórios
        pagamentos = [
            {
                'forma_pagamento': 'cartao_debito',
                'valor': 75.00
            }
        ]
        
        # Act
        resultado = inserir_pagamentos(venda_id, pagamentos)
        
        # Assert
        assert resultado is True
        
        response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
        assert len(response.data) == 1
        
        pagamento = response.data[0]
        assert pagamento['forma_pagamento'] == 'cartao_debito'
        assert pagamento['valor'] == 75.00
        # Campos opcionais devem ser None
        assert pagamento['numero_parcelas'] is None
        assert pagamento['valor_recebido'] is None
        assert pagamento['troco'] is None
        
        # Cleanup
        supabase.table('pagamentos').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()



class TestBuscarVendaCompleta:
    """Testes para a função buscar_venda_completa()"""
    
    def test_buscar_venda_completa_com_todos_dados(self):
        """
        Testa busca de venda completa com cliente, itens e pagamentos.
        
        Validates: Requirement 7.1
        """
        # Arrange - Criar uma venda completa
        from database import inserir_itens_venda, inserir_pagamentos, buscar_venda_completa
        
        # Criar venda com cliente
        dados_venda = {
            'valor_total': 200.00,
            'desconto_percentual': 10.0,
            'desconto_valor': 0.0,
            'valor_final': 180.00,
            'cliente_id': 1,  # Assumindo que existe um cliente com ID 1
            'usuario_id': 1,
            'status': 'finalizada'
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        # Adicionar itens
        itens = [
            {
                'produto_id': 1,
                'quantidade': 2,
                'preco_unitario': 50.00,
                'subtotal': 100.00
            },
            {
                'produto_id': 2,
                'quantidade': 1,
                'preco_unitario': 100.00,
                'subtotal': 100.00
            }
        ]
        assert inserir_itens_venda(venda_id, itens) is True
        
        # Adicionar pagamentos
        pagamentos = [
            {
                'forma_pagamento': 'dinheiro',
                'valor': 80.00,
                'valor_recebido': 80.00,
                'troco': 0.00
            },
            {
                'forma_pagamento': 'cartao_debito',
                'valor': 100.00
            }
        ]
        assert inserir_pagamentos(venda_id, pagamentos) is True
        
        # Act
        venda_completa = buscar_venda_completa(venda_id)
        
        # Assert
        assert venda_completa is not None, "Venda deveria ter sido encontrada"
        
        # Verificar dados da venda
        assert venda_completa['id'] == venda_id
        assert venda_completa['valor_total'] == 200.00
        assert venda_completa['desconto_percentual'] == 10.0
        assert venda_completa['desconto_valor'] == 0.0
        assert venda_completa['valor_final'] == 180.00
        assert venda_completa['status'] == 'finalizada'
        
        # Verificar que cliente está presente
        assert venda_completa['cliente'] is not None, "Cliente deveria estar presente"
        assert venda_completa['cliente']['id'] == 1
        
        # Verificar que vendedor está presente
        assert venda_completa['vendedor'] is not None, "Vendedor deveria estar presente"
        assert venda_completa['vendedor']['id'] == 1
        
        # Verificar itens
        assert len(venda_completa['itens']) == 2, "Deveriam existir 2 itens"
        item1 = next((i for i in venda_completa['itens'] if i['produto_id'] == 1), None)
        assert item1 is not None
        assert item1['quantidade'] == 2
        assert item1['preco_unitario'] == 50.00
        assert item1['subtotal'] == 100.00
        assert 'produto' in item1, "Item deveria incluir dados do produto"
        
        # Verificar pagamentos
        assert len(venda_completa['pagamentos']) == 2, "Deveriam existir 2 pagamentos"
        pag_dinheiro = next((p for p in venda_completa['pagamentos'] if p['forma_pagamento'] == 'dinheiro'), None)
        assert pag_dinheiro is not None
        assert pag_dinheiro['valor'] == 80.00
        assert pag_dinheiro['valor_recebido'] == 80.00
        
        # Cleanup
        supabase.table('pagamentos').delete().eq('venda_id', venda_id).execute()
        supabase.table('itens_venda').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_buscar_venda_completa_venda_avulsa(self):
        """
        Testa busca de venda avulsa (sem cliente).
        
        Validates: Requirement 7.1
        """
        # Arrange
        from database import inserir_itens_venda, inserir_pagamentos, buscar_venda_completa
        
        # Criar venda avulsa (sem cliente)
        dados_venda = {
            'valor_total': 50.00,
            'valor_final': 50.00,
            'usuario_id': 1,
            'status': 'finalizada'
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        # Adicionar um item
        itens = [
            {
                'produto_id': 1,
                'quantidade': 1,
                'preco_unitario': 50.00,
                'subtotal': 50.00
            }
        ]
        assert inserir_itens_venda(venda_id, itens) is True
        
        # Adicionar pagamento
        pagamentos = [
            {
                'forma_pagamento': 'pix',
                'valor': 50.00
            }
        ]
        assert inserir_pagamentos(venda_id, pagamentos) is True
        
        # Act
        venda_completa = buscar_venda_completa(venda_id)
        
        # Assert
        assert venda_completa is not None
        assert venda_completa['id'] == venda_id
        assert venda_completa['cliente'] is None, "Venda avulsa não deve ter cliente"
        assert venda_completa['vendedor'] is not None
        assert len(venda_completa['itens']) == 1
        assert len(venda_completa['pagamentos']) == 1
        
        # Cleanup
        supabase.table('pagamentos').delete().eq('venda_id', venda_id).execute()
        supabase.table('itens_venda').delete().eq('venda_id', venda_id).execute()
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_buscar_venda_completa_venda_cancelada(self):
        """
        Testa busca de venda cancelada com dados de cancelamento.
        
        Validates: Requirement 7.1
        """
        # Arrange
        from database import buscar_venda_completa
        
        # Criar venda e depois "cancelá-la" manualmente para teste
        dados_venda = {
            'valor_total': 100.00,
            'valor_final': 100.00,
            'usuario_id': 1,
            'status': 'finalizada'
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        # Simular cancelamento atualizando status
        from datetime import datetime
        supabase.table('vendas').update({
            'status': 'cancelada',
            'data_cancelamento': datetime.now().isoformat(),
            'motivo_cancelamento': 'Teste de cancelamento',
            'usuario_cancelamento_id': 1
        }).eq('id', venda_id).execute()
        
        # Act
        venda_completa = buscar_venda_completa(venda_id)
        
        # Assert
        assert venda_completa is not None
        assert venda_completa['status'] == 'cancelada'
        assert venda_completa['data_cancelamento'] is not None
        assert venda_completa['motivo_cancelamento'] == 'Teste de cancelamento'
        assert venda_completa['usuario_cancelamento'] is not None
        assert venda_completa['usuario_cancelamento']['id'] == 1
        
        # Cleanup
        supabase.table('vendas').delete().eq('id', venda_id).execute()
    
    def test_buscar_venda_completa_venda_inexistente(self):
        """
        Testa que função retorna None para venda inexistente.
        
        Validates: Requirement 7.1
        """
        # Arrange
        from database import buscar_venda_completa
        
        venda_id_inexistente = 999999
        
        # Act
        venda_completa = buscar_venda_completa(venda_id_inexistente)
        
        # Assert
        assert venda_completa is None, "Função deveria retornar None para venda inexistente"
    
    def test_buscar_venda_completa_sem_itens_nem_pagamentos(self):
        """
        Testa busca de venda sem itens nem pagamentos (caso edge).
        
        Validates: Requirement 7.1
        """
        # Arrange
        from database import buscar_venda_completa
        
        # Criar venda sem itens nem pagamentos
        dados_venda = {
            'valor_total': 0.00,
            'valor_final': 0.00,
            'usuario_id': 1,
            'status': 'finalizada'
        }
        venda_id = inserir_venda(dados_venda)
        assert venda_id is not None
        
        # Act
        venda_completa = buscar_venda_completa(venda_id)
        
        # Assert
        assert venda_completa is not None
        assert venda_completa['id'] == venda_id
        assert len(venda_completa['itens']) == 0, "Não deveriam existir itens"
        assert len(venda_completa['pagamentos']) == 0, "Não deveriam existir pagamentos"
        
        # Cleanup
        supabase.table('vendas').delete().eq('id', venda_id).execute()
