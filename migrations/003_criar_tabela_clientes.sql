-- Migração 003: Criar tabela 'clientes' para Sistema de Vendas
-- Sistema: DEKIDS Moda Infantil - Sistema de Vendas
-- Data: 2025-01-23
-- Versão: 1.0
-- Descrição: Cria tabela de clientes com todos os campos necessários e índices
-- Requisitos: 3.1, 13.3

-- ============================================================================
-- PARTE 1: Criar Tabela 'clientes'
-- ============================================================================

CREATE TABLE IF NOT EXISTS clientes (
    id BIGSERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(11) NOT NULL UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(255),
    endereco_rua VARCHAR(255),
    endereco_numero VARCHAR(20),
    endereco_complemento VARCHAR(100),
    endereco_bairro VARCHAR(100),
    endereco_cidade VARCHAR(100),
    endereco_estado VARCHAR(2),
    endereco_cep VARCHAR(8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- PARTE 2: Criar Índices
-- ============================================================================

-- Índice para CPF (já é UNIQUE, mas explicitamente criado para performance)
CREATE INDEX IF NOT EXISTS idx_clientes_cpf ON clientes(cpf);

-- Índice para busca por nome (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);

-- Índice para busca por telefone
CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes(telefone);

-- ============================================================================
-- PARTE 3: Comentários nas Colunas (Documentação)
-- ============================================================================

COMMENT ON TABLE clientes IS 'Tabela de clientes do sistema de vendas';
COMMENT ON COLUMN clientes.id IS 'Identificador único do cliente';
COMMENT ON COLUMN clientes.nome IS 'Nome completo do cliente';
COMMENT ON COLUMN clientes.cpf IS 'CPF do cliente (11 dígitos, único)';
COMMENT ON COLUMN clientes.telefone IS 'Telefone de contato do cliente';
COMMENT ON COLUMN clientes.email IS 'Email do cliente';
COMMENT ON COLUMN clientes.endereco_rua IS 'Logradouro do endereço';
COMMENT ON COLUMN clientes.endereco_numero IS 'Número do endereço';
COMMENT ON COLUMN clientes.endereco_complemento IS 'Complemento do endereço';
COMMENT ON COLUMN clientes.endereco_bairro IS 'Bairro do endereço';
COMMENT ON COLUMN clientes.endereco_cidade IS 'Cidade do endereço';
COMMENT ON COLUMN clientes.endereco_estado IS 'Estado do endereço (sigla UF)';
COMMENT ON COLUMN clientes.endereco_cep IS 'CEP do endereço (8 dígitos)';
COMMENT ON COLUMN clientes.created_at IS 'Data e hora de criação do registro';

-- ============================================================================
-- PARTE 4: Mensagem de Sucesso
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migração 003 executada com sucesso!';
    RAISE NOTICE 'Tabela "clientes" criada com sucesso.';
    RAISE NOTICE 'Índices criados: idx_clientes_cpf, idx_clientes_nome, idx_clientes_telefone';
END $$;
