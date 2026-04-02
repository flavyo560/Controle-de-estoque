# limpar_temporarios.py
"""
Remove arquivos temporários e de debug do projeto DEKIDS
Script seguro - remove apenas arquivos desnecessários
"""

import os
import shutil

print("🧹 LIMPEZA DE ARQUIVOS TEMPORÁRIOS - DEKIDS")
print("=" * 70)

# Lista de arquivos temporários para remover
arquivos_remover = [
    # Scripts de debug
    'add_debug_layout.py',
    'add_debug_sessao.py',
    'add_debug.py',
    'add_funcao_final.py',
    'add_funcao_sessao.txt',
    'add_more_debug.py',
    'add_try_except.py',
    
    # Scripts de correção já aplicados
    'fix_icons.py',
    'fix_icons2.py',
    'fix_login.py',
    'fix_logout.py',
    'fix_nav_rail_container.py',
    'fix_nav_rail_correct.py',
    'fix_nav_rail_expand.py',
    'fix_nav_rail_final.py',
    'fix_nav_rail_simple.py',
    'fix_nav_rail.py',
    'convert_menu_to_top.py',
    'create_app_unified.py',
    
    # Scripts de modificação já aplicados
    'change_to_desktop.py',
    'insert_funcao.py',
    'remove_bom.py',
    'remove_funcao.py',
    'simplify_pagination.py',
    'update_main.py',
    
    # Documentos de tarefas concluídas
    'TASK_29_SUMMARY.md',
    'TASK_30_SUMMARY.md',
    'TASK_35_3_ERROR_HANDLING_REVIEW.md',
    
    # Testes manuais/temporários
    'test_autenticacao_task30.py',
    'test_cancelar_venda_manual.py',
    'test_checkpoint_fase4.py',
    'test_checkpoint_fase7_completo.py',
    'test_datatable_fix.py',
    'test_flet.py',
    'test_navegacao_manual.py',
    'test_task30_simple.py',
    'test_tela_cancelamento_basico.py',
    'test_tela_clientes_basico.py',
    'test_tela_vendas_basico.py',
    'teste_simples.py',
    'teste_sistema_vendas_completo.py',
    
    # Arquivos não usados
    'validacao.py',
    'cleanup.py',
]

print("\n📋 Arquivos a serem removidos:")
print("-" * 70)

removidos = 0
nao_encontrados = 0
erros = 0
total_size = 0

for arquivo in arquivos_remover:
    if os.path.exists(arquivo):
        try:
            size = os.path.getsize(arquivo)
            os.remove(arquivo)
            print(f"  ✅ {arquivo:40s} ({size:,} bytes)")
            removidos += 1
            total_size += size
        except Exception as e:
            print(f"  ❌ ERRO ao remover {arquivo}: {e}")
            erros += 1
    else:
        nao_encontrados += 1

print("\n" + "=" * 70)
print("📊 RESUMO DA LIMPEZA")
print("=" * 70)
print(f"  ✅ Removidos: {removidos} arquivos")
print(f"  ⚠️  Não encontrados: {nao_encontrados} arquivos")
print(f"  ❌ Erros: {erros} arquivos")
print(f"  💾 Espaço liberado: {total_size:,} bytes ({total_size/1024:.1f} KB)")

# Limpar caches
print("\n" + "=" * 70)
print("🧹 LIMPANDO CACHES")
print("=" * 70)

caches = {
    '__pycache__': 'Cache Python',
    '.pytest_cache': 'Cache pytest',
    '.hypothesis': 'Cache Hypothesis',
}

for cache_dir, descricao in caches.items():
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print(f"  ✅ {cache_dir:20s} - {descricao}")
        except Exception as e:
            print(f"  ❌ Erro ao remover {cache_dir}: {e}")
    else:
        print(f"  ⚠️  {cache_dir:20s} - Não encontrado")

print("\n" + "=" * 70)
print("✅ LIMPEZA CONCLUÍDA!")
print("=" * 70)
print("\n📝 Arquivos essenciais mantidos:")
print("  • app.py (aplicação principal)")
print("  • main.py, login.py")
print("  • database.py, vendas.py, clientes.py, estoque.py")
print("  • tela_*.py (interfaces)")
print("  • relatorios.py, relatorios_estoque.py")
print("  • Documentação (.md)")
print("  • Configuração (.env, requirements.txt)")
print("\n🎯 Projeto limpo e organizado!")
