# -*- coding: utf-8 -*-
"""
Script de prueba SIMPLE para Windows
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("PRUEBA DE INSTALACION - Mercado Automotor")
print("=" * 60)
print()

# Test 1: Imports básicos
print("1. Probando imports básicos...")
try:
    import pandas as pd
    import numpy as np
    import requests
    from bs4 import BeautifulSoup
    print("   OK: Pandas, NumPy, Requests, BeautifulSoup")
except ImportError as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 2: FastAPI
print("\n2. Probando FastAPI...")
try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    print("   OK: FastAPI")
except ImportError as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 3: Streamlit
print("\n3. Probando Streamlit...")
try:
    import streamlit as st
    import plotly.express as px
    print("   OK: Streamlit y Plotly")
except ImportError as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 4: Backend modules
print("\n4. Probando módulos del backend...")
try:
    from backend.config.settings import settings
    print(f"   OK: Settings (Environment: {settings.environment})")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 5: Cliente BCRA
print("\n5. Probando cliente BCRA...")
try:
    from backend.api_clients.bcra_client import BCRAClient
    client = BCRAClient()
    print(f"   OK: Cliente BCRA (Base URL: {client.base_url})")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 6: Cliente MercadoLibre
print("\n6. Probando cliente MercadoLibre...")
try:
    from backend.api_clients.mercadolibre_client import MercadoLibreClient
    client = MercadoLibreClient()
    print(f"   OK: Cliente MercadoLibre (Base URL: {client.base_url})")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 7: Scrapers
print("\n7. Probando scrapers...")
try:
    from backend.scrapers.acara_scraper import AcaraScraper
    from backend.scrapers.adefa_scraper import AdefaScraper
    print("   OK: Scrapers ACARA y ADEFA")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 8: Modelos de BD
print("\n8. Probando modelos de base de datos...")
try:
    from backend.models import (
        Patentamiento,
        Produccion,
        BCRAIndicador,
        MercadoLibreListing,
        IndicadorCalculado
    )
    print("   OK: Modelos de base de datos")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 9: API BCRA (conexión real)
print("\n9. Probando conexión real a API BCRA...")
try:
    from backend.api_clients.bcra_client import BCRAClient

    client = BCRAClient()
    result = client.get_principales_variables()

    if result['status'] == 'success':
        num_vars = len(result['data'])
        print(f"   OK: API BCRA respondio ({num_vars} variables obtenidas)")
        print(f"   Ejemplos de variables:")
        for var in result['data'][:3]:
            print(f"      - {var.get('descripcion', 'N/A')}: {var.get('valor', 'N/A')}")
    else:
        print(f"   AVISO: API BCRA respondio con status: {result['status']}")

except Exception as e:
    print(f"   AVISO: No se pudo conectar a BCRA API: {e}")

# Test 10: API MercadoLibre (conexión real)
print("\n10. Probando conexión real a API MercadoLibre...")
try:
    from backend.api_clients.mercadolibre_client import MercadoLibreClient

    client = MercadoLibreClient()
    result = client.search_vehicles(marca="Toyota", limit=5)

    if result['status'] == 'success':
        print(f"   OK: API MercadoLibre respondio correctamente")
        print(f"   Total de Toyota encontrados: {result['total']:,}")
    else:
        print(f"   AVISO: API MercadoLibre respondio con error")

except Exception as e:
    print(f"   AVISO: No se pudo conectar a MercadoLibre API: {e}")

# Resumen
print()
print("=" * 60)
print("TODAS LAS PRUEBAS COMPLETADAS")
print("=" * 60)
print()
print("El proyecto esta correctamente instalado y funcional!")
print()
print("Proximos pasos:")
print("   1. Crear base de datos en PostgreSQL: mercado_automotor")
print("   2. Inicializar tablas: python manage.py init-db")
print("   3. Ejecutar scrapers: python manage.py run-scrapers --source bcra")
print("   4. Iniciar dashboard: python manage.py run-dashboard")
print()
