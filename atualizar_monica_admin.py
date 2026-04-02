"""
Script para atualizar o usuário Monica para role 'admin'
"""

import database as db

print("🔄 Atualizando usuário Monica para role 'admin'...")

# Listar usuários para encontrar o ID da Monica
usuarios = db.listar_usuarios()

monica_id = None
for usuario in usuarios:
    if usuario.get('username', '').lower() == 'monica':
        monica_id = usuario.get('id')
        print(f"✅ Usuário Monica encontrado - ID: {monica_id}")
        break

if not monica_id:
    print("❌ Usuário Monica não encontrado")
    print("\n📋 Usuários disponíveis:")
    for usuario in usuarios:
        print(f"  - ID: {usuario.get('id')}, Username: {usuario.get('username')}, Role: {usuario.get('role')}")
else:
    # Atualizar role para admin
    sucesso, mensagem = db.atualizar_role_usuario(monica_id, 'admin')
    
    if sucesso:
        print(f"✅ {mensagem}")
        print(f"\n🎉 Monica agora é ADMIN (acesso total)!")
    else:
        print(f"❌ {mensagem}")

print("\n" + "="*70)
