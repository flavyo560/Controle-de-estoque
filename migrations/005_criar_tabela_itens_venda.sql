-- Migração 005: Criar tabela 'itens_venda' para Sistema de Vendas
-- Sistema: DEKIDS Moda Infantil - Sistema de Vendas
-- Data: 2025-01-23
-- Versão: 1.0
-- Descrição: Cria tabela de itens de venda com relacionamentos para vendas e produtos
-- Requisitos: 5.4, 13.2

-- ============================================================================
-- PARTE 1: Criar Tabela 'itens_venda'
-- ============================================================================

CREATE TABLE IF NOT EXISTS itens_venda (
    id BIGSERIAL PRIMARY KEY,
    venda_id BIGINT NOT NULL REFERENCES vendas(id) ON DELETE CASCADE,
    produto_id BIGINT NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
    quantidade INTEGER NOT NULL,
    preco_unitario NUMERIC(10, 2) NOT NULL,
    subtotal NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PARTE 2: Criar Índices
-- ============================================================================

-- Índice para consultar itens por venda (usado ao exibir detalhes da venda)
CREATE INDEX IF NOT EXISTS idx_itens_venda_venda_id ON itens_venda(venda_id);

-- Índice para relatórios de vendas por produto
CREATE INDEX IF NOT EXISTS idx_itens_venda_produto_id ON itens_venda(produto_id);

-- ============================================================================
-- PARTE 3: Adicionar Constraints de Validação
-- ============================================================================

-- Validar que quantidade é positiva
ALTER TABLE itens_venda ADD CONSTRAINT chk_itens_venda_quantidade 
    CHECK (quantidade > 0);

-- Validar que preco_unitario é positivo
ALTER TABLE itens_venda ADD CONSTRAINT chk_itens_venda_preco_unitario 
    CHECK (preco_unitario > 0);

-- Validar que subtotal é não-negativo
ALTER TABLE itens_venda ADD CONSTRAINT chk_itens_venda_subtotal 
    CHECK (subtotal >= 0);

-- ============================================================================
-- PARTE 4: Comentários nas Colunas (Documentação)
-- ============================================================================

COMMENT ON TABLE itens_venda IS 'Tabela de itens (produtos) vendidos em cada venda';
COMMENT ON COLUMN itens_venda.id IS 'Identificador único do item de venda';
COMMENT ON COLUMN itens_venda.venda_id IS 'ID da venda (FK para vendas.id)';
COMMENT ON COLUMN itens_venda.produto_id IS 'ID do produto vendido (FK para produtos.id)';
COMMENT ON COLUMN itens_venda.quantidade IS 'Quantidade vendida do produto';
COMMENT ON COLUMN itens_venda.preco_unitario IS 'Preço unitário do produto no momento da venda';
COMMENT ON COLUMN itens_venda.subtotal IS 'Subtotal do item (quantidade * preco_unitario)';
COMMENT ON COLUMN itens_venda.created_at IS 'Data e hora de criação do registro';

-- ============================================================================
-- PARTE 5: Mensagem de Sucesso
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migração 005 executada com sucesso!';
    RAISE NOTICE 'Tabela "itens_venda" criada com sucesso.';
    RAISE NOTICE 'Índices criados: idx_itens_venda_venda_id, idx_itens_venda_produto_id';
    RAISE NOTICE 'Constraints criados: chk_itens_venda_quantidade, chk_itens_venda_preco_unitario, chk_itens_venda_subtotal';
    RAISE NOTICE 'Foreign keys: venda_id -> vendas(id) ON DELETE CASCADE, produto_id -> produtos(id) ON DELETE RESTRICT';
END $$;
