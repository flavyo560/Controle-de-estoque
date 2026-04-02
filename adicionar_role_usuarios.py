"""
Script para adicionar a coluna 'role' na tabela usuarios do Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"Conectando ao Supabase em: {url}")
supabase = create_client(url, key)

print("\n🔧 Adicionando coluna 'role' na tabela usuarios...")

# Verificar estrutura atual
try:
    print("\n1. Verificando estrutura atual da tabela usuarios...")
    response = supabase.table("usuarios").select("*").limit(1).execute()
    
    if response.data:
        print(f"✅ Tabela usuarios existe")
        print(f"📋 Colunas atuais: {list(response.data[0].keys())}")
        
        if 'role' in response.data[0]:
            print("✅ Coluna 'role' já existe!")
        else:
            print("⚠️  Coluna 'role' NÃO existe")
            print("\n⚠️  ATENÇÃO:")
            print("A coluna 'role' precisa ser adicionada manualmente no Supabase.")
            print("\nPara adicionar a coluna 'role', siga estes passos:")
            print("\n1. Acesse o Supabase Dashboard: https://supabase.com/dashboard")
            print("2. Selecione seu projeto")
            print("3. Vá em 'Table Editor' > 'usuarios'")
            print("4. Clique em '+ New Column'")
            print("5. Configure:")
            print("   - Name: role")
            print("   - Type: varchar ou text")
            print("   - Default value: 'user'")
            print("   - Is nullable: NO")
            print("6. Clique em 'Save'")
            print("\nOu execute este SQL no SQL Editor:")
            print("\n" + "="*70)
            print("ALTER TABLE usuarios ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';")
            print("ALTER TABLE usuarios ADD CONSTRAINT chk_usuarios_role CHECK (role IN ('admin', 'manager', 'user'));")
            print("UPDATE usuarios SET role = 'admin' WHERE username = 'Monica';")
            print("="*70)
    else:
        print("❌ Tabela usuarios está vazia ou não existe")
        
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n" + "="*70)
