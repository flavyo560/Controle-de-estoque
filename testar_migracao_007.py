import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv(override=True)

def testar_migracao():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("ERRO: Variaveis de ambiente SUPABASE_URL ou SUPABASE_KEY nao encontradas!")
        return
    
    supabase: Client = create_client(url, key)
    
    print("Iniciando verificacao da Migracao 007...")
    
    # 1. Verificar novo status na tabela vendas
    print("\n1. Verificando suporte ao status 'em_aberto' na tabela 'vendas'...")
    try:
        user_res = supabase.table("usuarios").select("id").limit(1).execute()
        if not user_res.data:
            print("Aviso: Nenhum usuario encontrado para teste de insercao.")
        else:
            user_id = user_res.data[0]['id']
            test_sale = {
                "valor_total": 0,
                "valor_final": 0,
                "usuario_id": user_id,
                "status": "em_aberto"
            }
            res = supabase.table("vendas").insert(test_sale).execute()
            if res.data:
                print("Sucesso: Tabela 'vendas' aceita o status 'em_aberto'.")
                supabase.table("vendas").delete().eq("id", res.data[0]['id']).execute()
            else:
                print("Erro: Falha ao inserir venda com status 'em_aberto'.")
    except Exception as e:
        print(f"Erro ao testar status 'em_aberto': {e}")
        print("   DICA: Voce aplicou a Parte 1 da migracao 007 no dashboard do Supabase?")

    # 2. Verificar tabelas financeiras
    tabelas = ["financeiro_categorias", "contas_pagar", "contas_receber", "fluxo_caixa"]
    print("\n2. Verificando novas tabelas financeiras...")
    
    for tabela in tabelas:
        try:
            supabase.table(tabela).select("id").limit(1).execute()
            print(f"Tabela '{tabela}' existe.")
        except Exception as e:
            print(f"Tabela '{tabela}' NAO encontrada ou erro: {e}")

    print("\n--- Fim da Verificacao ---")

if __name__ == "__main__":
    testar_migracao()
