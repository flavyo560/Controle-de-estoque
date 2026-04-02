#!/usr/bin/env python3
"""
Script para Criar Usuário Administrador - Sistema de Estoque DEKIDS
Cria o primeiro usuário administrador no sistema
"""

import os
import sys
import bcrypt
from supabase import create_client, Client
from dotenv import load_dotenv
from getpass import getpass

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
        print("✅ Conexão com Supabase estabelecida\n")
        return supabase
    except Exception as e:
        print(f"❌ ERRO ao conectar com Supabase: {e}")
        sys.exit(1)

def hash_senha(senha: str) -> str:
    """Gera hash bcrypt da senha"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def validar_senha(senha: str) -> tuple[bool, str]:
    """Valida requisitos mínimos de senha"""
    if len(senha) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres"
    
    if senha.lower() == "admin" or senha.lower() == "admin123":
        return False, "Não use senhas óbvias como 'admin' ou 'admin123'"
    
    return True, ""

def criar_usuario(supabase: Client, username: str, senha: str) -> bool:
    """Cria um novo usuário no banco de dados"""
    try:
        # Verificar se usuário já existe
        resultado = supabase.table("usuarios").select("id").eq("username", username).execute()
        
        if resultado.data:
            print(f"⚠️  Usuário '{username}' já existe no sistema")
            return False
        
        # Gerar hash da senha
        senha_hash = hash_senha(senha)
        
        # Inserir usuário
        novo_usuario = {
            "username": username,
            "senha_hash": senha_hash,
            "ativo": True,
            "tentativas_login": 0
        }
        
        resultado = supabase.table("usuarios").insert(novo_usuario).execute()
        
        if resultado.data:
            print(f"✅ Usuário '{username}' criado com sucesso!")
            return True
        else:
            print("❌ Erro ao criar usuário")
            return False
            
    except Exception as e:
        print(f"❌ ERRO ao criar usuário: {e}")
        return False

def main():
    """Função principal"""
    print("=" * 70)
    print("👤 CRIAR USUÁRIO ADMINISTRADOR - Sistema de Estoque DEKIDS")
    print("=" * 70)
    print()
    
    # Conectar ao Supabase
    supabase = conectar_supabase()
    
    # Solicitar dados do usuário
    print("📝 Informe os dados do usuário administrador:\n")
    
    username = input("Nome de usuário: ").strip()
    
    if not username:
        print("❌ Nome de usuário não pode ser vazio")
        sys.exit(1)
    
    if len(username) < 3:
        print("❌ Nome de usuário deve ter no mínimo 3 caracteres")
        sys.exit(1)
    
    # Solicitar senha com confirmação
    while True:
        senha = getpass("Senha: ")
        senha_confirmacao = getpass("Confirme a senha: ")
        
        if senha != senha_confirmacao:
            print("❌ As senhas não coincidem. Tente novamente.\n")
            continue
        
        valida, mensagem = validar_senha(senha)
        if not valida:
            print(f"❌ {mensagem}\n")
            continue
        
        break
    
    print()
    
    # Criar usuário
    if criar_usuario(supabase, username, senha):
        print("\n" + "=" * 70)
        print("✅ SUCESSO: Usuário administrador criado!")
        print(f"\n📋 Credenciais de acesso:")
        print(f"   Usuário: {username}")
        print(f"   Senha: (a que você definiu)")
        print("\n⚠️  IMPORTANTE:")
        print("   - Guarde essas credenciais em local seguro")
        print("   - Não compartilhe a senha com outras pessoas")
        print("   - Você pode criar mais usuários através do sistema")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("❌ FALHA: Não foi possível criar o usuário")
        print("   Verifique os erros acima e tente novamente")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
