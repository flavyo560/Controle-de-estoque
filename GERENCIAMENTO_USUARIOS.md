# 👥 Gerenciamento de Usuários - DEKIDS

## 📋 Níveis de Acesso

O sistema possui 3 níveis de acesso (roles):

### 1. **Admin** (Administrador/Master)
- ✅ Acesso total ao sistema
- ✅ Pode cadastrar, editar e excluir usuários
- ✅ Pode alterar roles de outros usuários
- ✅ Acesso a todos os relatórios e configurações
- ✅ Gerenciamento completo de estoque e vendas

**Exemplo**: Monica (usuário master atual)

### 2. **Manager** (Gerente)
- ✅ Acesso a relatórios e vendas
- ✅ Gerenciamento de estoque
- ✅ Visualização de dados financeiros
- ❌ Não pode cadastrar usuários
- ❌ Não pode alterar configurações do sistema

**Uso recomendado**: Gerentes de loja, supervisores

### 3. **User** (Usuário Comum)
- ✅ Acesso básico ao sistema
- ✅ Pode registrar vendas
- ✅ Pode consultar estoque
- ❌ Não pode acessar relatórios financeiros
- ❌ Não pode cadastrar usuários
- ❌ Acesso limitado a configurações

**Uso recomendado**: Vendedores, atendentes

---

## 🚀 Como Usar

### Opção 1: Script de Gerenciamento (Recomendado)

Execute o script de gerenciamento de usuários:

```bash
python gerenciar_usuarios.py
```

O script oferece um menu interativo com as seguintes opções:

1. **Listar todos os usuários** - Visualiza todos os usuários cadastrados
2. **Cadastrar novo usuário** - Cria um novo usuário com role específico
3. **Alterar role de usuário** - Muda o nível de acesso de um usuário
4. **Ativar/Desativar usuário** - Bloqueia ou desbloqueia acesso
5. **Excluir usuário** - Remove um usuário do sistema (soft delete)

### Opção 2: Via Python (Programático)

```python
import database as db

# Cadastrar novo usuário
sucesso, mensagem = db.criar_usuario(
    username="joao",
    senha="senha123",
    role="user"  # 'admin', 'manager' ou 'user'
)

# Listar usuários
usuarios = db.listar_usuarios()

# Alterar role
sucesso, mensagem = db.atualizar_role_usuario(
    usuario_id=3,
    novo_role="manager"
)

# Ativar/Desativar
sucesso, mensagem = db.ativar_desativar_usuario(
    usuario_id=3,
    ativo=False  # False para desativar
)
```

---

## 📝 Exemplos de Uso

### Cadastrar um Vendedor

```bash
python gerenciar_usuarios.py
```

1. Escolha opção `2` (Cadastrar novo usuário)
2. Digite o nome de usuário: `maria`
3. Digite a senha: `maria2024`
4. Escolha o role: `3` (user - Usuário comum)

### Promover Usuário a Gerente

```bash
python gerenciar_usuarios.py
```

1. Escolha opção `3` (Alterar role de usuário)
2. Veja a lista de usuários e anote o ID
3. Digite o ID do usuário
4. Escolha o novo role: `2` (manager)

### Desativar Usuário Temporariamente

```bash
python gerenciar_usuarios.py
```

1. Escolha opção `4` (Ativar/Desativar usuário)
2. Digite o ID do usuário
3. Digite `d` para desativar

---

## 🔒 Segurança

- ✅ Senhas são armazenadas com hash bcrypt
- ✅ Tentativas de login são limitadas (3 tentativas)
- ✅ Conta é bloqueada por 5 minutos após 3 tentativas falhas
- ✅ Sessões expiram automaticamente
- ✅ Soft delete: usuários excluídos não são removidos do banco

---

## ⚠️ Importante

1. **Sempre mantenha pelo menos 1 usuário admin ativo** para não perder acesso ao sistema
2. **Senhas devem ter no mínimo 4 caracteres** (recomendado: 8+ caracteres)
3. **Não compartilhe credenciais de admin** - crie usuários específicos para cada pessoa
4. **Revise periodicamente os usuários ativos** e desative contas não utilizadas

---

## 🆘 Problemas Comuns

### "Usuário já existe"
- O nome de usuário deve ser único
- Escolha outro nome de usuário

### "Erro ao conectar ao banco de dados"
- Verifique se o arquivo `.env` está configurado corretamente
- Verifique a conexão com o Supabase

### "Nenhum usuário encontrado"
- O banco de dados pode estar vazio
- Execute as migrações primeiro: `alembic upgrade head`

---

## 📞 Suporte

Para dúvidas ou problemas, entre em contato com o administrador do sistema.
