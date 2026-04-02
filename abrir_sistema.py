#!/usr/bin/env python3
"""
Script para abrir o sistema DEKIDS no navegador
"""
import webbrowser
import time

print("\n" + "="*70)
print("🧸 DEKIDS - Abrindo Sistema no Navegador")
print("="*70)
print("\n🌐 Abrindo http://localhost:8000 no navegador...")

# Abrir navegador
webbrowser.open("http://localhost:8000")

print("✅ Navegador aberto!")
print("\n⚠️  Se o navegador não abrir, acesse manualmente:")
print("   http://localhost:8000")
print("="*70 + "\n")

time.sleep(2)
