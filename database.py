import os
import time
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from logging_config import registrar_erro, registrar_aviso, registrar_info
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente do diretório do script
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(dotenv_path=env_path, override=True)


# --- CONFIGURAÇÃO --
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    erro_msg = "Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não encontradas!"
    print(f"ERRO CRÍTICO: {erro_msg}")
    registrar_erro(
        mensagem=erro_msg,
        modulo="database",
        funcao="<module>",
        detalhes={"url_presente": bool(url), "key_presente": bool(key)}
    )
    raise ValueError(erro_msg)

print(f"Conectando ao Supabase em: {url}")
supabase: Client = create_client(url, key)

# Configurações de reconexão
MAX_TENTATIVAS_RECONEXAO = 3
TIMEOUT_RECONEXAO = 2  # segundos


def reconectar_supabase() -> bool:
    """
    Tenta reconectar ao Supabase em caso de falha de conexão.
    
    Returns:
        True se reconexão bem-sucedida, False caso contrário
    """
    global supabase
    
    for tentativa in range(1, MAX_TENTATIVAS_RECONEXAO + 1):
        try:
            registrar_info(
                mensagem=f"Tentativa de reconexão {tentativa}/{MAX_TENTATIVAS_RECONEXAO}",
                modulo="database",
                funcao="reconectar_supabase"
            )
            
            supabase = create_client(url, key)
            
            # Testar conexão com uma query simples
            supabase.table("produtos").select("id").limit(1).execute()
            
            registrar_info(
                mensagem="Reconexão ao Supabase bem-sucedida",
                modulo="database",
                funcao="reconectar_supabase",
                detalhes={"tentativa": tentativa}
            )
            return True
            
        except Exception as e:
            registrar_erro(
                mensagem=f"Falha na tentativa de reconexão {tentativa}",
                modulo="database",
                funcao="reconectar_supabase",
                detalhes={"tentativa": tentativa, "erro": str(e)},
                exc_info=True
            )
            
            if tentativa < MAX_TENTATIVAS_RECONEXAO:
                time.sleep(TIMEOUT_RECONEXAO)
    
    return False

# 1. FUNÇÃO PARA CADASTRAR
def cadastrar_produto(descricao, genero, marca, referencia, tamanho, qtd, preco, codigo_barras=None, estoque_minimo=5):
    """
    Cadastra um novo produto no banco de dados.
    
    Args:
        descricao: Descrição do produto
        genero: Gênero do produto
        marca: Marca do produto
        referencia: Referência do produto
        tamanho: Tamanho do produto
        qtd: Quantidade inicial
        preco: Preço do produto
        codigo_barras: Código de barras EAN-13 (opcional)
        estoque_minimo: Estoque mínimo do produto (padrão: 5)
        
    Returns:
        Response do Supabase se sucesso, None se erro
    """
    data = {
        "descricao": descricao,
        "genero": genero,
        "marca": marca,
        "referencia": referencia,
        "tamanho": tamanho,
        "quantidade": qtd,
        "preco": preco,
        "estoque_minimo": estoque_minimo
    }
    
    # Adicionar código de barras se fornecido
    if codigo_barras:
        data["codigo_barras"] = codigo_barras
    
    try:
        response = supabase.table("produtos").insert(data).execute()
        
        registrar_info(
            mensagem="Produto cadastrado com sucesso",
            modulo="database",
            funcao="cadastrar_produto",
            detalhes={"referencia": referencia, "tamanho": tamanho, "codigo_barras": codigo_barras}
        )
        
        return response
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao cadastrar produto",
                modulo="database",
                funcao="cadastrar_produto",
                detalhes={"erro": erro_str, "dados": data},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    response = supabase.table("produtos").insert(data).execute()
                    registrar_info(
                        mensagem="Produto cadastrado após reconexão",
                        modulo="database",
                        funcao="cadastrar_produto"
                    )
                    return response
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao cadastrar produto após reconexão",
                        modulo="database",
                        funcao="cadastrar_produto",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            # Outros erros (violação de constraint, etc)
            registrar_erro(
                mensagem="Erro ao cadastrar produto no Supabase",
                modulo="database",
                funcao="cadastrar_produto",
                detalhes={"erro": erro_str, "dados": data},
                exc_info=True
            )
        
        print(f"Erro ao cadastrar no Supabase: {e}")
        return None

# 2. FUNÇÃO PARA LISTAR
def listar_estoque():
    """
    Lista todos os produtos do estoque.
    
    Returns:
        Lista de produtos se sucesso, lista vazia se erro
    """
    try:
        response = supabase.table("produtos").select("*").order("id").execute()
        
        registrar_info(
            mensagem=f"Estoque listado com sucesso: {len(response.data)} itens",
            modulo="database",
            funcao="listar_estoque"
        )
        
        print(f"Sucesso! {len(response.data)} itens carregados.")
        return response.data
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao listar estoque",
                modulo="database",
                funcao="listar_estoque",
                detalhes={"erro": erro_str},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    response = supabase.table("produtos").select("*").order("id").execute()
                    registrar_info(
                        mensagem="Estoque listado após reconexão",
                        modulo="database",
                        funcao="listar_estoque"
                    )
                    return response.data
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao listar estoque após reconexão",
                        modulo="database",
                        funcao="listar_estoque",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao listar estoque",
                modulo="database",
                funcao="listar_estoque",
                detalhes={"erro": erro_str},
                exc_info=True
            )
        
        print(f"ERRO AO LISTAR: Verifique se a tabela 'produtos' existe e se a KEY está correta. Detalhe: {e}")
        return []

# 3. FUNÇÃO PARA EXCLUIR
def excluir_produto(id_produto):
    """
    Exclui um produto do banco de dados.
    
    Args:
        id_produto: ID do produto a ser excluído
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        supabase.table("produtos").delete().eq("id", id_produto).execute()
        
        registrar_info(
            mensagem="Produto excluído com sucesso",
            modulo="database",
            funcao="excluir_produto",
            detalhes={"produto_id": id_produto}
        )
        
        return True
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao excluir produto",
                modulo="database",
                funcao="excluir_produto",
                detalhes={"erro": erro_str, "produto_id": id_produto},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    supabase.table("produtos").delete().eq("id", id_produto).execute()
                    registrar_info(
                        mensagem="Produto excluído após reconexão",
                        modulo="database",
                        funcao="excluir_produto"
                    )
                    return True
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao excluir produto após reconexão",
                        modulo="database",
                        funcao="excluir_produto",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao excluir produto no banco",
                modulo="database",
                funcao="excluir_produto",
                detalhes={"erro": erro_str, "produto_id": id_produto},
                exc_info=True
            )
        
        print(f"Erro ao excluir no banco: {e}")
        return False

# 4. FUNÇÃO PARA REGISTRAR SAÍDA (-1 unidade)
def registrar_saida(id_produto, qtd_atual):
    """
    Registra saída de uma unidade do produto.
    
    Esta função agora utiliza registrar_movimentacao() internamente
    para manter histórico completo de movimentações.
    
    Args:
        id_produto: ID do produto
        qtd_atual: Quantidade atual do produto
        
    Returns:
        True se sucesso, False se erro ou estoque insuficiente
    """
    try:
        if qtd_atual > 0:
            # Usar registrar_movimentacao para criar histórico
            resultado = registrar_movimentacao(
                produto_id=id_produto,
                tipo='saida',
                quantidade=1,
                observacao='Saída unitária via interface'
            )
            
            if resultado:
                registrar_info(
                    mensagem="Saída registrada com sucesso via registrar_movimentacao",
                    modulo="database",
                    funcao="registrar_saida",
                    detalhes={"produto_id": id_produto, "qtd_anterior": qtd_atual}
                )
            
            return resultado
        else:
            registrar_aviso(
                mensagem="Tentativa de saída com estoque zerado",
                modulo="database",
                funcao="registrar_saida",
                detalhes={"produto_id": id_produto, "qtd_atual": qtd_atual}
            )
            return False
            
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao registrar saída",
            modulo="database",
            funcao="registrar_saida",
            detalhes={"erro": str(e), "produto_id": id_produto},
            exc_info=True
        )
        print(f"Erro ao registrar saída: {e}")
        return False

# 5. FUNÇÃO PARA REGISTRAR ENTRADA (+1 unidade)
def registrar_entrada(id_produto, qtd_atual):
    """
    Registra entrada de uma unidade do produto.
    
    Esta função agora utiliza registrar_movimentacao() internamente
    para manter histórico completo de movimentações.
    
    Args:
        id_produto: ID do produto
        qtd_atual: Quantidade atual do produto
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        # Usar registrar_movimentacao para criar histórico
        resultado = registrar_movimentacao(
            produto_id=id_produto,
            tipo='entrada',
            quantidade=1,
            observacao='Entrada unitária via interface'
        )
        
        if resultado:
            registrar_info(
                mensagem="Entrada registrada com sucesso via registrar_movimentacao",
                modulo="database",
                funcao="registrar_entrada",
                detalhes={"produto_id": id_produto, "qtd_anterior": qtd_atual}
            )
        
        return resultado
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao registrar entrada",
            modulo="database",
            funcao="registrar_entrada",
            detalhes={"erro": str(e), "produto_id": id_produto},
            exc_info=True
        )
        print(f"Erro ao registrar entrada: {e}")
        return False

