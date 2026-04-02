# Migração 006: Tabela de Pagamentos

## Descrição

Esta migração cria a tabela `pagamentos` no banco de dados Supabase para o Sistema de Vendas DEKIDS. Esta tabela armazena as formas de pagamento utilizadas em cada venda, suportando múltiplas formas de pagamento por venda (pagamentos mistos).

## O que será criado

### Tabela: pagamentos

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| id | BIGSERIAL | PRIMARY KEY | Identificador único auto-incrementado |
| venda_id | BIGINT | FK -> vendas(id), NOT NULL | ID da venda associada |
| forma_pagamento | VARCHAR(20) | NOT NULL, CHECK | Forma de pagamento utilizada |
| valor | NUMERIC(10, 2) | NOT NULL, CHECK (> 0) | Valor do pagamento |
| numero_parcelas | INTEGER | NULL, CHECK (1-12) | Número de parcelas (apenas cartão crédito) |
| valor_recebido | NUMERIC(10, 2) | NULL, CHECK (>= valor) | Valor recebido (apenas dinheiro) |
| troco | NUMERIC(10, 2) | NULL, CHECK (>= 0) | Troco devolvido (apenas dinheiro) |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Data/hora de criação do registro |

### Formas de Pagamento Permitidas

- `dinheiro` - Pagamento em dinheiro (requer valor_recebido e troco)
- `cartao_credito` - Cartão de crédito (permite parcelamento de 1 a 12x)
- `cartao_debito` - Cartão de débito (à vista)
- `pix` - Pagamento via PIX (à vista)

### Índices

- `idx_pagamentos_venda_id` - Para consultar pagamentos de uma venda específica
- `idx_pagamentos_forma_pagamento` - Para relatórios por forma de pagamento

### Foreign Keys

- `venda_id` REFERENCES `vendas(id)` ON DELETE CASCADE
  - Obrigatório (NOT NULL)
  - Quando uma venda é deletada, seus pagamentos são deletados automaticamente
  - Garante integridade referencial

### Constraints de Validação

- `chk_pagamentos_forma_pagamento` - Forma de pagamento deve ser: 'dinheiro', 'cartao_credito', 'cartao_debito' ou 'pix'
- `chk_pagamentos_valor` - Valor deve ser maior que zero
- `chk_pagamentos_numero_parcelas` - Número de parcelas entre 1 e 12 (quando não NULL)
- `chk_pagamentos_valor_recebido` - Valor recebido deve ser >= valor (quando não NULL)
- `chk_pagamentos_troco` - Troco não pode ser negativo (quando não NULL)

## Pré-requisitos

⚠️ **IMPORTANTE**: Esta migração depende das seguintes tabelas:

- ✅ `vendas` (Migração 004) - Deve estar criada

Verifique se essa tabela existe antes de executar esta migração.

## Como Executar

### Opção 1: Via Dashboard do Supabase (Recomendado)

1. Acesse o dashboard do Supabase: https://app.supabase.com
2. Selecione seu projeto
3. No menu lateral, clique em **SQL Editor**
4. Clique em **New Query**
5. Copie todo o conteúdo do arquivo `006_criar_tabela_pagamentos.sql`
6. Cole no editor SQL
7. Clique em **Run** (ou pressione Ctrl+Enter)
8. Verifique se a mensagem "Migração 006 executada com sucesso!" aparece

### Opção 2: Via CLI do Supabase

```bash
supabase db push --file migrations/006_criar_tabela_pagamentos.sql
```

### Opção 3: Via Script Python

```bash
python migrations/executar_006_pagamentos.py
```

## Verificação

Após executar a migração, verifique se a tabela foi criada corretamente:

```sql
-- Verificar se a tabela existe
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'pagamentos';

-- Verificar estrutura da tabela
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'pagamentos'
ORDER BY ordinal_position;

-- Verificar índices criados
SELECT indexname, indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'pagamentos';

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
  AND tc.table_name = 'pagamentos';

-- Verificar constraints de validação
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'pagamentos'::regclass
  AND contype = 'c';
```

## Teste Rápido

Após a migração, você pode testar inserindo pagamentos de exemplo:

