-- Migração 001 V2: Adicionar novas tabelas e campos ao sistema de estoque
-- Sistema: DEKIDS Moda Infantil - Sistema de Estoque Melhorado
-- Data: 2024
-- Versão: 2.0 - Com tratamento automático de duplicados
-- Descrição: Adiciona suporte a movimentações, usuários, sessões e novos campos em produtos
--            Esta versão trata automaticamente produtos duplicados antes de criar constraints

-- ============================================================================
-- PARTE 0: Tratamento Automático de Duplicados
-- ============================================================================

DO $$
DECLARE
    duplicados_count INTEGER;
BEGIN
    -- Verificar se existem duplicados
  