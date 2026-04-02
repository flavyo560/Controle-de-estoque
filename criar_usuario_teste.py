#!/usr/bin/env python3
"""
Script para Criar Usuário de Teste - Sistema PDV DEKIDS
Cria um usuário de teste com ID=1 para testes automatizados
"""

import os
import sys
import bcrypt
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

def hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def criar_usuario_teste(supabase: Client) -> bool:
    """Cria usuário de teste com ID=1"""
    try:
        # Verificar se usuário com ID=1 já existe
        resultado = supabase.table("usuarios").select("id, username").eq("id", 1).execute()
        
        if resultado.data:
            print(f"✅ Usuário de teste já existe: {resultado.data[0]['username']}")
            return True
        
        # Gerar hash da senha 'teste123'
        senha_hash = hash_senha('teste123')
        
        # Inserir usuário com ID=1
        novo_usuario = {
            "id": 1,
            "username": "teste",
            "senha_hash": senha_hash,
            "ativo": True,
            "tentativas_login": 0
        }
        
        resultado = supabase.table("usuarios").insert(novo_usuario).execute()
        
        if resultado.data:
            print(f"✅ Usuário de teste criado com sucesso!")
            print(f"   Username: teste")
            print(f"   Senha: teste123")
            print(f"   ID: 1")
            return True
        else:
            print("❌ Erro ao criar usuário de teste")
            return False
            
    except Exception as e:
        print(f"❌ ERRO ao criar usuário de teste: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("🧪 CRIAR USUÁRIO DE TESTE - Sistema PDV DEKIDS")
    print("=" * 60)
    print()
    
    # Conectar ao Supabase
    supabase = conectar_supabase()
    
    # Criar usuário de teste
    if criar_usuario_teste(supabase):
        print()
        print("=" * 60)
        print("✅ SUCESSO: Usuário de teste configurado!")
        print()
        print("📋 Credenciais de teste:")
        print("   Username: teste")
        print("   Senha: teste123")
        print("   ID: 1")
        print()
        print("⚠️  Este usuário é apenas para testes automatizados")
        print("=" * 60)
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("❌ FALHA: Não foi possível criar o usuário de teste")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