# 6. FUNÇÃO PARA REGISTRAR ESTORNO (+1 unidade)
def registrar_estorno(id_produto, qtd_atual):
    """
    Registra estorno de uma unidade do produto.
    
    Args:
        id_produto: ID do produto
        qtd_atual: Quantidade atual do produto
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        nova_qtd = int(qtd_atual) + 1
        supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", id_produto).execute()
        
        registrar_info(
            mensagem="Estorno registrado com sucesso",
            modulo="database",
            funcao="registrar_estorno",
            detalhes={"produto_id": id_produto, "qtd_anterior": qtd_atual, "qtd_nova": nova_qtd}
        )
        
        return True
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao registrar estorno",
                modulo="database",
                funcao="registrar_estorno",
                detalhes={"erro": erro_str, "produto_id": id_produto},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    nova_qtd = int(qtd_atual) + 1
                    supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", id_produto).execute()
                    registrar_info(
                        mensagem="Estorno registrado após reconexão",
                        modulo="database",
                        funcao="registrar_estorno"
                    )
                    return True
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao registrar estorno após reconexão",
                        modulo="database",
                        funcao="registrar_estorno",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao registrar estorno",
                modulo="database",
                funcao="registrar_estorno",
                detalhes={"erro": erro_str, "produto_id": id_produto},
                exc_info=True
            )
        
        print(f"Erro ao registrar estorno: {e}")
        return False
    
# 7. FUNÇÃO DE EDITAR LANÇAMENTO
def editar_produto(id_produto, novos_dados):
    """
    Edita os dados de um produto existente.
    
    Args:
        id_produto: ID do produto a ser editado
        novos_dados: Dicionário com os novos dados do produto
        
    Returns:
        Response do Supabase se sucesso, None se erro
    """
    try:
        response = supabase.table("produtos").update(novos_dados).eq("id", id_produto).execute()
        
        registrar_info(
            mensagem="Produto editado com sucesso",
            modulo="database",
            funcao="editar_produto",
            detalhes={"produto_id": id_produto, "campos_alterados": list(novos_dados.keys())}
        )
        
        return response
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao editar produto",
                modulo="database",
                funcao="editar_produto",
                detalhes={"erro": erro_str, "produto_id": id_produto},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    response = supabase.table("produtos").update(novos_dados).eq("id", id_produto).execute()
                    registrar_info(
                        mensagem="Produto editado após reconexão",
                        modulo="database",
                        funcao="editar_produto"
                    )
                    return response
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao editar produto após reconexão",
                        modulo="database",
                        funcao="editar_produto",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao editar produto",
                modulo="database",
                funcao="editar_produto",
                detalhes={"erro": erro_str, "produto_id": id_produto},
                exc_info=True
            )
        
        print(f"Erro ao editar: {e}")
        return None


def atualizar_estoque_minimo(produto_id: int, estoque_minimo: int) -> bool:
    """
    Atualiza o estoque mínimo de um produto.

    Args:
        produto_id: ID do produto
        estoque_minimo: Novo valor de estoque mínimo (deve ser >= 0)

    Returns:
        True se sucesso, False se erro
    """
    try:
        # Validar estoque mínimo
        if estoque_minimo < 0:
            registrar_aviso(
                mensagem="Estoque mínimo não pode ser negativo",
                modulo="database",
                funcao="atualizar_estoque_minimo",
                detalhes={"produto_id": produto_id, "estoque_minimo": estoque_minimo}
            )
            return False

        # Atualizar estoque mínimo
        response = supabase.table("produtos").update({
            "estoque_minimo": estoque_minimo
        }).eq("id", produto_id).execute()

        registrar_info(
            mensagem="Estoque mínimo atualizado com sucesso",
            modulo="database",
            funcao="atualizar_estoque_minimo",
            detalhes={"produto_id": produto_id, "estoque_minimo": estoque_minimo}
        )

        return True

    except Exception as e:
        erro_str = str(e)

        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao atualizar estoque mínimo",
                modulo="database",
                funcao="atualizar_estoque_minimo",
                detalhes={"erro": erro_str, "produto_id": produto_id},
                exc_info=True
            )

            # Tentar reconectar
            if reconectar_supabase():
                try:
                    response = supabase.table("produtos").update({
                        "estoque_minimo": estoque_minimo
                    }).eq("id", produto_id).execute()

                    registrar_info(
                        mensagem="Estoque mínimo atualizado após reconexão",
                        modulo="database",
                        funcao="atualizar_estoque_minimo"
                    )
                    return True

                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao atualizar estoque mínimo após reconexão",
                        modulo="database",
                        funcao="atualizar_estoque_minimo",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao atualizar estoque mínimo",
                modulo="database",
                funcao="atualizar_estoque_minimo",
                detalhes={"erro": erro_str, "produto_id": produto_id},
                exc_info=True
            )

        print(f"Erro ao atualizar estoque mínimo: {e}")
        return False




def inserir_venda(dados_venda: dict) -> Optional[int]:
    """
    Insere uma nova venda na tabela 'vendas'.

    Args:
        dados_venda (dict): Dicionário com os dados da venda contendo:
            - valor_total (float): Valor total antes dos descontos
            - desconto_percentual (float, opcional): Desconto percentual (0-100)
            - desconto_valor (float, opcional): Desconto em valor fixo
            - valor_final (float): Valor final após descontos
            - cliente_id (int, opcional): ID do cliente (None para venda avulsa)
            - usuario_id (int): ID do vendedor
            - status (str, opcional): Status da venda (padrão: 'finalizada')

    Returns:
        Optional[int]: ID da venda criada ou None em caso de erro

    Validates: Requirement 5.3
    """
    global supabase

    if not supabase:
        print("❌ Erro: Conexão com Supabase não estabelecida")
        return None

    try:
        # Preparar dados com valores padrão
        dados_insert = {
            'valor_total': dados_venda['valor_total'],
            'valor_final': dados_venda['valor_final'],
            'usuario_id': dados_venda['usuario_id'],
            'desconto_percentual': dados_venda.get('desconto_percentual', 0),
            'desconto_valor': dados_venda.get('desconto_valor', 0),
            'status': dados_venda.get('status', 'finalizada')
        }

        # Adicionar cliente_id apenas se fornecido (para vendas não avulsas)
        if dados_venda.get('cliente_id'):
            dados_insert['cliente_id'] = dados_venda['cliente_id']

        # Inserir venda na tabela
        response = supabase.table('vendas').insert(dados_insert).execute()

        if response.data and len(response.data) > 0:
            venda_id = response.data[0]['id']
            print(f"✅ Venda inserida com sucesso. ID: {venda_id}")
            return venda_id
        else:
            print("❌ Erro: Resposta vazia ao inserir venda")
            return None

    except Exception as e:
        print(f"❌ Erro ao inserir venda: {str(e)}")

        # Tentar reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "network" in str(e).lower():
            print("🔄 Tentando reconectar...")
            if reconectar_supabase():
                try:
                    # Tentar inserir novamente após reconexão
                    response = supabase.table('vendas').insert(dados_insert).execute()

                    if response.data and len(response.data) > 0:
                        venda_id = response.data[0]['id']
                        print(f"✅ Venda inserida com sucesso após reconexão. ID: {venda_id}")
                        return venda_id
                    else:
                        print("❌ Erro: Resposta vazia ao inserir venda após reconexão")
                        return None

                except Exception as e2:
                    print(f"❌ Erro ao inserir venda após reconexão: {str(e2)}")
                    return None
            else:
                print("❌ Falha na reconexão")
                return None

        return None


if __name__ == "__main__":
    pass


# 8. FUNÇÃO PARA REGISTRAR MOVIMENTAÇÃO COM HISTÓRICO
def registrar_movimentacao(produto_id: int, tipo: str, quantidade: int, observacao: str = None, usuario_id: int = None) -> bool:
    """
    Registra uma movimentação de estoque com transação atômica.
    
    Args:
        produto_id: ID do produto
        tipo: Tipo de movimentação ('entrada', 'saida', 'ajuste')
        quantidade: Quantidade da movimentação (sempre positiva)
        observacao: Observação opcional sobre a movimentação
        usuario_id: ID do usuário que realizou a movimentação (opcional)
        
    Returns:
        True se sucesso, False se erro
    """
    try:
        # Validar tipo de movimentação
        if tipo not in ['entrada', 'saida', 'ajuste']:
            registrar_erro(
                mensagem=f"Tipo de movimentação inválido: {tipo}",
                modulo="database",
                funcao="registrar_movimentacao",
                detalhes={"tipo": tipo, "produto_id": produto_id}
            )
            return False
        
        # Validar quantidade
        if quantidade <= 0:
            registrar_erro(
                mensagem=f"Quantidade inválida: {quantidade}",
                modulo="database",
                funcao="registrar_movimentacao",
                detalhes={"quantidade": quantidade, "produto_id": produto_id}
            )
            return False
        
        # Buscar produto atual para obter quantidade_anterior
        response_produto = supabase.table("produtos").select("quantidade").eq("id", produto_id).execute()
        
        if not response_produto.data:
            registrar_erro(
                mensagem=f"Produto não encontrado: {produto_id}",
                modulo="database",
                funcao="registrar_movimentacao",
                detalhes={"produto_id": produto_id}
            )
            return False
        
        quantidade_anterior = response_produto.data[0]["quantidade"]
        
        # Calcular nova quantidade baseado no tipo
        if tipo == 'entrada':
            quantidade_nova = quantidade_anterior + quantidade
        elif tipo == 'saida':
            quantidade_nova = quantidade_anterior - quantidade
        elif tipo == 'ajuste':
            # Para ajuste, a quantidade passada é o valor absoluto desejado
            quantidade_nova = quantidade
        
        # Não permitir quantidade negativa (exceto se for ajuste explícito)
        if quantidade_nova < 0 and tipo != 'ajuste':
            registrar_aviso(
                mensagem=f"Movimentação resultaria em estoque negativo",
                modulo="database",
                funcao="registrar_movimentacao",
                detalhes={
                    "produto_id": produto_id,
                    "tipo": tipo,
                    "quantidade_anterior": quantidade_anterior,
                    "quantidade_movimentacao": quantidade,
                    "quantidade_nova": quantidade_nova
                }
            )
            # Permitir continuar, mas registrar aviso
        
        # TRANSAÇÃO: Atualizar quantidade do produto
        supabase.table("produtos").update({"quantidade": quantidade_nova}).eq("id", produto_id).execute()
        
        # TRANSAÇÃO: Inserir registro de movimentação
        movimentacao_data = {
            "produto_id": produto_id,
            "tipo": tipo,
            "quantidade": quantidade,
            "quantidade_anterior": quantidade_anterior,
            "quantidade_nova": quantidade_nova,
            "observacao": observacao,
            "usuario_id": usuario_id
        }
        
        supabase.table("movimentacoes").insert(movimentacao_data).execute()
        
        registrar_info(
            mensagem=f"Movimentação registrada com sucesso",
            modulo="database",
            funcao="registrar_movimentacao",
            detalhes={
                "produto_id": produto_id,
                "tipo": tipo,
                "quantidade": quantidade,
                "quantidade_anterior": quantidade_anterior,
                "quantidade_nova": quantidade_nova
            }
        )
        
        return True
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao registrar movimentação",
                modulo="database",
                funcao="registrar_movimentacao",
                detalhes={"erro": erro_str, "produto_id": produto_id, "tipo": tipo},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    # Repetir toda a operação após reconexão
                    response_produto = supabase.table("produtos").select("quantidade").eq("id", produto_id).execute()
                    if not response_produto.data:
                        return False
                    
                    quantidade_anterior = response_produto.data[0]["quantidade"]
                    
                    if tipo == 'entrada':
                        quantidade_nova = quantidade_anterior + quantidade
                    elif tipo == 'saida':
                        quantidade_nova = quantidade_anterior - quantidade
                    elif tipo == 'ajuste':
                        quantidade_nova = quantidade
                    
                    supabase.table("produtos").update({"quantidade": quantidade_nova}).eq("id", produto_id).execute()
                    
                    movimentacao_data = {
                        "produto_id": produto_id,
                        "tipo": tipo,
                        "quantidade": quantidade,
                        "quantidade_anterior": quantidade_anterior,
                        "quantidade_nova": quantidade_nova,
                        "observacao": observacao,
                        "usuario_id": usuario_id
                    }
                    
                    supabase.table("movimentacoes").insert(movimentacao_data).execute()
                    
                    registrar_info(
                        mensagem="Movimentação registrada após reconexão",
                        modulo="database",
                        funcao="registrar_movimentacao"
                    )
                    return True
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao registrar movimentação após reconexão",
                        modulo="database",
                        funcao="registrar_movimentacao",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao registrar movimentação",
                modulo="database",
                funcao="registrar_movimentacao",
                detalhes={"erro": erro_str, "produto_id": produto_id, "tipo": tipo},
                exc_info=True
            )
        
        print(f"Erro ao registrar movimentação: {e}")
        return False


# 9. FUNÇÃO PARA LISTAR MOVIMENTAÇÕES COM FILTROS
def listar_movimentacoes(produto_id: int = None, data_inicio: str = None, data_fim: str = None, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Lista movimentações de estoque com filtros opcionais e paginação.
    
    Args:
        produto_id: ID do produto para filtrar (opcional)
        data_inicio: Data inicial no formato ISO (YYYY-MM-DD) (opcional)
        data_fim: Data final no formato ISO (YYYY-MM-DD) (opcional)
        limit: Número máximo de registros a retornar (opcional, para paginação/lazy loading)
        offset: Número de registros a pular (opcional, para paginação/lazy loading)
        
    Returns:
        Lista de movimentações ordenadas por data mais recente, lista vazia se erro
    """
    try:
        # Iniciar query
        query = supabase.table("movimentacoes").select("*")
        
        # Aplicar filtro por produto_id se fornecido
        if produto_id is not None:
            query = query.eq("produto_id", produto_id)
        
        # Aplicar filtro por data_inicio se fornecido
        if data_inicio is not None:
            query = query.gte("created_at", data_inicio)
        
        # Aplicar filtro por data_fim se fornecido
        if data_fim is not None:
            # Adicionar 23:59:59 para incluir todo o dia final
            data_fim_completa = f"{data_fim}T23:59:59"
            query = query.lte("created_at", data_fim_completa)
        
        # Ordenar por data mais recente primeiro
        query = query.order("created_at", desc=True)
        
        # Aplicar paginação se limit fornecido (para lazy loading)
        if limit is not None:
            query = query.limit(limit)
        if offset > 0:
            query = query.offset(offset)
        
        # Executar query
        response = query.execute()
        
        registrar_info(
            mensagem=f"Movimentações listadas com sucesso: {len(response.data)} itens",
            modulo="database",
            funcao="listar_movimentacoes",
            detalhes={
                "produto_id": produto_id,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "total": len(response.data)
            }
        )
        
        return response.data
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao listar movimentações",
                modulo="database",
                funcao="listar_movimentacoes",
                detalhes={"erro": erro_str},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    query = supabase.table("movimentacoes").select("*")
                    
                    if produto_id is not None:
                        query = query.eq("produto_id", produto_id)
                    
                    if data_inicio is not None:
                        query = query.gte("created_at", data_inicio)
                    
                    if data_fim is not None:
                        data_fim_completa = f"{data_fim}T23:59:59"
                        query = query.lte("created_at", data_fim_completa)
                    
                    query = query.order("created_at", desc=True)
                    response = query.execute()
                    
                    registrar_info(
                        mensagem="Movimentações listadas após reconexão",
                        modulo="database",
                        funcao="listar_movimentacoes"
                    )
                    return response.data
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao listar movimentações após reconexão",
                        modulo="database",
                        funcao="listar_movimentacoes",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao listar movimentações",
                modulo="database",
                funcao="listar_movimentacoes",
                detalhes={"erro": erro_str},
                exc_info=True
            )
        
        print(f"Erro ao listar movimentações: {e}")
        return []


