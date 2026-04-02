# Migrações do Banco de Dados - Sistema de Estoque DEKIDS

Este diretório contém os scripts de migração SQL para o banco de dados Supabase do sistema de estoque.

## Estrutura

- `001_add_new_tables.sql` - Adiciona tabelas de usuários, movimentações, sessões e novos campos em produtos

## Como Executar as Migrações

### Opção 1: Via Dashboard do Supabase (Recomendado)

1. Acesse o dashboard do seu projeto Supabase: https://app.supabase.com
2. No menu lateral, clique em **SQL Editor**
3. Clique em **New Query** para criar uma nova consulta
4. Copie todo o conteúdo do arquivo `001_add_new_tables.sql`
5. Cole no editor SQL
6. Clique em **Run** (ou pressione Ctrl+Enter)
7. Verifique se a mensagem "Migração 001 executada com sucesso!" aparece
8. Verifique se não há erros na execução

### Opção 2: Via CLI do Supabase

Se você tem o Supabase CLI instalado:

```bash
# Navegar até o diretório do projeto
cd /caminho/para/seu/projeto

# Executar a migração
supabase db push --file migrations/001_add_new_tables.sql
```

### Opção 3: Via Python (Programático)

Você pode executar a migração via código Python:

```python
from supabase import create_client
import os

# Configurar cliente Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Ler o arquivo SQL
with open('migrations/001_add_new_tables.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

# Executar (nota: pode precisar executar via API REST ou psycopg2)
# O cliente Python do Supabase não suporta SQL direto
# Recomenda-se usar o dashboard ou CLI
```

## Verificação Pós-Migração

Após executar a migração, verifique se as seguintes tabelas e campos foram criados:

### Tabela `produtos` (expandida)
- ✅ Campo `estoque_minimo` (INTEGER, padrão 5)
- ✅ Campo `codigo_barras` (TEXT, único)
- ✅ Campo `created_at` (TIMESTAMP)
- ✅ Campo `updated_at` (TIMESTAMP)
- ✅ Constraint `unique_referencia_tamanho`
- ✅ Constraint `unique_codigo_barras`

### Tabela `usuarios` (nova)
- ✅ Campos: id, username, senha_hash, ativo, tentativas_login, bloqueado_ate, ultimo_acesso, created_at
- ✅ Constraint de unicidade em `username`

### Tabela `movimentacoes` (nova)
- ✅ Campos: id, produto_id, tipo, quantidade, quantidade_anterior, quantidade_nova, observacao, usuario_id, created_at
- ✅ Índices: idx_movimentacoes_produto, idx_movimentacoes_data, idx_movimentacoes_tipo, idx_movimentacoes_usuario
- ✅ Foreign keys para produtos e usuarios
- ✅ Check constraint em `tipo` (entrada, saida, ajuste)

### Tabela `sessoes` (nova)
- ✅ Campos: id, usuario_id, token, expira_em, created_at
- ✅ Índices: idx_sessoes_token, idx_sessoes_expiracao, idx_sessoes_usuario
- ✅ Foreign key para usuarios
- ✅ Constraint de unicidade em `token`

## Verificação via SQL

Execute esta query no SQL Editor para verificar a estrutura:

```sql
-- Verificar tabelas criadas
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('produtos', 'usuarios', 'movimentacoes', 'sessoes');

-- Verificar colunas da tabela produtos
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'produtos'
ORDER BY ordinal_position;

-- Verificar índices criados
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename IN ('movimentacoes', 'sessoes');

-- Verificar constraints
SELECT conname, contype, conrelid::regclass AS table_name
FROM pg_constraint
WHERE conrelid IN ('produtos'::regclass, 'usuarios'::regclass, 'movimentacoes'::regclass, 'sessoes'::regclass);
```

## Rollback (Reverter Migração)

Se precisar reverter a migração, execute:

```sql
-- ATENÇÃO: Isso irá deletar todas as tabelas e dados!
-- Use apenas em ambiente de desenvolvimento/teste

DROP TABLE IF EXISTS sessoes CASCADE;
DROP TABLE IF EXISTS movimentacoes CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

ALTER TABLE produtos 
DROP COLUMN IF EXISTS estoque_minimo,
DROP COLUMN IF EXISTS codigo_barras,
DROP COLUMN IF EXISTS created_at,
DROP COLUMN IF EXISTS updated_at,
DROP CONSTRAINT IF EXISTS unique_referencia_tamanho,
DROP CONSTRAINT IF EXISTS unique_codigo_barras;
```

## Problemas Comuns

### Erro: "relation already exists"
- **Causa**: A tabela já foi criada anteriormente
- **Solução**: A migração usa `IF NOT EXISTS`, então pode executar novamente sem problemas

### Erro: "constraint already exists"
- **Causa**: A constraint já existe
- **Solução**: Você pode ignorar ou remover a constraint antes de executar

### Erro: "permission denied"
- **Causa**: Usuário sem permissões adequadas
- **Solução**: Use o usuário administrador do Supabase ou verifique as permissões

### Erro: "column already exists"
- **Causa**: A coluna já foi adicionada
- **Solução**: A migração usa `IF NOT EXISTS`, então pode executar novamente

## Próximos Passos

Após executar a migração com sucesso:

1. ✅ Criar usuário administrador inicial (se não criado automaticamente)
2. ✅ Testar conexão com as novas tabelas
3. ✅ Executar testes de integridade
4. ✅ Continuar com a implementação das funcionalidades (Fase 2 do plano)

## Suporte

Se encontrar problemas durante a migração:
1. Verifique os logs de erro no dashboard do Supabase
2. Consulte a documentação do Supabase: https://supabase.com/docs
3. Revise o arquivo de migração para entender o que está sendo executado
