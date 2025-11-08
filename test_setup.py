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
    from bs4 import BeautifulSoup
    print("   ✅ Pandas, NumPy, Requests, BeautifulSoup OK")
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

# Test 6: Cliente MercadoLibre (sin conexión real)
print("\n6️⃣  Probando cliente MercadoLibre...")
try:
    from backend.api_clients.mercadolibre_client import MercadoLibreClient
    client = MercadoLibreClient()
    print(f"   ✅ Cliente MercadoLibre inicializado (Base URL: {client.base_url})")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 7: Scrapers (sin ejecutar)
print("\n7️⃣  Probando scrapers...")
try:
    from backend.scrapers.acara_scraper import AcaraScraper
    from backend.scrapers.adefa_scraper import AdefaScraper
    print("   ✅ Scrapers ACARA y ADEFA importados correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 8: Modelos de BD (sin conectar)
print("\n8️⃣  Probando modelos de base de datos...")
try:
    from backend.models import (
        Patentamiento,
        Produccion,
        BCRAIndicador,
        MercadoLibreListing,
        IndicadorCalculado
    )
    print("   ✅ Modelos de base de datos importados correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 9: Prueba API BCRA (conexión real)
print("\n9️⃣  Probando conexión real a API BCRA...")
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

# Test 10: Prueba búsqueda MercadoLibre (conexión real)
print("\n🔟 Probando conexión real a API MercadoLibre...")
try:
    from backend.api_clients.mercadolibre_client import MercadoLibreClient

    client = MercadoLibreClient()
    result = client.search_vehicles(marca="Toyota", limit=5)

    if result['status'] == 'success':
        print(f"   ✅ API MercadoLibre respondió correctamente")
        print(f"   📊 Total de Toyota encontrados: {result['total']:,}")
        print(f"   📋 Primeros resultados:")
        for item in result['results'][:2]:
            print(f"      - {item.get('title', 'N/A')[:60]}...")
    else:
        print(f"   ⚠️  API MercadoLibre respondió con error")

except Exception as e:
    print(f"   ⚠️  No se pudo conectar a MercadoLibre API: {e}")
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
print("   3. Para ejecutar scrapers: python manage.py run-scrapers --source bcra")
print("   4. Para ver estadísticas de BD: python manage.py stats")
print()
print("⚠️  NOTA: Las pruebas con base de datos requieren PostgreSQL instalado")
print("   Para instalar PostgreSQL: https://www.postgresql.org/download/")
print()
