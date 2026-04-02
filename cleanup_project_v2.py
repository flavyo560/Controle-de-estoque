# cleanup_project_v2.py
"""
Análise completa de arquivos do projeto DEKIDS
Versão 2 - Análise corrigida
"""

import os

print("🔍 ANÁLISE COMPLETA DO PROJETO DEKIDS\n")
print("=" * 80)

# ============================================================================
# ARQUIVOS ESSENCIAIS - NÃO REMOVER
# ============================================================================
essenciais = {
    # === APLICAÇÃO PRINCIPAL ===
    'app.py': 'Arquivo principal unificado (login + sistema)',
    'main.py': 'Sistema principal (importado por app.py)',
    'login.py': 'Funções de autenticação',
    
    # === MÓDULOS CORE ===
    'database.py': 'Banco de dados Supabase',
    'vendas.py': 'Lógica de vendas e carrinho',
    'clientes.py': 'Gestão de clientes',
    'estoque.py': 'Gestão de estoque',
    'barcode.py': 'Geração de códigos de barras/QR',
    'relatorios.py': '⚠️ ESSENCIAL - Usado por tela_relatorios.py e tests',
    'relatorios_estoque.py': 'Relatórios específicos de estoque',
    'validacao_vendas.py': 'Validação de regras de negócio',
    'logging_config.py': 'Configuração de logs',
    
    # === TELAS (UI) ===
    'tela_vendas.py': 'Interface PDV',
    'tela_clientes.py': 'Interface de clientes',
    'tela_relatorios.py': 'Interface de relatórios',
    'tela_cancelamento.py': 'Interface de cancelamento',
    
    # === CONFIGURAÇÃO ===
    '.env': 'Variáveis de ambiente (credenciais)',
    '.env.example': 'Exemplo de configuração',
    'requirements.txt': 'Dependências Python',
    'pytest.ini': 'Configuração de testes',
    
    # === DOCUMENTAÇÃO ===
    'DOCUMENTACAO_TECNICA.md': 'Documentação técnica',
    'MANUAL_USUARIO_VENDAS.md': 'Manual do usuário',
    'GUIA_RAPIDO_VENDAS.md': 'Guia rápido',
    'FLUXOGRAMAS_VENDAS.md': 'Fluxogramas do sistema',
}

# ============================================================================
# ARQUIVOS TEMPORÁRIOS - PODEM SER REMOVIDOS
# ============================================================================
temporarios = {
    # === SCRIPTS DE DEBUG ===
    'add_debug_layout.py': 'Script de debug temporário',
    'add_debug_sessao.py': 'Script de debug temporário',
    'add_debug.py': 'Script de debug temporário',
    'add_funcao_final.py': 'Script de modificação temporário',
    'add_funcao_sessao.txt': 'Arquivo de texto temporário',
    'add_more_debug.py': 'Script de debug temporário',
    'add_try_except.py': 'Script de modificação temporário',
    
    # === SCRIPTS DE CORREÇÃO (JÁ APLICADOS) ===
    'fix_icons.py': 'Correção já aplicada',
    'fix_icons2.py': 'Correção já aplicada',
    'fix_login.py': 'Correção já aplicada',
    'fix_logout.py': 'Correção já aplicada',
    'fix_nav_rail_container.py': 'Correção já aplicada',
    'fix_nav_rail_correct.py': 'Correção já aplicada',
    'fix_nav_rail_expand.py': 'Correção já aplicada',
    'fix_nav_rail_final.py': 'Correção já aplicada',
    'fix_nav_rail_simple.py': 'Correção já aplicada',
    'fix_nav_rail.py': 'Correção já aplicada',
    'convert_menu_to_top.py': 'Conversão já aplicada',
    'create_app_unified.py': 'Criação já aplicada',
    
    # === SCRIPTS DE MODIFICAÇÃO (JÁ APLICADOS) ===
    'change_to_desktop.py': 'Modificação já aplicada',
    'insert_funcao.py': 'Modificação já aplicada',
    'remove_bom.py': 'Modificação já aplicada',
    'remove_funcao.py': 'Modificação já aplicada',
    'simplify_pagination.py': 'Modificação já aplicada',
    'update_main.py': 'Modificação já aplicada',
    
    # === DOCUMENTOS DE TAREFAS ===
    'TASK_29_SUMMARY.md': 'Resumo de tarefa concluída',
    'TASK_30_SUMMARY.md': 'Resumo de tarefa concluída',
    'TASK_35_3_ERROR_HANDLING_REVIEW.md': 'Revisão de tarefa concluída',
    
    # === TESTES MANUAIS/TEMPORÁRIOS ===
    'test_autenticacao_task30.py': 'Teste manual temporário',
    'test_cancelar_venda_manual.py': 'Teste manual temporário',
    'test_checkpoint_fase4.py': 'Teste de checkpoint temporário',
    'test_checkpoint_fase7_completo.py': 'Teste de checkpoint temporário',
    'test_datatable_fix.py': 'Teste de correção temporário',
    'test_flet.py': 'Teste temporário',
    'test_navegacao_manual.py': 'Teste manual temporário',
    'test_task30_simple.py': 'Teste temporário',
    'test_tela_cancelamento_basico.py': 'Teste básico temporário',
    'test_tela_clientes_basico.py': 'Teste básico temporário',
    'test_tela_vendas_basico.py': 'Teste básico temporário',
    'teste_simples.py': 'Teste temporário',
    'teste_sistema_vendas_completo.py': 'Teste temporário',
}

