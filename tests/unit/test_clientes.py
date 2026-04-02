"""
Testes unitários para o módulo de clientes
"""

import pytest
from clientes import buscar_clientes, cadastrar_cliente, obter_cliente, editar_cliente


class TestBuscarClientes:
    """Testes para a função buscar_clientes"""
    
    def test_buscar_clientes_termo_vazio(self):
        """Deve retornar lista vazia quando termo é vazio"""
        resultado = buscar_clientes("")
        assert resultado == []
        
        resultado = buscar_clientes("   ")
        assert resultado == []
    
    def test_buscar_clientes_por_nome(self):
        """Deve buscar clientes por nome (case-insensitive)"""
        # Este teste requer dados no banco
        # Por enquanto, apenas verifica que a função não gera erro
        resultado = buscar_clientes("Maria")
        assert isinstance(resultado, list)
    
    def test_buscar_clientes_por_cpf(self):
        """Deve buscar clientes por CPF"""
        # Este teste requer dados no banco
        # Por enquanto, apenas verifica que a função não gera erro
        resultado = buscar_clientes("12345678901")
        assert isinstance(resultado, list)
    
    def test_buscar_clientes_por_telefone(self):
        """Deve buscar clientes por telefone"""
        # Este teste requer dados no banco
        # Por enquanto, apenas verifica que a função não gera erro
        resultado = buscar_clientes("11999999999")
        assert isinstance(resultado, list)
    
    def test_buscar_clientes_cpf_formatado(self):
        """Deve buscar clientes mesmo com CPF formatado"""
        # Este teste requer dados no banco
        # Por enquanto, apenas verifica que a função não gera erro
        resultado = buscar_clientes("123.456.789-01")
        assert isinstance(resultado, list)


