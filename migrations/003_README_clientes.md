# Migração 003: Tabela de Clientes

## Descrição

Esta migração cria a tabela `clientes` no banco de dados Supabase para o Sistema de Vendas DEKIDS.

## O que será criado

### Tabela: clientes

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| id | BIGSERIAL | PRIMARY KEY | Identificador único auto-incrementado |
| nome | VARCHAR(255) | NOT NULL | Nome completo do cliente |
| cpf | VARCHAR(11) | NOT NULL, UNIQUE | CPF do cliente (11 dígitos) |
| telefone | VARCHAR(20) | - | Telefone de contato |
| email | VARCHAR(255) | - | Email do cliente |
| endereco_rua | VARCHAR(255) | - | Logradouro |
| endereco_numero | VARCHAR(20) | - | Número do endereço |
| endereco_complemento | VARCHAR(100) | - | Complemento |
| endereco_bairro | VARCHAR(100) | - | Bairro |
| endereco_cidade | VARCHAR(100) | - | Cidade |
| endereco_estado | VARCHAR(2) | - | Estado (sigla UF) |
| endereco_cep | VARCHAR(8) | - | CEP (8 dígitos) |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Data/hora de criação |

### Índices

- `idx_clientes_cpf` - Para busca rápida por CPF (também garante unicidade)
- `idx_clientes_nome` - Para busca por nome
- `idx_clientes_telefone` - Para busca por telefone

## Como Executar

### Opção 1: Via Dashboard do Supabase (Recomendado)

1. Acesse o dashboard do Supabase: https://app.supabase.com
2. Selecione seu projeto
3. No menu lateral, clique em **SQL Editor**
4. Clique em **New Query**
5. Copie todo o conteúdo do arquivo `003_criar_tabela_clientes.sql`
6. Cole no editor SQL
7. Clique em **Run** (ou pressione Ctrl+Enter)
8. Verifique se a mensagem "Migração 003 executada com sucesso!" aparece

### Opção 2: Via CLI do Supabase

```bash
supabase db push --file migrations/003_criar_tabela_clientes.sql
```

## Verificação

Após executar a migração, verifique se a tabela foi criada corretamente:

```sql
-- Verificar se a tabela existe
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'clientes';

-- Verificar estrutura da tabela
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'clientes'
ORDER BY ordinal_position;

-- Verificar índices criados
SELECT indexname, indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'clientes';

-- Verificar constraint de unicidade do CPF
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'clientes'::regclass;
```

## Teste Rápido

Após a migração, você pode testar inserindo um cliente de exemplo:

```sql
-- Inserir cliente de teste
INSERT INTO clientes (nome, cpf, telefone, email, endereco_rua, endereco_numero, endereco_cidade, endereco_estado, endereco_cep)
VALUES ('João da Silva', '12345678901', '11987654321', 'joao@example.com', 'Rua Teste', '123', 'São Paulo', 'SP', '01234567');

-- Buscar cliente inserido
SELECT * FROM clientes WHERE cpf = '12345678901';

-- Testar constraint de CPF único (deve falhar)
INSERT INTO clientes (nome, cpf)
VALUES ('Maria Santos', '12345678901');
-- Erro esperado: duplicate key value violates unique constraint "clientes_cpf_key"

-- Limpar teste (opcional)
DELETE FROM clientes WHERE cpf = '12345678901';
```

## Rollback (Reverter)

Se precisar reverter esta migração:

```sql
-- ATENÇÃO: Isso irá deletar a tabela e todos os dados!
DROP TABLE IF EXISTS clientes CASCADE;
```

## Próximos Passos

Após executar esta migração com sucesso:

1. ✅ Tabela `clientes` criada
2. ⏭️ Próxima tarefa: 1.2 - Criar tabela 'vendas'
3. ⏭️ Implementar módulo `clientes.py` (Fase 2)

## Requisitos Atendidos

- ✅ Requisito 3.1: Armazenar dados completos do cliente
- ✅ Requisito 13.3: Criar tabela clientes no Supabase

## Notas Importantes

- O CPF é armazenado como VARCHAR(11) apenas com dígitos (sem formatação)
- O campo `cpf` tem constraint UNIQUE para evitar duplicados
- Todos os campos de endereço são opcionais (nullable)
- O campo `created_at` é preenchido automaticamente com a data/hora atual
- Os índices melhoram a performance de buscas por CPF, nome e telefone
