"""
Script para executar a migração 006 - Criar tabela 'pagamentos'
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
    
    tabelas_necessarias = ['vendas']
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
        return False
    
    print("✅ Todos os pré-requisitos atendidos!\n")
    return True


def executar_migracao():
    """Executa a migração 006 para criar a tabela pagamentos"""
    
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
        migration_file = Path(__file__).parent / '006_criar_tabela_pagamentos.sql'
        
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
        print("   - Cole o conteúdo do arquivo: 006_criar_tabela_pagamentos.sql")
        print("   - Clique em 'Run'\n")
        
        print("2️⃣  VIA CLI DO SUPABASE:")
        print("   supabase db push --file migrations/006_criar_tabela_pagamentos.sql\n")
        
        print("3️⃣  VIA PSYCOPG2 (Conexão direta PostgreSQL):")
        print("   Requer credenciais de conexão direta ao PostgreSQL\n")
        
        print("="*70)
        print("\n📋 CONTEÚDO DO ARQUIVO SQL:\n")
        print(sql_script)
        print("\n" + "="*70)
        
        # Tentar verificar se a tabela já existe
        print("\n🔍 Verificando se a tabela 'pagamentos' já existe...")
        
        try:
            # Tentar fazer uma query simples na tabela
            response = supabase.table("pagamentos").select("id").limit(1).execute()
            print("✅ A tabela 'pagamentos' JÁ EXISTE no banco de dados!")
            print(f"   Resposta: {response}")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "does not exist" in error_msg or "relation" in error_msg:
                print("⚠️  A tabela 'pagamentos' NÃO EXISTE ainda.")
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
        print("🔍 VERIFICANDO MIGRAÇÃO 006")
        print("="*70 + "\n")
        
        # Verificar se a tabela existe
        print("1️⃣  Verificando existência da tabela 'pagamentos'...")
        
        try:
            response = supabase.table("pagamentos").select("id").limit(1).execute()
            print("   ✅ Tabela 'pagamentos' existe!")
            
            # Verificar se a tabela vendas existe
            print("\n2️⃣  Verificando foreign key...")
            
            try:
                supabase.table("vendas").select("id").limit(1).execute()
                print("   ✅ Foreign key para 'vendas' OK")
            except:
                print("   ⚠️  Tabela 'vendas' não encontrada")
                return False
            
            # Tentar inserir registros de teste
            print("\n3️⃣  Testando inserção de registros...")
            
            # Primeiro, buscar ou criar uma venda de teste
            print("   📝 Criando venda de teste...")
            
            # Buscar um usuario_id válido
            usuarios_response = supabase.table("usuarios").select("id").limit(1).execute()
            
            if not usuarios_response.data or len(usuarios_response.data) == 0:
                print("   ⚠️  Nenhum usuário encontrado. Não é possível testar inserção.")
                print("   ✅ Mas a tabela 'pagamentos' existe e está acessível!")
                return True
            
            usuario_id = usuarios_response.data[0]['id']
            
            # Criar venda de teste
            venda_data = {
                "valor_total": 100.00,
                "valor_final": 100.00,
                "usuario_id": usuario_id,
                "status": "finalizada"
            }
            
            venda_response = supabase.table("vendas").insert(venda_data).execute()
            
            if not venda_response.data or len(venda_response.data) == 0:
                print("   ⚠️  Não foi possível criar venda de teste")
                return False
            
            venda_id = venda_response.data[0]['id']
            print(f"   ✅ Venda de teste criada (ID: {venda_id})")
            
            # Teste 1: Pagamento em dinheiro
            print("\n4️⃣  Testando pagamento em dinheiro...")
            
            pagamento_dinheiro = {
                "venda_id": venda_id,
                "forma_pagamento": "dinheiro",
                "valor": 50.00,
                "valor_recebido": 100.00,
                "troco": 50.00
            }
            
            pag1_response = supabase.table("pagamentos").insert(pagamento_dinheiro).execute()
            print("   ✅ Pagamento em dinheiro inserido com sucesso!")
            
            # Teste 2: Pagamento com cartão de crédito parcelado
            print("\n5️⃣  Testando pagamento com cartão de crédito parcelado...")
            
            pagamento_credito = {
                "venda_id": venda_id,
                "forma_pagamento": "cartao_credito",
                "valor": 50.00,
                "numero_parcelas": 3
            }
            
            pag2_response = supabase.table("pagamentos").insert(pagamento_credito).execute()
            print("   ✅ Pagamento com cartão de crédito inserido com sucesso!")
            
            # Teste 3: Pagamento via PIX
            print("\n6️⃣  Testando pagamento via PIX...")
            
            pagamento_pix = {
                "venda_id": venda_id,
                "forma_pagamento": "pix",
                "valor": 100.00
            }
            
            pag3_response = supabase.table("pagamentos").insert(pagamento_pix).execute()
            print("   ✅ Pagamento via PIX inserido com sucesso!")
            
            # Buscar todos os pagamentos da venda
            print("\n7️⃣  Testando busca de pagamentos por venda...")
            
            search_response = supabase.table("pagamentos").select("*").eq("venda_id", venda_id).execute()
            
            if search_response.data and len(search_response.data) >= 3:
                print(f"   ✅ Busca bem-sucedida! {len(search_response.data)} pagamentos encontrados")
                
                for pag in search_response.data:
                    print(f"      - {pag['forma_pagamento']}: R$ {pag['valor']}")
                
                # Testar CASCADE DELETE
                print("\n8️⃣  Testando CASCADE DELETE...")
                
                delete_response = supabase.table("vendas").delete().eq("id", venda_id).execute()
                print("   ✅ Venda deletada!")
                
                # Verificar se pagamentos foram deletados
                verify_response = supabase.table("pagamentos").select("id").eq("venda_id", venda_id).execute()
                
                if not verify_response.data or len(verify_response.data) == 0:
                    print("   ✅ Pagamentos deletados automaticamente (CASCADE)!")
                    
                    print("\n" + "="*70)
                    print("✅ MIGRAÇÃO 006 VERIFICADA COM SUCESSO!")
                    print("="*70)
                    print("\n📊 Resumo:")
                    print("   ✅ Tabela 'pagamentos' criada")
                    print("   ✅ Foreign key funcionando")
                    print("   ✅ Inserção de pagamentos OK")
                    print("   ✅ Pagamento em dinheiro OK")
                    print("   ✅ Pagamento parcelado OK")
                    print("   ✅ Pagamento via PIX OK")
                    print("   ✅ Busca de pagamentos OK")
                    print("   ✅ CASCADE DELETE funcionando")
                    return True
                else:
                    print("   ⚠️  Pagamentos não foram deletados automaticamente")
                    # Limpar manualmente
                    supabase.table("pagamentos").delete().eq("venda_id", venda_id).execute()
                    return False
            else:
                print("   ⚠️  Pagamentos não encontrados após inserção")
                # Limpar
                supabase.table("vendas").delete().eq("id", venda_id).execute()
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "does not exist" in error_msg or "relation" in error_msg:
                print("   ❌ Tabela 'pagamentos' NÃO EXISTE!")
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
    print("MIGRAÇÃO 006: CRIAR TABELA 'PAGAMENTOS'")
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
