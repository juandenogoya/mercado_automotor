"""
Test del cliente de MercadoLibre API con autenticación OAuth2.

Pre-requisitos:
1. Tener credenciales configuradas en .env
2. Haber ejecutado el flujo de autenticación (backend/auth/mercadolibre_oauth.py)
3. Tener archivo .meli_tokens.json con tokens válidos

Ejecución:
python test_mercadolibre_authenticated.py
"""

import sys
from pathlib import Path

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

from backend.auth.mercadolibre_oauth import MercadoLibreAuth
from backend.api_clients.mercadolibre_client import MercadoLibreClient
from backend.config.logger import setup_logger
from backend.config.settings import settings

print("=" * 80)
print("🔐 TEST - CLIENTE MERCADOLIBRE CON OAUTH2")
print("=" * 80)

# Setup logger
setup_logger()

# Verificar credenciales
print("\n1️⃣ Verificando credenciales...")

if not settings.mercadolibre_client_id or not settings.mercadolibre_client_secret:
    print("   ❌ ERROR: Credenciales no configuradas")
    print("\n   Ejecutar primero:")
    print("   1. Ver GUIA_REGISTRO_MERCADOLIBRE_DEVELOPER.md")
    print("   2. Configurar credenciales en .env")
    print("   3. python backend/auth/verify_credentials.py")
    sys.exit(1)

print(f"   ✅ Client ID encontrado: {settings.mercadolibre_client_id[:10]}...")

# Crear gestor de autenticación
print("\n2️⃣ Inicializando autenticación OAuth2...")

try:
    auth = MercadoLibreAuth()
except ValueError as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Verificar si está autenticado
print("\n3️⃣ Verificando autenticación...")

if not auth.is_authenticated():
    print("   ❌ No estás autenticado")
    print("\n   Ejecutar primero:")
    print("   python backend/auth/mercadolibre_oauth.py")
    sys.exit(1)

print("   ✅ Autenticado correctamente")
print(f"   📊 User ID: {auth._user_id}")
print(f"   ⏰ Token expira: {auth._token_expires_at}")

# Crear cliente con autenticación
print("\n4️⃣ Inicializando cliente MercadoLibre con OAuth2...")

client = MercadoLibreClient(auth=auth)

print("   ✅ Cliente inicializado con autenticación")

# TEST 1: Búsqueda de vehículos Toyota
print("\n" + "=" * 80)
print("5️⃣ TEST 1: Búsqueda de vehículos Toyota")
print("=" * 80)

result = client.search_vehicles(marca="Toyota", limit=5)

if result['status'] == 'success':
    print(f"   ✅ Búsqueda exitosa!")
    print(f"   📊 Total resultados disponibles: {result['total']:,}")
    print(f"   📄 Resultados obtenidos: {len(result['results'])}")

    if result['results']:
        print(f"\n   Primeros 3 resultados:")
        for i, item in enumerate(result['results'][:3], 1):
            print(f"\n   {i}. {item['title'][:60]}")
            print(f"      💰 ${item['price']:,.0f} {item['currency_id']}")
            print(f"      🏷️ {item['condition']} | 📍 {item.get('location', {}).get('city', {}).get('name', 'N/A')}")
else:
    print(f"   ❌ Error: {result.get('error', 'Unknown')}")
    print(f"   Status: {result['status']}")
    print("\n   Si el error es 403, verificar:")
    print("   - Que el token no esté expirado")
    print("   - Que la aplicación tenga los permisos correctos")

# TEST 2: Búsqueda de vehículos 0km
print("\n" + "=" * 80)
print("6️⃣ TEST 2: Búsqueda de vehículos 0km")
print("=" * 80)

result_new = client.search_vehicles(condicion="new", limit=5)

if result_new['status'] == 'success':
    print(f"   ✅ Búsqueda exitosa!")
    print(f"   📊 Total vehículos 0km disponibles: {result_new['total']:,}")

    # Calcular precio promedio
    if result_new['results']:
        precios = [item['price'] for item in result_new['results']]
        precio_promedio = sum(precios) / len(precios)
        print(f"   💰 Precio promedio (muestra): ${precio_promedio:,.0f}")
else:
    print(f"   ❌ Error: {result_new.get('error', 'Unknown')}")

# TEST 3: Búsqueda de vehículos usados
print("\n" + "=" * 80)
print("7️⃣ TEST 3: Búsqueda de vehículos usados")
print("=" * 80)

result_used = client.search_vehicles(condicion="used", limit=5)

if result_used['status'] == 'success':
    print(f"   ✅ Búsqueda exitosa!")
    print(f"   📊 Total vehículos usados disponibles: {result_used['total']:,}")

    # Calcular precio promedio
    if result_used['results']:
        precios = [item['price'] for item in result_used['results']]
        precio_promedio = sum(precios) / len(precios)
        print(f"   💰 Precio promedio (muestra): ${precio_promedio:,.0f}")
else:
    print(f"   ❌ Error: {result_used.get('error', 'Unknown')}")

