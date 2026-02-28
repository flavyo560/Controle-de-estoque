"""
Módulo de Gestão de Clientes - Sistema de Vendas DEKIDS

Este módulo gerencia o cadastro, busca, edição e histórico de compras de clientes.
"""

from typing import Optional, List, Dict, Tuple
from database import supabase


def cadastrar_cliente(dados: Dict) -> Tuple[bool, str, Optional[int]]:
    """
    Cadastra um novo cliente no sistema.
    
    Args:
        dados: Dicionário contendo os dados do cliente
            - nome: str (obrigatório)
            - cpf: str (obrigatório, 11 dígitos)
            - telefone: str (opcional)
            - email: str (opcional)
            - endereco_logradouro: str (opcional)
            - endereco_numero: str (opcional)
            - endereco_complemento: str (opcional)
            - endereco_bairro: str (opcional)
            - endereco_cidade: str (opcional)
            - endereco_estado: str (opcional)
            - endereco_cep: str (opcional)
    
    Returns:
        Tupla (sucesso, mensagem, cliente_id)
        - sucesso: bool indicando se o cadastro foi bem-sucedido
        - mensagem: str com mensagem de sucesso ou erro
        - cliente_id: int com ID do cliente cadastrado ou None em caso de erro
    
    Requisitos: 3.1, 3.2, 3.3, 3.4
    """
    from validacao_vendas import validar_cpf, validar_email
    
    try:
        # Validar campos obrigatórios
        if not dados.get('nome'):
            return False, "Nome é obrigatório", None
        
        if not dados.get('cpf'):
            return False, "CPF é obrigatório", None
        
        # Validar CPF
        cpf_valido, mensagem_cpf = validar_cpf(dados['cpf'])
        if not cpf_valido:
            return False, mensagem_cpf, None
        
        # Validar email se fornecido
        if dados.get('email'):
            email_valido, mensagem_email = validar_email(dados['email'])
            if not email_valido:
                return False, mensagem_email, None
        
        # Verificar CPF duplicado no banco
        cpf_limpo = dados['cpf'].replace('.', '').replace('-', '')
        response_cpf = supabase.table("clientes").select("id").eq("cpf", cpf_limpo).execute()
        
        if response_cpf.data and len(response_cpf.data) > 0:
            return False, "CPF já cadastrado no sistema", None
        
        # Preparar dados para inserção
        cliente_data = {
            "nome": dados['nome'],
            "cpf": cpf_limpo,
            "telefone": dados.get('telefone'),
            "email": dados.get('email'),
            "endereco_rua": dados.get('endereco_logradouro') or dados.get('endereco_rua'),
            "endereco_numero": dados.get('endereco_numero'),
            "endereco_complemento": dados.get('endereco_complemento'),
            "endereco_bairro": dados.get('endereco_bairro'),
            "endereco_cidade": dados.get('endereco_cidade'),
            "endereco_estado": dados.get('endereco_estado'),
            "endereco_cep": dados.get('endereco_cep')
        }
        
        # Inserir cliente no banco
        response = supabase.table("clientes").insert(cliente_data).execute()
        
        if response.data and len(response.data) > 0:
            cliente_id = response.data[0]['id']
            return True, "Cliente cadastrado com sucesso", cliente_id
        else:
            return False, "Erro ao cadastrar cliente no banco de dados", None
    
    except Exception as e:
        return False, f"Erro ao cadastrar cliente: {str(e)}", None


