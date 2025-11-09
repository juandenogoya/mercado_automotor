"""
Test de endpoints públicos de MercadoLibre (sin autenticación)
Identifica qué información podemos acceder sin credenciales
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://api.mercadolibre.com"
SITE_ID = "MLA"
CATEGORIA_AUTOS = "MLA1743"

# Deshabilitar warnings SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("=" * 80)
print("🔓 TEST - ENDPOINTS PÚBLICOS MERCADOLIBRE (SIN AUTENTICACIÓN)")
print("=" * 80)
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

session = requests.Session()
session.verify = False

# Lista de endpoints a probar
endpoints_to_test = [
    {
        "name": "Información del sitio MLA",
        "url": f"{BASE_URL}/sites/{SITE_ID}",
        "descripcion": "Info general del sitio Argentina"
    },
    {
        "name": "Categoría principal Autos",
        "url": f"{BASE_URL}/categories/{CATEGORIA_AUTOS}",
        "descripcion": "Info de la categoría de autos"
    },
    {
        "name": "Búsqueda simple - Toyota",
        "url": f"{BASE_URL}/sites/{SITE_ID}/search?q=Toyota",
        "descripcion": "Búsqueda básica sin categoría"
    },
    {
        "name": "Búsqueda con categoría",
        "url": f"{BASE_URL}/sites/{SITE_ID}/search?category={CATEGORIA_AUTOS}&limit=10",
        "descripcion": "Búsqueda en categoría autos"
    },
    {
        "name": "Item específico público",
        "url": f"{BASE_URL}/items/MLA1459025408",
        "descripcion": "Detalle de un item conocido"
    },
    {
        "name": "Tendencias del sitio",
        "url": f"{BASE_URL}/trends/{SITE_ID}/MLA1743",
        "descripcion": "Búsquedas tendencia en autos"
    },
    {
        "name": "Monedas disponibles",
        "url": f"{BASE_URL}/currencies",
        "descripcion": "Lista de monedas"
    },
    {
        "name": "Tipos de listado",
        "url": f"{BASE_URL}/sites/{SITE_ID}/listing_types",
        "descripcion": "Tipos de publicación disponibles"
    }
]

resultados = []

for i, endpoint in enumerate(endpoints_to_test, 1):
    print(f"\n[{i}/{len(endpoints_to_test)}] {endpoint['name']}")
    print(f"   📝 {endpoint['descripcion']}")
    print(f"   🔗 {endpoint['url'][:80]}{'...' if len(endpoint['url']) > 80 else ''}")

    try:
        response = session.get(endpoint['url'], timeout=15)

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS - Status 200")

            # Mostrar información relevante según el tipo de endpoint
            if 'total_items' in data:
                print(f"      📊 Total items: {data['total_items']:,}")
            if 'paging' in data and 'total' in data['paging']:
                print(f"      📊 Total resultados: {data['paging']['total']:,}")
                print(f"      📄 Resultados en respuesta: {len(data.get('results', []))}")
            if 'name' in data:
                print(f"      📌 Nombre: {data['name']}")
            if 'id' in data and 'title' in data:
                print(f"      📦 Item: {data['title'][:60]}")
                print(f"      💰 Precio: ${data.get('price', 0):,.0f}")

            resultados.append({
                "endpoint": endpoint['name'],
                "status": "OK",
                "status_code": 200,
                "tiene_datos": len(data) > 0
            })
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            print(f"      Error: {response.text[:100]}")

            resultados.append({
                "endpoint": endpoint['name'],
                "status": "FAIL",
                "status_code": response.status_code,
                "tiene_datos": False
            })

    except Exception as e:
        print(f"   ❌ ERROR - {str(e)[:80]}")
        resultados.append({
            "endpoint": endpoint['name'],
            "status": "ERROR",
            "status_code": None,
            "tiene_datos": False
        })

# Resumen final
print("\n" + "=" * 80)
print("📊 RESUMEN DE ACCESIBILIDAD")
print("=" * 80)

endpoints_ok = sum(1 for r in resultados if r['status'] == 'OK')
endpoints_fail = sum(1 for r in resultados if r['status'] == 'FAIL')
endpoints_error = sum(1 for r in resultados if r['status'] == 'ERROR')

print(f"\n✅ Accesibles: {endpoints_ok}/{len(endpoints_to_test)}")
print(f"❌ Bloqueados (403): {endpoints_fail}/{len(endpoints_to_test)}")
print(f"⚠️ Errores: {endpoints_error}/{len(endpoints_to_test)}")

print("\n📋 Detalle por endpoint:")
for r in resultados:
    status_icon = "✅" if r['status'] == 'OK' else "❌" if r['status'] == 'FAIL' else "⚠️"
    print(f"   {status_icon} {r['endpoint']}: {r['status']} ({r.get('status_code', 'N/A')})")

# Conclusiones
print("\n" + "=" * 80)
print("💡 CONCLUSIONES")
print("=" * 80)

if endpoints_ok > 0:
    print(f"\n✅ Hay {endpoints_ok} endpoints accesibles sin autenticación")
    print("   Podemos obtener:")
    print("   • Información de categorías")
    print("   • Detalles de items individuales")
    print("   • Información del sitio/monedas")
else:
    print("\n❌ No hay endpoints públicos accesibles")
    print("   Se requiere autenticación OAuth2 para MercadoLibre API")

if endpoints_fail > 0:
    print(f"\n⚠️ {endpoints_fail} endpoints requieren autenticación:")
    print("   • Búsquedas (search)")
    print("   • Listados completos")
    print("   • Tendencias")
    print("\n   📚 Documentación: https://developers.mercadolibre.com.ar/")
    print("   🔑 Se necesita:")
    print("      1. Crear una aplicación en MercadoLibre Developers")
    print("      2. Obtener Client ID y Client Secret")
    print("      3. Implementar OAuth2 flow")

print("\n" + "=" * 80)