```sql
-- Primeiro, criar uma venda de teste (assumindo que existe usuario_id=1)
INSERT INTO vendas (valor_total, valor_final, usuario_id)
VALUES (100.00, 100.00, 1)
RETURNING id;

-- Substitua <venda_id> pelo ID retornado acima

-- Teste 1: Pagamento em dinheiro
INSERT INTO pagamentos (
    venda_id, 
    forma_pagamento, 
    valor, 
    valor_recebido, 
    troco
)
VALUES (
    <venda_id>,
    'dinheiro',
    100.00,
    150.00,
    50.00
);

-- Teste 2: Pagamento com cartão de crédito parcelado
INSERT INTO pagamentos (
    venda_id, 
    forma_pagamento, 
    valor, 
    numero_parcelas
)
VALUES (
    <venda_id>,
    'cartao_credito',
    100.00,
    3
);

-- Teste 3: Pagamento com cartão de débito
INSERT INTO pagamentos (
    venda_id, 
    forma_pagamento, 
    valor
)
VALUES (
    <venda_id>,
    'cartao_debito',
    100.00
);

-- Teste 4: Pagamento via PIX
INSERT INTO pagamentos (
    venda_id, 
    forma_pagamento, 
    valor
)
VALUES (
    <venda_id>,
    'pix',
    100.00
);

-- Buscar pagamentos inseridos
SELECT * FROM pagamentos WHERE venda_id = <venda_id>;

-- Testar constraint de forma_pagamento (deve falhar)
INSERT INTO pagamentos (venda_id, forma_pagamento, valor)
VALUES (<venda_id>, 'boleto', 100.00);
-- Erro esperado: new row violates check constraint "chk_pagamentos_forma_pagamento"

-- Testar constraint de valor (deve falhar)
INSERT INTO pagamentos (venda_id, forma_pagamento, valor)
VALUES (<venda_id>, 'dinheiro', 0);
-- Erro esperado: new row violates check constraint "chk_pagamentos_valor"

-- Testar constraint de numero_parcelas (deve falhar)
INSERT INTO pagamentos (venda_id, forma_pagamento, valor, numero_parcelas)
VALUES (<venda_id>, 'cartao_credito', 100.00, 15);
-- Erro esperado: new row violates check constraint "chk_pagamentos_numero_parcelas"

-- Testar constraint de valor_recebido (deve falhar)
INSERT INTO pagamentos (venda_id, forma_pagamento, valor, valor_recebido, troco)
VALUES (<venda_id>, 'dinheiro', 100.00, 50.00, 0);
-- Erro esperado: new row violates check constraint "chk_pagamentos_valor_recebido"

-- Limpar testes
DELETE FROM vendas WHERE id = <venda_id>;
-- Os pagamentos serão deletados automaticamente (CASCADE)
```

## Teste de Pagamento Misto

```sql
-- Criar venda de R$ 100,00
INSERT INTO vendas (valor_total, valor_final, usuario_id)
VALUES (100.00, 100.00, 1)
RETURNING id;

-- Substitua <venda_id> pelo ID retornado

-- Pagamento misto: R$ 50,00 em dinheiro + R$ 50,00 no cartão
INSERT INTO pagamentos (venda_id, forma_pagamento, valor, valor_recebido, troco)
VALUES (<venda_id>, 'dinheiro', 50.00, 50.00, 0);

INSERT INTO pagamentos (venda_id, forma_pagamento, valor)
VALUES (<venda_id>, 'cartao_debito', 50.00);

-- Verificar pagamentos da venda
SELECT 
    forma_pagamento,
    valor,
    numero_parcelas,
    valor_recebido,
    troco
FROM pagamentos 
WHERE venda_id = <venda_id>;

-- Verificar soma dos pagamentos
SELECT 
    venda_id,
    SUM(valor) as total_pago
FROM pagamentos 
WHERE venda_id = <venda_id>
GROUP BY venda_id;

-- Limpar teste
DELETE FROM vendas WHERE id = <venda_id>;
```

## Teste de CASCADE DELETE

```sql
-- Criar venda com pagamentos
INSERT INTO vendas (valor_total, valor_final, usuario_id)
VALUES (100.00, 100.00, 1)
RETURNING id;

-- Substitua <venda_id> pelo ID retornado

-- Adicionar pagamentos
INSERT INTO pagamentos (venda_id, forma_pagamento, valor)
VALUES 
    (<venda_id>, 'dinheiro', 50.00),
    (<venda_id>, 'pix', 50.00);

-- Verificar pagamentos criados
SELECT COUNT(*) FROM pagamentos WHERE venda_id = <venda_id>;
-- Deve retornar 2

-- Deletar a venda
DELETE FROM vendas WHERE id = <venda_id>;

-- Verificar que pagamentos foram deletados automaticamente
SELECT COUNT(*) FROM pagamentos WHERE venda_id = <venda_id>;
-- Deve retornar 0 (pagamentos foram deletados em cascata)
```