# TEST 4: Detalle de un item específico
if result['status'] == 'success' and result['results']:
    print("\n" + "=" * 80)
    print("8️⃣ TEST 4: Obtener detalle completo de un item")
    print("=" * 80)

    item_id = result['results'][0]['id']
    print(f"   Item ID: {item_id}")

    detail = client.get_item_detail(item_id)

    if detail:
        print(f"   ✅ Detalle obtenido exitosamente!")
        print(f"\n   📝 Título: {detail['title']}")
        print(f"   💰 Precio: ${detail['price']:,.0f} {detail['currency_id']}")
        print(f"   🏷️ Condición: {detail['condition']}")
        print(f"   📦 Estado: {detail['status']}")
        print(f"   📷 Imágenes: {len(detail.get('pictures', []))}")

        # Atributos del vehículo
        attributes = {attr['id']: attr for attr in detail.get('attributes', [])}

        print(f"\n   🚗 Atributos del vehículo:")

        marca = attributes.get('BRAND', {}).get('value_name', 'N/A')
        modelo = attributes.get('MODEL', {}).get('value_name', 'N/A')
        anio = attributes.get('VEHICLE_YEAR', {}).get('value_name', 'N/A')
        km = attributes.get('KILOMETERS', {}).get('value_name', 'N/A')
        combustible = attributes.get('FUEL_TYPE', {}).get('value_name', 'N/A')
        transmision = attributes.get('TRANSMISSION', {}).get('value_name', 'N/A')

        print(f"      • Marca: {marca}")
        print(f"      • Modelo: {modelo}")
        print(f"      • Año: {anio}")
        print(f"      • Kilómetros: {km}")
        print(f"      • Combustible: {combustible}")
        print(f"      • Transmisión: {transmision}")

        # Ubicación
        location = detail.get('location', {})
        if location:
            ciudad = location.get('city', {}).get('name', 'N/A')
            provincia = location.get('state', {}).get('name', 'N/A')
            print(f"\n   📍 Ubicación:")
            print(f"      • Ciudad: {ciudad}")
            print(f"      • Provincia: {provincia}")

        # Seller info
        seller = detail.get('seller_address', {})
        if seller:
            print(f"\n   👤 Vendedor:")
            print(f"      • ID: {detail.get('seller_id', 'N/A')}")

    else:
        print(f"   ❌ No se pudo obtener detalle del item")

# TEST 5: Búsqueda con filtros múltiples
print("\n" + "=" * 80)
print("9️⃣ TEST 5: Búsqueda con filtros múltiples")
print("=" * 80)

print("   Buscando: Ford Ranger 0km...")

result_filtered = client.search_vehicles(
    marca="Ford",
    modelo="Ranger",
    condicion="new",
    limit=5
)

if result_filtered['status'] == 'success':
    print(f"   ✅ Búsqueda exitosa!")
    print(f"   📊 Total Ford Ranger 0km: {result_filtered['total']:,}")

    if result_filtered['results']:
        print(f"\n   Resultados encontrados:")
        for i, item in enumerate(result_filtered['results'], 1):
            print(f"   {i}. {item['title'][:60]}")
            print(f"      💰 ${item['price']:,.0f}")
else:
    print(f"   ❌ Error: {result_filtered.get('error', 'Unknown')}")

# Resumen final
print("\n" + "=" * 80)
print("📊 RESUMEN DE TESTS CON OAUTH2")
print("=" * 80)

tests_ok = 0
tests_total = 5

test_results = [
    ("Búsqueda por marca (Toyota)", result['status'] == 'success'),
    ("Búsqueda vehículos 0km", result_new['status'] == 'success'),
    ("Búsqueda vehículos usados", result_used['status'] == 'success'),
    ("Detalle de item", detail is not None if result['results'] else True),
    ("Búsqueda con filtros múltiples", result_filtered['status'] == 'success')
]

for test_name, test_passed in test_results:
    if test_passed:
        print(f"✅ {test_name}: OK")
        tests_ok += 1
    else:
        print(f"❌ {test_name}: FAIL")

print(f"\n🎯 Tests pasados: {tests_ok}/{tests_total}")

if tests_ok == tests_total:
    print("\n" + "=" * 80)
    print("✅ ¡ÉXITO TOTAL!")
    print("=" * 80)
    print("\n🎉 Todos los tests pasaron correctamente")
    print("🔓 Acceso completo a la API de MercadoLibre habilitado")
    print("\n📊 Ya podés:")
    print("   • Buscar vehículos con filtros avanzados")
    print("   • Obtener detalles completos de listados")
    print("   • Generar snapshots del mercado")
    print("   • Analizar precios y tendencias")
    print("\n🚀 Próximos pasos:")
    print("   • Crear scraper automático diario")
    print("   • Implementar análisis de precios")
    print("   • Generar dashboards con Streamlit")
elif tests_ok > 0:
    print(f"\n⚠️ Algunos tests fallaron ({tests_total - tests_ok}/{tests_total})")
    print("   Revisar los errores arriba para más detalles")
else:
    print("\n❌ TODOS LOS TESTS FALLARON")
    print("\n   Posibles causas:")
    print("   • Token expirado (ejecutar de nuevo: python backend/auth/mercadolibre_oauth.py)")
    print("   • Credenciales incorrectas")
    print("   • Permisos insuficientes en la aplicación")

print("\n" + "=" * 80)
