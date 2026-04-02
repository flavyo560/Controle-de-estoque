#!/usr/bin/env python3
"""
Script de Inicialização do Sistema - DEKIDS Moda Infantil
Sistema de Controle de Estoque Melhorado

Este script realiza a configuração inicial do sistema:
- Verifica conexão com Supabase
- Executa migrações do banco de dados
- Cria usuário administrador padrão
- Valida estrutura do banco de dados

Uso: python setup.py
"""

import os
import sys
import bcrypt
from supabase import create_client, Client
from dotenv import load_dotenv
from getpass import getpass

# Carregar variáveis de ambiente
load_dotenv()

# Cores para output no terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(texto):
    """Imprime cabeçalho formatado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{texto}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def print_success(texto):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.OKGREEN}✅ {texto}{Colors.ENDC}")

def print_error(texto):
    """Imprime mensagem de erro"""
    print(f"{Colors.FAIL}❌ {texto}{Colors.ENDC}")

def print_warning(texto):
    """Imprime mensagem de aviso"""
    print(f"{Colors.WARNING}⚠️  {texto}{Colors.ENDC}")

def print_info(texto):
    """Imprime mensagem informativa"""
    print(f"{Colors.OKCYAN}ℹ️  {texto}{Colors.ENDC}")


def verificar_variaveis_ambiente():
    """
    Verifica se as variáveis de ambiente necessárias estão configuradas.
    
    Returns:
        Tupla (sucesso, url, key)
    """
    print_info("Verificando variáveis de ambiente...")
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print_error("Variáveis SUPABASE_URL e/ou SUPABASE_KEY não encontradas")
        print_info("Configure-as no arquivo .env na raiz do projeto")
        print_info("Exemplo:")
        print("   SUPABASE_URL=https://seu-projeto.supabase.co")
        print("   SUPABASE_KEY=sua-chave-aqui")
        return False, "", ""
    
    print_success("Variáveis de ambiente encontradas")
    return True, url, key

def conectar_supabase(url, key):
    """
    Tenta conectar ao Supabase.
    
    Args:
        url: URL do projeto Supabase
        key: Chave de API do Supabase
        
    Returns:
        Tupla (sucesso, cliente)
    """
    print_info("Conectando ao Supabase...")
    
    try:
        supabase = create_client(url, key)
        
        # Testar conexão com uma query simples
        supabase.table("produtos").select("id").limit(1).execute()
        
        print_success("Conexão com Supabase estabelecida")
        return True, supabase
        
    except Exception as e:
        print_error(f"Falha ao conectar com Supabase: {e}")
        print_info("Verifique se:")
        print("   - A URL e a chave estão corretas")
        print("   - Você tem acesso à internet")
        print("   - O projeto Supabase está ativo")
        return False, None

def verificar_tabela_existe(supabase, nome_tabela):
    """
    Verifica se uma tabela existe no banco de dados.
    
    Args:
        supabase: Cliente Supabase
        nome_tabela: Nome da tabela a verificar
        
    Returns:
        True se a tabela existe, False caso contrário
    """
    try:
        supabase.table(nome_tabela).select("*").limit(1).execute()
        return True
    except Exception:
        return False


def executar_migracao(supabase):
    """
    Executa o script de migração do banco de dados.
    
    Args:
        supabase: Cliente Supabase
        
    Returns:
        True se sucesso, False caso contrário
    """
    print_info("Verificando estrutura do banco de dados...")
    
    # Verificar se as tabelas necessárias existem
    tabelas_necessarias = ["produtos", "usuarios", "movimentacoes", "sessoes"]
    tabelas_faltando = []
    
    for tabela in tabelas_necessarias:
        if not verificar_tabela_existe(supabase, tabela):
            tabelas_faltando.append(tabela)
    
    if not tabelas_faltando:
        print_success("Todas as tabelas necessárias já existem")
        return True
    
    print_warning(f"Tabelas faltando: {', '.join(tabelas_faltando)}")
    print_info("Executando migração do banco de dados...")
    
    # Ler script de migração
    migration_file = "migrations/001_add_new_tables.sql"
    
    if not os.path.exists(migration_file):
        print_error(f"Arquivo de migração não encontrado: {migration_file}")
        print_info("Execute a migração manualmente no Supabase SQL Editor")
        return False
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print_info("Script de migração carregado")
        print_warning("ATENÇÃO: A migração deve ser executada manualmente no Supabase")
        print_info("Passos:")
        print("   1. Acesse o Supabase Dashboard")
        print("   2. Vá em SQL Editor")
        print(f"   3. Execute o conteúdo do arquivo: {migration_file}")
        print()
        
        resposta = input("Você já executou a migração? (s/n): ").strip().lower()
        
        if resposta == 's':
            # Verificar novamente se as tabelas foram criadas
            tabelas_ainda_faltando = []
            for tabela in tabelas_faltando:
                if not verificar_tabela_existe(supabase, tabela):
                    tabelas_ainda_faltando.append(tabela)
            
            if tabelas_ainda_faltando:
                print_error(f"Tabelas ainda não encontradas: {', '.join(tabelas_ainda_faltando)}")
                print_info("Execute a migração no Supabase e tente novamente")
                return False
            
            print_success("Migração verificada com sucesso")
            return True
        else:
            print_warning("Execute a migração e rode este script novamente")
            return False
            
    except Exception as e:
        print_error(f"Erro ao processar migração: {e}")
        return False


def validar_estrutura_banco(supabase):
    """
    Valida se a estrutura do banco de dados está correta.
    
    Args:
        supabase: Cliente Supabase
        
    Returns:
        True se estrutura válida, False caso contrário
    """
    print_info("Validando estrutura do banco de dados...")
    
    validacoes = []
    
    # Verificar tabela produtos
    try:
        resultado = supabase.table("produtos").select("*").limit(1).execute()
        
        # Verificar se campos necessários existem
        if resultado.data:
            produto = resultado.data[0]
            campos_necessarios = ["id", "descricao", "referencia", "tamanho", "quantidade", "preco", "estoque_minimo"]
            campos_faltando = [campo for campo in campos_necessarios if campo not in produto]
            
            if campos_faltando:
                print_warning(f"Campos faltando na tabela produtos: {', '.join(campos_faltando)}")
                validacoes.append(False)
            else:
                print_success("Tabela 'produtos' validada")
                validacoes.append(True)
        else:
            print_success("Tabela 'produtos' existe (vazia)")
            validacoes.append(True)
            
    except Exception as e:
        print_error(f"Erro ao validar tabela produtos: {e}")
        validacoes.append(False)
    
    # Verificar tabela usuarios
    try:
        supabase.table("usuarios").select("id").limit(1).execute()
        print_success("Tabela 'usuarios' validada")
        validacoes.append(True)
    except Exception as e:
        print_error(f"Erro ao validar tabela usuarios: {e}")
        validacoes.append(False)
    
    # Verificar tabela movimentacoes
    try:
        supabase.table("movimentacoes").select("id").limit(1).execute()
        print_success("Tabela 'movimentacoes' validada")
        validacoes.append(True)
    except Exception as e:
        print_error(f"Erro ao validar tabela movimentacoes: {e}")
        validacoes.append(False)
    
    # Verificar tabela sessoes
    try:
        supabase.table("sessoes").select("id").limit(1).execute()
        print_success("Tabela 'sessoes' validada")
        validacoes.append(True)
    except Exception as e:
        print_error(f"Erro ao validar tabela sessoes: {e}")
        validacoes.append(False)
    
    return all(validacoes)

def hash_senha(senha):
    """Gera hash bcrypt da senha"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def validar_senha(senha):
    """Valida requisitos mínimos de senha"""
    if len(senha) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres"
    
    if senha.lower() in ["admin", "admin123", "123456", "password"]:
        return False, "Não use senhas óbvias como 'admin', 'admin123', '123456' ou 'password'"
    
    return True, ""


