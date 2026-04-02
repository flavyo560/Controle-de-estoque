#!/usr/bin/env python3
"""
Script de Preparação para Deployment no Render
Atualiza todos os arquivos necessários para deployment
"""

import os
import shutil
from datetime import datetime

print("="*70)
print("🚀 PREPARANDO SISTEMA DEKIDS PARA RENDER")
print("="*70)
print()

# 1. ATUALIZAR REQUIREMENTS.TXT
print("📝 1/6 - Atualizando requirements.txt...")
requirements_content = """# Dependências do Sistema DEKIDS
# Versões fixas para garantir compatibilidade no Render

# Framework UI - IMPORTANTE: Usar versão 0.25.0
flet==0.25.0

# Database
supabase>=1.0.0

# Testing
hypothesis>=6.0.0
pytest>=7.0.0
pytest-cov>=4.0.0

# Security
bcrypt>=4.0.0

# Utilities
python-dotenv>=1.0.0
qrcode>=7.0.0
pillow>=10.0.0
python-barcode>=0.15.0
reportlab>=4.0.0
"""

with open('requirements.txt', 'w', encoding='utf-8') as f:
    f.write(requirements_content)
print("   ✅ requirements.txt atualizado com Flet 0.25.0")

# 2. ATUALIZAR APP.PY PARA MODO WEB
print("\n🌐 2/6 - Atualizando app.py para modo web...")
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Substituir a linha do ft.app
old_line = '    ft.app(target=main)'
new_line = '    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")'

if old_line in app_content:
    app_content = app_content.replace(old_line, new_line)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("   ✅ app.py configurado para modo web (Render)")
else:
    print("   ⚠️  Linha não encontrada - verifique manualmente")

# 3. CRIAR .GITIGNORE
print("\n🔒 3/6 - Criando .gitignore...")
gitignore_content = """# Arquivos de Ambiente (NUNCA COMMITAR!)
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/
env/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Database
*.db
*.sqlite
*.sqlite3

# Backups e Exports
backup_*/
exports/
comprovantes/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Temporary files
*.tmp
*.temp
temp/
tmp/

# OS
Thumbs.db
.DS_Store

# Kiro (IDE local)
.kiro/

# Scripts temporários
cleanup_*.py
limpar_*.py
remove_*.py
prepare_*.py
"""

with open('.gitignore', 'w', encoding='utf-8') as f:
    f.write(gitignore_content)
print("   ✅ .gitignore criado")

# 4. CRIAR README.MD
print("\n📖 4/6 - Criando README.md...")
readme_content = """# 🧸 DEKIDS - Sistema de Gestão

Sistema completo de gestão de estoque e vendas desenvolvido com Flet e Supabase.

## 🚀 Deploy no Render

### Pré-requisitos
- Conta no [Render.com](https://render.com)
- Conta no [Supabase](https://supabase.com)
- Repositório no GitHub

### Configuração Rápida

#### 1. Configurar Supabase
1. Acesse [supabase.com](https://supabase.com)
2. Crie/use um projeto existente
3. Anote:
   - `SUPABASE_URL`: URL do projeto
   - `SUPABASE_KEY`: Chave anon/public

#### 2. Deploy no Render
1. Acesse [dashboard.render.com](https://dashboard.render.com)
2. **New +** → **Web Service**
3. Conecte este repositório GitHub
4. Configure:
   - **Name**: `dekids-sistema`
   - **Region**: Escolha a mais próxima
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

#### 3. Variáveis de Ambiente
No Render, adicione em **Environment**:

