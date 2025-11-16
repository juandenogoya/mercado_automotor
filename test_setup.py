"""
Script de prueba para verificar que la instalación funciona correctamente.
NO requiere base de datos, solo verifica las importaciones y clientes API.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("🧪 PRUEBA DE INSTALACIÓN - Mercado Automotor")
print("=" * 60)
print()

# Test 1: Imports básicos
print("1️⃣  Probando imports básicos...")
try:
    import pandas as pd
    import numpy as np
    import requests
    print("   ✅ Pandas, NumPy, Requests OK")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: FastAPI
print("\n2️⃣  Probando FastAPI...")
try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    print("   ✅ FastAPI OK")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 3: Streamlit
print("\n3️⃣  Probando Streamlit...")
try:
    import streamlit as st
    import plotly.express as px
    print("   ✅ Streamlit y Plotly OK")
except ImportError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 4: Backend modules
print("\n4️⃣  Probando módulos del backend...")
try:
    from backend.config.settings import settings
    print(f"   ✅ Settings cargado (Environment: {settings.environment})")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 5: Cliente BCRA (sin conexión real)
print("\n5️⃣  Probando cliente BCRA...")
try:
    from backend.api_clients.bcra_client import BCRAClient
    client = BCRAClient()
    print(f"   ✅ Cliente BCRA inicializado (Base URL: {client.base_url})")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 6: Modelos de BD (sin conectar)
print("\n6️⃣  Probando modelos de base de datos...")
try:
    from backend.models import (
        Patentamiento,
        Produccion,
        BCRAIndicador,
        IndicadorCalculado
    )
    print("   ✅ Modelos de base de datos importados correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 7: Prueba API BCRA (conexión real)
print("\n7️⃣  Probando conexión real a API BCRA...")
try:
    from backend.api_clients.bcra_client import BCRAClient

    client = BCRAClient()
    result = client.get_principales_variables()

    if result['status'] == 'success':
        num_vars = len(result['data'])
        print(f"   ✅ API BCRA respondió correctamente ({num_vars} variables obtenidas)")
        print(f"   📊 Ejemplos de variables:")
        for var in result['data'][:3]:
            print(f"      - {var.get('descripcion', 'N/A')}: {var.get('valor', 'N/A')}")
    else:
        print(f"   ⚠️  API BCRA respondió con status: {result['status']}")

except Exception as e:
    print(f"   ⚠️  No se pudo conectar a BCRA API: {e}")
    print("   (Esto es normal si no hay conexión a internet)")

# Resumen
print()
print("=" * 60)
print("✅ TODAS LAS PRUEBAS COMPLETADAS")
print("=" * 60)
print()
print("🎉 El proyecto está correctamente instalado y funcional!")
print()
print("📝 Próximos pasos:")
print("   1. Para iniciar el dashboard: python manage.py run-dashboard")
print("   2. Para iniciar la API: python manage.py run-api")
print("   3. Para sincronizar BCRA: python manage.py sync-bcra")
print("   4. Para ver estadísticas de BD: python manage.py stats")
print()
print("⚠️  NOTA: Las pruebas con base de datos requieren PostgreSQL instalado")
print("   Para instalar PostgreSQL: https://www.postgresql.org/download/")
print()
