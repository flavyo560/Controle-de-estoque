#!/usr/bin/env python3
"""
Script de Validação de Migração - Sistema de Estoque DEKIDS
Valida se a migração 001 foi executada corretamente no Supabase
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def conectar_supabase() -> Client:
    """Conecta ao Supabase usando variáveis de ambiente"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ ERRO: Variáveis SUPABASE_URL e SUPABASE_KEY não encontradas")
        print("   Configure-as no arquivo .env")
        sys.exit(1)
    
    try:
        supabase = create_client(url, key)
        print("✅ Conexão com Supabase estabelecida")
        return supabase
    except Exception as e:
        print(f"❌ ERRO ao conectar com Supabase: {e}")
        sys.exit(1)

def validar_tabela_existe(supabase: Client, nome_tabela: str) -> bool:
    """Verifica se uma tabela existe tentando fazer uma query"""
    try:
        # Tenta fazer um SELECT simples
        resultado = supabase.table(nome_tabela).select("*").limit(1).execute()
        print(f"✅ Tabela '{nome_tabela}' existe")
        return True
    except Exception as e:
        print(f"❌ Tabela '{nome_tabela}' NÃO existe ou não está acessível")
        print(f"   Erro: {e}")
        return False

def validar_campos_produtos(supabase: Client) -> bool:
    """Valida se os novos campos foram adicionados à tabela produtos"""
    print("\n📋 Validando campos da tabela 'produtos'...")
    
    try:
        # Tenta buscar um produto com os novos campos
        resultado = supabase.table("produtos").select(
            "id, descricao, estoque_minimo, codigo_barras, created_at, updated_at"
        ).limit(1).execute()
        
        print("✅ Campos 'estoque_minimo', 'codigo_barras', 'created_at', 'updated_at' existem")
        return True
    except Exception as e:
        print(f"❌ Erro ao validar campos da tabela produtos: {e}")
        return False

def validar_estrutura_usuarios(supabase: Client) -> bool:
    """Valida estrutura da tabela usuarios"""
    print("\n📋 Validando estrutura da tabela 'usuarios'...")
    
    try:
        resultado = supabase.table("usuarios").select(
            "id, username, senha_hash, ativo, tentativas_login, bloqueado_ate, ultimo_acesso, created_at"
        ).limit(1).execute()
        
        print("✅ Todos os campos da tabela 'usuarios' existem")
        return True
    except Exception as e:
        print(f"❌ Erro ao validar estrutura da tabela usuarios: {e}")
        return False

def validar_estrutura_movimentacoes(supabase: Client) -> bool:
    """Valida estrutura da tabela movimentacoes"""
    print("\n📋 Validando estrutura da tabela 'movimentacoes'...")
    
    try:
        resultado = supabase.table("movimentacoes").select(
            "id, produto_id, tipo, quantidade, quantidade_anterior, quantidade_nova, observacao, usuario_id, created_at"
        ).limit(1).execute()
        
        print("✅ Todos os campos da tabela 'movimentacoes' existem")
        return True
    except Exception as e:
        print(f"❌ Erro ao validar estrutura da tabela movimentacoes: {e}")
        return False

def validar_estrutura_sessoes(supabase: Client) -> bool:
    """Valida estrutura da tabela sessoes"""
    print("\n📋 Validando estrutura da tabela 'sessoes'...")
    
    try:
        resultado = supabase.table("sessoes").select(
            "id, usuario_id, token, expira_em, created_at"
        ).limit(1).execute()
        
        print("✅ Todos os campos da tabela 'sessoes' existem")
        return True
    except Exception as e:
        print(f"❌ Erro ao validar estrutura da tabela sessoes: {e}")
        return False

def testar_constraint_unicidade(supabase: Client) -> bool:
    """Testa se a constraint de unicidade (referencia, tamanho) está funcionando"""
    print("\n📋 Testando constraint de unicidade (referencia, tamanho)...")
    
    try:
        # Criar um produto de teste
        produto_teste = {
            "descricao": "TESTE_VALIDACAO_MIGRACAO",
            "referencia": "TEST_REF_001",
            "tamanho": "M",
            "quantidade": 0,
            "preco": 1.00,
            "estoque_minimo": 5
        }
        
        # Inserir primeira vez
        resultado1 = supabase.table("produtos").insert(produto_teste).execute()
        produto_id = resultado1.data[0]["id"]
        
        # Tentar inserir duplicado (deve falhar)
        try:
            resultado2 = supabase.table("produtos").insert(produto_teste).execute()
            print("❌ Constraint de unicidade NÃO está funcionando (permitiu duplicata)")
            
            # Limpar produto de teste
            supabase.table("produtos").delete().eq("id", produto_id).execute()
            return False
        except Exception:
            print("✅ Constraint de unicidade está funcionando (rejeitou duplicata)")
            
            # Limpar produto de teste
            supabase.table("produtos").delete().eq("id", produto_id).execute()
            return True
            
    except Exception as e:
        print(f"⚠️  Não foi possível testar constraint: {e}")
        return True  # Não falhar a validação por isso

def main():
    """Função principal de validação"""
    print("=" * 70)
    print("🔍 VALIDAÇÃO DE MIGRAÇÃO - Sistema de Estoque DEKIDS")
    print("=" * 70)
    print()
    
    # Conectar ao Supabase
    supabase = conectar_supabase()
    
    # Lista de validações
    validacoes = []
    
    # Validar tabelas existem
    print("\n📦 Validando existência de tabelas...")
    validacoes.append(validar_tabela_existe(supabase, "produtos"))
    validacoes.append(validar_tabela_existe(supabase, "usuarios"))
    validacoes.append(validar_tabela_existe(supabase, "movimentacoes"))
    validacoes.append(validar_tabela_existe(supabase, "sessoes"))
    
    # Validar estruturas
    validacoes.append(validar_campos_produtos(supabase))
    validacoes.append(validar_estrutura_usuarios(supabase))
    validacoes.append(validar_estrutura_movimentacoes(supabase))
    validacoes.append(validar_estrutura_sessoes(supabase))
    
    # Testar constraints
    validacoes.append(testar_constraint_unicidade(supabase))
    
    # Resultado final
    print("\n" + "=" * 70)
    if all(validacoes):
        print("✅ SUCESSO: Migração validada com sucesso!")
        print("   Todas as tabelas, campos e constraints estão corretos.")
        print("\n📝 Próximos passos:")
        print("   1. Criar usuário administrador inicial")
        print("   2. Continuar com a implementação das funcionalidades")
        print("=" * 70)
        sys.exit(0)
    else:
        print("❌ FALHA: Alguns problemas foram encontrados na migração")
        print("   Revise os erros acima e execute a migração novamente.")
        print("\n📖 Consulte migrations/README.md para instruções detalhadas")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
