@echo off
echo ====================================================================
echo PREPARANDO SISTEMA DEKIDS PARA RENDER
echo ====================================================================
echo.

echo 1/6 - Atualizando requirements.txt...
(
echo # Dependencias do Sistema DEKIDS
echo # Versoes fixas para garantir compatibilidade no Render
echo.
echo # Framework UI - IMPORTANTE: Usar versao 0.25.0
echo flet==0.25.0
echo.
echo # Database
echo supabase^>=1.0.0
echo.
echo # Testing
echo hypothesis^>=6.0.0
echo pytest^>=7.0.0
echo pytest-cov^>=4.0.0
echo.
echo # Security
echo bcrypt^>=4.0.0
echo.
echo # Utilities
echo python-dotenv^>=1.0.0
echo qrcode^>=7.0.0
echo pillow^>=10.0.0
echo python-barcode^>=0.15.0
echo reportlab^>=4.0.0
) > requirements.txt
echo    OK - requirements.txt atualizado
echo.

echo 2/6 - Criando .gitignore...
(
echo # Arquivos de Ambiente
echo .env
echo .env.local
echo __pycache__/
echo *.pyc
echo logs/
echo comprovantes/
echo exports/
echo backup_*/
echo venv/
echo .kiro/
) > .gitignore
echo    OK - .gitignore criado
echo.

echo 3/6 - Criando Procfile...
echo web: python app.py > Procfile
echo    OK - Procfile criado
echo.

echo 4/6 - Criando runtime.txt...
echo python-3.11.0 > runtime.txt
echo    OK - runtime.txt criado
echo.

echo 5/6 - Criando README.md...
(
echo # DEKIDS - Sistema de Gestao
echo.
echo Sistema de gestao de estoque e vendas com Flet e Supabase.
echo.
echo ## Deploy no Render
echo.
echo 1. Crie Web Service no Render
echo 2. Conecte o repositorio GitHub
echo 3. Configure variaveis de ambiente:
echo    - SUPABASE_URL
echo    - SUPABASE_KEY
echo    - PORT=8000
echo 4. Deploy!
echo.
echo ## Credenciais
echo Usuario: Monica ^| Senha: monica123
) > README.md
echo    OK - README.md criado
echo.

echo 6/6 - Atualizando app.py...
powershell -Command "(Get-Content app.py) -replace '    ft.app\(target=main\)', '    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host=\"0.0.0.0\")' | Set-Content app.py"
echo    OK - app.py atualizado
echo.

echo ====================================================================
echo CONCLUIDO! Arquivos prontos para upload no GitHub
echo ====================================================================
echo.
echo Proximos passos:
echo 1. git add requirements.txt app.py .gitignore README.md Procfile runtime.txt
echo 2. git commit -m "Preparado para Render"
echo 3. git push origin main
echo.
pause
