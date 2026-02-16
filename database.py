import os
from supabase import create_client, Client

# --- CONFIGURAÇÃO --
# Agora o código lê os valores que você cadastrou no painel do Render
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Cria a conexão usando as variáveis seguras
supabase: Client = create_client(url, key)

# 1. FUNÇÃO PARA CADASTRAR
def cadastrar_produto(descricao, genero, marca, referencia, tamanho, qtd, preco):
    data = {
        "descricao": descricao,
        "genero": genero,
        "marca": marca,
        "referencia": referencia,
        "tamanho": tamanho,
        "quantidade": qtd,
        "preco": preco
    }
    try:
        response = supabase.table("produtos").insert(data).execute()
        return response
    except Exception as e:
        print(f"Erro ao conectar com o Supabase: {e}")
        return None

# 2. FUNÇÃO PARA LISTAR
def listar_estoque():
    try:
        response = supabase.table("produtos").select("*").order("id").execute()
        return response.data
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return []

# 3. FUNÇÃO PARA EXCLUIR
def excluir_produto(id_produto):
    try:
        supabase.table("produtos").delete().eq("id", id_produto).execute()
        return True
    except Exception as e:
        print(f"Erro ao excluir no banco: {e}")
        return False

# 4. FUNÇÃO PARA REGISTRAR SAÍDA (-1 unidade)
def registrar_saida(id_produto, qtd_atual):
    try:
        if qtd_atual > 0:
            nova_qtd = qtd_atual - 1
            supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", id_produto).execute()
            return True
        return False 
    except Exception as e:
        print(f"Erro ao registrar saída: {e}")
        return False

# 5. FUNÇÃO PARA REGISTRAR ENTRADA (+1 unidade - Reposição)
def registrar_entrada(id_produto, qtd_atual):
    try:
        nova_qtd = qtd_atual + 1
        supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", id_produto).execute()
        return True
    except Exception as e:
        print(f"Erro ao registrar entrada: {e}")
        return False

# 6. FUNÇÃO PARA REGISTRAR ESTORNO (+1 unidade - Devolução do Cliente)
def registrar_estorno(id_produto, qtd_atual):
    try:
        # A lógica é a mesma da entrada, mas o nome ajuda na organização do código
        nova_qtd = qtd_atual + 1
        supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", id_produto).execute()
        return True
    except Exception as e:
        print(f"Erro ao registrar estorno: {e}")
        return False

# --- ÁREA DE TESTES (Sempre ao final) ---
if __name__ == "__main__":
    # Caso queira testar algo direto por aqui
    pass