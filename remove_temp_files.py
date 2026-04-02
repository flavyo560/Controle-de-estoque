# remove_temp_files.py
"""
Remove arquivos temporários e de debug do projeto
"""

import os
import shutil

arquivos_remover = [
    'add_debug_layout.py',
    'add_debug_sessao.py',
    'add_debug.py',
    'add_funcao_final.py',
    'add_funcao_sessao.txt',
    'add_more_debug.py',
    'add_try_except.py',
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
    'change_to_desktop.py',
    'insert_funcao.py',
    'remove_bom.py',
    'remove_funcao.py',
    'simplify_pagination.py',
    'update_main.py',
    'TASK_29_SUMMARY.md',
    'TASK_30_SUMMARY.md',
    'TASK_35_3_ERROR_HANDLING_REVIEW.md',
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
]

print("🗑️  Removendo arquivos temporários...")
removidos = 0
erros = 0

for arquivo in arquivos_remover:
    if os.path.exists(arquivo):
        try:
            os.remove(arquivo)
            print(f"  ✅ Removido: {arquivo}")
            removidos += 1
        except Exception as e:
            print(f"  ❌ Erro ao remover {arquivo}: {e}")
            erros += 1
    else:
        print(f"  ⚠️  Não encontrado: {arquivo}")

print(f"\n✅ Removidos: {removidos} arquivos")
if erros > 0:
    print(f"❌ Erros: {erros}")

print("\n🧹 Limpando caches...")
caches = ['__pycache__', '.pytest_cache', '.hypothesis']
for cache in caches:
    if os.path.exists(cache):
        try:
            shutil.rmtree(cache)
            print(f"  ✅ Removido: {cache}/")
        except Exception as e:
            print(f"  ❌ Erro ao remover {cache}: {e}")

print("\n✅ Limpeza concluída!")
