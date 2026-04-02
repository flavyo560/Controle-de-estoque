"""Script de teste para verificar conexão com Supabase"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"Conectando ao Supabase em: {url}")
supabase = create_client(url, key)

print("✅ Conexão estabelecida!")

# Testar query simples
try:
    print("\nTestando query na tabela produtos...")
    response = supabase.table("produtos").select("id").limit(1).execute()
    print(f"✅ Query produtos OK - {len(response.data)} registros")
except Exception as e:
    print(f"❌ Erro na query produtos: {e}")

# Testar query na tabela usuarios
try:
    print("\nTestando query na tabela usuarios...")
    response = supabase.table("usuarios").select("id").limit(1).execute()
    print(f"✅ Query usuarios OK - {len(response.data)} registros")
except Exception as e:
    print(f"❌ Erro na query usuarios: {e}")

# Testar query na tabela sessoes
try:
    print("\nTestando query na tabela sessoes...")
    response = supabase.table("sessoes").select("id").limit(1).execute()
    print(f"✅ Query sessoes OK - {len(response.data)} registros")
except Exception as e:
    print(f"❌ Erro na query sessoes: {e}")

print("\n✅ Todos os testes concluídos!")
