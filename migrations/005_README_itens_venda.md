# Migração 005: Tabela de Itens de Venda

## Descrição

Esta migração cria a tabela `itens_venda` no banco de dados Supabase para o Sistema de Vendas DEKIDS. Esta tabela armazena os produtos (itens) vendidos em cada transação de venda.

## O que será criado

### Tabela: itens_venda

| Campo | Tipo | Restrições | Descrição |
|-------|------|------------|-----------|
| id | BIGSERIAL | PRIMARY KEY | Identificador único auto-incrementado |
| venda_id | BIGINT | FK -> vendas(id), NOT NULL | ID da venda (relacionamento com vendas) |
| produto_id | BIGINT | FK -> produtos(id), NOT NULL | ID do produto vendido |
| quantidade | INTEGER | NOT NULL, CHECK (> 0) | Quantidade vendida do produto |
| preco_unitario | NUMERIC(10, 2) | NOT NULL, CHECK (> 0) | Preço unitário no momento da venda |
| subtotal | NUMERIC(10, 2) | NOT NULL, CHECK (>= 0) | Subtotal do item (quantidade × preço) |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Data/hora de criação do registro |

### Índices

- `idx_itens_venda_venda_id` - Para consultar todos os itens de uma venda específica
- `idx_itens_venda_produto_id` - Para relatórios de vendas por produto

### Foreign Keys

- `venda_id` REFERENCES `vendas(id)` ON DELETE CASCADE
  - Obrigatório (NOT NULL)
  - Quando uma venda é deletada, todos os seus itens são deletados automaticamente
  - Garante integridade referencial: não pode haver item sem venda
  
- `produto_id` REFERENCES `produtos(id)` ON DELETE RESTRICT
  - Obrigatório (NOT NULL)
  - Não permite deletar um produto que tem histórico de vendas
  - Preserva histórico: produtos vendidos não podem ser removidos do sistema

### Constraints de Validação

- `chk_itens_venda_quantidade` - Quantidade deve ser maior que zero
- `chk_itens_venda_preco_unitario` - Preço unitário deve ser maior que zero
- `chk_itens_venda_subtotal` - Subtotal não pode ser negativo

## Pré-requisitos

⚠️ **IMPORTANTE**: Esta migração depende das seguintes tabelas:

- ✅ `vendas` (Migração 004) - Deve estar criada
- ✅ `produtos` (Sistema de estoque existente) - Deve estar criada

Verifique se essas tabelas existem antes de executar esta migração.

## Como Executar

### Opção 1: Via Dashboard do Supabase (Recomendado)

1. Acesse o dashboard do Supabase: https://app.supabase.com
2. Selecione seu projeto
3. No menu lateral, clique em **SQL Editor**
4. Clique em **New Query**
5. Copie todo o conteúdo do arquivo `005_criar_tabela_itens_venda.sql`
6. Cole no editor SQL
7. Clique em **Run** (ou pressione Ctrl+Enter)
8. Verifique se a mensagem "Migração 005 executada com sucesso!" aparece

### Opção 2: Via CLI do Supabase

```bash
supabase db push --file migrations/005_criar_tabela_itens_venda.sql
```

### Opção 3: Via Script Python

```bash
python migrations/executar_005_itens_venda.py
```

## Verificação

Após executar a migração, verifique se a tabela foi criada corretamente:

```sql
-- Verificar se a tabela existe
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'itens_venda';

-- Verificar estrutura da tabela
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'itens_venda'
ORDER BY ordinal_position;

-- Verificar índices criados
SELECT indexname, indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'itens_venda';

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
  AND tc.table_name = 'itens_venda';

-- Verificar constraints de validação
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'itens_venda'::regclass
  AND contype = 'c';
```

## Teste Rápido

Após a migração, você pode testar inserindo itens de venda de exemplo:

