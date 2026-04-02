"""
Script para atualizar Monica para admin diretamente no Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"Conectando ao Supabase em: {url}")
supabase = create_client(url, key)

print("\n🔄 Atualizando Monica para role 'admin'...")

try:
    # Atualizar role da Monica
    response = supabase.table("usuarios")\
        .update({"role": "admin"})\
        .eq("username", "Monica")\
        .execute()
    
    print(f"✅ Monica atualizada para admin com sucesso!")
    print(f"📋 Resposta: {response.data}")
    
    # Verificar
    print("\n🔍 Verificando...")
    response = supabase.table("usuarios")\
        .select("id, username, role")\
        .eq("username", "Monica")\
        .execute()
    
    if response.data:
        usuario = response.data[0]
        print(f"✅ Confirmado: {usuario['username']} - Role: {usuario['role']}")
    
except Exception as e:
    print(f"❌ Erro: {e}")

print("\n" + "="*70)
print("⚠️  IMPORTANTE: Faça logout e login novamente para aplicar as mudanças!")
print("="*70)