# ============================================================================
# ARQUIVOS OPCIONAIS - REVISAR
# ============================================================================
opcionais = {
    'cleanup.py': 'Script de limpeza genérico - pode remover',
    'criar_usuario_teste.py': 'Útil para criar usuários - MANTER',
    'validacao.py': '⚠️ NÃO USADO - pode remover',
    'setup.py': 'Configuração de instalação - manter se for distribuir',
}

# ============================================================================
# EXIBIR ANÁLISE
# ============================================================================

print("\n📦 ARQUIVOS ESSENCIAIS (NÃO REMOVER)")
print("=" * 80)
for arquivo, descricao in sorted(essenciais.items()):
    status = "✅" if os.path.exists(arquivo) else "❌ FALTANDO"
    print(f"  {status} {arquivo:30s} - {descricao}")

print("\n🗑️  ARQUIVOS TEMPORÁRIOS (PODEM SER REMOVIDOS)")
print("=" * 80)
total_size = 0
count = 0
for arquivo, descricao in sorted(temporarios.items()):
    if os.path.exists(arquivo):
        size = os.path.getsize(arquivo)
        total_size += size
        count += 1
        print(f"  ❌ {arquivo:35s} - {descricao}")

print(f"\n  💾 Total: {count} arquivos, {total_size:,} bytes ({total_size/1024:.1f} KB)")

print("\n⚠️  ARQUIVOS OPCIONAIS (REVISAR)")
print("=" * 80)
for arquivo, descricao in sorted(opcionais.items()):
    if os.path.exists(arquivo):
        print(f"  ⚠️  {arquivo:30s} - {descricao}")

print("\n📁 DIRETÓRIOS")
print("=" * 80)
dirs_info = {
    '.kiro/': ('✅ MANTER', 'Especificações e configurações'),
    'tests/': ('✅ MANTER', 'Testes unitários e de propriedade'),
    'comprovantes/': ('✅ MANTER', 'PDFs de vendas gerados'),
    'exports/': ('✅ MANTER', 'Backups e exportações CSV'),
    'logs/': ('✅ MANTER', 'Logs do sistema'),
    'migrations/': ('✅ MANTER', 'Migrações de banco de dados'),
    '.hypothesis/': ('🧹 LIMPAR', 'Cache de testes (pode limpar)'),
    '.pytest_cache/': ('🧹 LIMPAR', 'Cache de pytest (pode limpar)'),
    '__pycache__/': ('🧹 LIMPAR', 'Cache Python (pode limpar)'),
    'test_data/': ('⚠️  REVISAR', 'Dados de teste (verificar se necessário)'),
}

for dir_name, (status, descricao) in sorted(dirs_info.items()):
    exists = "📁" if os.path.exists(dir_name) else "❌"
    print(f"  {exists} {status} {dir_name:20s} - {descricao}")

print("\n" + "=" * 80)
print("🎯 RESUMO DA ANÁLISE")
print("=" * 80)
print(f"  ✅ Arquivos essenciais: {len(essenciais)}")
print(f"  ❌ Arquivos temporários: {count} ({total_size/1024:.1f} KB)")
print(f"  ⚠️  Arquivos opcionais: {len([f for f in opcionais if os.path.exists(f)])}")

print("\n" + "=" * 80)
print("🔧 AÇÕES RECOMENDADAS")
print("=" * 80)
print("  1. ✅ Remover arquivos temporários (scripts de correção já aplicados)")
print("  2. ✅ Remover testes manuais temporários")
print("  3. ✅ Remover documentos de tarefas concluídas")
print("  4. 🧹 Limpar caches (.hypothesis, .pytest_cache, __pycache__)")
print("  5. ⚠️  Revisar validacao.py (não está sendo usado)")
print("  6. ✅ MANTER relatorios.py (usado por tela_relatorios.py)")

print("\n❓ Deseja criar um script para remover os arquivos temporários? (s/n): ", end='')