```sql
-- Inserir item de venda de teste (assumindo que existe venda_id=1 e produto_id=1)
INSERT INTO itens_venda (
    venda_id,
    produto_id,
    quantidade,
    preco_unitario,
    subtotal
)
VALUES (
    1,      -- venda_id (deve existir na tabela vendas)
    1,      -- produto_id (deve existir na tabela produtos)
    3,      -- quantidade
    25.50,  -- preco_unitario
    76.50   -- subtotal (3 × 25.50)
);

-- Buscar itens de uma venda específica
SELECT * FROM itens_venda WHERE venda_id = 1;

-- Buscar todas as vendas de um produto específico
SELECT 
    iv.*,
    v.data_hora,
    v.valor_final
FROM itens_venda iv
JOIN vendas v ON iv.venda_id = v.id
WHERE iv.produto_id = 1
ORDER BY v.data_hora DESC;

-- Testar constraint de quantidade (deve falhar)
INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
VALUES (1, 1, 0, 25.50, 0);
-- Erro esperado: new row violates check constraint "chk_itens_venda_quantidade"

-- Testar constraint de preco_unitario (deve falhar)
INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
VALUES (1, 1, 1, 0, 0);
-- Erro esperado: new row violates check constraint "chk_itens_venda_preco_unitario"

-- Limpar teste (opcional)
DELETE FROM itens_venda WHERE venda_id = 1 AND produto_id = 1;
```

## Teste de Relacionamentos

```sql
-- Testar ON DELETE CASCADE (deletar venda deleta itens)
-- Inserir venda de teste
INSERT INTO vendas (valor_total, valor_final, usuario_id)
VALUES (100.00, 100.00, 1)
RETURNING id;

-- Inserir itens para a venda (substitua <venda_id> pelo ID retornado acima)
INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
VALUES 
    (<venda_id>, 1, 2, 25.00, 50.00),
    (<venda_id>, 2, 1, 50.00, 50.00);

-- Verificar itens inseridos
SELECT * FROM itens_venda WHERE venda_id = <venda_id>;

-- Deletar a venda (deve deletar os itens automaticamente)
DELETE FROM vendas WHERE id = <venda_id>;

-- Verificar que os itens foram deletados
SELECT * FROM itens_venda WHERE venda_id = <venda_id>;
-- Resultado esperado: nenhum registro encontrado

-- Testar ON DELETE RESTRICT (não pode deletar produto com vendas)
-- Tentar deletar um produto que tem itens vendidos
DELETE FROM produtos WHERE id = 1;
-- Erro esperado: update or delete on table "produtos" violates foreign key constraint
```

## Consultas Úteis

```sql
-- Calcular total de itens de uma venda
SELECT 
    venda_id,
    COUNT(*) as total_itens,
    SUM(quantidade) as quantidade_total,
    SUM(subtotal) as valor_total_itens
FROM itens_venda
WHERE venda_id = 1
GROUP BY venda_id;

-- Produtos mais vendidos (quantidade)
SELECT 
    p.descricao,
    p.referencia,
    SUM(iv.quantidade) as quantidade_vendida,
    SUM(iv.subtotal) as faturamento_gerado
FROM itens_venda iv
JOIN produtos p ON iv.produto_id = p.id
JOIN vendas v ON iv.venda_id = v.id
WHERE v.status = 'finalizada'
GROUP BY p.id, p.descricao, p.referencia
ORDER BY quantidade_vendida DESC
LIMIT 10;

-- Histórico de vendas de um produto específico
SELECT 
    v.id as venda_id,
    v.data_hora,
    iv.quantidade,
    iv.preco_unitario,
    iv.subtotal,
    v.status
FROM itens_venda iv
JOIN vendas v ON iv.venda_id = v.id
WHERE iv.produto_id = 1
ORDER BY v.data_hora DESC;

-- Verificar consistência de subtotais
SELECT 
    id,
    quantidade,
    preco_unitario,
    subtotal,
    (quantidade * preco_unitario) as subtotal_calculado,
    CASE 
        WHEN ABS(subtotal - (quantidade * preco_unitario)) > 0.01 
        THEN 'INCONSISTENTE' 
        ELSE 'OK' 
    END as status
FROM itens_venda
WHERE ABS(subtotal - (quantidade * preco_unitario)) > 0.01;
```

