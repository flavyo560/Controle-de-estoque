-- Migração 006: Criar tabela 'pagamentos' para Sistema de Vendas
-- Sistema: DEKIDS Moda Infantil - Sistema de Vendas
-- Data: 2025-01-23
-- Versão: 1.0
-- Descrição: Cria tabela de pagamentos com todos os campos necessários, relacionamentos e índices
-- Requisitos: 4.9, 13.4

-- ============================================================================
-- PARTE 1: Criar Tabela 'pagamentos'
-- ============================================================================

CREATE TABLE IF NOT EXISTS pagamentos (
    id BIGSERIAL PRIMARY KEY,
    venda_id BIGINT NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
    forma_pagamento VARCHAR(20) NOT NULL,
    valor NUMERIC(10, 2) NOT NULL,
    numero_parcelas INTEGER,
    valor_recebido NUMERIC(10, 2),
    troco NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PARTE 2: Criar Índices
-- ============================================================================

-- Índice para consultar pagamentos de uma venda específica
CREATE INDEX IF NOT EXISTS idx_pagamentos_venda_id ON pagamentos(venda_id);

-- Índice para relatórios por forma de pagamento
CREATE INDEX IF NOT EXISTS idx_pagamentos_forma_pagamento ON pagamentos(forma_pagamento);

-- ============================================================================
-- PARTE 3: Adicionar Constraints de Validação
-- ============================================================================

-- Validar que forma_pagamento é um dos valores permitidos
ALTER TABLE pagamentos ADD CONSTRAINT chk_pagamentos_forma_pagamento 
    CHECK (forma_pagamento IN ('dinheiro', 'cartao_credito', 'cartao_debito', 'pix'));

-- Validar que valor é maior que zero
ALTER TABLE pagamentos ADD CONSTRAINT chk_pagamentos_valor 
    CHECK (valor > 0);

-- Validar que numero_parcelas está entre 1 e 12 (quando não é NULL)
ALTER TABLE pagamentos ADD CONSTRAINT chk_pagamentos_numero_parcelas 
    CHECK (numero_parcelas IS NULL OR (numero_parcelas >= 1 AND numero_parcelas <= 12));

-- Validar que valor_recebido é maior ou igual ao valor (quando não é NULL, para pagamentos em dinheiro)
ALTER TABLE pagamentos ADD CONSTRAINT chk_pagamentos_valor_recebido 
    CHECK (valor_recebido IS NULL OR valor_recebido >= valor);

-- Validar que troco não é negativo (quando não é NULL)
ALTER TABLE pagamentos ADD CONSTRAINT chk_pagamentos_troco 
    CHECK (troco IS NULL OR troco >= 0);

-- ============================================================================
-- PARTE 4: Comentários nas Colunas (Documentação)
-- ============================================================================

COMMENT ON TABLE pagamentos IS 'Tabela de pagamentos das vendas';
COMMENT ON COLUMN pagamentos.id IS 'Identificador único do pagamento';
COMMENT ON COLUMN pagamentos.venda_id IS 'ID da venda associada';
COMMENT ON COLUMN pagamentos.forma_pagamento IS 'Forma de pagamento: dinheiro, cartao_credito, cartao_debito, pix';
COMMENT ON COLUMN pagamentos.valor IS 'Valor do pagamento';
COMMENT ON COLUMN pagamentos.numero_parcelas IS 'Número de parcelas (apenas para cartão de crédito)';
COMMENT ON COLUMN pagamentos.valor_recebido IS 'Valor recebido em dinheiro (apenas para pagamento em dinheiro)';
COMMENT ON COLUMN pagamentos.troco IS 'Troco devolvido (apenas para pagamento em dinheiro)';
COMMENT ON COLUMN pagamentos.created_at IS 'Data e hora de criação do registro';

-- ============================================================================
-- PARTE 5: Mensagem de Sucesso
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migração 006 executada com sucesso!';
    RAISE NOTICE 'Tabela "pagamentos" criada com sucesso.';
    RAISE NOTICE 'Índices criados: idx_pagamentos_venda_id, idx_pagamentos_forma_pagamento';
    RAISE NOTICE 'Constraints criados: chk_pagamentos_forma_pagamento, chk_pagamentos_valor, chk_pagamentos_numero_parcelas, chk_pagamentos_valor_recebido, chk_pagamentos_troco';
    RAISE NOTICE 'Foreign key: venda_id -> vendas(id) ON DELETE CASCADE';
END $$;
