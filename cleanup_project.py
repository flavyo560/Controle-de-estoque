# cleanup_project.py
"""
Analisa e lista arquivos desnecessários para limpeza do projeto
"""

import os

print("🔍 Analisando arquivos do projeto...\n")

# Arquivos ESSENCIAIS (NÃO REMOVER)
essenciais = {
    # Aplicação principal
    'app.py',           # ✅ Arquivo principal unificado (login + sistema)
    'main.py',          # ✅ Sistema principal (importado por app.py)
    'login.py',         # ✅ Funções de autenticação (importado por app.py)
    
    # Módulos core
    'database.py',      # ✅ Banco de dados
    'vendas.py',        # ✅ Lógica de vendas
    'clientes.py',      # ✅ Gestão de clientes
    'estoque.py',       # ✅ Gestão de estoque
    'barcode.py',       # ✅ Geração de códigos de barras/QR
    
    # Telas
    'tela_vendas.py',   # ✅ Interface de vendas
    'tela_clientes.py', # ✅ Interface de clientes
    'tela_relatorios.py', # ✅ Interface de relatórios
    'tela_cancelamento.py', # ✅ Interface de cancelamento
    
    # Relatórios e validação
    'relatorios_estoque.py', # ✅ Relatórios de estoque
    'validacao_vendas.py',   # ✅ Validação de vendas
    'logging_config.py',     # ✅ Configuração de logs
    
    # Configuração
    '.env',             # ✅ Variáveis de ambiente
    '.env.example',     # ✅ Exemplo de configuração
    'requirements.txt', # ✅ Dependências Python
    'pytest.ini',       # ✅ Configuração de testes
    
    # Documentação
    'DOCUMENTACAO_TECNICA.md',
    'MANUAL_USUARIO_VENDAS.md',
    'GUIA_RAPIDO_VENDAS.md',
    'FLUXOGRAMAS_VENDAS.md',
}

# Arquivos TEMPORÁRIOS/DEBUG (REMOVER)
temporarios = [
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
    
    # Arquivos de resumo de tarefas
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
]

# Arquivos OPCIONAIS (manter se útil)
opcionais = {
    'cleanup.py': 'Script de limpeza genérico',
    'criar_usuario_teste.py': 'Útil para criar usuários de teste',
    'relatorios.py': 'Verificar se é usado ou duplicado',
    'validacao.py': 'Verificar se é usado ou duplicado',
    'setup.py': 'Configuração de instalação (manter se for distribuir)',
}

print("=" * 70)
print("📋 ARQUIVOS ESSENCIAIS (NÃO REMOVER)")
print("=" * 70)
for arquivo in sorted(essenciais):
    if os.path.exists(arquivo):
        print(f"  ✅ {arquivo}")

print("\n" + "=" * 70)
print("🗑️  ARQUIVOS TEMPORÁRIOS/DEBUG (PODEM SER REMOVIDOS)")
print("=" * 70)
total_size = 0
for arquivo in sorted(temporarios):
    if os.path.exists(arquivo):
        size = os.path.getsize(arquivo)
        total_size += size
        print(f"  ❌ {arquivo} ({size:,} bytes)")

print(f"\n  💾 Total a liberar: {total_size:,} bytes ({total_size/1024:.1f} KB)")

print("\n" + "=" * 70)
print("⚠️  ARQUIVOS OPCIONAIS (REVISAR)")
print("=" * 70)
for arquivo, descricao in sorted(opcionais.items()):
    if os.path.exists(arquivo):
        print(f"  ⚠️  {arquivo} - {descricao}")

print("\n" + "=" * 70)
print("📁 DIRETÓRIOS")
print("=" * 70)
print("  ✅ .kiro/          - Especificações e configurações (MANTER)")
print("  ✅ tests/          - Testes unitários (MANTER)")
print("  ✅ comprovantes/   - PDFs de vendas (MANTER)")
print("  ✅ exports/        - Backups e exportações (MANTER)")
print("  ✅ logs/           - Logs do sistema (MANTER)")
print("  ✅ migrations/     - Migrações de banco (MANTER)")
print("  ⚠️  .hypothesis/   - Cache de testes (pode limpar)")
print("  ⚠️  .pytest_cache/ - Cache de pytest (pode limpar)")
print("  ⚠️  __pycache__/   - Cache Python (pode limpar)")
print("  ⚠️  test_data/     - Dados de teste (revisar)")

print("\n" + "=" * 70)
print("🔧 AÇÕES RECOMENDADAS")
print("=" * 70)
print("  1. Remover arquivos temporários/debug")
print("  2. Limpar caches (.hypothesis, .pytest_cache, __pycache__)")
print("  3. Revisar arquivos opcionais")
print("  4. Manter backups antes de remover")

print("\n❓ Deseja criar um script para remover os arquivos temporários? (s/n)")
resposta = input().lower()

if resposta == 's':
    print("\n🔄 Criando script de remoção...")
    
    script_content = '''# remove_temp_files.py
"""
Remove arquivos temporários e de debug do projeto
"""

import os
import shutil

arquivos_remover = [
'''
    
    for arquivo in temporarios:
        script_content += f"    '{arquivo}',\n"
    
    script_content += ''']

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

print(f"\\n✅ Removidos: {removidos} arquivos")
if erros > 0:
    print(f"❌ Erros: {erros}")

print("\\n🧹 Limpando caches...")
caches = ['__pycache__', '.pytest_cache', '.hypothesis']
for cache in caches:
    if os.path.exists(cache):
        try:
            shutil.rmtree(cache)
            print(f"  ✅ Removido: {cache}/")
        except Exception as e:
            print(f"  ❌ Erro ao remover {cache}: {e}")

print("\\n✅ Limpeza concluída!")
'''
    
    with open('remove_temp_files.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script criado: remove_temp_files.py")
    print("\n🔄 Para executar a limpeza:")
    print("   python remove_temp_files.py")
else:
    print("\n✅ Análise concluída. Nenhuma ação tomada.")
