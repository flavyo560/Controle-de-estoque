# Migração 004: Tabela de Vendas

## Descrição

Esta migração cria a tabela `vendas` no banco de dados Supabase para o Sistema de Vendas DEKIDS. Esta é a tabela principal que armazena todas as transações de venda.

## O que será criado

### Tabela: vendas

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| id | BIGSERIAL | PRIMARY KEY | Identificador único auto-incrementado |
| data_hora | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Data e hora da venda |
| valor_total | NUMERIC(10, 2) | NOT NULL | Valor total antes dos descontos |
| desconto_percentual | NUMERIC(5, 2) | DEFAULT 0, CHECK (0-100) | Desconto percentual aplicado |
| desconto_valor | NUMERIC(10, 2) | DEFAULT 0, CHECK (>= 0) | Desconto em valor fixo |
| valor_final | NUMERIC(10, 2) | NOT NULL, CHECK (>= 0) | Valor final após descontos |
| cliente_id | BIGINT | FK -> clientes(id), NULL | ID do cliente (NULL para vendas avulsas) |
| usuario_id | BIGINT | FK -> usuarios(id), NOT NULL | ID do vendedor |
| status | VARCHAR(20) | DEFAULT 'finalizada', CHECK | Status: 'finalizada' ou 'cancelada' |
| data_cancelamento | TIMESTAMP WITH TIME ZONE | NULL | Data/hora do cancelamento |
| motivo_cancelamento | TEXT | NULL | Motivo do cancelamento |
| usuario_cancelamento_id | BIGINT | FK -> usuarios(id), NULL | ID do usuário que cancelou |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Data/hora de criação do registro |

### Índices

- `idx_vendas_data_hora` - Para consultas por período (relatórios)
- `idx_vendas_cliente_id` - Para histórico de compras do cliente
- `idx_vendas_usuario_id` - Para relatórios de desempenho do vendedor
- `idx_vendas_status` - Para filtrar vendas ativas/canceladas

### Foreign Keys

- `cliente_id` REFERENCES `clientes(id)` ON DELETE SET NULL
  - Permite vendas avulsas (NULL)
  - Se cliente for deletado, venda mantém registro mas perde referência
  
- `usuario_id` REFERENCES `usuarios(id)` ON DELETE RESTRICT
  - Obrigatório (NOT NULL)
  - Não permite deletar usuário que tem vendas registradas
  
- `usuario_cancelamento_id` REFERENCES `usuarios(id)` ON DELETE SET NULL
  - Opcional (NULL)
  - Se usuário for deletado, venda mantém registro mas perde referência

### Constraints de Validação

- `chk_vendas_status` - Status deve ser 'finalizada' ou 'cancelada'
- `chk_vendas_desconto_percentual` - Desconto percentual entre 0 e 100
- `chk_vendas_desconto_valor` - Desconto em valor não pode ser negativo
- `chk_vendas_valor_total` - Valor total não pode ser negativo
- `chk_vendas_valor_final` - Valor final não pode ser negativo

## Pré-requisitos

⚠️ **IMPORTANTE**: Esta migração depende das seguintes tabelas:

- ✅ `clientes` (Migração 003) - Deve estar criada
- ✅ `usuarios` (Sistema existente) - Deve estar criada

Verifique se essas tabelas existem antes de executar esta migração.

## Como Executar

### Opção 1: Via Dashboard do Supabase (Recomendado)

1. Acesse o dashboard do Supabase: https://app.supabase.com
2. Selecione seu projeto
3. No menu lateral, clique em **SQL Editor**
4. Clique em **New Query**
5. Copie todo o conteúdo do arquivo `004_criar_tabela_vendas.sql`
6. Cole no editor SQL
7. Clique em **Run** (ou pressione Ctrl+Enter)
8. Verifique se a mensagem "Migração 004 executada com sucesso!" aparece

### Opção 2: Via CLI do Supabase

```bash
supabase db push --file migrations/004_criar_tabela_vendas.sql
```

### Opção 3: Via Script Python

```bash
python migrations/executar_004_vendas.py
```

## Verificação

Após executar a migração, verifique se a tabela foi criada corretamente:

```sql
-- Verificar se a tabela existe
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'vendas';

-- Verificar estrutura da tabela
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'vendas'
ORDER BY ordinal_position;

-- Verificar índices criados
SELECT indexname, indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'vendas';

-- Verificar foreign keys
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'vendas';

-- Verificar constraints de validação
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'vendas'::regclass
  AND contype = 'c';
```

## Teste Rápido

Após a migração, você pode testar inserindo uma venda de exemplo:

