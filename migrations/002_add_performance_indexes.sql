-- Migration 002: Add performance indexes for better query performance
-- Task 30: Melhorar responsividade e performance

-- Índices para a tabela produtos (melhorar busca e ordenação)
CREATE INDEX IF NOT EXISTS idx_produtos_descricao ON produtos(descricao);
CREATE INDEX IF NOT EXISTS idx_produtos_marca ON produtos(marca);
CREATE INDEX IF NOT EXISTS idx_produtos_referencia ON produtos(referencia);
CREATE INDEX IF NOT EXISTS idx_produtos_genero ON produtos(genero);
CREATE INDEX IF NOT EXISTS idx_produtos_preco ON produtos(preco);
CREATE INDEX IF NOT EXISTS idx_produtos_quantidade ON produtos(quantidade);
CREATE INDEX IF NOT EXISTS idx_produtos_estoque_minimo ON produtos(estoque_minimo);

-- Índices compostos para queries comuns
CREATE INDEX IF NOT EXISTS idx_produtos_genero_marca ON produtos(genero, marca);
CREATE INDEX IF NOT EXISTS idx_produtos_quantidade_estoque_minimo ON produtos(quantidade, estoque_minimo);

-- Índices para a tabela movimentacoes (já existem alguns, adicionar mais)
-- Os índices idx_movimentacoes_produto e idx_movimentacoes_data já foram criados na migration 001

-- Índice composto para queries de histórico com filtro de data e produto
CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto_data ON movimentacoes(produto_id, created_at DESC);

-- Índice para tipo de movimentação (útil para relatórios)
CREATE INDEX IF NOT EXISTS idx_movimentacoes_tipo ON movimentacoes(tipo);

-- Índice composto para queries de relatórios por período e tipo
CREATE INDEX IF NOT EXISTS idx_movimentacoes_data_tipo ON movimentacoes(created_at DESC, tipo);

-- Comentários sobre os índices
COMMENT ON INDEX idx_produtos_descricao IS 'Melhora busca por descrição';
COMMENT ON INDEX idx_produtos_marca IS 'Melhora filtro por marca';
COMMENT ON INDEX idx_produtos_referencia IS 'Melhora busca por referência';
COMMENT ON INDEX idx_produtos_genero IS 'Melhora filtro por gênero';
COMMENT ON INDEX idx_produtos_preco IS 'Melhora ordenação por preço';
COMMENT ON INDEX idx_produtos_quantidade IS 'Melhora ordenação por quantidade';
COMMENT ON INDEX idx_produtos_estoque_minimo IS 'Melhora queries de estoque baixo';
COMMENT ON INDEX idx_produtos_genero_marca IS 'Melhora filtros combinados de gênero e marca';
COMMENT ON INDEX idx_produtos_quantidade_estoque_minimo IS 'Melhora queries de alerta de estoque baixo';
COMMENT ON INDEX idx_movimentacoes_produto_data IS 'Melhora histórico de movimentações por produto';
COMMENT ON INDEX idx_movimentacoes_tipo IS 'Melhora filtros por tipo de movimentação';
COMMENT ON INDEX idx_movimentacoes_data_tipo IS 'Melhora relatórios de movimentações por período e tipo';