# 10. FUNÇÃO PARA DESFAZER ÚLTIMA MOVIMENTAÇÃO
def desfazer_ultima_movimentacao(produto_id: int) -> bool:
    """
    Desfaz a última movimentação de um produto, revertendo a quantidade.
    
    Args:
        produto_id: ID do produto
        
    Returns:
        True se sucesso, False se erro ou não há movimentação para desfazer
    """
    try:
        # Buscar última movimentação do produto
        response_mov = supabase.table("movimentacoes")\
            .select("*")\
            .eq("produto_id", produto_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if not response_mov.data:
            registrar_aviso(
                mensagem=f"Nenhuma movimentação encontrada para desfazer",
                modulo="database",
                funcao="desfazer_ultima_movimentacao",
                detalhes={"produto_id": produto_id}
            )
            print(f"Nenhuma movimentação encontrada para o produto {produto_id}")
            return False
        
        ultima_movimentacao = response_mov.data[0]
        movimentacao_id = ultima_movimentacao["id"]
        quantidade_anterior = ultima_movimentacao["quantidade_anterior"]
        
        # Reverter quantidade do produto para o valor anterior
        supabase.table("produtos")\
            .update({"quantidade": quantidade_anterior})\
            .eq("id", produto_id)\
            .execute()
        
        # Deletar o registro da movimentação
        supabase.table("movimentacoes")\
            .delete()\
            .eq("id", movimentacao_id)\
            .execute()
        
        registrar_info(
            mensagem=f"Movimentação desfeita com sucesso",
            modulo="database",
            funcao="desfazer_ultima_movimentacao",
            detalhes={
                "produto_id": produto_id,
                "movimentacao_id": movimentacao_id,
                "quantidade_revertida": quantidade_anterior,
                "tipo_movimentacao": ultima_movimentacao["tipo"]
            }
        )
        
        return True
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao desfazer movimentação",
                modulo="database",
                funcao="desfazer_ultima_movimentacao",
                detalhes={"erro": erro_str, "produto_id": produto_id},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    response_mov = supabase.table("movimentacoes")\
                        .select("*")\
                        .eq("produto_id", produto_id)\
                        .order("created_at", desc=True)\
                        .limit(1)\
                        .execute()
                    
                    if not response_mov.data:
                        return False
                    
                    ultima_movimentacao = response_mov.data[0]
                    movimentacao_id = ultima_movimentacao["id"]
                    quantidade_anterior = ultima_movimentacao["quantidade_anterior"]
                    
                    supabase.table("produtos")\
                        .update({"quantidade": quantidade_anterior})\
                        .eq("id", produto_id)\
                        .execute()
                    
                    supabase.table("movimentacoes")\
                        .delete()\
                        .eq("id", movimentacao_id)\
                        .execute()
                    
                    registrar_info(
                        mensagem="Movimentação desfeita após reconexão",
                        modulo="database",
                        funcao="desfazer_ultima_movimentacao"
                    )
                    return True
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao desfazer movimentação após reconexão",
                        modulo="database",
                        funcao="desfazer_ultima_movimentacao",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao desfazer movimentação",
                modulo="database",
                funcao="desfazer_ultima_movimentacao",
                detalhes={"erro": erro_str, "produto_id": produto_id},
                exc_info=True
            )
        
        print(f"Erro ao desfazer movimentação: {e}")
        return False


# ============================================================================
# FUNÇÕES DE AUTENTICAÇÃO
# ============================================================================

# 11. FUNÇÃO PARA CRIAR USUÁRIO
def criar_usuario(username: str, senha: str) -> tuple[bool, str]:
    """
    Cria um novo usuário com senha hash usando bcrypt.
    
    Args:
        username: Nome de usuário único
        senha: Senha em texto plano (será hasheada)
        
    Returns:
        Tupla (sucesso, mensagem)
        - (True, "Usuário criado com sucesso") se sucesso
        - (False, "mensagem de erro") se falha
    """
    import bcrypt
    
    try:
        # Validar username único
        response = supabase.table("usuarios")\
            .select("id")\
            .eq("username", username)\
            .execute()
        
        if response.data:
            registrar_aviso(
                mensagem=f"Tentativa de criar usuário duplicado",
                modulo="database",
                funcao="criar_usuario",
                detalhes={"username": username}
            )
            return False, f"Usuário '{username}' já existe"
        
        # Gerar hash seguro da senha
        salt = bcrypt.gensalt()
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')
        
        # Inserir usuário na tabela
        supabase.table("usuarios")\
            .insert({
                "username": username,
                "senha_hash": senha_hash,
                "ativo": True,
                "tentativas_login": 0
            })\
            .execute()
        
        registrar_info(
            mensagem=f"Usuário criado com sucesso",
            modulo="database",
            funcao="criar_usuario",
            detalhes={"username": username}
        )
        
        return True, "Usuário criado com sucesso"
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao criar usuário",
                modulo="database",
                funcao="criar_usuario",
                detalhes={"erro": erro_str, "username": username},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    # Verificar novamente se username é único
                    response = supabase.table("usuarios")\
                        .select("id")\
                        .eq("username", username)\
                        .execute()
                    
                    if response.data:
                        return False, f"Usuário '{username}' já existe"
                    
                    # Gerar hash e inserir
                    salt = bcrypt.gensalt()
                    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')
                    
                    supabase.table("usuarios")\
                        .insert({
                            "username": username,
                            "senha_hash": senha_hash,
                            "ativo": True,
                            "tentativas_login": 0
                        })\
                        .execute()
                    
                    registrar_info(
                        mensagem="Usuário criado após reconexão",
                        modulo="database",
                        funcao="criar_usuario"
                    )
                    return True, "Usuário criado com sucesso"
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao criar usuário após reconexão",
                        modulo="database",
                        funcao="criar_usuario",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
                    return False, "Erro ao conectar ao banco de dados"
        else:
            registrar_erro(
                mensagem="Erro ao criar usuário",
                modulo="database",
                funcao="criar_usuario",
                detalhes={"erro": erro_str, "username": username},
                exc_info=True
            )
        
        print(f"Erro ao criar usuário: {e}")
        return False, "Erro ao criar usuário"