```sql
-- Inserir venda de teste (assumindo que existe cliente_id=1 e usuario_id=1)
INSERT INTO vendas (
    valor_total, 
    desconto_percentual, 
    desconto_valor, 
    valor_final, 
    cliente_id, 
    usuario_id, 
    status
)
VALUES (
    100.00,  -- valor_total
    10.00,   -- desconto_percentual (10%)
    5.00,    -- desconto_valor (R$ 5,00)
    85.00,   -- valor_final (100 - 10% - 5 = 85)
    1,       -- cliente_id (ou NULL para venda avulsa)
    1,       -- usuario_id
    'finalizada'
);

-- Buscar venda inserida
SELECT * FROM vendas ORDER BY id DESC LIMIT 1;

-- Testar venda avulsa (sem cliente)
INSERT INTO vendas (valor_total, valor_final, usuario_id)
VALUES (50.00, 50.00, 1);

-- Testar constraint de status (deve falhar)
INSERT INTO vendas (valor_total, valor_final, usuario_id, status)
VALUES (50.00, 50.00, 1, 'pendente');
-- Erro esperado: new row violates check constraint "chk_vendas_status"

-- Testar constraint de desconto percentual (deve falhar)
INSERT INTO vendas (valor_total, desconto_percentual, valor_final, usuario_id)
VALUES (100.00, 150.00, 50.00, 1);
-- Erro esperado: new row violates check constraint "chk_vendas_desconto_percentual"

-- Limpar testes (opcional)
DELETE FROM vendas WHERE valor_total IN (100.00, 50.00);
```

## Teste de Cancelamento

```sql
-- Inserir venda para testar cancelamento
INSERT INTO vendas (valor_total, valor_final, usuario_id)
VALUES (100.00, 100.00, 1)
RETURNING id;

-- Cancelar a venda (substitua <venda_id> pelo ID retornado acima)
UPDATE vendas 
SET status = 'cancelada',
    data_cancelamento = NOW(),
    motivo_cancelamento = 'Teste de cancelamento',
    usuario_cancelamento_id = 1
WHERE id = <venda_id>;

-- Verificar cancelamento
SELECT * FROM vendas WHERE id = <venda_id>;

-- Limpar teste
DELETE FROM vendas WHERE id = <venda_id>;
```

## Rollback (Reverter)

Se precisar reverter esta migração:

```sql
-- ATENÇÃO: Isso irá deletar a tabela e todos os dados!
-- Também irá deletar em cascata as tabelas itens_venda e pagamentos quando forem criadas
DROP TABLE IF EXISTS vendas CASCADE;
```

## Próximos Passos

Após executar esta migração com sucesso:

1. ✅ Tabela `vendas` criada
2. ⏭️ Próxima tarefa: 1.3 - Criar tabela 'itens_venda'
3. ⏭️ Próxima tarefa: 1.4 - Criar tabela 'pagamentos'
4. ⏭️ Implementar módulo `vendas.py` (Fase 3)

## Requisitos Atendidos

- ✅ Requisito 5.3: Registrar venda com data, hora, valor total, desconto, cliente e vendedor
- ✅ Requisito 13.1: Criar tabela vendas no Supabase com todos os campos necessários

## Notas Importantes

- O campo `cliente_id` é **nullable** para permitir vendas avulsas (sem cliente cadastrado)
- O campo `usuario_id` é **obrigatório** para rastreabilidade (quem fez a venda)
- O campo `status` tem valor padrão 'finalizada' e só aceita 'finalizada' ou 'cancelada'
- Os campos de cancelamento (`data_cancelamento`, `motivo_cancelamento`, `usuario_cancelamento_id`) são opcionais
- O `valor_final` deve ser calculado pela aplicação: `valor_total - desconto_valor - (valor_total * desconto_percentual / 100)`
- A constraint `ON DELETE RESTRICT` em `usuario_id` impede deletar vendedores que têm vendas registradas
- A constraint `ON DELETE SET NULL` em `cliente_id` permite deletar clientes, mas mantém o histórico de vendas
- Todos os valores monetários usam `NUMERIC(10, 2)` para precisão decimal
- Os índices foram criados para otimizar as consultas mais comuns (relatórios por período, histórico de cliente, desempenho de vendedor)

## Integração com Sistema Existente

Esta tabela se integra com:

- **Tabela `clientes`** (Migração 003) - Para vincular vendas a clientes
- **Tabela `usuarios`** (Sistema existente) - Para rastreabilidade de vendedores
- **Tabela `itens_venda`** (Migração 005) - Para armazenar produtos vendidos
- **Tabela `pagamentos`** (Migração 006) - Para armazenar formas de pagamento