## Rollback (Reverter)

Se precisar reverter esta migração:

```sql
-- ATENÇÃO: Isso irá deletar a tabela e todos os dados!
DROP TABLE IF EXISTS itens_venda CASCADE;
```

## Próximos Passos

Após executar esta migração com sucesso:

1. ✅ Tabela `itens_venda` criada
2. ⏭️ Próxima tarefa: 1.4 - Criar tabela 'pagamentos'
3. ⏭️ Implementar funções de vendas em `database.py` (Fase 4)
4. ⏭️ Implementar módulo `vendas.py` com carrinho de compras (Fase 3)

## Requisitos Atendidos

- ✅ Requisito 5.4: Registrar cada item da venda com produto_id, quantidade, preço unitário e subtotal
- ✅ Requisito 13.2: Criar tabela itens_venda no Supabase com relacionamentos

## Notas Importantes

### Relacionamentos e Integridade

- **ON DELETE CASCADE em venda_id**: Quando uma venda é deletada, todos os seus itens são automaticamente removidos. Isso garante que não fiquem itens "órfãos" no banco de dados.

- **ON DELETE RESTRICT em produto_id**: Produtos que já foram vendidos não podem ser deletados do sistema. Isso preserva o histórico de vendas e evita perda de dados importantes para relatórios e auditoria.

### Armazenamento de Preço

- O campo `preco_unitario` armazena o preço do produto **no momento da venda**, não uma referência ao preço atual do produto.
- Isso é essencial porque o preço de um produto pode mudar ao longo do tempo, mas o histórico de vendas deve refletir o preço praticado em cada transação.
- Exemplo: Se um produto custava R$ 50,00 em janeiro e foi vendido nesse valor, mesmo que o preço atual seja R$ 60,00, o item_venda deve mostrar R$ 50,00.

### Cálculo de Subtotal

- O `subtotal` deve ser calculado pela aplicação: `quantidade × preco_unitario`
- A constraint garante que o subtotal não seja negativo, mas não valida se o cálculo está correto
- É responsabilidade da aplicação garantir que: `subtotal = quantidade × preco_unitario`

### Índices e Performance

- O índice em `venda_id` otimiza a consulta de todos os itens de uma venda (operação muito comum)
- O índice em `produto_id` otimiza relatórios de vendas por produto
- Esses índices são essenciais para performance em tabelas que crescem rapidamente

### Tipos de Dados

- `quantidade`: INTEGER (números inteiros positivos)
- `preco_unitario` e `subtotal`: NUMERIC(10, 2) para precisão decimal (até R$ 99.999.999,99)
- Usar NUMERIC em vez de FLOAT evita problemas de arredondamento em cálculos monetários

## Integração com Sistema Existente

Esta tabela se integra com:

- **Tabela `vendas`** (Migração 004) - Relacionamento pai-filho (uma venda tem muitos itens)
- **Tabela `produtos`** (Sistema de estoque) - Para identificar qual produto foi vendido
- **Função `registrar_movimentacao()`** (database.py) - Para baixa de estoque ao finalizar venda
- **Módulo `vendas.py`** (Fase 3) - Para gerenciar carrinho e finalização de vendas

## Exemplo de Uso na Aplicação

```python
# Ao finalizar uma venda, inserir itens:
itens = [
    {
        "venda_id": venda_id,
        "produto_id": 1,
        "quantidade": 2,
        "preco_unitario": 25.50,
        "subtotal": 51.00
    },
    {
        "venda_id": venda_id,
        "produto_id": 5,
        "quantidade": 1,
        "preco_unitario": 49.90,
        "subtotal": 49.90
    }
]

# Inserir em lote
supabase.table("itens_venda").insert(itens).execute()

# Buscar itens de uma venda
response = supabase.table("itens_venda")\
    .select("*, produtos(descricao, referencia)")\
    .eq("venda_id", venda_id)\
    .execute()
```