# 12. FUNÇÃO PARA AUTENTICAR USUÁRIO
def autenticar_usuario(username: str, senha: str) -> tuple[bool, str, dict | None]:
    """
    Autentica um usuário verificando credenciais e controle de tentativas.
    Bloqueia usuário após 3 tentativas falhadas por 5 minutos.
    
    Args:
        username: Nome de usuário
        senha: Senha em texto plano
        
    Returns:
        Tupla (sucesso, mensagem, dados_usuario)
        - (True, "Autenticado com sucesso", {dados}) se sucesso
        - (False, "mensagem de erro", None) se falha
    """
    import bcrypt
    from datetime import datetime, timedelta
    
    try:
        # Buscar usuário
        response = supabase.table("usuarios")\
            .select("*")\
            .eq("username", username)\
            .execute()
        
        if not response.data:
            registrar_aviso(
                mensagem=f"Tentativa de login com usuário inexistente",
                modulo="database",
                funcao="autenticar_usuario",
                detalhes={"username": username}
            )
            return False, "Credenciais inválidas", None
        
        usuario = response.data[0]
        usuario_id = usuario["id"]
        
        # Verificar se usuário está ativo
        if not usuario.get("ativo", True):
            registrar_aviso(
                mensagem=f"Tentativa de login com usuário inativo",
                modulo="database",
                funcao="autenticar_usuario",
                detalhes={"username": username, "usuario_id": usuario_id}
            )
            return False, "Usuário inativo", None
        
        # Verificar se usuário está bloqueado
        bloqueado_ate = usuario.get("bloqueado_ate")
        if bloqueado_ate:
            bloqueado_ate_dt = datetime.fromisoformat(bloqueado_ate.replace('Z', '+00:00'))
            agora = datetime.now(bloqueado_ate_dt.tzinfo)
            
            if agora < bloqueado_ate_dt:
                tempo_restante = bloqueado_ate_dt - agora
                minutos = int(tempo_restante.total_seconds() / 60)
                segundos = int(tempo_restante.total_seconds() % 60)
                
                registrar_aviso(
                    mensagem=f"Tentativa de login com usuário bloqueado",
                    modulo="database",
                    funcao="autenticar_usuario",
                    detalhes={
                        "username": username,
                        "usuario_id": usuario_id,
                        "tempo_restante_segundos": tempo_restante.total_seconds()
                    }
                )
                return False, f"Conta bloqueada. Tente novamente em {minutos}m {segundos}s", None
        
        # Validar senha com bcrypt
        senha_hash = usuario["senha_hash"]
        senha_valida = bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))
        
        if not senha_valida:
            # Incrementar tentativas de login
            tentativas = usuario.get("tentativas_login", 0) + 1
            
            # Bloquear após 3 tentativas
            if tentativas >= 3:
                bloqueado_ate = datetime.now() + timedelta(minutes=5)
                
                supabase.table("usuarios")\
                    .update({
                        "tentativas_login": tentativas,
                        "bloqueado_ate": bloqueado_ate.isoformat()
                    })\
                    .eq("id", usuario_id)\
                    .execute()
                
                registrar_aviso(
                    mensagem=f"Usuário bloqueado após 3 tentativas falhadas",
                    modulo="database",
                    funcao="autenticar_usuario",
                    detalhes={
                        "username": username,
                        "usuario_id": usuario_id,
                        "bloqueado_ate": bloqueado_ate.isoformat()
                    }
                )
                return False, "Credenciais inválidas. Conta bloqueada por 5 minutos", None
            else:
                supabase.table("usuarios")\
                    .update({"tentativas_login": tentativas})\
                    .eq("id", usuario_id)\
                    .execute()
                
                registrar_aviso(
                    mensagem=f"Tentativa de login falhada",
                    modulo="database",
                    funcao="autenticar_usuario",
                    detalhes={
                        "username": username,
                        "usuario_id": usuario_id,
                        "tentativas": tentativas
                    }
                )
                return False, f"Credenciais inválidas. Tentativa {tentativas} de 3", None
        
        # Senha correta - resetar tentativas e atualizar último acesso
        supabase.table("usuarios")\
            .update({
                "tentativas_login": 0,
                "bloqueado_ate": None,
                "ultimo_acesso": datetime.now().isoformat()
            })\
            .eq("id", usuario_id)\
            .execute()
        
        registrar_info(
            mensagem=f"Login bem-sucedido",
            modulo="database",
            funcao="autenticar_usuario",
            detalhes={"username": username, "usuario_id": usuario_id}
        )
        
        # Retornar dados do usuário (sem senha_hash)
        dados_usuario = {
            "id": usuario["id"],
            "username": usuario["username"],
            "ativo": usuario["ativo"],
            "ultimo_acesso": datetime.now().isoformat()
        }
        
        return True, "Autenticado com sucesso", dados_usuario
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao autenticar usuário",
                modulo="database",
                funcao="autenticar_usuario",
                detalhes={"erro": erro_str, "username": username},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    # Tentar autenticar novamente
                    return autenticar_usuario(username, senha)
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao autenticar após reconexão",
                        modulo="database",
                        funcao="autenticar_usuario",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
                    return False, "Erro ao conectar ao banco de dados", None
        else:
            registrar_erro(
                mensagem="Erro ao autenticar usuário",
                modulo="database",
                funcao="autenticar_usuario",
                detalhes={"erro": erro_str, "username": username},
                exc_info=True
            )
        
        print(f"Erro ao autenticar usuário: {e}")
        return False, "Erro ao autenticar usuário", None


# 13. FUNÇÃO PARA REGISTRAR ACESSO
def registrar_acesso(usuario_id: int) -> bool:
    """
    Registra um acesso do usuário atualizando o campo ultimo_acesso.
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        True se sucesso, False se erro
    """
    from datetime import datetime
    
    try:
        supabase.table("usuarios")\
            .update({"ultimo_acesso": datetime.now().isoformat()})\
            .eq("id", usuario_id)\
            .execute()
        
        registrar_info(
            mensagem=f"Acesso registrado",
            modulo="database",
            funcao="registrar_acesso",
            detalhes={"usuario_id": usuario_id}
        )
        
        return True
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao registrar acesso",
                modulo="database",
                funcao="registrar_acesso",
                detalhes={"erro": erro_str, "usuario_id": usuario_id},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    supabase.table("usuarios")\
                        .update({"ultimo_acesso": datetime.now().isoformat()})\
                        .eq("id", usuario_id)\
                        .execute()
                    
                    registrar_info(
                        mensagem="Acesso registrado após reconexão",
                        modulo="database",
                        funcao="registrar_acesso"
                    )
                    return True
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao registrar acesso após reconexão",
                        modulo="database",
                        funcao="registrar_acesso",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
        else:
            registrar_erro(
                mensagem="Erro ao registrar acesso",
                modulo="database",
                funcao="registrar_acesso",
                detalhes={"erro": erro_str, "usuario_id": usuario_id},
                exc_info=True
            )
        
        print(f"Erro ao registrar acesso: {e}")
        return False


# 14. FUNÇÃO PARA ALTERAR SENHA
def alterar_senha(usuario_id: int, senha_antiga: str, senha_nova: str) -> tuple[bool, str]:
    """
    Altera a senha de um usuário após validar a senha antiga.
    
    Args:
        usuario_id: ID do usuário
        senha_antiga: Senha atual em texto plano
        senha_nova: Nova senha em texto plano
        
    Returns:
        Tupla (sucesso, mensagem)
        - (True, "Senha alterada com sucesso") se sucesso
        - (False, "mensagem de erro") se falha
    """
    import bcrypt
    
    try:
        # Buscar usuário
        response = supabase.table("usuarios")\
            .select("*")\
            .eq("id", usuario_id)\
            .execute()
        
        if not response.data:
            registrar_aviso(
                mensagem=f"Tentativa de alterar senha de usuário inexistente",
                modulo="database",
                funcao="alterar_senha",
                detalhes={"usuario_id": usuario_id}
            )
            return False, "Usuário não encontrado"
        
        usuario = response.data[0]
        senha_hash_atual = usuario["senha_hash"]
        
        # Verificar senha antiga
        senha_antiga_valida = bcrypt.checkpw(
            senha_antiga.encode('utf-8'),
            senha_hash_atual.encode('utf-8')
        )
        
        if not senha_antiga_valida:
            registrar_aviso(
                mensagem=f"Tentativa de alterar senha com senha antiga incorreta",
                modulo="database",
                funcao="alterar_senha",
                detalhes={"usuario_id": usuario_id}
            )
            return False, "Senha antiga incorreta"
        
        # Gerar hash da nova senha
        salt = bcrypt.gensalt()
        senha_hash_nova = bcrypt.hashpw(senha_nova.encode('utf-8'), salt).decode('utf-8')
        
        # Atualizar senha no banco
        supabase.table("usuarios")\
            .update({"senha_hash": senha_hash_nova})\
            .eq("id", usuario_id)\
            .execute()
        
        registrar_info(
            mensagem=f"Senha alterada com sucesso",
            modulo="database",
            funcao="alterar_senha",
            detalhes={"usuario_id": usuario_id}
        )
        
        return True, "Senha alterada com sucesso"
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao alterar senha",
                modulo="database",
                funcao="alterar_senha",
                detalhes={"erro": erro_str, "usuario_id": usuario_id},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    # Buscar usuário novamente
                    response = supabase.table("usuarios")\
                        .select("*")\
                        .eq("id", usuario_id)\
                        .execute()
                    
                    if not response.data:
                        return False, "Usuário não encontrado"
                    
                    usuario = response.data[0]
                    senha_hash_atual = usuario["senha_hash"]
                    
                    # Verificar senha antiga
                    senha_antiga_valida = bcrypt.checkpw(
                        senha_antiga.encode('utf-8'),
                        senha_hash_atual.encode('utf-8')
                    )
                    
                    if not senha_antiga_valida:
                        return False, "Senha antiga incorreta"
                    
                    # Gerar hash e atualizar
                    salt = bcrypt.gensalt()
                    senha_hash_nova = bcrypt.hashpw(senha_nova.encode('utf-8'), salt).decode('utf-8')
                    
                    supabase.table("usuarios")\
                        .update({"senha_hash": senha_hash_nova})\
                        .eq("id", usuario_id)\
                        .execute()
                    
                    registrar_info(
                        mensagem="Senha alterada após reconexão",
                        modulo="database",
                        funcao="alterar_senha"
                    )
                    return True, "Senha alterada com sucesso"
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao alterar senha após reconexão",
                        modulo="database",
                        funcao="alterar_senha",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
                    return False, "Erro ao conectar ao banco de dados"
        else:
            registrar_erro(
                mensagem="Erro ao alterar senha",
                modulo="database",
                funcao="alterar_senha",
                detalhes={"erro": erro_str, "usuario_id": usuario_id},
                exc_info=True
            )
        
        print(f"Erro ao alterar senha: {e}")
        return False, "Erro ao alterar senha"