def criar_usuario_admin(supabase):
    """
    Cria usuário administrador padrão.
    
    Args:
        supabase: Cliente Supabase
        
    Returns:
        True se sucesso, False caso contrário
    """
    print_info("Verificando usuário administrador...")
    
    try:
        # Verificar se já existe algum usuário
        resultado = supabase.table("usuarios").select("id, username").execute()
        
        if resultado.data:
            print_success(f"Sistema já possui {len(resultado.data)} usuário(s) cadastrado(s)")
            print_info("Usuários existentes:")
            for usuario in resultado.data:
                print(f"   - {usuario.get('username', 'N/A')}")
            
            resposta = input("\nDeseja criar um novo usuário administrador? (s/n): ").strip().lower()
            
            if resposta != 's':
                return True
        
        print()
        print_info("Criando usuário administrador...")
        print()
        
        # Solicitar dados do usuário
        username = input("Nome de usuário: ").strip()
        
        if not username:
            print_error("Nome de usuário não pode ser vazio")
            return False
        
        if len(username) < 3:
            print_error("Nome de usuário deve ter no mínimo 3 caracteres")
            return False
        
        # Verificar se usuário já existe
        resultado = supabase.table("usuarios").select("id").eq("username", username).execute()
        
        if resultado.data:
            print_error(f"Usuário '{username}' já existe no sistema")
            return False
        
        # Solicitar senha com confirmação
        while True:
            senha = getpass("Senha: ")
            senha_confirmacao = getpass("Confirme a senha: ")
            
            if senha != senha_confirmacao:
                print_error("As senhas não coincidem. Tente novamente.\n")
                continue
            
            valida, mensagem = validar_senha(senha)
            if not valida:
                print_error(mensagem + "\n")
                continue
            
            break
        
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
            print()
            print_success(f"Usuário '{username}' criado com sucesso!")
            print()
            print_info("Credenciais de acesso:")
            print(f"   Usuário: {username}")
            print(f"   Senha: (a que você definiu)")
            print()
            print_warning("IMPORTANTE:")
            print("   - Guarde essas credenciais em local seguro")
            print("   - Não compartilhe a senha com outras pessoas")
            print("   - Você pode criar mais usuários através do sistema")
            return True
        else:
            print_error("Erro ao criar usuário")
            return False
            
    except Exception as e:
        print_error(f"Erro ao criar usuário administrador: {e}")
        return False


