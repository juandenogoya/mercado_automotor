"""
Test del cliente de MercadoLibre API
Verifica acceso a la API y funcionalidades básicas

EJECUCIÓN:
python test_mercadolibre_client.py
"""

import sys
from pathlib import Path

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

from backend.api_clients.mercadolibre_client import MercadoLibreClient
from backend.config.logger import setup_logger

print("=" * 80)
print("🧪 TEST - CLIENTE MERCADOLIBRE API")
print("=" * 80)

# Setup logger
setup_logger()

# Crear cliente
print("\n1️⃣ Inicializando cliente MercadoLibre...")
client = MercadoLibreClient()
print("   ✅ Cliente inicializado")

# Test 1: Búsqueda simple
print("\n" + "=" * 80)
print("2️⃣ TEST: Búsqueda de vehículos Toyota")
print("=" * 80)

result = client.search_vehicles(marca="Toyota", limit=5)

if result['status'] == 'success':
    print(f"   ✅ Búsqueda exitosa!")
    print(f"   📊 Total resultados: {result['total']:,}")
    print(f"   📄 Resultados obtenidos: {len(result['results'])}")

    if result['results']:
        print(f"\n   Primeros resultados:")
        for i, item in enumerate(result['results'][:3], 1):
            print(f"\n   {i}. {item['title'][:70]}")
            print(f"      💰 ${item['price']:,.0f} {item['currency_id']}")
            print(f"      🏷️ {item['condition']}")
else:
    print(f"   ❌ Error: {result.get('error', 'Unknown')}")
    print(f"   Status: {result['status']}")

# Test 2: Búsqueda con filtros
print("\n" + "=" * 80)
print("3️⃣ TEST: Búsqueda de vehículos 0km")
print("=" * 80)

result_new = client.search_vehicles(condicion="new", limit=5)

if result_new['status'] == 'success':
    print(f"   ✅ Búsqueda exitosa!")
    print(f"   📊 Total 0km disponibles: {result_new['total']:,}")
else:
    print(f"   ❌ Error: {result_new.get('error', 'Unknown')}")

# Test 3: Búsqueda usados
print("\n" + "=" * 80)
print("4️⃣ TEST: Búsqueda de vehículos usados")
print("=" * 80)

result_used = client.search_vehicles(condicion="used", limit=5)

if result_used['status'] == 'success':
    print(f"   ✅ Búsqueda exitosa!")
    print(f"   📊 Total usados disponibles: {result_used['total']:,}")
else:
    print(f"   ❌ Error: {result_used.get('error', 'Unknown')}")

# Test 4: Detalle de item (si tenemos resultados)
if result['status'] == 'success' and result['results']:
    print("\n" + "=" * 80)
    print("5️⃣ TEST: Obtener detalle de un item")
    print("=" * 80)

    item_id = result['results'][0]['id']
    print(f"   Item ID: {item_id}")

    detail = client.get_item_detail(item_id)

    if detail:
        print(f"   ✅ Detalle obtenido!")
        print(f"   📝 Título: {detail['title']}")
        print(f"   💰 Precio: ${detail['price']:,.0f}")
        print(f"   📷 Imágenes: {len(detail.get('pictures', []))}")
        print(f"   🔧 Atributos: {len(detail.get('attributes', []))}")

        # Mostrar algunos atributos
        print(f"\n   Atributos del vehículo:")
        for attr in detail.get('attributes', [])[:5]:
            print(f"      • {attr.get('name', 'N/A')}: {attr.get('value_name', 'N/A')}")
    else:
        print(f"   ❌ No se pudo obtener detalle")

# Resumen final
print("\n" + "=" * 80)
print("📊 RESUMEN DE TESTS")
print("=" * 80)

tests_ok = 0
tests_total = 4

if result['status'] == 'success':
    tests_ok += 1
    print("✅ Búsqueda por marca: OK")
else:
    print("❌ Búsqueda por marca: FAIL")

if result_new['status'] == 'success':
    tests_ok += 1
    print("✅ Búsqueda 0km: OK")
else:
    print("❌ Búsqueda 0km: FAIL")

if result_used['status'] == 'success':
    tests_ok += 1
    print("✅ Búsqueda usados: OK")
else:
    print("❌ Búsqueda usados: FAIL")

if result['status'] == 'success' and result['results']:
    detail_test = client.get_item_detail(result['results'][0]['id'])
    if detail_test:
        tests_ok += 1
        print("✅ Detalle de item: OK")
    else:
        print("❌ Detalle de item: FAIL")
else:
    print("⚠️ Detalle de item: SKIP (sin resultados)")
    tests_total = 3

print(f"\n🎯 Tests pasados: {tests_ok}/{tests_total}")

if tests_ok == tests_total:
    print("\n✅ TODOS LOS TESTS PASARON - Cliente MercadoLibre funcionando correctamente")
else:
    print(f"\n⚠️ ALGUNOS TESTS FALLARON - Revisar configuración de API")

print("\n" + "=" * 80)