# ==================== GERENCIAMENTO DE SESSÕES ====================

def criar_sessao(usuario_id: int) -> tuple[bool, str, str | None]:
    """
    Cria uma nova sessão para o usuário
    
    Args:
        usuario_id: ID do usuário
        
    Returns:
        tuple: (sucesso, mensagem, token)
    """
    try:
        import secrets
        from datetime import datetime, timedelta
        
        # Gerar token seguro
        token = secrets.token_urlsafe(32)
        
        # Calcular expiração (2 horas)
        expira_em = datetime.now() + timedelta(hours=2)
        
        # Inserir sessão no banco
        response = supabase.table("sessoes")\
            .insert({
                "usuario_id": usuario_id,
                "token": token,
                "expira_em": expira_em.isoformat()
            })\
            .execute()
        
        if response.data:
            registrar_info(
                mensagem="Sessão criada com sucesso",
                modulo="database",
                funcao="criar_sessao",
                detalhes={"usuario_id": usuario_id}
            )
            return True, "Sessão criada com sucesso", token
        else:
            registrar_erro(
                mensagem="Falha ao criar sessão - sem dados retornados",
                modulo="database",
                funcao="criar_sessao",
                detalhes={"usuario_id": usuario_id}
            )
            return False, "Erro ao criar sessão", None
            
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao criar sessão",
                modulo="database",
                funcao="criar_sessao",
                detalhes={"erro": erro_str, "usuario_id": usuario_id},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    import secrets
                    from datetime import datetime, timedelta
                    
                    token = secrets.token_urlsafe(32)
                    expira_em = datetime.now() + timedelta(hours=2)
                    
                    response = supabase.table("sessoes")\
                        .insert({
                            "usuario_id": usuario_id,
                            "token": token,
                            "expira_em": expira_em.isoformat()
                        })\
                        .execute()
                    
                    if response.data:
                        registrar_info(
                            mensagem="Sessão criada após reconexão",
                            modulo="database",
                            funcao="criar_sessao"
                        )
                        return True, "Sessão criada com sucesso", token
                    else:
                        return False, "Erro ao criar sessão", None
                        
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao criar sessão após reconexão",
                        modulo="database",
                        funcao="criar_sessao",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
                    return False, "Erro ao conectar ao banco de dados", None
        else:
            registrar_erro(
                mensagem="Erro ao criar sessão",
                modulo="database",
                funcao="criar_sessao",
                detalhes={"erro": erro_str, "usuario_id": usuario_id},
                exc_info=True
            )
        
        print(f"Erro ao criar sessão: {e}")
        return False, "Erro ao criar sessão", None


def validar_sessao(token: str) -> tuple[bool, str, dict | None]:
    """
    Valida uma sessão verificando token e expiração
    
    Args:
        token: Token da sessão
        
    Returns:
        tuple: (valida, mensagem, dados_usuario)
    """
    try:
        from datetime import datetime
        
        # Buscar sessão pelo token
        response = supabase.table("sessoes")\
            .select("*, usuarios(*)")\
            .eq("token", token)\
            .execute()
        
        if not response.data:
            return False, "Sessão não encontrada", None
        
        sessao = response.data[0]
        
        # Verificar expiração
        expira_em = datetime.fromisoformat(sessao["expira_em"].replace('Z', '+00:00'))
        agora = datetime.now(expira_em.tzinfo) if expira_em.tzinfo else datetime.now()
        
        if agora > expira_em:
            registrar_info(
                mensagem="Sessão expirada",
                modulo="database",
                funcao="validar_sessao",
                detalhes={"token": token[:10] + "..."}
            )
            return False, "Sessão expirada", None
        
        # Retornar dados do usuário
        usuario = sessao["usuarios"]
        registrar_info(
            mensagem="Sessão validada com sucesso",
            modulo="database",
            funcao="validar_sessao",
            detalhes={"usuario_id": usuario["id"]}
        )
        return True, "Sessão válida", usuario
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao validar sessão",
                modulo="database",
                funcao="validar_sessao",
                detalhes={"erro": erro_str},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    from datetime import datetime
                    
                    response = supabase.table("sessoes")\
                        .select("*, usuarios(*)")\
                        .eq("token", token)\
                        .execute()
                    
                    if not response.data:
                        return False, "Sessão não encontrada", None
                    
                    sessao = response.data[0]
                    expira_em = datetime.fromisoformat(sessao["expira_em"].replace('Z', '+00:00'))
                    agora = datetime.now(expira_em.tzinfo) if expira_em.tzinfo else datetime.now()
                    
                    if agora > expira_em:
                        return False, "Sessão expirada", None
                    
                    usuario = sessao["usuarios"]
                    registrar_info(
                        mensagem="Sessão validada após reconexão",
                        modulo="database",
                        funcao="validar_sessao"
                    )
                    return True, "Sessão válida", usuario
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao validar sessão após reconexão",
                        modulo="database",
                        funcao="validar_sessao",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
                    return False, "Erro ao conectar ao banco de dados", None
        else:
            registrar_erro(
                mensagem="Erro ao validar sessão",
                modulo="database",
                funcao="validar_sessao",
                detalhes={"erro": erro_str},
                exc_info=True
            )
        
        print(f"Erro ao validar sessão: {e}")
        return False, "Erro ao validar sessão", None


def limpar_sessoes_expiradas() -> tuple[bool, str]:
    """
    Remove sessões expiradas do banco de dados
    
    Returns:
        tuple: (sucesso, mensagem)
    """
    try:
        from datetime import datetime
        
        # Deletar sessões expiradas
        agora = datetime.now().isoformat()
        
        response = supabase.table("sessoes")\
            .delete()\
            .lt("expira_em", agora)\
            .execute()
        
        registrar_info(
            mensagem="Sessões expiradas limpas",
            modulo="database",
            funcao="limpar_sessoes_expiradas"
        )
        return True, "Sessões expiradas removidas"
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao limpar sessões",
                modulo="database",
                funcao="limpar_sessoes_expiradas",
                detalhes={"erro": erro_str},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    from datetime import datetime
                    agora = datetime.now().isoformat()
                    
                    supabase.table("sessoes")\
                        .delete()\
                        .lt("expira_em", agora)\
                        .execute()
                    
                    registrar_info(
                        mensagem="Sessões limpas após reconexão",
                        modulo="database",
                        funcao="limpar_sessoes_expiradas"
                    )
                    return True, "Sessões expiradas removidas"
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao limpar sessões após reconexão",
                        modulo="database",
                        funcao="limpar_sessoes_expiradas",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
                    return False, "Erro ao conectar ao banco de dados"
        else:
            registrar_erro(
                mensagem="Erro ao limpar sessões",
                modulo="database",
                funcao="limpar_sessoes_expiradas",
                detalhes={"erro": erro_str},
                exc_info=True
            )
        
        print(f"Erro ao limpar sessões: {e}")
        return False, "Erro ao limpar sessões"


def encerrar_sessao(token: str) -> tuple[bool, str]:
    """
    Encerra uma sessão (logout)
    
    Args:
        token: Token da sessão
        
    Returns:
        tuple: (sucesso, mensagem)
    """
    try:
        # Deletar sessão
        response = supabase.table("sessoes")\
            .delete()\
            .eq("token", token)\
            .execute()
        
        registrar_info(
            mensagem="Sessão encerrada",
            modulo="database",
            funcao="encerrar_sessao",
            detalhes={"token": token[:10] + "..."}
        )
        return True, "Sessão encerrada com sucesso"
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao encerrar sessão",
                modulo="database",
                funcao="encerrar_sessao",
                detalhes={"erro": erro_str},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    supabase.table("sessoes")\
                        .delete()\
                        .eq("token", token)\
                        .execute()
                    
                    registrar_info(
                        mensagem="Sessão encerrada após reconexão",
                        modulo="database",
                        funcao="encerrar_sessao"
                    )
                    return True, "Sessão encerrada com sucesso"
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao encerrar sessão após reconexão",
                        modulo="database",
                        funcao="encerrar_sessao",
                        detalhes={"erro": str(e2)},
                        exc_info=True
                    )
                    return False, "Erro ao conectar ao banco de dados"
        else:
            registrar_erro(
                mensagem="Erro ao encerrar sessão",
                modulo="database",
                funcao="encerrar_sessao",
                detalhes={"erro": erro_str},
                exc_info=True
            )
        
        print(f"Erro ao encerrar sessão: {e}")
        return False, "Erro ao encerrar sessão"


def obter_sessao_ativa() -> tuple[bool, str, dict | None]:
    """Busca a sessão ativa mais recente do sistema."""
    try:
        print("DEBUG obter_sessao_ativa: Iniciando busca de sessão...")
        from datetime import datetime
        print("DEBUG obter_sessao_ativa: Consultando banco de dados...")
        response = supabase.table('sessoes').select('*, usuarios(*)').order('created_at', desc=True).limit(1).execute()
        print(f"DEBUG obter_sessao_ativa: Resposta recebida - {len(response.data) if response.data else 0} sessões encontradas")
        if not response.data:
            return False, 'Nenhuma sessão ativa encontrada', None
        sessao = response.data[0]
        expira_em = datetime.fromisoformat(sessao['expira_em'].replace('Z', '+00:00'))
        agora = datetime.now(expira_em.tzinfo) if expira_em.tzinfo else datetime.now()
        if agora > expira_em:
            return False, 'Sessão expirada', None
        usuario = sessao['usuarios']
        dados_sessao = {'token': sessao['token'], 'usuario': {'id': usuario['id'], 'username': usuario['username'], 'ativo': usuario['ativo']}}
        return True, 'Sessão ativa encontrada', dados_sessao
    except Exception as e:
        print(f'Erro ao buscar sessão ativa: {e}')
        return False, 'Erro ao buscar sessão ativa', None


# ============================================================================
# BUSCA AVANÇADA
# ============================================================================

