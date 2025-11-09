"""
Diagnóstico de endpoints accesibles de MercadoLibre API con OAuth2.
Prueba diferentes endpoints para ver cuáles están disponibles.
"""

import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))

from backend.auth.mercadolibre_oauth import MercadoLibreAuth
from backend.config.logger import setup_logger

setup_logger()

print("=" * 80)
print("🔍 DIAGNÓSTICO - ENDPOINTS MERCADOLIBRE")
print("=" * 80)

# Inicializar autenticación
auth = MercadoLibreAuth()

if not auth.is_authenticated():
    print("❌ No autenticado. Ejecutar: python -m backend.auth.mercadolibre_oauth")
    sys.exit(1)

access_token = auth.get_access_token()
print(f"\n✅ Token obtenido: {access_token[:20]}...")
print(f"👤 User ID: {auth._user_id}")

# Headers con autenticación
headers = {
    'Authorization': f'Bearer {access_token}',
    'Accept': 'application/json'
}

BASE_URL = "https://api.mercadolibre.com"

# Lista de endpoints a probar
endpoints_to_test = [
    {
        "name": "Mi información de usuario",
        "url": f"{BASE_URL}/users/{auth._user_id}",
        "method": "GET",
        "description": "Info del usuario autenticado"
    },
    {
        "name": "Sitio MLA (Argentina)",
        "url": f"{BASE_URL}/sites/MLA",
        "method": "GET",
        "description": "Información del sitio Argentina"
    },
    {
        "name": "Categoría Autos",
        "url": f"{BASE_URL}/categories/MLA1743",
        "method": "GET",
        "description": "Info de categoría de autos"
    },
    {
        "name": "Búsqueda pública - Toyota",
        "url": f"{BASE_URL}/sites/MLA/search?q=Toyota&category=MLA1743&limit=5",
        "method": "GET",
        "description": "Búsqueda en mercado público"
    },
    {
        "name": "Mis items/publicaciones",
        "url": f"{BASE_URL}/users/{auth._user_id}/items/search",
        "method": "GET",
        "description": "Items publicados por el usuario"
    },
    {
        "name": "Item específico",
        "url": f"{BASE_URL}/items/MLA1459025408",
        "method": "GET",
        "description": "Detalle de un item conocido"
    },
    {
        "name": "Mis favoritos",
        "url": f"{BASE_URL}/users/{auth._user_id}/bookmarks",
        "method": "GET",
        "description": "Items favoritos del usuario"
    },
]

print("\n" + "=" * 80)
print("PROBANDO ENDPOINTS")
print("=" * 80)

resultados = []

for i, endpoint in enumerate(endpoints_to_test, 1):
    print(f"\n[{i}/{len(endpoints_to_test)}] {endpoint['name']}")
    print(f"   📝 {endpoint['description']}")
    print(f"   🔗 {endpoint['url'][:80]}...")

    try:
        if endpoint['method'] == 'GET':
            response = requests.get(endpoint['url'], headers=headers, timeout=15)

        status_code = response.status_code

        if status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Status 200")

            # Mostrar datos relevantes según el endpoint
            if 'nickname' in data:
                print(f"      👤 Nickname: {data.get('nickname', 'N/A')}")
            if 'name' in data:
                print(f"      📌 Nombre: {data['name']}")
            if 'paging' in data:
                print(f"      📊 Total resultados: {data['paging'].get('total', 0):,}")
                print(f"      📄 Resultados: {len(data.get('results', []))}")
            if 'results' in data and isinstance(data['results'], list):
                print(f"      📄 Items encontrados: {len(data['results'])}")
            if 'id' in data and 'title' in data:
                print(f"      📦 Item: {data.get('title', '')[:60]}")

            resultados.append({
                "endpoint": endpoint['name'],
                "status": "OK",
                "status_code": 200
            })
        elif status_code == 403:
            print(f"   ❌ FORBIDDEN - Status 403")
            print(f"      ⚠️ Token válido pero sin permisos para este endpoint")
            resultados.append({
                "endpoint": endpoint['name'],
                "status": "FORBIDDEN",
                "status_code": 403
            })
        elif status_code == 401:
            print(f"   ❌ UNAUTHORIZED - Status 401")
            print(f"      ⚠️ Token inválido o expirado")
            resultados.append({
                "endpoint": endpoint['name'],
                "status": "UNAUTHORIZED",
                "status_code": 401
            })
        else:
            print(f"   ⚠️ Status {status_code}")
            try:
                error_data = response.json()
                print(f"      Error: {error_data.get('message', 'Unknown')}")
            except:
                print(f"      Response: {response.text[:100]}")

            resultados.append({
                "endpoint": endpoint['name'],
                "status": f"ERROR_{status_code}",
                "status_code": status_code
            })

    except Exception as e:
        print(f"   ❌ EXCEPTION - {str(e)[:80]}")
        resultados.append({
            "endpoint": endpoint['name'],
            "status": "EXCEPTION",
            "status_code": None
        })

# Resumen
print("\n" + "=" * 80)
print("📊 RESUMEN DE ACCESIBILIDAD")
print("=" * 80)

ok_count = sum(1 for r in resultados if r['status'] == 'OK')
forbidden_count = sum(1 for r in resultados if r['status'] == 'FORBIDDEN')
error_count = len(resultados) - ok_count - forbidden_count

print(f"\n✅ Accesibles (200): {ok_count}/{len(resultados)}")
print(f"❌ Bloqueados (403): {forbidden_count}/{len(resultados)}")
print(f"⚠️ Otros errores: {error_count}/{len(resultados)}")

print("\n📋 Detalle:")
for r in resultados:
    if r['status'] == 'OK':
        icon = "✅"
    elif r['status'] == 'FORBIDDEN':
        icon = "🔒"
    else:
        icon = "❌"

    print(f"   {icon} {r['endpoint']}: {r['status']} ({r.get('status_code', 'N/A')})")

# Conclusiones
print("\n" + "=" * 80)
print("💡 CONCLUSIONES Y PRÓXIMOS PASOS")
print("=" * 80)

if ok_count == 0:
    print("\n❌ NO HAY ENDPOINTS ACCESIBLES")
    print("   Posibles causas:")
    print("   1. Los scopes solicitados son insuficientes")
    print("   2. La aplicación necesita aprobación de MercadoLibre")
    print("   3. El endpoint de búsqueda pública ya no existe")
    print("\n   Opciones:")
    print("   A) Solicitar más scopes en la aplicación de ML")
    print("   B) Contactar soporte de MercadoLibre Developers")
    print("   C) Usar web scraping en lugar de API")
elif forbidden_count > 0:
    print(f"\n⚠️ {forbidden_count} endpoints están bloqueados (403)")
    print(f"✅ Pero {ok_count} endpoints SÍ funcionan")
    print("\n   Endpoints accesibles:")
    for r in resultados:
        if r['status'] == 'OK':
            print(f"      • {r['endpoint']}")
    print("\n   Endpoints bloqueados:")
    for r in resultados:
        if r['status'] == 'FORBIDDEN':
            print(f"      • {r['endpoint']}")
    print("\n   📌 RECOMENDACIÓN:")
    print("      Usar endpoints disponibles y combinar con otras fuentes de datos")
else:
    print(f"\n✅ TODOS LOS ENDPOINTS FUNCIONAN ({ok_count}/{len(resultados)})")
    print("   Podés acceder a toda la información de MercadoLibre")

print("\n" + "=" * 80)
