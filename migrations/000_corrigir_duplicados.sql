-- Script de Correção de Duplicados
-- Sistema: DEKIDS Moda Infantil - Sistema de Estoque
-- Objetivo: Identificar e corrigir produtos duplicados antes da migração 001
-- 
-- IMPORTANTE: Execute este script ANTES da migração 001_add_new_tables.sql
-- 
-- Este script identifica produtos com mesma referência e tamanho e oferece
-- duas estratégias de correção:
-- 1. Manter apenas o mais recente (maior ID)
-- 2. Consolidar quantidades e manter o mais recente

-- ============================================================================
-- PARTE 1: ANÁLISE - Identificar duplicados
-- ============================================================================

-- Visualizar todos os produtos duplicados
SELECT 
    referencia,
    tamanho,
    COUNT(*) as total_duplicados,
    STRING_AGG(id::TEXT, ', ' ORDER BY id) as ids_duplicados,
    STRING_AGG(quantidade::TEXT, ', ' ORDER BY id) as quantidades,
    STRING_AGG(descricao, ' | ' ORDER BY id) as descricoes
FROM produtos
GROUP BY referencia, tamanho
HAVING COUNT(*) > 1
ORDER BY referencia, tamanho;

-- Contar total de registros duplicados
SELECT 
    COUNT(*) as total_grupos_duplicados,
    SUM(total - 1) as registros_a_remover
FROM (
    SELECT COUNT(*) as total
    FROM produtos
    GROUP BY referencia, tamanho
    HAVING COUNT(*) > 1
) subquery;

-- ============================================================================
-- PARTE 2: ESTRATÉGIA 1 - Manter apenas o mais recente (SEM consolidar)
-- ============================================================================
-- Use esta estratégia se você quer simplesmente remover duplicados
-- mantendo apenas o registro com maior ID (mais recente)

-- ATENÇÃO: Descomente o bloco abaixo para executar a ESTRATÉGIA 1

/*
-- Criar tabela temporária com IDs a manter
CREATE TEMP TABLE ids_manter AS
SELECT DISTINCT ON (referencia, tamanho)
    id,
    referencia,
    tamanho,
    quantidade,
    descricao
FROM produtos
ORDER BY referencia, tamanho, id DESC;

-- Criar tabela temporária com IDs a remover
CREATE TEMP TABLE ids_remover AS
SELECT p.id, p.referencia, p.tamanho, p.quantidade, p.descricao
FROM produtos p
WHERE NOT EXISTS (
    SELECT 1 FROM ids_manter m WHERE m.id = p.id
);

-- Mostrar o que será removido
SELECT 
    'SERÁ REMOVIDO' as acao,
    id,
    referencia,
    tamanho,
    quantidade,
    descricao
FROM ids_remover
ORDER BY referencia, tamanho, id;

-- Mostrar o que será mantido
SELECT 
    'SERÁ MANTIDO' as acao,
    id,
    referencia,
    tamanho,
    quantidade,
    descricao
FROM ids_manter
ORDER BY referencia, tamanho;

-- EXECUTAR REMOÇÃO (descomente a linha abaixo após revisar)
-- DELETE FROM produtos WHERE id IN (SELECT id FROM ids_remover);

-- Limpar tabelas temporárias
-- DROP TABLE IF EXISTS ids_manter;
-- DROP TABLE IF EXISTS ids_remover;
*/

-- ============================================================================
-- PARTE 3: ESTRATÉGIA 2 - Consolidar quantidades (RECOMENDADO)
-- ============================================================================
-- Use esta estratégia se você quer somar as quantidades dos duplicados
-- antes de remover, mantendo o registro mais recente

-- ATENÇÃO: Descomente o bloco abaixo para executar a ESTRATÉGIA 2

/*
-- Criar tabela temporária com consolidação
CREATE TEMP TABLE consolidacao AS
SELECT 
    MAX(id) as id_manter,
    referencia,
    tamanho,
    SUM(quantidade) as quantidade_total,
    MAX(descricao) as descricao,
    MAX(genero) as genero,
    MAX(marca) as marca,
    MAX(preco) as preco
FROM produtos
GROUP BY referencia, tamanho
HAVING COUNT(*) > 1;

-- Mostrar consolidação planejada
SELECT 
    c.referencia,
    c.tamanho,
    c.id_manter,
    p.quantidade as quantidade_atual,
    c.quantidade_total as quantidade_consolidada,
    c.quantidade_total - p.quantidade as quantidade_adicional
FROM consolidacao c
JOIN produtos p ON p.id = c.id_manter
ORDER BY c.referencia, c.tamanho;

-- Atualizar quantidades nos registros que serão mantidos
-- UPDATE produtos p
-- SET quantidade = c.quantidade_total
-- FROM consolidacao c
-- WHERE p.id = c.id_manter;

-- Remover duplicados (mantendo apenas o registro atualizado)
-- DELETE FROM produtos p
-- WHERE EXISTS (
--     SELECT 1 FROM consolidacao c
--     WHERE p.referencia = c.referencia 
--     AND p.tamanho = c.tamanho
--     AND p.id != c.id_manter
-- );

-- Limpar tabela temporária
-- DROP TABLE IF EXISTS consolidacao;
*/

-- ============================================================================
-- PARTE 4: VERIFICAÇÃO FINAL
-- ============================================================================

-- Verificar se ainda existem duplicados
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN 'OK - Nenhum duplicado encontrado'
        ELSE 'ATENÇÃO - Ainda existem ' || COUNT(*) || ' grupos duplicados'
    END as status
FROM (
    SELECT referencia, tamanho
    FROM produtos
    GROUP BY referencia, tamanho
    HAVING COUNT(*) > 1
) subquery;

-- Mostrar estatísticas finais
SELECT 
    COUNT(*) as total_produtos,
    COUNT(DISTINCT referencia) as referencias_unicas,
    COUNT(DISTINCT (referencia, tamanho)) as combinacoes_unicas
FROM produtos;

-- ============================================================================
-- INSTRUÇÕES DE USO
-- ============================================================================

-- 1. Execute primeiro a PARTE 1 (ANÁLISE) para ver os duplicados
-- 2. Escolha uma estratégia:
--    - ESTRATÉGIA 1: Remove duplicados mantendo apenas o mais recente
--    - ESTRATÉGIA 2: Consolida quantidades antes de remover (RECOMENDADO)
-- 3. Descomente o bloco da estratégia escolhida
-- 4. Execute as queries de visualização primeiro (SELECT)
-- 5. Revise os dados que serão alterados
-- 6. Descomente as queries de modificação (UPDATE/DELETE)
-- 7. Execute a PARTE 4 (VERIFICAÇÃO) para confirmar
-- 8. Após confirmar que não há mais duplicados, execute a migração 001