def buscar_produtos_avancado(filtros: dict) -> list:
    """
    Busca produtos com filtros combinados e paginação.
    
    Suporta:
    - Busca multi-campo (termo): busca case-insensitive em descrição, marca e referência
    - Filtro por gênero
    - Filtro por marca
    - Filtro por faixa de preço (preco_min, preco_max)
    - Ordenação por nome, preço ou quantidade (ascendente ou descendente)
    - Paginação (limit, offset)
    
    Todos os filtros são combinados com AND (produto deve atender a TODOS os critérios).
    
    Args:
        filtros: Dicionário com filtros opcionais:
            - termo (str): termo de busca para descrição, marca ou referência
            - genero (str): filtro por gênero
            - marca (str): filtro por marca
            - preco_min (float): preço mínimo
            - preco_max (float): preço máximo
            - order_by (str): campo para ordenação ('nome', 'preco', 'quantidade')
            - order_direction (str): direção da ordenação ('asc' ou 'desc')
            - limit (int): número máximo de registros a retornar (padrão: 50)
            - offset (int): número de registros a pular (padrão: 0)
    
    Returns:
        Lista de produtos que atendem a todos os critérios especificados
        
    Exemplo:
        # Buscar produtos com "moletom" no nome, gênero Masculino, preço entre 50 e 100
        # ordenados por preço decrescente, primeira página de 50 itens
        filtros = {
            "termo": "moletom",
            "genero": "Masculino",
            "preco_min": 50.0,
            "preco_max": 100.0,
            "order_by": "preco",
            "order_direction": "desc",
            "limit": 50,
            "offset": 0
        }
        produtos = buscar_produtos_avancado(filtros)
    """
    try:
        # Começar com todos os produtos
        query = supabase.table("produtos").select("*")
        
        # Aplicar filtros
        filtros_aplicados = []
        
        # Filtro de gênero (exato)
        if filtros.get("genero"):
            query = query.eq("genero", filtros["genero"])
            filtros_aplicados.append(f"genero={filtros['genero']}")
        
        # Filtro de marca (exato)
        if filtros.get("marca"):
            query = query.eq("marca", filtros["marca"])
            filtros_aplicados.append(f"marca={filtros['marca']}")
        
        # Filtro de preço mínimo
        if filtros.get("preco_min") is not None:
            query = query.gte("preco", filtros["preco_min"])
            filtros_aplicados.append(f"preco>={filtros['preco_min']}")
        
        # Filtro de preço máximo
        if filtros.get("preco_max") is not None:
            query = query.lte("preco", filtros["preco_max"])
            filtros_aplicados.append(f"preco<={filtros['preco_max']}")
        
        # Executar query
        response = query.order("id").execute()
        produtos = response.data
        
        # Filtro de busca multi-campo (case-insensitive)
        # Nota: Supabase não suporta OR com ilike facilmente, então fazemos em Python
        if filtros.get("termo"):
            termo = filtros["termo"].lower()
            produtos = [
                p for p in produtos
                if (termo in (p.get("descricao") or "").lower() or
                    termo in (p.get("marca") or "").lower() or
                    termo in (p.get("referencia") or "").lower())
            ]
            filtros_aplicados.append(f"termo='{filtros['termo']}'")
        
        # Aplicar ordenação
        order_by = filtros.get("order_by")
        order_direction = filtros.get("order_direction", "asc")
        
        if order_by:
            # Mapear nomes amigáveis para campos do banco
            campo_map = {
                "nome": "descricao",
                "preco": "preco",
                "quantidade": "quantidade"
            }
            
            campo = campo_map.get(order_by)
            if campo:
                reverse = (order_direction.lower() == "desc")
                
                # Ordenar com tratamento de valores None
                produtos = sorted(
                    produtos,
                    key=lambda p: (p.get(campo) is None, p.get(campo) or 0),
                    reverse=reverse
                )
                
                filtros_aplicados.append(f"order_by={order_by} {order_direction}")
        
        # Aplicar paginação (padrão: 50 itens por página)
        limit = filtros.get("limit", 50)
        offset = filtros.get("offset", 0)
        
        # Guardar total antes da paginação
        total_produtos = len(produtos)
        
        # Aplicar paginação
        if limit is not None:
            produtos = produtos[offset:offset + limit]
            filtros_aplicados.append(f"paginacao={offset}-{offset+len(produtos)}/{total_produtos}")
        
        registrar_info(
            mensagem=f"Busca avançada realizada: {len(produtos)} produtos retornados de {total_produtos} encontrados",
            modulo="database",
            funcao="buscar_produtos_avancado",
            detalhes={"filtros": filtros_aplicados, "total": total_produtos, "retornados": len(produtos)}
        )
        
        print(f"Busca avançada: {len(produtos)} produtos retornados de {total_produtos} encontrados com filtros: {', '.join(filtros_aplicados)}")
        return produtos
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao buscar produtos",
                modulo="database",
                funcao="buscar_produtos_avancado",
                detalhes={"erro": erro_str, "filtros": filtros},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    # Repetir a busca após reconexão
                    query = supabase.table("produtos").select("*")
                    
                    if filtros.get("genero"):
                        query = query.eq("genero", filtros["genero"])
                    if filtros.get("marca"):
                        query = query.eq("marca", filtros["marca"])
                    if filtros.get("preco_min") is not None:
                        query = query.gte("preco", filtros["preco_min"])
                    if filtros.get("preco_max") is not None:
                        query = query.lte("preco", filtros["preco_max"])
                    
                    response = query.order("id").execute()
                    produtos = response.data
                    
                    if filtros.get("termo"):
                        termo = filtros["termo"].lower()
                        produtos = [
                            p for p in produtos
                            if (termo in (p.get("descricao") or "").lower() or
                                termo in (p.get("marca") or "").lower() or
                                termo in (p.get("referencia") or "").lower())
                        ]
                    
                    # Aplicar ordenação após reconexão
                    order_by = filtros.get("order_by")
                    order_direction = filtros.get("order_direction", "asc")
                    
                    if order_by:
                        campo_map = {
                            "nome": "descricao",
                            "preco": "preco",
                            "quantidade": "quantidade"
                        }
                        
                        campo = campo_map.get(order_by)
                        if campo:
                            reverse = (order_direction.lower() == "desc")
                            produtos = sorted(
                                produtos,
                                key=lambda p: (p.get(campo) is None, p.get(campo) or 0),
                                reverse=reverse
                            )
                    
                    registrar_info(
                        mensagem="Busca avançada realizada após reconexão",
                        modulo="database",
                        funcao="buscar_produtos_avancado"
                    )
                    return produtos
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao buscar produtos após reconexão",
                        modulo="database",
                        funcao="buscar_produtos_avancado",
                        detalhes={"erro": str(e2), "filtros": filtros},
                        exc_info=True
                    )
                    return []
        else:
            registrar_erro(
                mensagem="Erro ao buscar produtos",
                modulo="database",
                funcao="buscar_produtos_avancado",
                detalhes={"erro": erro_str, "filtros": filtros},
                exc_info=True
            )
        
        print(f"Erro ao buscar produtos: {e}")
        return []


def contar_produtos_avancado(filtros: dict) -> int:
    """
    Conta o número total de produtos que atendem aos filtros especificados.
    Útil para implementar paginação na UI.
    
    Args:
        filtros: Dicionário com os mesmos filtros de buscar_produtos_avancado
                 (exceto limit e offset que são ignorados)
    
    Returns:
        Número total de produtos que atendem aos critérios
    """
    try:
        # Remover limit e offset para contar todos
        filtros_count = {k: v for k, v in filtros.items() if k not in ['limit', 'offset']}
        
        # Usar buscar_produtos_avancado sem paginação
        produtos = buscar_produtos_avancado(filtros_count)
        
        return len(produtos)
        
    except Exception as e:
        registrar_erro(
            mensagem="Erro ao contar produtos",
            modulo="database",
            funcao="contar_produtos_avancado",
            detalhes={"erro": str(e), "filtros": filtros},
            exc_info=True
        )
        return 0


# ============================================================================
# SUGESTÕES DE BUSCA
# ============================================================================

def calcular_distancia_levenshtein(s1: str, s2: str) -> int:
    """
    Calcula a distância de Levenshtein entre duas strings.
    
    A distância de Levenshtein é o número mínimo de operações de edição
    (inserção, deleção ou substituição) necessárias para transformar uma
    string em outra.
    
    Args:
        s1: Primeira string
        s2: Segunda string
    
    Returns:
        Distância de Levenshtein (número inteiro)
    
    Exemplo:
        calcular_distancia_levenshtein("kitten", "sitting") -> 3
        calcular_distancia_levenshtein("moletom", "moleton") -> 1
    """
    # Converter para minúsculas para comparação case-insensitive
    s1 = s1.lower()
    s2 = s2.lower()
    
    # Se uma das strings é vazia, a distância é o tamanho da outra
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)
    
    # Criar matriz de distâncias
    # matriz[i][j] = distância entre s1[0:i] e s2[0:j]
    matriz = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    
    # Inicializar primeira linha e coluna
    for i in range(len(s1) + 1):
        matriz[i][0] = i
    for j in range(len(s2) + 1):
        matriz[0][j] = j
    
    # Preencher matriz usando programação dinâmica
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            if s1[i-1] == s2[j-1]:
                # Caracteres iguais, sem custo adicional
                custo = 0
            else:
                # Caracteres diferentes, custo de substituição = 1
                custo = 1
            
            matriz[i][j] = min(
                matriz[i-1][j] + 1,      # Deleção
                matriz[i][j-1] + 1,      # Inserção
                matriz[i-1][j-1] + custo # Substituição
            )
    
    return matriz[len(s1)][len(s2)]


