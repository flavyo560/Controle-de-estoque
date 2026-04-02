-- Migração 007: Módulo Financeiro e Melhorias nas Vendas
-- Sistema: DEKIDS Moda Infantil - Sistema de Vendas
-- Data: 2026-04-02
-- Descrição: Criação de tabelas para controle financeiro e atualização de status de vendas

-- ============================================================================
-- PARTE 1: Atualizar Tabela 'vendas' para permitir vendas em aberto
-- ============================================================================

-- Remover constraint antiga para permitir novo status
ALTER TABLE vendas DROP CONSTRAINT IF EXISTS chk_vendas_status;

-- Adicionar nova constraint com status 'em_aberto'
ALTER TABLE vendas ADD CONSTRAINT chk_vendas_status 
    CHECK (status IN ('finalizada', 'cancelada', 'em_aberto'));

-- Atualizar comentário
COMMENT ON COLUMN vendas.status IS 'Status da venda: finalizada, cancelada ou em_aberto';

-- ============================================================================
-- PARTE 2: Criar Tabela 'financeiro_categorias'
-- ============================================================================

CREATE TABLE IF NOT EXISTS financeiro_categorias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('receita', 'despesa')),
    descricao TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserir categorias básicas
INSERT INTO financeiro_categorias (nome, tipo, descricao) VALUES 
('Venda de Produtos', 'receita', 'Receitas provenientes de vendas no PDV'),
('Serviços', 'receita', 'Receitas de prestação de serviços'),
('Outras Receitas', 'receita', 'Diversas receitas'),
('Fornecedores', 'despesa', 'Pagamento de mercadorias e insumos'),
('Aluguel', 'despesa', 'Custo de locação do espaço'),
('Salários', 'despesa', 'Pagamento de funcionários'),
('Impostos', 'despesa', 'Taxas e tributos'),
('Marketing', 'despesa', 'Publicidade e propaganda'),
('Manutenção', 'despesa', 'Reparos e manutenção geral'),
('Diversos', 'despesa', 'Outras despesas')
ON CONFLICT (nome) DO NOTHING;

-- ============================================================================
-- PARTE 3: Criar Tabela 'contas_pagar'
-- ============================================================================

CREATE TABLE IF NOT EXISTS contas_pagar (
    id BIGSERIAL PRIMARY KEY,
    descricao TEXT NOT NULL,
    valor NUMERIC(10, 2) NOT NULL CHECK (valor > 0),
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    categoria_id INTEGER REFERENCES financeiro_categorias(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'pago', 'atrasado', 'cancelado')),
    fornecedor_id BIGINT, -- Pode ser futuramente linkado a uma tabela de fornecedores
    observacao TEXT,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_contas_pagar_vencimento ON contas_pagar(data_vencimento);
CREATE INDEX idx_contas_pagar_status ON contas_pagar(status);

-- ============================================================================
-- PARTE 4: Criar Tabela 'contas_receber'
-- ============================================================================

CREATE TABLE IF NOT EXISTS contas_receber (
    id BIGSERIAL PRIMARY KEY,
    descricao TEXT NOT NULL,
    valor NUMERIC(10, 2) NOT NULL CHECK (valor > 0),
    data_vencimento DATE NOT NULL,
    data_recebimento DATE,
    venda_id BIGINT REFERENCES vendas(id) ON DELETE CASCADE,
    cliente_id BIGINT REFERENCES clientes(id) ON DELETE SET NULL,
    categoria_id INTEGER REFERENCES financeiro_categorias(id),
    status VARCHAR(20) NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente', 'recebido', 'atrasado', 'cancelado')),
    forma_recebimento VARCHAR(20),
    observacao TEXT,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_contas_receber_vencimento ON contas_receber(data_vencimento);
CREATE INDEX idx_contas_receber_status ON contas_receber(status);
CREATE INDEX idx_contas_receber_venda_id ON contas_receber(venda_id);

-- ============================================================================
-- PARTE 5: Criar Tabela 'fluxo_caixa'
-- ============================================================================

CREATE TABLE IF NOT EXISTS fluxo_caixa (
    id BIGSERIAL PRIMARY KEY,
    data_movimento TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    valor NUMERIC(10, 2) NOT NULL CHECK (valor > 0),
    descricao TEXT NOT NULL,
    categoria_id INTEGER REFERENCES financeiro_categorias(id),
    origem_id BIGINT, -- ID da conta_pagar ou conta_receber
    origem_tipo VARCHAR(20), -- 'conta_pagar', 'conta_receber', 'venda_direta'
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fluxo_caixa_data ON fluxo_caixa(data_movimento);
CREATE INDEX idx_fluxo_caixa_tipo ON fluxo_caixa(tipo);

-- ============================================================================
-- PARTE 6: Trigger para atualizar updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_contas_pagar_modtime
    BEFORE UPDATE ON contas_pagar
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_contas_receber_modtime
    BEFORE UPDATE ON contas_receber
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