def buscar_clientes(termo: str) -> List[Dict]:
    """
    Busca clientes por CPF, nome ou telefone.
    
    Args:
        termo: Termo de busca (pode ser CPF, nome ou telefone)
    
    Returns:
        Lista de dicionários contendo dados dos clientes encontrados
    
    Requisitos: 3.5
    """
    try:
        if not termo or not termo.strip():
            return []
        
        # Limpar o termo de busca
        termo_busca = termo.strip()
        
        # Remover formatação do CPF se o termo parecer ser um CPF
        termo_cpf = termo_busca.replace('.', '').replace('-', '').replace(' ', '')
        
        # Buscar usando ILIKE para busca case-insensitive e parcial
        # Busca em CPF, nome e telefone
        response = supabase.table("clientes").select("*").or_(
            f"cpf.ilike.%{termo_cpf}%,"
            f"nome.ilike.%{termo_busca}%,"
            f"telefone.ilike.%{termo_busca}%"
        ).execute()
        
        if response.data:
            return response.data
        else:
            return []
    
    except Exception as e:
        print(f"Erro ao buscar clientes: {str(e)}")
        return []


def obter_cliente(cliente_id: int) -> Optional[Dict]:
    """
    Obtém dados completos de um cliente específico.
    
    Args:
        cliente_id: ID do cliente
    
    Returns:
        Dicionário com dados do cliente ou None se não encontrado
    
    Requisitos: 3.8
    """
    try:
        # Buscar cliente por ID
        response = supabase.table("clientes").select("*").eq("id", cliente_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return None
    
    except Exception as e:
        print(f"Erro ao obter cliente: {str(e)}")
        return None


def editar_cliente(cliente_id: int, dados: Dict) -> Tuple[bool, str]:
    """
    Edita dados de um cliente existente.

    Args:
        cliente_id: ID do cliente a ser editado
        dados: Dicionário contendo os campos a serem atualizados

    Returns:
        Tupla (sucesso, mensagem)
        - sucesso: bool indicando se a edição foi bem-sucedida
        - mensagem: str com mensagem de sucesso ou erro

    Requisitos: 3.8
    """
    from validacao_vendas import validar_cpf, validar_email

    try:
        # Verificar se o cliente existe
        cliente_existente = obter_cliente(cliente_id)
        if not cliente_existente:
            return False, "Cliente não encontrado"

        # Preparar dados para atualização (apenas campos fornecidos)
        dados_atualizacao = {}

        # Validar e processar CPF se fornecido
        if 'cpf' in dados:
            cpf_valido, mensagem_cpf = validar_cpf(dados['cpf'])
            if not cpf_valido:
                return False, mensagem_cpf

            # Limpar CPF
            cpf_limpo = dados['cpf'].replace('.', '').replace('-', '')

            # Verificar se CPF já existe em outro cliente (excluir o cliente atual da verificação)
            response_cpf = supabase.table("clientes").select("id").eq("cpf", cpf_limpo).neq("id", cliente_id).execute()

            if response_cpf.data and len(response_cpf.data) > 0:
                return False, "CPF já cadastrado para outro cliente"

            dados_atualizacao['cpf'] = cpf_limpo

        # Validar email se fornecido
        if 'email' in dados and dados['email']:
            email_valido, mensagem_email = validar_email(dados['email'])
            if not email_valido:
                return False, mensagem_email
            dados_atualizacao['email'] = dados['email']
        elif 'email' in dados and not dados['email']:
            # Permitir limpar o email
            dados_atualizacao['email'] = None

        # Adicionar outros campos se fornecidos
        campos_permitidos = [
            'nome', 'telefone', 'endereco_logradouro', 'endereco_rua',
            'endereco_numero', 'endereco_complemento', 'endereco_bairro',
            'endereco_cidade', 'endereco_estado', 'endereco_cep'
        ]

        for campo in campos_permitidos:
            if campo in dados:
                # Mapear endereco_logradouro para endereco_rua se necessário
                if campo == 'endereco_logradouro':
                    dados_atualizacao['endereco_rua'] = dados[campo]
                else:
                    dados_atualizacao[campo] = dados[campo]

        # Verificar se há dados para atualizar
        if not dados_atualizacao:
            return False, "Nenhum dado válido fornecido para atualização"

        # Atualizar cliente no banco
        response = supabase.table("clientes").update(dados_atualizacao).eq("id", cliente_id).execute()

        if response.data and len(response.data) > 0:
            return True, "Cliente atualizado com sucesso"
        else:
            return False, "Erro ao atualizar cliente no banco de dados"

    except Exception as e:
        return False, f"Erro ao editar cliente: {str(e)}"



def obter_historico_compras(cliente_id: int) -> Dict:
    """
    Obtém histórico completo de compras de um cliente.
    
    Args:
        cliente_id: ID do cliente
    
    Returns:
        Dicionário contendo:
        - vendas: Lista de vendas do cliente ordenadas por data DESC
        - valor_total_gasto: Soma de todas as vendas
        - numero_compras: Contagem de vendas
        - data_ultima_compra: Data da última compra
        - produtos_mais_comprados: Lista de produtos mais comprados
    
    Requisitos: 11.1, 11.2, 11.5, 11.6, 11.7, 11.8
    """
    try:
        # Buscar todas as vendas do cliente ordenadas por data DESC
        # Excluir vendas canceladas do histórico
        response_vendas = supabase.table("vendas").select(
            "id, data_hora, valor_final, status"
        ).eq("cliente_id", cliente_id).order("data_hora", desc=True).execute()
        
        vendas = response_vendas.data if response_vendas.data else []
        
        # Calcular métricas
        # Considerar apenas vendas finalizadas (não canceladas) para cálculos
        vendas_finalizadas = [v for v in vendas if v.get('status') == 'finalizada']
        
        # Calcular valor total gasto (soma de todas as vendas finalizadas)
        valor_total_gasto = sum(float(v.get('valor_final', 0)) for v in vendas_finalizadas)
        
        # Calcular número de compras (contagem de vendas finalizadas)
        numero_compras = len(vendas_finalizadas)
        
        # Identificar data da última compra (primeira venda finalizada na lista ordenada DESC)
        data_ultima_compra = None
        if vendas_finalizadas:
            data_ultima_compra = vendas_finalizadas[0].get('data_hora')
        
        # Agregar produtos mais comprados
        # Buscar todos os itens de venda das vendas finalizadas do cliente
        produtos_mais_comprados = []
        
        if vendas_finalizadas:
            # Obter IDs das vendas finalizadas
            vendas_ids = [v['id'] for v in vendas_finalizadas]
            
            # Buscar itens de venda com JOIN para obter informações do produto
            response_itens = supabase.table("itens_venda").select(
                "produto_id, quantidade, produtos(id, descricao, marca, referencia)"
            ).in_("venda_id", vendas_ids).execute()
            
            if response_itens.data:
                # Agregar produtos por produto_id
                produtos_agregados = {}
                
                for item in response_itens.data:
                    produto_id = item.get('produto_id')
                    quantidade = item.get('quantidade', 0)
                    produto_info = item.get('produtos')
                    
                    if produto_id not in produtos_agregados:
                        produtos_agregados[produto_id] = {
                            'produto_id': produto_id,
                            'descricao': produto_info.get('descricao') if produto_info else 'Produto desconhecido',
                            'marca': produto_info.get('marca') if produto_info else '',
                            'referencia': produto_info.get('referencia') if produto_info else '',
                            'quantidade_total': 0
                        }
                    
                    produtos_agregados[produto_id]['quantidade_total'] += quantidade
                
                # Ordenar produtos por quantidade total (descending)
                produtos_mais_comprados = sorted(
                    produtos_agregados.values(),
                    key=lambda x: x['quantidade_total'],
                    reverse=True
                )
        
        # Retornar histórico completo
        return {
            'vendas': vendas,
            'valor_total_gasto': valor_total_gasto,
            'numero_compras': numero_compras,
            'data_ultima_compra': data_ultima_compra,
            'produtos_mais_comprados': produtos_mais_comprados
        }
    
    except Exception as e:
        print(f"Erro ao obter histórico de compras: {str(e)}")
        # Retornar estrutura vazia em caso de erro
        return {
            'vendas': [],
            'valor_total_gasto': 0.0,
            'numero_compras': 0,
            'data_ultima_compra': None,
            'produtos_mais_comprados': []
        }
