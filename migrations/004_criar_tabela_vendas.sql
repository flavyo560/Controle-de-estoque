-- Migração 004: Criar tabela 'vendas' para Sistema de Vendas
-- Sistema: DEKIDS Moda Infantil - Sistema de Vendas
-- Data: 2025-01-23
-- Versão: 1.0
-- Descrição: Cria tabela de vendas com todos os campos necessários, relacionamentos e índices
-- Requisitos: 5.3, 13.1

-- ============================================================================
-- PARTE 1: Criar Tabela 'vendas'
-- ============================================================================

CREATE TABLE IF NOT EXISTS vendas (
    id BIGSERIAL PRIMARY KEY,
    data_hora TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valor_total NUMERIC(10, 2) NOT NULL,
    desconto_percentual NUMERIC(5, 2) DEFAULT 0,
    desconto_valor NUMERIC(10, 2) DEFAULT 0,
    valor_final NUMERIC(10, 2) NOT NULL,
    cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'finalizada',
    data_cancelamento TIMESTAMP WITH TIME ZONE,
    motivo_cancelamento TEXT,
    usuario_cancelamento_id BIGINT REFERENCES usuarios(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PARTE 2: Criar Índices
-- ============================================================================

-- Índice para consultas por data/hora (relatórios por período)
CREATE INDEX IF NOT EXISTS idx_vendas_data_hora ON vendas(data_hora);

-- Índice para histórico de compras do cliente
CREATE INDEX IF NOT EXISTS idx_vendas_cliente_id ON vendas(cliente_id);

-- Índice para relatórios de desempenho do vendedor
CREATE INDEX IF NOT EXISTS idx_vendas_usuario_id ON vendas(usuario_id);

-- Índice para filtrar vendas ativas/canceladas
CREATE INDEX IF NOT EXISTS idx_vendas_status ON vendas(status);

-- ============================================================================
-- PARTE 3: Adicionar Constraints de Validação
-- ============================================================================

-- Validar que status é 'finalizada' ou 'cancelada'
ALTER TABLE vendas ADD CONSTRAINT chk_vendas_status 
    CHECK (status IN ('finalizada', 'cancelada'));

-- Validar que desconto_percentual está entre 0 e 100
ALTER TABLE vendas ADD CONSTRAINT chk_vendas_desconto_percentual 
    CHECK (desconto_percentual >= 0 AND desconto_percentual <= 100);

-- Validar que desconto_valor não é negativo
ALTER TABLE vendas ADD CONSTRAINT chk_vendas_desconto_valor 
    CHECK (desconto_valor >= 0);

-- Validar que valor_total não é negativo
ALTER TABLE vendas ADD CONSTRAINT chk_vendas_valor_total 
    CHECK (valor_total >= 0);

-- Validar que valor_final não é negativo
ALTER TABLE vendas ADD CONSTRAINT chk_vendas_valor_final 
    CHECK (valor_final >= 0);

-- ============================================================================
-- PARTE 4: Comentários nas Colunas (Documentação)
-- ============================================================================

COMMENT ON TABLE vendas IS 'Tabela de vendas do sistema';
COMMENT ON COLUMN vendas.id IS 'Identificador único da venda';
COMMENT ON COLUMN vendas.data_hora IS 'Data e hora da venda';
COMMENT ON COLUMN vendas.valor_total IS 'Valor total da venda antes dos descontos';
COMMENT ON COLUMN vendas.desconto_percentual IS 'Desconto percentual aplicado (0-100)';
COMMENT ON COLUMN vendas.desconto_valor IS 'Desconto em valor fixo aplicado';
COMMENT ON COLUMN vendas.valor_final IS 'Valor final da venda após descontos';
COMMENT ON COLUMN vendas.cliente_id IS 'ID do cliente (NULL para vendas avulsas)';
COMMENT ON COLUMN vendas.usuario_id IS 'ID do vendedor que realizou a venda';
COMMENT ON COLUMN vendas.status IS 'Status da venda: finalizada ou cancelada';
COMMENT ON COLUMN vendas.data_cancelamento IS 'Data e hora do cancelamento (se aplicável)';
COMMENT ON COLUMN vendas.motivo_cancelamento IS 'Motivo do cancelamento (se aplicável)';
COMMENT ON COLUMN vendas.usuario_cancelamento_id IS 'ID do usuário que cancelou a venda';
COMMENT ON COLUMN vendas.created_at IS 'Data e hora de criação do registro';

-- ============================================================================
-- PARTE 5: Mensagem de Sucesso
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migração 004 executada com sucesso!';
    RAISE NOTICE 'Tabela "vendas" criada com sucesso.';
    RAISE NOTICE 'Índices criados: idx_vendas_data_hora, idx_vendas_cliente_id, idx_vendas_usuario_id, idx_vendas_status';
    RAISE NOTICE 'Constraints criados: chk_vendas_status, chk_vendas_desconto_percentual, chk_vendas_desconto_valor, chk_vendas_valor_total, chk_vendas_valor_final';
    RAISE NOTICE 'Foreign keys: cliente_id -> clientes(id), usuario_id -> usuarios(id), usuario_cancelamento_id -> usuarios(id)';
END $$;
