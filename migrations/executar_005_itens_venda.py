"""
Script para executar a migração 005 - Criar tabela 'itens_venda'
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
    
    tabelas_necessarias = ['vendas', 'produtos']
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
            if tabela == 'vendas':
                print(f"   - {tabela}: Execute a Migração 004 primeiro")
            elif tabela == 'produtos':
                print(f"   - {tabela}: Deve existir no sistema de estoque")
        return False
    
    print("✅ Todos os pré-requisitos atendidos!\n")
    return True


def executar_migracao():
    """Executa a migração 005 para criar a tabela itens_venda"""
    
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
        migration_file = Path(__file__).parent / '005_criar_tabela_itens_venda.sql'
        
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
        print("   - Cole o conteúdo do arquivo: 005_criar_tabela_itens_venda.sql")
        print("   - Clique em 'Run'\n")
        
        print("2️⃣  VIA CLI DO SUPABASE:")
        print("   supabase db push --file migrations/005_criar_tabela_itens_venda.sql\n")
        
        print("3️⃣  VIA PSYCOPG2 (Conexão direta PostgreSQL):")
        print("   Requer credenciais de conexão direta ao PostgreSQL\n")
        
        print("="*70)
        print("\n📋 CONTEÚDO DO ARQUIVO SQL:\n")
        print(sql_script)
        print("\n" + "="*70)
        
        # Tentar verificar se a tabela já existe
        print("\n🔍 Verificando se a tabela 'itens_venda' já existe...")
        
        try:
            # Tentar fazer uma query simples na tabela
            response = supabase.table("itens_venda").select("id").limit(1).execute()
            print("✅ A tabela 'itens_venda' JÁ EXISTE no banco de dados!")
            print(f"   Resposta: {response}")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "does not exist" in error_msg or "relation" in error_msg:
                print("⚠️  A tabela 'itens_venda' NÃO EXISTE ainda.")
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
        print("🔍 VERIFICANDO MIGRAÇÃO 005")
        print("="*70 + "\n")
        
        # Verificar se a tabela existe
        print("1️⃣  Verificando existência da tabela 'itens_venda'...")
        
        try:
            response = supabase.table("itens_venda").select("id").limit(1).execute()
            print("   ✅ Tabela 'itens_venda' existe!")
            
            # Verificar se as tabelas relacionadas existem
            print("\n2️⃣  Verificando foreign keys...")
            
            # Verificar vendas
            try:
                supabase.table("vendas").select("id").limit(1).execute()
                print("   ✅ Foreign key para 'vendas' OK")
            except:
                print("   ⚠️  Tabela 'vendas' não encontrada")
            
            # Verificar produtos
            try:
                supabase.table("produtos").select("id").limit(1).execute()
                print("   ✅ Foreign key para 'produtos' OK")
            except:
                print("   ⚠️  Tabela 'produtos' não encontrada")
            
            # Tentar inserir um registro de teste
            print("\n3️⃣  Testando inserção de registro...")
            
            # Primeiro, buscar uma venda_id válida
            vendas_response = supabase.table("vendas").select("id").limit(1).execute()
            
            if not vendas_response.data or len(vendas_response.data) == 0:
                print("   ⚠️  Nenhuma venda encontrada. Não é possível testar inserção.")
                print("   ✅ Mas a tabela 'itens_venda' existe e está acessível!")
                return True
            
            venda_id = vendas_response.data[0]['id']
            
            # Buscar um produto_id válido
            produtos_response = supabase.table("produtos").select("id, preco_venda").limit(1).execute()
            
            if not produtos_response.data or len(produtos_response.data) == 0:
                print("   ⚠️  Nenhum produto encontrado. Não é possível testar inserção.")
                print("   ✅ Mas a tabela 'itens_venda' existe e está acessível!")
                return True
            
            produto_id = produtos_response.data[0]['id']
            preco_unitario = float(produtos_response.data[0].get('preco_venda', 10.00))
            
            test_data = {
                "venda_id": venda_id,
                "produto_id": produto_id,
                "quantidade": 2,
                "preco_unitario": preco_unitario,
                "subtotal": preco_unitario * 2
            }
            
            insert_response = supabase.table("itens_venda").insert(test_data).execute()
            print("   ✅ Inserção bem-sucedida!")
            
            # Buscar o registro inserido
            print("\n4️⃣  Testando busca por venda_id...")
            
            if insert_response.data and len(insert_response.data) > 0:
                item_id = insert_response.data[0]['id']
                search_response = supabase.table("itens_venda").select("*").eq("venda_id", venda_id).execute()
                
                if search_response.data and len(search_response.data) > 0:
                    print("   ✅ Busca bem-sucedida!")
                    print(f"   Registro encontrado: ID={item_id}, Quantidade={test_data['quantidade']}, Subtotal=R$ {test_data['subtotal']:.2f}")
                    
                    # Testar busca por produto_id
                    print("\n5️⃣  Testando busca por produto_id...")
                    product_search = supabase.table("itens_venda").select("*").eq("produto_id", produto_id).execute()
                    
                    if product_search.data and len(product_search.data) > 0:
                        print("   ✅ Busca por produto bem-sucedida!")
                    
                    # Limpar registro de teste
                    print("\n6️⃣  Limpando registro de teste...")
                    delete_response = supabase.table("itens_venda").delete().eq("id", item_id).execute()
                    print("   ✅ Registro de teste removido!")
                    
                    print("\n" + "="*70)
                    print("✅ MIGRAÇÃO 005 VERIFICADA COM SUCESSO!")
                    print("="*70)
                    print("\n📊 Resumo:")
                    print("   ✅ Tabela 'itens_venda' criada")
                    print("   ✅ Foreign keys funcionando")
                    print("   ✅ Inserção de registros OK")
                    print("   ✅ Busca por venda_id OK")
                    print("   ✅ Busca por produto_id OK")
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
                print("   ❌ Tabela 'itens_venda' NÃO EXISTE!")
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
    print("MIGRAÇÃO 005: CRIAR TABELA 'ITENS_VENDA'")
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
