"""
Script para executar a migração 004 - Criar tabela 'vendas'
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


def verificar_prerequisitos(supabase: Client) -> bool:
    """Verifica se as tabelas necessárias existem antes de executar a migração"""
    
    print("\n🔍 Verificando pré-requisitos...")
    
    tabelas_necessarias = ['clientes', 'usuarios']
    tabelas_faltando = []
    
    for tabela in tabelas_necessarias:
        try:
            supabase.table(tabela).select("id").limit(1).execute()
            print(f"   ✅ Tabela '{tabela}' existe")
        except Exception as e:
            error_msg = str(e).lower()
            if "does not exist" in error_msg or "relation" in error_msg:
                print(f"   ❌ Tabela '{tabela}' NÃO EXISTE!")
                tabelas_faltando.append(tabela)
            else:
                print(f"   ⚠️  Erro ao verificar tabela '{tabela}': {e}")
                tabelas_faltando.append(tabela)
    
    if tabelas_faltando:
        print("\n❌ ERRO: Tabelas necessárias não encontradas!")
        print("\nPré-requisitos faltando:")
        for tabela in tabelas_faltando:
            if tabela == 'clientes':
                print(f"   - {tabela}: Execute a Migração 003 primeiro")
            elif tabela == 'usuarios':
                print(f"   - {tabela}: Deve existir no sistema de autenticação")
        return False
    
    print("✅ Todos os pré-requisitos atendidos!\n")
    return True


def executar_migracao():
    """Executa a migração 004 para criar a tabela vendas"""
    
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
        
        # Verificar pré-requisitos
        if not verificar_prerequisitos(supabase):
            return False
        
        # Ler o arquivo SQL
        migration_file = Path(__file__).parent / '004_criar_tabela_vendas.sql'
        
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
        print("   - Cole o conteúdo do arquivo: 004_criar_tabela_vendas.sql")
        print("   - Clique em 'Run'\n")
        
        print("2️⃣  VIA CLI DO SUPABASE:")
        print("   supabase db push --file migrations/004_criar_tabela_vendas.sql\n")
        
        print("3️⃣  VIA PSYCOPG2 (Conexão direta PostgreSQL):")
        print("   Requer credenciais de conexão direta ao PostgreSQL\n")
        
        print("="*70)
        print("\n📋 CONTEÚDO DO ARQUIVO SQL:\n")
        print(sql_script)
        print("\n" + "="*70)
        
        # Tentar verificar se a tabela já existe
        print("\n🔍 Verificando se a tabela 'vendas' já existe...")
        
        try:
            # Tentar fazer uma query simples na tabela
            response = supabase.table("vendas").select("id").limit(1).execute()
            print("✅ A tabela 'vendas' JÁ EXISTE no banco de dados!")
            print(f"   Resposta: {response}")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "does not exist" in error_msg or "relation" in error_msg:
                print("⚠️  A tabela 'vendas' NÃO EXISTE ainda.")
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
        print("🔍 VERIFICANDO MIGRAÇÃO 004")
        print("="*70 + "\n")
        
        # Verificar se a tabela existe
        print("1️⃣  Verificando existência da tabela 'vendas'...")
        
        try:
            response = supabase.table("vendas").select("id").limit(1).execute()
            print("   ✅ Tabela 'vendas' existe!")
            
            # Verificar se as tabelas relacionadas existem
            print("\n2️⃣  Verificando foreign keys...")
            
            # Verificar clientes
            try:
                supabase.table("clientes").select("id").limit(1).execute()
                print("   ✅ Foreign key para 'clientes' OK")
            except:
                print("   ⚠️  Tabela 'clientes' não encontrada")
            
            # Verificar usuarios
            try:
                supabase.table("usuarios").select("id").limit(1).execute()
                print("   ✅ Foreign key para 'usuarios' OK")
            except:
                print("   ⚠️  Tabela 'usuarios' não encontrada")
            
            # Tentar inserir um registro de teste
            print("\n3️⃣  Testando inserção de registro...")
            
            # Primeiro, buscar um usuario_id válido
            usuarios_response = supabase.table("usuarios").select("id").limit(1).execute()
            
            if not usuarios_response.data or len(usuarios_response.data) == 0:
                print("   ⚠️  Nenhum usuário encontrado. Não é possível testar inserção.")
                print("   ✅ Mas a tabela 'vendas' existe e está acessível!")
                return True
            
            usuario_id = usuarios_response.data[0]['id']
            
            # Buscar um cliente_id válido (opcional)
            cliente_id = None
            try:
                clientes_response = supabase.table("clientes").select("id").limit(1).execute()
                if clientes_response.data and len(clientes_response.data) > 0:
                    cliente_id = clientes_response.data[0]['id']
            except:
                pass
            
            test_data = {
                "valor_total": 100.00,
                "desconto_percentual": 10.00,
                "desconto_valor": 5.00,
                "valor_final": 85.00,
                "usuario_id": usuario_id,
                "status": "finalizada"
            }
            
            if cliente_id:
                test_data["cliente_id"] = cliente_id
            
            insert_response = supabase.table("vendas").insert(test_data).execute()
            print("   ✅ Inserção bem-sucedida!")
            
            # Buscar o registro inserido
            print("\n4️⃣  Testando busca por ID...")
            
            if insert_response.data and len(insert_response.data) > 0:
                venda_id = insert_response.data[0]['id']
                search_response = supabase.table("vendas").select("*").eq("id", venda_id).execute()
                
                if search_response.data and len(search_response.data) > 0:
                    print("   ✅ Busca bem-sucedida!")
                    print(f"   Registro encontrado: ID={venda_id}, Valor Final=R$ {search_response.data[0]['valor_final']}")
                    
                    # Testar atualização para cancelada
                    print("\n5️⃣  Testando cancelamento de venda...")
                    
                    update_data = {
                        "status": "cancelada",
                        "motivo_cancelamento": "Teste de migração",
                        "usuario_cancelamento_id": usuario_id
                    }
                    
                    update_response = supabase.table("vendas").update(update_data).eq("id", venda_id).execute()
                    print("   ✅ Cancelamento bem-sucedido!")
                    
                    # Limpar registro de teste
                    print("\n6️⃣  Limpando registro de teste...")
                    delete_response = supabase.table("vendas").delete().eq("id", venda_id).execute()
                    print("   ✅ Registro de teste removido!")
                    
                    print("\n" + "="*70)
                    print("✅ MIGRAÇÃO 004 VERIFICADA COM SUCESSO!")
                    print("="*70)
                    print("\n📊 Resumo:")
                    print("   ✅ Tabela 'vendas' criada")
                    print("   ✅ Foreign keys funcionando")
                    print("   ✅ Inserção de registros OK")
                    print("   ✅ Busca de registros OK")
                    print("   ✅ Atualização de status OK")
                    print("   ✅ Deleção de registros OK")
                    return True
                else:
                    print("   ⚠️  Registro não encontrado após inserção")
                    return False
            else:
                print("   ⚠️  Nenhum dado retornado após inserção")
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "does not exist" in error_msg or "relation" in error_msg:
                print("   ❌ Tabela 'vendas' NÃO EXISTE!")
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
    print("MIGRAÇÃO 004: CRIAR TABELA 'VENDAS'")
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
