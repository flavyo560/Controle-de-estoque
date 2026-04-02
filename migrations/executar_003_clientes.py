"""
Script para executar a migração 003 - Criar tabela 'clientes'
Sistema: DEKIDS Moda Infantil - Sistema de Vendas
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Adicionar diretório pai ao path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

# Carregar variáveis de ambiente
script_dir = Path(__file__).parent.parent
env_path = script_dir / '.env'
load_dotenv(dotenv_path=env_path, override=True)


def executar_migracao():
    """Executa a migração 003 para criar a tabela clientes"""
    
    # Configurar cliente Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ ERRO: Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não encontradas!")
        print("   Verifique se o arquivo .env existe e contém as credenciais corretas.")
        return False
    
    print(f"🔗 Conectando ao Supabase: {url}")
    
    try:
        supabase: Client = create_client(url, key)
        print("✅ Conexão estabelecida com sucesso!")
        
        # Ler o arquivo SQL
        migration_file = Path(__file__).parent / '003_criar_tabela_clientes.sql'
        
        if not migration_file.exists():
            print(f"❌ ERRO: Arquivo de migração não encontrado: {migration_file}")
            return False
        
        print(f"📄 Lendo arquivo de migração: {migration_file.name}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("\n" + "="*70)
        print("⚠️  ATENÇÃO: Executar migração via Python requer acesso direto ao PostgreSQL")
        print("="*70)
        print("\nO cliente Python do Supabase não suporta execução direta de SQL DDL.")
        print("\nPara executar esta migração, você tem 3 opções:\n")
        
        print("1️⃣  VIA DASHBOARD DO SUPABASE (Recomendado):")
        print("   - Acesse: https://app.supabase.com")
        print("   - Vá em: SQL Editor > New Query")
        print("   - Cole o conteúdo do arquivo: 003_criar_tabela_clientes.sql")
        print("   - Clique em 'Run'\n")
        
        print("2️⃣  VIA CLI DO SUPABASE:")
        print("   supabase db push --file migrations/003_criar_tabela_clientes.sql\n")
        
        print("3️⃣  VIA PSYCOPG2 (Conexão direta PostgreSQL):")
        print("   Requer credenciais de conexão direta ao PostgreSQL\n")
        
        print("="*70)
        print("\n📋 CONTEÚDO DO ARQUIVO SQL:\n")
        print(sql_script)
        print("\n" + "="*70)
        
        # Tentar verificar se a tabela já existe
        print("\n🔍 Verificando se a tabela 'clientes' já existe...")
        
        try:
            # Tentar fazer uma query simples na tabela
            response = supabase.table("clientes").select("id").limit(1).execute()
            print("✅ A tabela 'clientes' JÁ EXISTE no banco de dados!")
            print(f"   Resposta: {response}")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "does not exist" in error_msg or "relation" in error_msg:
                print("⚠️  A tabela 'clientes' NÃO EXISTE ainda.")
                print("   Por favor, execute a migração usando uma das opções acima.")
                return False
            else:
                print(f"⚠️  Erro ao verificar tabela: {e}")
                return False
        
    except Exception as e:
        print(f"❌ ERRO ao conectar ao Supabase: {e}")
        return False


def verificar_migracao():
    """Verifica se a migração foi executada com sucesso"""
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ ERRO: Variáveis de ambiente não encontradas!")
        return False
    
    try:
        supabase: Client = create_client(url, key)
        
        print("\n" + "="*70)
        print("🔍 VERIFICANDO MIGRAÇÃO 003")
        print("="*70 + "\n")
        
        # Verificar se a tabela existe
        print("1️⃣  Verificando existência da tabela 'clientes'...")
        
        try:
            response = supabase.table("clientes").select("id").limit(1).execute()
            print("   ✅ Tabela 'clientes' existe!")
            
            # Tentar inserir e buscar um registro de teste
            print("\n2️⃣  Testando inserção de registro...")
            
            test_data = {
                "nome": "Cliente Teste Migração",
                "cpf": "99999999999",
                "telefone": "11999999999",
                "email": "teste@migracao.com"
            }
            
            insert_response = supabase.table("clientes").insert(test_data).execute()
            print("   ✅ Inserção bem-sucedida!")
            
            # Buscar o registro inserido
            print("\n3️⃣  Testando busca por CPF...")
            search_response = supabase.table("clientes").select("*").eq("cpf", "99999999999").execute()
            
            if search_response.data and len(search_response.data) > 0:
                print("   ✅ Busca bem-sucedida!")
                print(f"   Registro encontrado: {search_response.data[0]}")
                
                # Limpar registro de teste
                print("\n4️⃣  Limpando registro de teste...")
                delete_response = supabase.table("clientes").delete().eq("cpf", "99999999999").execute()
                print("   ✅ Registro de teste removido!")
                
                print("\n" + "="*70)
                print("✅ MIGRAÇÃO 003 VERIFICADA COM SUCESSO!")
                print("="*70)
                return True
            else:
                print("   ⚠️  Registro não encontrado após inserção")
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "does not exist" in error_msg or "relation" in error_msg:
                print("   ❌ Tabela 'clientes' NÃO EXISTE!")
                print("\n   Por favor, execute a migração primeiro.")
                return False
            else:
                print(f"   ❌ Erro: {e}")
                return False
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MIGRAÇÃO 003: CRIAR TABELA 'CLIENTES'")
    print("Sistema de Vendas DEKIDS")
    print("="*70 + "\n")
    
    # Executar migração (mostra instruções)
    executar_migracao()
    
    # Perguntar se deseja verificar
    print("\n" + "="*70)
    resposta = input("\n❓ Deseja verificar se a migração foi executada? (s/n): ").strip().lower()
    
    if resposta == 's':
        verificar_migracao()
    else:
        print("\n✅ Script finalizado.")