## Rollback (Reverter)

Se precisar reverter esta migração:

```sql
-- ATENÇÃO: Isso irá deletar a tabela e todos os dados!
DROP TABLE IF EXISTS pagamentos CASCADE;
```

## Próximos Passos

Após executar esta migração com sucesso:

1. ✅ Tabela `pagamentos` criada
2. ✅ Fase 1 (Fundação e Banco de Dados) COMPLETA
3. ⏭️ Próxima fase: Fase 2 - Criar módulos base Python
4. ⏭️ Implementar módulo `vendas.py` com validações de pagamento

## Requisitos Atendidos

- ✅ Requisito 4.9: Armazenar cada forma de pagamento com tipo, valor e número de parcelas
- ✅ Requisito 13.4: Criar tabela pagamentos no Supabase com todos os campos necessários

## Notas Importantes

### Regras de Negócio

- **Pagamento em Dinheiro**: Deve incluir `valor_recebido` e `troco`
  - `valor_recebido` >= `valor` (validado por constraint)
  - `troco` = `valor_recebido` - `valor` (calculado pela aplicação)

- **Cartão de Crédito**: Pode incluir `numero_parcelas` (1 a 12)
  - Se não informado, assume-se pagamento à vista (1 parcela)

- **Cartão de Débito e PIX**: Sempre à vista
  - `numero_parcelas` deve ser NULL
  - Não requer `valor_recebido` nem `troco`

### Pagamentos Mistos

- Uma venda pode ter múltiplos registros de pagamento
- A soma dos valores de todos os pagamentos deve ser igual ao `valor_final` da venda
- Esta validação é feita pela aplicação, não pelo banco de dados

### Integridade Referencial

- `ON DELETE CASCADE` garante que ao deletar uma venda, seus pagamentos são deletados automaticamente
- Isso mantém a consistência do banco de dados
- Importante para cancelamento de vendas

### Precisão Decimal

- Todos os valores monetários usam `NUMERIC(10, 2)` para precisão decimal
- Suporta valores até R$ 99.999.999,99
- Evita problemas de arredondamento com ponto flutuante

### Índices para Performance

- `idx_pagamentos_venda_id`: Otimiza consultas de pagamentos por venda
- `idx_pagamentos_forma_pagamento`: Otimiza relatórios por forma de pagamento

## Integração com Sistema Existente

Esta tabela se integra com:

- **Tabela `vendas`** (Migração 004) - Relacionamento obrigatório
- **Módulo `vendas.py`** - Para validação de pagamentos
- **Módulo `validacao_vendas.py`** - Para validação de formas de pagamento
- **Módulo `relatorios.py`** - Para relatórios por forma de pagamento

## Exemplos de Uso na Aplicação

### Finalizar Venda com Pagamento Único

```python
# Venda de R$ 100,00 em dinheiro
venda_data = {
    "valor_total": 100.00,
    "valor_final": 100.00,
    "usuario_id": 1
}

pagamento_data = {
    "forma_pagamento": "dinheiro",
    "valor": 100.00,
    "valor_recebido": 150.00,
    "troco": 50.00
}
```

### Finalizar Venda com Pagamento Misto

```python
# Venda de R$ 100,00: R$ 50 dinheiro + R$ 50 cartão
venda_data = {
    "valor_total": 100.00,
    "valor_final": 100.00,
    "usuario_id": 1
}

pagamentos_data = [
    {
        "forma_pagamento": "dinheiro",
        "valor": 50.00,
        "valor_recebido": 50.00,
        "troco": 0.00
    },
    {
        "forma_pagamento": "cartao_debito",
        "valor": 50.00
    }
]
```

### Finalizar Venda Parcelada

```python
# Venda de R$ 300,00 parcelada em 3x no cartão
venda_data = {
    "valor_total": 300.00,
    "valor_final": 300.00,
    "usuario_id": 1
}

pagamento_data = {
    "forma_pagamento": "cartao_credito",
    "valor": 300.00,
    "numero_parcelas": 3
}
```
