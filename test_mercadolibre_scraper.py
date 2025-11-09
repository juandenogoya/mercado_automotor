"""
Test del scraper de MercadoLibre.

Este script prueba el web scraping y registra detalladamente cualquier bloqueo.

Ejecución:
python test_mercadolibre_scraper.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.scrapers.mercadolibre_scraper import (
    MercadoLibreScraper,
    BlockedByMercadoLibreException
)
from backend.config.logger import setup_logger

# Configurar logging
setup_logger()

print("=" * 80)
print("🧪 TEST - WEB SCRAPING MERCADOLIBRE")
print("=" * 80)
print("\nEste test verifica si podemos scrapear MercadoLibre")
print("y detecta cualquier intento de bloqueo.\n")

# Crear scraper
print("1️⃣ Inicializando scraper...")
scraper = MercadoLibreScraper()
print("   ✅ Scraper inicializado")

# Test 1: Búsqueda simple
print("\n" + "=" * 80)
print("2️⃣ TEST 1: Búsqueda simple de Toyota (1 página)")
print("=" * 80)

try:
    result = scraper.search_vehicles(
        marca="Toyota",
        max_pages=1
    )

    if result['status'] == 'success':
        print(f"\n   ✅ Scraping exitoso!")
        print(f"   📊 Total scrapeado: {result['total_scraped']} items")
        print(f"   📄 Páginas: {result['pages_scraped']}")

        if result['items']:
            print(f"\n   Primeros 3 resultados:")
            for i, item in enumerate(result['items'][:3], 1):
                print(f"\n   {i}. {item.get('title', 'N/A')[:70]}")
                if item.get('price'):
                    print(f"      💰 ${item['price']:,.0f}")
                if item.get('location'):
                    print(f"      📍 {item['location']}")
                if item.get('meli_id'):
                    print(f"      🆔 {item['meli_id']}")
        else:
            print("\n   ⚠️ No se encontraron items (posible cambio en HTML)")
    else:
        print(f"   ❌ Error: {result.get('error', 'Unknown')}")

except BlockedByMercadoLibreException as e:
    print(f"\n   🔒 BLOQUEADO: {e}")
    print("\n   Posibles causas:")
    print("   - Tu IP fue bloqueada temporalmente")
    print("   - MercadoLibre detectó scraping automático")
    print("   - CAPTCHA activado")
    print("\n   Soluciones:")
    print("   - Esperar 15-30 minutos")
    print("   - Cambiar IP (VPN/proxy)")
    print("   - Ajustar delays en settings.py")

except Exception as e:
    print(f"\n   ❌ Error inesperado: {e}")

# Test 2: Guardar en base de datos
if result.get('items'):
    print("\n" + "=" * 80)
    print("3️⃣ TEST 2: Guardar resultados en PostgreSQL")
    print("=" * 80)

    try:
        saved_count = scraper.save_to_database(result['items'])
        print(f"\n   ✅ Guardados {saved_count} items en la base de datos")
    except Exception as e:
        print(f"\n   ❌ Error guardando en BD: {e}")

# Test 3: Búsqueda con filtros
print("\n" + "=" * 80)
print("4️⃣ TEST 3: Búsqueda de vehículos 0km (1 página)")
print("=" * 80)

try:
    result_new = scraper.search_vehicles(
        query="auto",
        condition="new",
        max_pages=1
    )

    if result_new['status'] == 'success':
        print(f"\n   ✅ Scraping exitoso!")
        print(f"   📊 Vehículos 0km encontrados: {result_new['total_scraped']}")

        if result_new['items']:
            # Calcular precio promedio
            precios = [item['price'] for item in result_new['items'] if item.get('price')]
            if precios:
                precio_promedio = sum(precios) / len(precios)
                precio_min = min(precios)
                precio_max = max(precios)
                print(f"\n   📊 Estadísticas de precios:")
                print(f"      Promedio: ${precio_promedio:,.0f}")
                print(f"      Mínimo: ${precio_min:,.0f}")
                print(f"      Máximo: ${precio_max:,.0f}")
    else:
        print(f"   ❌ Error: {result_new.get('error', 'Unknown')}")

except BlockedByMercadoLibreException as e:
    print(f"\n   🔒 BLOQUEADO: {e}")

except Exception as e:
    print(f"\n   ❌ Error: {e}")

# Resumen final
print("\n" + "=" * 80)
print("📊 RESUMEN DE TESTS")
print("=" * 80)

tests_ok = 0
tests_total = 3

if result.get('status') == 'success':
    tests_ok += 1
    print("✅ Búsqueda simple: OK")
else:
    print("❌ Búsqueda simple: FAIL")

if result.get('items') and saved_count > 0:
    tests_ok += 1
    print("✅ Guardar en BD: OK")
else:
    print("❌ Guardar en BD: FAIL")

if result_new.get('status') == 'success':
    tests_ok += 1
    print("✅ Búsqueda con filtros: OK")
else:
    print("❌ Búsqueda con filtros: FAIL")

print(f"\n🎯 Tests pasados: {tests_ok}/{tests_total}")

if tests_ok == tests_total:
    print("\n" + "=" * 80)
    print("✅ ¡SCRAPING FUNCIONAL!")
    print("=" * 80)
    print("\n🎉 El scraper funciona correctamente")
    print("🔓 MercadoLibre NO está bloqueando el scraping")
    print("\n📊 Ya podés:")
    print("   • Scrapear vehículos por marca/modelo")
    print("   • Obtener precios del mercado retail")
    print("   • Guardar datos en PostgreSQL")
    print("   • Generar snapshots diarios del mercado")
    print("\n🚀 Próximos pasos:")
    print("   • Ejecutar: python scripts/scrape_mercadolibre.py")
    print("   • Automatizar con Airflow/cron")
    print("   • Crear dashboards con Streamlit")

elif tests_ok > 0:
    print(f"\n⚠️ Algunos tests fallaron ({tests_total - tests_ok}/{tests_total})")
    print("   Revisar los errores arriba para más detalles")
    print("\n   Si ves mensajes de BLOQUEADO:")
    print("   • Esperar antes de reintentar")
    print("   • Ajustar delays en .env")
    print("   • Considerar usar proxies")

else:
    print("\n❌ TODOS LOS TESTS FALLARON")
    print("\n   Posibles causas:")
    print("   • MercadoLibre bloqueó tu IP")
    print("   • Cambió la estructura HTML del sitio")
    print("   • Problemas de conexión")
    print("\n   Revisar logs detallados arriba")

print("\n" + "=" * 80)
print("📝 Logs guardados en: logs/app.log")
print("=" * 80)
