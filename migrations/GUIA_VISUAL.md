# 🎯 Guia Visual Rápido - Migração em 3 Passos

## Sistema de Estoque DEKIDS

---

## 📍 PASSO 1: Executar Migração (2 minutos)

### 🌐 Acesse o Supabase

```
https://app.supabase.com
```

### 📝 Abra o SQL Editor

```
Menu Lateral → SQL Editor → New Query
```

### 📋 Cole e Execute

```
1. Abra: migrations/001_add_new_tables.sql
2. Copie TUDO (Ctrl+A, Ctrl+C)
3. Cole no editor (Ctrl+V)
4. Clique em "Run" (ou Ctrl+Enter)
```

### ✅ Verifique o Sucesso

Você deve ver:
```
NOTICE: Migração 001 executada com sucesso!
```

---

## 📍 PASSO 2: Validar (1 minuto)

### 🔍 Verificar Tabelas

No Supabase, vá em **Table Editor** e confirme que existem:

```
✅ produtos (com novos campos)
✅ usuarios (nova)
✅ movimentacoes (nova)
✅ sessoes (nova)
```

### 🧪 Executar Teste Automatizado (Opcional)

```bash
python migrations/teste_rapido.py
```

Deve mostrar:
```
✅ SUCESSO: Todos os testes passaram!
```

---

## 📍 PASSO 3: Criar Usuário Admin (1 minuto)

### 👤 Executar Script

```bash
python migrations/criar_usuario_admin.py
```

### 📝 Informar Dados

```
Nome de usuário: admin
Senha: [sua senha segura]
Confirme a senha: [sua senha segura]
```

### ✅ Confirmar Criação

Deve mostrar:
```
✅ SUCESSO: Usuário administrador criado!
```

---

## 🎉 PRONTO!

Sua migração está completa. Agora você tem:

```
✅ Tabelas criadas
✅ Campos adicionados
✅ Índices otimizados
✅ Usuário admin criado
✅ Sistema pronto para novas funcionalidades
```

---

## 📊 Estrutura Criada

```
┌─────────────────────────────────────────────────────────┐
│                    BANCO DE DADOS                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📦 produtos (expandida)                                 │
│     ├─ estoque_minimo (novo)                            │
│     ├─ codigo_barras (novo)                             │
│     ├─ created_at (novo)                                │
│     └─ updated_at (novo)                                │
│                                                          │
│  👥 usuarios (nova)                                      │
│     ├─ username                                          │
│     ├─ senha_hash                                        │
│     ├─ tentativas_login                                  │
│     └─ bloqueado_ate                                     │
│                                                          │
│  📋 movimentacoes (nova)                                 │
│     ├─ produto_id → produtos                             │
│     ├─ tipo (entrada/saida/ajuste)                       │
│     ├─ quantidade                                        │
│     └─ usuario_id → usuarios                             │
│                                                          │
│  🔐 sessoes (nova)                                       │
│     ├─ usuario_id → usuarios                             │
│     ├─ token                                             │
│     └─ expira_em                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🆘 Problemas?

### ❌ Erro ao executar SQL

**Solução:** Verifique se você está usando o usuário admin do Supabase

### ❌ Tabela já existe

**Solução:** Não é problema! O script usa `IF NOT EXISTS`

### ❌ Script Python não funciona

**Solução:** 
```bash
pip install supabase python-dotenv bcrypt
```

### ❌ Variáveis de ambiente não encontradas

**Solução:** Crie arquivo `.env`:
```env
SUPABASE_URL=sua_url_aqui
SUPABASE_KEY=sua_chave_aqui
```

---

## 📚 Documentação Completa

Para mais detalhes, consulte:

| Arquivo | Conteúdo |
|---------|----------|
| `INSTRUCOES_MIGRACAO.md` | Guia completo passo a passo |
| `migrations/README.md` | Documentação técnica |
| `migrations/RESUMO_TECNICO.md` | Detalhes do schema |
| `ACAO_NECESSARIA_USUARIO.md` | Resumo de ações |

---

## ⏭️ Próximos Passos

Após completar a migração:

1. ✅ Testar login no sistema
2. ✅ Avisar que a migração foi concluída
3. ✅ Continuar com a implementação das funcionalidades

---

## 📞 Comandos Úteis

```bash
# Validar migração
python migrations/validar_migracao.py

# Testar migração
python migrations/teste_rapido.py

# Criar usuário admin
python migrations/criar_usuario_admin.py
```

---

## ✅ Checklist Final

Antes de continuar, confirme:

- [ ] Executei o SQL no Supabase
- [ ] Vi a mensagem de sucesso
- [ ] Verifiquei as 4 tabelas no Table Editor
- [ ] Criei o usuário administrador
- [ ] (Opcional) Executei os testes

---

**🚀 Tudo pronto? Avise para continuarmos!**