def main():
    """Função principal do script de inicialização"""
    print_header("🚀 INICIALIZAÇÃO DO SISTEMA - DEKIDS Moda Infantil")
    print_info("Sistema de Controle de Estoque Melhorado")
    print()
    
    # Passo 1: Verificar variáveis de ambiente
    print_header("Passo 1: Verificação de Configuração")
    sucesso, url, key = verificar_variaveis_ambiente()
    
    if not sucesso:
        print()
        print_error("FALHA: Configure as variáveis de ambiente e tente novamente")
        sys.exit(1)
    
    # Passo 2: Conectar ao Supabase
    print_header("Passo 2: Conexão com Banco de Dados")
    sucesso, supabase = conectar_supabase(url, key)
    
    if not sucesso:
        print()
        print_error("FALHA: Não foi possível conectar ao Supabase")
        sys.exit(1)
    
    # Passo 3: Executar migrações
    print_header("Passo 3: Migração do Banco de Dados")
    sucesso = executar_migracao(supabase)
    
    if not sucesso:
        print()
        print_error("FALHA: Execute a migração e rode este script novamente")
        sys.exit(1)
    
    # Passo 4: Validar estrutura
    print_header("Passo 4: Validação da Estrutura")
    sucesso = validar_estrutura_banco(supabase)
    
    if not sucesso:
        print()
        print_error("FALHA: Estrutura do banco de dados inválida")
        print_info("Execute a migração completa e tente novamente")
        sys.exit(1)
    
    # Passo 5: Criar usuário administrador
    print_header("Passo 5: Usuário Administrador")
    sucesso = criar_usuario_admin(supabase)
    
    if not sucesso:
        print()
        print_warning("AVISO: Não foi possível criar usuário administrador")
        print_info("Você pode criar manualmente usando: python migrations/criar_usuario_admin.py")
    
    # Finalização
    print_header("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print_success("O sistema está pronto para uso!")
    print()
    print_info("Próximos passos:")
    print("   1. Execute o sistema: python main.py")
    print("   2. Faça login com as credenciais criadas")
    print("   3. Comece a cadastrar produtos")
    print()
    print_info("Para criar mais usuários:")
    print("   - Use o script: python migrations/criar_usuario_admin.py")
    print("   - Ou crie através da interface do sistema (em desenvolvimento)")
    print()
    print_header("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("\nInicialização cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Erro inesperado: {e}")
        sys.exit(1)
