"""Script de teste para verificar inicialização do app"""
import os
from dotenv import load_dotenv

load_dotenv()

print("1. Importando database...")
import database as db
print("✅ database importado")

print("\n2. Testando obter_sessao_ativa...")
sucesso, mensagem, sessao = db.obter_sessao_ativa()
print(f"✅ obter_sessao_ativa OK - Sucesso: {sucesso}, Mensagem: {mensagem}")

print("\n3. Importando main...")
from main import main as main_sistema
print("✅ main importado")

print("\n4. Importando flet...")
import flet as ft
print("✅ flet importado")

print("\n✅ Todas as importações OK!")
print("\nO problema pode estar no ft.app() tentando abrir o navegador.")
print("Tente acessar manualmente: http://localhost:8000")
