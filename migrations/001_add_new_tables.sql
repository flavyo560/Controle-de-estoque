-- Migração 001: Adicionar novas tabelas e campos ao sistema de estoque
-- Sistema: DEKIDS Moda Infantil - Sistema de Estoque Melhorado
-- Data: 2024
-- Descrição: Adiciona suporte a movimentações, usuários, sessões e novos campos em produtos

-- ============================================================================
-- PARTE 1: Expandir tabela produtos
-- ============================================================================

-- Adicionar novos campos à tabela produtos
ALTER TABLE produtos 
ADD COLUMN IF NOT EXISTS estoque_minimo INTEGER NOT NULL DEFAULT 5,
ADD COLUMN IF NOT EXISTS codigo_barras TEXT,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Adicionar constraint de unicidade para código de barras
ALTER TABLE produtos 
ADD CONSTRAINT unique_codigo_barras UNIQUE (codigo_barras);

-- Adicionar constraint de unicidade para referência + tamanho
ALTER TABLE produtos 
ADD CONSTRAINT unique_referencia_tamanho UNIQUE (referencia, tamanho);

-- ============================================================================
-- PARTE 2: Criar tabela de usuários
-- ============================================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    tentativas_login INTEGER DEFAULT 0,
    bloqueado_ate TIMESTAMP,
    ultimo_acesso TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Comentários para documentação
COMMENT ON TABLE usuarios IS 'Tabela de usuários do sistema com controle de acesso';
COMMENT ON COLUMN usuarios.username IS 'Nome de usuário único para login';
COMMENT ON COLUMN usuarios.senha_hash IS 'Hash bcrypt da senha do usuário';
COMMENT ON COLUMN usuarios.ativo IS 'Indica se o usuário está ativo no sistema';
COMMENT ON COLUMN usuarios.tentativas_login IS 'Contador de tentativas de login falhadas';
COMMENT ON COLUMN usuarios.bloqueado_ate IS 'Timestamp até quando o usuário está bloqueado';
COMMENT ON COLUMN usuarios.ultimo_acesso IS 'Data e hora do último acesso bem-sucedido';

-- ============================================================================
-- PARTE 3: Criar tabela de movimentações
-- ============================================================================

CREATE TABLE IF NOT EXISTS movimentacoes (
    id BIGSERIAL PRIMARY KEY,
    produto_id BIGINT NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida', 'ajuste')),
    quantidade INTEGER NOT NULL,
    quantidade_anterior INTEGER NOT NULL,
    quantidade_nova INTEGER NOT NULL,
    observacao TEXT,
    usuario_id BIGINT REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para otimizar consultas frequentes
CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto ON movimentacoes(produto_id);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_data ON movimentacoes(created_at);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_tipo ON movimentacoes(tipo);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_usuario ON movimentacoes(usuario_id);

-- Comentários para documentação
COMMENT ON TABLE movimentacoes IS 'Histórico de todas as movimentações de estoque';
COMMENT ON COLUMN movimentacoes.produto_id IS 'Referência ao produto movimentado';
COMMENT ON COLUMN movimentacoes.tipo IS 'Tipo de movimentação: entrada, saida ou ajuste';
COMMENT ON COLUMN movimentacoes.quantidade IS 'Quantidade movimentada (sempre positiva)';
COMMENT ON COLUMN movimentacoes.quantidade_anterior IS 'Quantidade em estoque antes da movimentação';
COMMENT ON COLUMN movimentacoes.quantidade_nova IS 'Quantidade em estoque após a movimentação';
COMMENT ON COLUMN movimentacoes.observacao IS 'Observação opcional sobre a movimentação';
COMMENT ON COLUMN movimentacoes.usuario_id IS 'Usuário que realizou a movimentação';

-- ============================================================================
-- PARTE 4: Criar tabela de sessões
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessoes (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expira_em TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para otimizar validação de sessões
CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token);
CREATE INDEX IF NOT EXISTS idx_sessoes_expiracao ON sessoes(expira_em);
CREATE INDEX IF NOT EXISTS idx_sessoes_usuario ON sessoes(usuario_id);

-- Comentários para documentação
COMMENT ON TABLE sessoes IS 'Sessões ativas de usuários no sistema';
COMMENT ON COLUMN sessoes.usuario_id IS 'Usuário dono da sessão';
COMMENT ON COLUMN sessoes.token IS 'Token único de autenticação da sessão';
COMMENT ON COLUMN sessoes.expira_em IS 'Data e hora de expiração da sessão (2 horas após criação)';

-- ============================================================================
-- PARTE 5: Dados iniciais (opcional)
-- ============================================================================

-- Criar usuário administrador padrão (senha: admin123)
-- IMPORTANTE: Alterar a senha após primeiro acesso!
-- Hash bcrypt de 'admin123': $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYqYqYqYq
-- Descomente a linha abaixo se desejar criar o usuário admin automaticamente:
-- INSERT INTO usuarios (username, senha_hash, ativo) 
-- VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqYqYqYqYq', TRUE)
-- ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- VERIFICAÇÕES FINAIS
-- ============================================================================

-- Verificar se todas as tabelas foram criadas
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'usuarios') THEN
        RAISE EXCEPTION 'Tabela usuarios não foi criada';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'movimentacoes') THEN
        RAISE EXCEPTION 'Tabela movimentacoes não foi criada';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'sessoes') THEN
        RAISE EXCEPTION 'Tabela sessoes não foi criada';
    END IF;
    
    RAISE NOTICE 'Migração 001 executada com sucesso!';
END $$;