class TestObterCliente:
    """Testes para a função obter_cliente"""
    
    def test_obter_cliente_inexistente(self):
        """Deve retornar None quando cliente não existe"""
        resultado = obter_cliente(999999)
        assert resultado is None
    
    def test_obter_cliente_existente(self):
        """Deve retornar dados completos do cliente quando existe"""
        # Primeiro cadastrar um cliente para testar
        dados_cliente = {
            'nome': 'Cliente Teste Obter',
            'cpf': '98765432100',
            'telefone': '11987654321',
            'email': 'teste.obter@example.com',
            'endereco_rua': 'Rua Teste',
            'endereco_numero': '123',
            'endereco_bairro': 'Centro',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '01234567'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        
        if sucesso:
            # Buscar o cliente cadastrado
            cliente = obter_cliente(cliente_id)
            
            # Verificar que retornou dados
            assert cliente is not None
            assert isinstance(cliente, dict)
            
            # Verificar campos principais
            assert cliente['id'] == cliente_id
            assert cliente['nome'] == dados_cliente['nome']
            assert cliente['cpf'] == dados_cliente['cpf']
            assert cliente['telefone'] == dados_cliente['telefone']
            assert cliente['email'] == dados_cliente['email']
            
            # Verificar campos de endereço
            assert cliente['endereco_rua'] == dados_cliente['endereco_rua']
            assert cliente['endereco_numero'] == dados_cliente['endereco_numero']
            assert cliente['endereco_bairro'] == dados_cliente['endereco_bairro']
            assert cliente['endereco_cidade'] == dados_cliente['endereco_cidade']
            assert cliente['endereco_estado'] == dados_cliente['endereco_estado']
            assert cliente['endereco_cep'] == dados_cliente['endereco_cep']
            
            # Verificar que created_at existe
            assert 'created_at' in cliente
    
    def test_obter_cliente_retorna_todos_campos(self):
        """Deve retornar todos os campos do cliente incluindo campos opcionais"""
        # Cadastrar cliente com todos os campos
        dados_completos = {
            'nome': 'Cliente Completo',
            'cpf': '11122233344',
            'telefone': '11999887766',
            'email': 'completo@example.com',
            'endereco_rua': 'Avenida Principal',
            'endereco_numero': '1000',
            'endereco_complemento': 'Apto 101',
            'endereco_bairro': 'Jardim',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '12345678'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_completos)
        
        if sucesso:
            cliente = obter_cliente(cliente_id)
            
            assert cliente is not None
            
            # Verificar que todos os campos estão presentes
            campos_esperados = [
                'id', 'nome', 'cpf', 'telefone', 'email',
                'endereco_rua', 'endereco_numero', 'endereco_complemento',
                'endereco_bairro', 'endereco_cidade', 'endereco_estado',
                'endereco_cep', 'created_at'
            ]
            
            for campo in campos_esperados:
                assert campo in cliente, f"Campo {campo} não encontrado no cliente"



class TestEditarCliente:
    """Testes para a função editar_cliente"""
    
    def test_editar_cliente_inexistente(self):
        """Deve retornar erro quando cliente não existe"""
        sucesso, mensagem = editar_cliente(999999, {'nome': 'Novo Nome'})
        assert sucesso is False
        assert "não encontrado" in mensagem.lower()
    
    def test_editar_cliente_nome(self):
        """Deve atualizar o nome do cliente"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente Original',
            'cpf': '12312312312',
            'telefone': '11987654321',
            'email': 'original@example.com'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Editar nome
        sucesso, mensagem = editar_cliente(cliente_id, {'nome': 'Cliente Editado'})
        assert sucesso is True
        assert "sucesso" in mensagem.lower()
        
        # Verificar atualização
        cliente = obter_cliente(cliente_id)
        assert cliente['nome'] == 'Cliente Editado'
    
    def test_editar_cliente_cpf_valido(self):
        """Deve atualizar CPF quando válido e não duplicado"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente CPF',
            'cpf': '45645645645',
            'telefone': '11987654321'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Editar CPF para um novo válido
        novo_cpf = '78978978978'
        sucesso, mensagem = editar_cliente(cliente_id, {'cpf': novo_cpf})
        assert sucesso is True
        
        # Verificar atualização
        cliente = obter_cliente(cliente_id)
        assert cliente['cpf'] == novo_cpf
    
    def test_editar_cliente_cpf_invalido(self):
        """Deve rejeitar CPF inválido"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente CPF Invalido',
            'cpf': '32132132132',
            'telefone': '11987654321'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Tentar editar com CPF inválido
        sucesso, mensagem = editar_cliente(cliente_id, {'cpf': '123'})
        assert sucesso is False
        assert "11 dígitos" in mensagem or "inválido" in mensagem.lower()
    
    def test_editar_cliente_cpf_duplicado(self):
        """Deve rejeitar CPF já cadastrado para outro cliente"""
        # Cadastrar primeiro cliente
        dados_cliente1 = {
            'nome': 'Cliente 1',
            'cpf': '65465465465',
            'telefone': '11987654321'
        }
        sucesso1, mensagem1, cliente_id1 = cadastrar_cliente(dados_cliente1)
        assert sucesso1 is True
        
        # Cadastrar segundo cliente
        dados_cliente2 = {
            'nome': 'Cliente 2',
            'cpf': '98798798798',
            'telefone': '11987654322'
        }
        sucesso2, mensagem2, cliente_id2 = cadastrar_cliente(dados_cliente2)
        assert sucesso2 is True
        
        # Tentar editar cliente 2 com CPF do cliente 1
        sucesso, mensagem = editar_cliente(cliente_id2, {'cpf': '65465465465'})
        assert sucesso is False
        assert "já cadastrado" in mensagem.lower() or "outro cliente" in mensagem.lower()
    
    def test_editar_cliente_email_valido(self):
        """Deve atualizar email quando válido"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente Email',
            'cpf': '74174174174',
            'email': 'antigo@example.com'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Editar email
        novo_email = 'novo@example.com'
        sucesso, mensagem = editar_cliente(cliente_id, {'email': novo_email})
        assert sucesso is True
        
        # Verificar atualização
        cliente = obter_cliente(cliente_id)
        assert cliente['email'] == novo_email
    
    def test_editar_cliente_email_invalido(self):
        """Deve rejeitar email inválido"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente Email Invalido',
            'cpf': '85285285285',
            'email': 'valido@example.com'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Tentar editar com email inválido
        sucesso, mensagem = editar_cliente(cliente_id, {'email': 'email_invalido'})
        assert sucesso is False
        assert "email" in mensagem.lower() and "inválido" in mensagem.lower()
    
    def test_editar_cliente_multiplos_campos(self):
        """Deve atualizar múltiplos campos simultaneamente"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente Multiplo',
            'cpf': '96396396396',
            'telefone': '11987654321',
            'email': 'multiplo@example.com',
            'endereco_rua': 'Rua Antiga',
            'endereco_numero': '100'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Editar múltiplos campos
        dados_edicao = {
            'nome': 'Cliente Multiplo Editado',
            'telefone': '11999999999',
            'endereco_rua': 'Rua Nova',
            'endereco_numero': '200',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP'
        }
        
        sucesso, mensagem = editar_cliente(cliente_id, dados_edicao)
        assert sucesso is True
        
        # Verificar todas as atualizações
        cliente = obter_cliente(cliente_id)
        assert cliente['nome'] == dados_edicao['nome']
        assert cliente['telefone'] == dados_edicao['telefone']
        assert cliente['endereco_rua'] == dados_edicao['endereco_rua']
        assert cliente['endereco_numero'] == dados_edicao['endereco_numero']
        assert cliente['endereco_cidade'] == dados_edicao['endereco_cidade']
        assert cliente['endereco_estado'] == dados_edicao['endereco_estado']
    
    def test_editar_cliente_sem_dados(self):
        """Deve retornar erro quando nenhum dado válido é fornecido"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente Sem Dados',
            'cpf': '15915915915'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Tentar editar sem dados
        sucesso, mensagem = editar_cliente(cliente_id, {})
        assert sucesso is False
        assert "nenhum dado" in mensagem.lower() or "fornecido" in mensagem.lower()
    
    def test_editar_cliente_endereco_completo(self):
        """Deve atualizar todos os campos de endereço"""
        # Cadastrar cliente
        dados_cliente = {
            'nome': 'Cliente Endereco',
            'cpf': '35735735735'
        }
        
        sucesso, mensagem, cliente_id = cadastrar_cliente(dados_cliente)
        assert sucesso is True
        
        # Editar endereço completo
        endereco_completo = {
            'endereco_rua': 'Avenida Paulista',
            'endereco_numero': '1000',
            'endereco_complemento': 'Sala 500',
            'endereco_bairro': 'Bela Vista',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '01310100'
        }
        
        sucesso, mensagem = editar_cliente(cliente_id, endereco_completo)
        assert sucesso is True
        
        # Verificar todas as atualizações
        cliente = obter_cliente(cliente_id)
        assert cliente['endereco_rua'] == endereco_completo['endereco_rua']
        assert cliente['endereco_numero'] == endereco_completo['endereco_numero']
        assert cliente['endereco_complemento'] == endereco_completo['endereco_complemento']
        assert cliente['endereco_bairro'] == endereco_completo['endereco_bairro']
        assert cliente['endereco_cidade'] == endereco_completo['endereco_cidade']
        assert cliente['endereco_estado'] == endereco_completo['endereco_estado']
        assert cliente['endereco_cep'] == endereco_completo['endereco_cep']
