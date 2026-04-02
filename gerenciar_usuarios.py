"""
Script para gerenciar usuários do sistema DEKIDS
Permite cadastrar, listar, ativar/desativar e alterar roles de usuários
"""

import database as db
from datetime import datetime


def exibir_menu():
    """Exibe o menu principal"""
    print("\n" + "="*70)
    print("🧸 DEKIDS - GERENCIAMENTO DE USUÁRIOS")
    print("="*70)
    print("\n1. Listar todos os usuários")
    print("2. Cadastrar novo usuário")
    print("3. Alterar role de usuário")
    print("4. Ativar/Desativar usuário")
    print("5. Excluir usuário")
    print("0. Sair")
    print("="*70)


def listar_usuarios():
    """Lista todos os usuários do sistema"""
    print("\n📋 LISTA DE USUÁRIOS")
    print("-"*70)
    
    usuarios = db.listar_usuarios()
    
    if not usuarios:
        print("❌ Nenhum usuário encontrado")
        return
    
    print(f"\n{'ID':<5} {'Username':<20} {'Role':<10} {'Status':<10} {'Último Acesso':<20}")
    print("-"*70)
    
    for usuario in usuarios:
        user_id = usuario.get('id', 'N/A')
        username = usuario.get('username', 'N/A')
        role = usuario.get('role', 'user')
        ativo = "Ativo" if usuario.get('ativo', False) else "Inativo"
        ultimo_acesso = usuario.get('ultimo_acesso', 'Nunca')
        
        if ultimo_acesso and ultimo_acesso != 'Nunca':
            try:
                dt = datetime.fromisoformat(ultimo_acesso.replace('Z', '+00:00'))
                ultimo_acesso = dt.strftime('%d/%m/%Y %H:%M')
            except:
                pass
        
        print(f"{user_id:<5} {username:<20} {role:<10} {ativo:<10} {ultimo_acesso:<20}")
    
    print("-"*70)
    print(f"Total: {len(usuarios)} usuários")


def cadastrar_usuario():
    """Cadastra um novo usuário"""
    print("\n➕ CADASTRAR NOVO USUÁRIO")
    print("-"*70)
    
    username = input("Nome de usuário: ").strip()
    if not username:
        print("❌ Nome de usuário não pode ser vazio")
        return
    
    senha = input("Senha: ").strip()
    if not senha:
        print("❌ Senha não pode ser vazia")
        return
    
    if len(senha) < 4:
        print("❌ Senha deve ter pelo menos 4 caracteres")
        return
    
    print("\nEscolha o role (função) do usuário:")
    print("1. admin   - Acesso total (pode cadastrar usuários)")
    print("2. manager - Gerente (acesso a relatórios e vendas)")
    print("3. user    - Usuário comum (acesso básico)")
    
    role_opcao = input("\nOpção (1-3): ").strip()
    
    role_map = {
        '1': 'admin',
        '2': 'manager',
        '3': 'user'
    }
    
    role = role_map.get(role_opcao, 'user')
    
    print(f"\n📝 Criando usuário '{username}' com role '{role}'...")
    
    sucesso, mensagem = db.criar_usuario(username, senha, role)
    
    if sucesso:
        print(f"✅ {mensagem}")
    else:
        print(f"❌ {mensagem}")


def alterar_role():
    """Altera o role de um usuário"""
    print("\n🔄 ALTERAR ROLE DE USUÁRIO")
    print("-"*70)
    
    listar_usuarios()
    
    try:
        usuario_id = int(input("\nID do usuário: ").strip())
    except ValueError:
        print("❌ ID inválido")
        return
    
    print("\nEscolha o novo role:")
    print("1. admin   - Acesso total")
    print("2. manager - Gerente")
    print("3. user    - Usuário comum")
    
    role_opcao = input("\nOpção (1-3): ").strip()
    
    role_map = {
        '1': 'admin',
        '2': 'manager',
        '3': 'user'
    }
    
    novo_role = role_map.get(role_opcao)
    
    if not novo_role:
        print("❌ Opção inválida")
        return
    
    sucesso, mensagem = db.atualizar_role_usuario(usuario_id, novo_role)
    
    if sucesso:
        print(f"✅ {mensagem}")
    else:
        print(f"❌ {mensagem}")


def ativar_desativar():
    """Ativa ou desativa um usuário"""
    print("\n🔓 ATIVAR/DESATIVAR USUÁRIO")
    print("-"*70)
    
    listar_usuarios()
    
    try:
        usuario_id = int(input("\nID do usuário: ").strip())
    except ValueError:
        print("❌ ID inválido")
        return
    
    acao = input("Ativar ou Desativar? (a/d): ").strip().lower()
    
    if acao not in ['a', 'd']:
        print("❌ Opção inválida")
        return
    
    ativo = (acao == 'a')
    
    sucesso, mensagem = db.ativar_desativar_usuario(usuario_id, ativo)
    
    if sucesso:
        print(f"✅ {mensagem}")
    else:
        print(f"❌ {mensagem}")


def excluir():
    """Exclui um usuário"""
    print("\n🗑️  EXCLUIR USUÁRIO")
    print("-"*70)
    
    listar_usuarios()
    
    try:
        usuario_id = int(input("\nID do usuário: ").strip())
    except ValueError:
        print("❌ ID inválido")
        return
    
    confirmacao = input(f"⚠️  Tem certeza que deseja excluir o usuário ID {usuario_id}? (s/n): ").strip().lower()
    
    if confirmacao != 's':
        print("❌ Operação cancelada")
        return
    
    sucesso, mensagem = db.excluir_usuario(usuario_id)
    
    if sucesso:
        print(f"✅ {mensagem}")
    else:
        print(f"❌ {mensagem}")


def main():
    """Função principal"""
    while True:
        exibir_menu()
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == '1':
            listar_usuarios()
        elif opcao == '2':
            cadastrar_usuario()
        elif opcao == '3':
            alterar_role()
        elif opcao == '4':
            ativar_desativar()
        elif opcao == '5':
            excluir()
        elif opcao == '0':
            print("\n👋 Até logo!")
            break
        else:
            print("\n❌ Opção inválida")
        
        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    main()