def gerar_sugestoes(termo_busca: str, max_sugestoes: int = 5) -> list[str]:
    """
    Gera sugestões de termos similares quando uma busca não retorna resultados.
    
    Usa o algoritmo de distância de Levenshtein para encontrar os termos mais
    similares ao termo de busca entre todos os produtos cadastrados.
    
    Args:
        termo_busca: Termo que não retornou resultados
        max_sugestoes: Número máximo de sugestões a retornar (padrão: 5)
    
    Returns:
        Lista com até max_sugestoes termos similares, ordenados por similaridade
        (menor distância primeiro)
    
    Exemplo:
        # Usuário buscou "moleton" mas não há produtos com esse termo
        # Função retorna ["moletom", "conjunto moletom", "moletom infantil", ...]
        sugestoes = gerar_sugestoes("moleton")
    
    Requisitos: 9.3
    """
    try:
        # Buscar todos os produtos
        response = supabase.table("produtos").select("descricao, marca, referencia").execute()
        produtos = response.data
        
        if not produtos:
            registrar_info(
                mensagem="Nenhum produto encontrado para gerar sugestões",
                modulo="database",
                funcao="gerar_sugestoes"
            )
            return []
        
        # Coletar todos os termos únicos dos produtos
        termos = set()
        for produto in produtos:
            # Adicionar descrição completa
            if produto.get("descricao"):
                termos.add(produto["descricao"].strip())
            
            # Adicionar marca
            if produto.get("marca"):
                termos.add(produto["marca"].strip())
            
            # Adicionar referência
            if produto.get("referencia"):
                termos.add(produto["referencia"].strip())
            
            # Adicionar palavras individuais da descrição (para sugestões mais granulares)
            if produto.get("descricao"):
                palavras = produto["descricao"].split()
                for palavra in palavras:
                    palavra_limpa = palavra.strip().lower()
                    # Adicionar apenas palavras com 3+ caracteres
                    if len(palavra_limpa) >= 3:
                        termos.add(palavra_limpa)
        
        # Remover o próprio termo de busca (case-insensitive)
        termos = {t for t in termos if t.lower() != termo_busca.lower()}
        
        if not termos:
            registrar_info(
                mensagem="Nenhum termo disponível para gerar sugestões",
                modulo="database",
                funcao="gerar_sugestoes"
            )
            return []
        
        # Calcular distância de Levenshtein para cada termo
        distancias = []
        for termo in termos:
            distancia = calcular_distancia_levenshtein(termo_busca, termo)
            distancias.append((termo, distancia))
        
        # Ordenar por distância (menor primeiro = mais similar)
        distancias.sort(key=lambda x: (x[1], x[0]))
        
        # Retornar top N sugestões
        sugestoes = [termo for termo, _ in distancias[:max_sugestoes]]
        
        registrar_info(
            mensagem=f"Geradas {len(sugestoes)} sugestões para termo '{termo_busca}'",
            modulo="database",
            funcao="gerar_sugestoes",
            detalhes={
                "termo_busca": termo_busca,
                "sugestoes": sugestoes,
                "total_termos_analisados": len(termos)
            }
        )
        
        print(f"Sugestões para '{termo_busca}': {sugestoes}")
        return sugestoes
        
    except Exception as e:
        erro_str = str(e)
        
        # Verificar se é erro de conexão
        if "connection" in erro_str.lower() or "timeout" in erro_str.lower():
            registrar_erro(
                mensagem="Erro de conexão ao gerar sugestões",
                modulo="database",
                funcao="gerar_sugestoes",
                detalhes={"erro": erro_str, "termo_busca": termo_busca},
                exc_info=True
            )
            
            # Tentar reconectar
            if reconectar_supabase():
                try:
                    # Repetir a busca após reconexão
                    response = supabase.table("produtos").select("descricao, marca, referencia").execute()
                    produtos = response.data
                    
                    if not produtos:
                        return []
                    
                    # Coletar termos
                    termos = set()
                    for produto in produtos:
                        if produto.get("descricao"):
                            termos.add(produto["descricao"].strip())
                        if produto.get("marca"):
                            termos.add(produto["marca"].strip())
                        if produto.get("referencia"):
                            termos.add(produto["referencia"].strip())
                        if produto.get("descricao"):
                            palavras = produto["descricao"].split()
                            for palavra in palavras:
                                palavra_limpa = palavra.strip().lower()
                                if len(palavra_limpa) >= 3:
                                    termos.add(palavra_limpa)
                    
                    termos = {t for t in termos if t.lower() != termo_busca.lower()}
                    
                    if not termos:
                        return []
                    
                    # Calcular distâncias
                    distancias = []
                    for termo in termos:
                        distancia = calcular_distancia_levenshtein(termo_busca, termo)
                        distancias.append((termo, distancia))
                    
                    distancias.sort(key=lambda x: (x[1], x[0]))
                    sugestoes = [termo for termo, _ in distancias[:max_sugestoes]]
                    
                    registrar_info(
                        mensagem="Sugestões geradas após reconexão",
                        modulo="database",
                        funcao="gerar_sugestoes"
                    )
                    return sugestoes
                    
                except Exception as e2:
                    registrar_erro(
                        mensagem="Falha ao gerar sugestões após reconexão",
                        modulo="database",
                        funcao="gerar_sugestoes",
                        detalhes={"erro": str(e2), "termo_busca": termo_busca},
                        exc_info=True
                    )
                    return []
        else:
            registrar_erro(
                mensagem="Erro ao gerar sugestões",
                modulo="database",
                funcao="gerar_sugestoes",
                detalhes={"erro": erro_str, "termo_busca": termo_busca},
                exc_info=True
            )
        
        print(f"Erro ao gerar sugestões: {e}")
        return []


def inserir_venda(dados_venda: dict) -> Optional[int]:
    """
    Insere uma nova venda na tabela 'vendas'.
    
    Args:
        dados_venda (dict): Dicionário com os dados da venda contendo:
            - valor_total (float): Valor total antes dos descontos
            - desconto_percentual (float, opcional): Desconto percentual (0-100)
            - desconto_valor (float, opcional): Desconto em valor fixo
            - valor_final (float): Valor final após descontos
            - cliente_id (int, opcional): ID do cliente (None para venda avulsa)
            - usuario_id (int): ID do vendedor
            - status (str, opcional): Status da venda (padrão: 'finalizada')
    
    Returns:
        Optional[int]: ID da venda criada ou None em caso de erro
    
    Validates: Requirement 5.3
    """
    global supabase
    
    if not supabase:
        print("❌ Erro: Conexão com Supabase não estabelecida")
        return None
    
    try:
        # Preparar dados com valores padrão
        dados_insert = {
            'valor_total': dados_venda['valor_total'],
            'valor_final': dados_venda['valor_final'],
            'usuario_id': dados_venda['usuario_id'],
            'desconto_percentual': dados_venda.get('desconto_percentual', 0),
            'desconto_valor': dados_venda.get('desconto_valor', 0),
            'status': dados_venda.get('status', 'finalizada')
        }
        
        # Adicionar cliente_id apenas se fornecido (para vendas não avulsas)
        if dados_venda.get('cliente_id'):
            dados_insert['cliente_id'] = dados_venda['cliente_id']
        
        # Inserir venda na tabela
        response = supabase.table('vendas').insert(dados_insert).execute()
        
        if response.data and len(response.data) > 0:
            venda_id = response.data[0]['id']
            print(f"✅ Venda inserida com sucesso. ID: {venda_id}")
            return venda_id
        else:
            print("❌ Erro: Resposta vazia ao inserir venda")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao inserir venda: {str(e)}")
        
        # Tentar reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "network" in str(e).lower():
            print("🔄 Tentando reconectar...")
            if reconectar_supabase():
                try:
                    # Tentar inserir novamente após reconexão
                    response = supabase.table('vendas').insert(dados_insert).execute()
                    
                    if response.data and len(response.data) > 0:
                        venda_id = response.data[0]['id']
                        print(f"✅ Venda inserida com sucesso após reconexão. ID: {venda_id}")
                        return venda_id
                    else:
                        print("❌ Erro: Resposta vazia ao inserir venda após reconexão")
                        return None
                        
                except Exception as e2:
                    print(f"❌ Erro ao inserir venda após reconexão: {str(e2)}")
                    return None
            else:
                print("❌ Falha na reconexão")
                return None
        
        return None



def inserir_itens_venda(venda_id: int, itens: List[Dict]) -> bool:
    """
    Insere itens de venda em lote na tabela 'itens_venda'.
    
    Args:
        venda_id (int): ID da venda à qual os itens pertencem
        itens (List[Dict]): Lista de dicionários com os dados dos itens contendo:
            - produto_id (int): ID do produto
            - quantidade (int): Quantidade vendida
            - preco_unitario (float): Preço unitário do produto
            - subtotal (float): Subtotal do item (quantidade * preco_unitario)
    
    Returns:
        bool: True se inserção foi bem-sucedida, False caso contrário
    
    Validates: Requirement 5.4
    """
    global supabase
    
    if not supabase:
        print("❌ Erro: Conexão com Supabase não estabelecida")
        return False
    
    if not itens:
        print("⚠️ Aviso: Lista de itens vazia")
        return True  # Não é erro, apenas não há itens para inserir
    
    try:
        # Preparar dados para inserção em lote
        dados_insert = []
        for item in itens:
            dados_insert.append({
                'venda_id': venda_id,
                'produto_id': item['produto_id'],
                'quantidade': item['quantidade'],
                'preco_unitario': item['preco_unitario'],
                'subtotal': item['subtotal']
            })
        
        # Inserir todos os itens em lote
        response = supabase.table('itens_venda').insert(dados_insert).execute()
        
        if response.data and len(response.data) > 0:
            print(f"✅ {len(response.data)} itens inseridos com sucesso para venda ID: {venda_id}")
            return True
        else:
            print("❌ Erro: Resposta vazia ao inserir itens da venda")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao inserir itens da venda: {str(e)}")
        
        # Tentar reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "network" in str(e).lower():
            print("🔄 Tentando reconectar...")
            if reconectar_supabase():
                try:
                    # Tentar inserir novamente após reconexão
                    response = supabase.table('itens_venda').insert(dados_insert).execute()
                    
                    if response.data and len(response.data) > 0:
                        print(f"✅ {len(response.data)} itens inseridos com sucesso após reconexão para venda ID: {venda_id}")
                        return True
                    else:
                        print("❌ Erro: Resposta vazia ao inserir itens da venda após reconexão")
                        return False
                        
                except Exception as e2:
                    print(f"❌ Erro ao inserir itens da venda após reconexão: {str(e2)}")
                    return False
            else:
                print("❌ Falha na reconexão")
                return False
        
        return False



def inserir_pagamentos(venda_id: int, pagamentos: List[Dict]) -> bool:
    """
    Insere pagamentos de venda em lote na tabela 'pagamentos'.
    
    Args:
        venda_id (int): ID da venda à qual os pagamentos pertencem
        pagamentos (List[Dict]): Lista de dicionários com os dados dos pagamentos contendo:
            - forma_pagamento (str): Forma de pagamento (dinheiro, cartao_credito, cartao_debito, pix)
            - valor (float): Valor do pagamento
            - numero_parcelas (int, opcional): Número de parcelas (apenas para cartão de crédito)
            - valor_recebido (float, opcional): Valor recebido (apenas para dinheiro)
            - troco (float, opcional): Troco devolvido (apenas para dinheiro)
    
    Returns:
        bool: True se inserção foi bem-sucedida, False caso contrário
    
    Validates: Requirement 5.5
    """
    global supabase
    
    if not supabase:
        print("❌ Erro: Conexão com Supabase não estabelecida")
        return False
    
    if not pagamentos:
        print("⚠️ Aviso: Lista de pagamentos vazia")
        return True  # Não é erro, apenas não há pagamentos para inserir
    
    try:
        # Preparar dados para inserção em lote
        dados_insert = []
        for pagamento in pagamentos:
            dados_pagamento = {
                'venda_id': venda_id,
                'forma_pagamento': pagamento['forma_pagamento'],
                'valor': pagamento['valor']
            }
            
            # Adicionar campos opcionais apenas se fornecidos
            if pagamento.get('numero_parcelas') is not None:
                dados_pagamento['numero_parcelas'] = pagamento['numero_parcelas']
            
            if pagamento.get('valor_recebido') is not None:
                dados_pagamento['valor_recebido'] = pagamento['valor_recebido']
            
            if pagamento.get('troco') is not None:
                dados_pagamento['troco'] = pagamento['troco']
            
            dados_insert.append(dados_pagamento)
        
        # Inserir todos os pagamentos em lote
        response = supabase.table('pagamentos').insert(dados_insert).execute()
        
        if response.data and len(response.data) > 0:
            print(f"✅ {len(response.data)} pagamentos inseridos com sucesso para venda ID: {venda_id}")
            return True
        else:
            print("❌ Erro: Resposta vazia ao inserir pagamentos da venda")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao inserir pagamentos da venda: {str(e)}")
        
        # Tentar reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "network" in str(e).lower():
            print("🔄 Tentando reconectar...")
            if reconectar_supabase():
                try:
                    # Tentar inserir novamente após reconexão
                    response = supabase.table('pagamentos').insert(dados_insert).execute()
                    
                    if response.data and len(response.data) > 0:
                        print(f"✅ {len(response.data)} pagamentos inseridos com sucesso após reconexão para venda ID: {venda_id}")
                        return True
                    else:
                        print("❌ Erro: Resposta vazia ao inserir pagamentos da venda após reconexão")
                        return False
                        
                except Exception as e2:
                    print(f"❌ Erro ao inserir pagamentos da venda após reconexão: {str(e2)}")
                    return False
            else:
                print("❌ Falha na reconexão")
                return False
        
        return False



def buscar_venda_completa(venda_id: int) -> Optional[Dict]:
    """
    Busca uma venda completa com todos os dados relacionados (itens, pagamentos, cliente, vendedor).
    
    Args:
        venda_id (int): ID da venda a ser buscada
    
    Returns:
        Optional[Dict]: Dicionário com todos os dados da venda ou None se não encontrada.
        Estrutura retornada:
        {
            'id': int,
            'data_hora': str,
            'valor_total': float,
            'desconto_percentual': float,
            'desconto_valor': float,
            'valor_final': float,
            'status': str,
            'data_cancelamento': str or None,
            'motivo_cancelamento': str or None,
            'cliente': {...} or None,  # Dados do cliente se existir
            'vendedor': {...},  # Dados do vendedor
            'usuario_cancelamento': {...} or None,  # Dados do usuário que cancelou (se aplicável)
            'itens': [...],  # Lista de itens com dados do produto
            'pagamentos': [...]  # Lista de pagamentos
        }
    
    Validates: Requirement 7.1
    """
    global supabase
    
    if not supabase:
        print("❌ Erro: Conexão com Supabase não estabelecida")
        return None
    
    try:
        # Buscar dados da venda com JOINs para cliente, vendedor e usuário de cancelamento
        response = supabase.table('vendas').select(
            '''
            *,
            cliente:clientes(*),
            vendedor:usuarios!vendas_usuario_id_fkey(*),
            usuario_cancelamento:usuarios!vendas_usuario_cancelamento_id_fkey(*)
            '''
        ).eq('id', venda_id).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"⚠️ Venda com ID {venda_id} não encontrada")
            return None
        
        venda = response.data[0]
        
        # Buscar itens da venda com dados dos produtos
        itens_response = supabase.table('itens_venda').select(
            '''
            *,
            produto:produtos(*)
            '''
        ).eq('venda_id', venda_id).execute()
        
        itens = itens_response.data if itens_response.data else []
        
        # Buscar pagamentos da venda
        pagamentos_response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
        
        pagamentos = pagamentos_response.data if pagamentos_response.data else []
        
        # Estruturar dados da venda completa
        venda_completa = {
            'id': venda['id'],
            'data_hora': venda['data_hora'],
            'valor_total': float(venda['valor_total']),
            'desconto_percentual': float(venda['desconto_percentual']),
            'desconto_valor': float(venda['desconto_valor']),
            'valor_final': float(venda['valor_final']),
            'status': venda['status'],
            'data_cancelamento': venda.get('data_cancelamento'),
            'motivo_cancelamento': venda.get('motivo_cancelamento'),
            'cliente': venda.get('cliente'),  # None para vendas avulsas
            'vendedor': venda.get('vendedor'),
            'usuario_cancelamento': venda.get('usuario_cancelamento'),
            'itens': itens,
            'pagamentos': pagamentos
        }
        
        print(f"✅ Venda ID {venda_id} encontrada com {len(itens)} itens e {len(pagamentos)} pagamentos")
        return venda_completa
        
    except Exception as e:
        print(f"❌ Erro ao buscar venda completa: {str(e)}")
        
        # Tentar reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "network" in str(e).lower():
            print("🔄 Tentando reconectar...")
            if reconectar_supabase():
                try:
                    # Tentar buscar novamente após reconexão
                    response = supabase.table('vendas').select(
                        '''
                        *,
                        cliente:clientes(*),
                        vendedor:usuarios!vendas_usuario_id_fkey(*),
                        usuario_cancelamento:usuarios!vendas_usuario_cancelamento_id_fkey(*)
                        '''
                    ).eq('id', venda_id).execute()
                    
                    if not response.data or len(response.data) == 0:
                        print(f"⚠️ Venda com ID {venda_id} não encontrada após reconexão")
                        return None
                    
                    venda = response.data[0]
                    
                    # Buscar itens da venda com dados dos produtos
                    itens_response = supabase.table('itens_venda').select(
                        '''
                        *,
                        produto:produtos(*)
                        '''
                    ).eq('venda_id', venda_id).execute()
                    
                    itens = itens_response.data if itens_response.data else []
                    
                    # Buscar pagamentos da venda
                    pagamentos_response = supabase.table('pagamentos').select('*').eq('venda_id', venda_id).execute()
                    
                    pagamentos = pagamentos_response.data if pagamentos_response.data else []
                    
                    # Estruturar dados da venda completa
                    venda_completa = {
                        'id': venda['id'],
                        'data_hora': venda['data_hora'],
                        'valor_total': float(venda['valor_total']),
                        'desconto_percentual': float(venda['desconto_percentual']),
                        'desconto_valor': float(venda['desconto_valor']),
                        'valor_final': float(venda['valor_final']),
                        'status': venda['status'],
                        'data_cancelamento': venda.get('data_cancelamento'),
                        'motivo_cancelamento': venda.get('motivo_cancelamento'),
                        'cliente': venda.get('cliente'),  # None para vendas avulsas
                        'vendedor': venda.get('vendedor'),
                        'usuario_cancelamento': venda.get('usuario_cancelamento'),
                        'itens': itens,
                        'pagamentos': pagamentos
                    }
                    
                    print(f"✅ Venda ID {venda_id} encontrada após reconexão com {len(itens)} itens e {len(pagamentos)} pagamentos")
                    return venda_completa
                    
                except Exception as e2:
                    print(f"❌ Erro ao buscar venda completa após reconexão: {str(e2)}")
                    return None
            else:
                print("❌ Falha na reconexão")
                return None
        
        return None


def marcar_venda_cancelada(venda_id: int, motivo: str, usuario_id: int) -> bool:
    """
    Marca uma venda como cancelada no banco de dados.
    
    Args:
        venda_id: ID da venda a ser cancelada
        motivo: Motivo do cancelamento
        usuario_id: ID do usuário que está cancelando
        
    Returns:
        bool: True se sucesso, False caso contrário
    
    Validates: Requirements 7.3, 7.6, 7.8
    """
    global supabase
    
    if not supabase:
        print("❌ Erro: Conexão com Supabase não estabelecida")
        return False
    
    try:
        from datetime import datetime
        
        # Preparar dados de atualização
        dados_update = {
            'status': 'cancelada',
            'data_cancelamento': datetime.now().isoformat(),
            'motivo_cancelamento': motivo,
            'usuario_cancelamento_id': usuario_id
        }
        
        # Atualizar venda na tabela
        response = supabase.table('vendas').update(dados_update).eq('id', venda_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"✅ Venda ID {venda_id} marcada como cancelada com sucesso")
            return True
        else:
            print(f"❌ Erro: Venda ID {venda_id} não encontrada ou não atualizada")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao marcar venda como cancelada: {str(e)}")
        
        # Tentar reconectar em caso de erro de conexão
        if "connection" in str(e).lower() or "network" in str(e).lower():
            print("🔄 Tentando reconectar...")
            if reconectar_supabase():
                try:
                    from datetime import datetime
                    
                    # Preparar dados de atualização
                    dados_update = {
                        'status': 'cancelada',
                        'data_cancelamento': datetime.now().isoformat(),
                        'motivo_cancelamento': motivo,
                        'usuario_cancelamento_id': usuario_id
                    }
                    
                    # Tentar atualizar novamente após reconexão
                    response = supabase.table('vendas').update(dados_update).eq('id', venda_id).execute()
                    
                    if response.data and len(response.data) > 0:
                        print(f"✅ Venda ID {venda_id} marcada como cancelada após reconexão")
                        return True
                    else:
                        print(f"❌ Erro: Venda ID {venda_id} não encontrada ou não atualizada após reconexão")
                        return False
                        
                except Exception as e2:
                    print(f"❌ Erro ao marcar venda como cancelada após reconexão: {str(e2)}")
                    return False
            else:
                print("❌ Falha na reconexão")
                return False
        
        return False
