"""
Test de la nueva API BCRA v4.0
"""
import requests
import urllib3
from datetime import date, timedelta

# Deshabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL_V4 = "https://api.bcra.gob.ar/estadisticas/v4.0"
BASE_URL_V2 = "https://api.bcra.gob.ar/estadisticas/v2.0"

def test_endpoint(url, descripcion):
    """Prueba un endpoint específico."""
    print(f"\n{'='*80}")
    print(f"TEST: {descripcion}")
    print(f"URL: {url}")
    print('='*80)

    try:
        response = requests.get(url, timeout=30, verify=False)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ OK")

            # Mostrar estructura de respuesta
            if isinstance(data, dict):
                print(f"Claves: {list(data.keys())}")
                if 'results' in data:
                    print(f"Resultados: {len(data['results'])} items")
                    if data['results']:
                        print(f"Primer resultado: {data['results'][0]}")
            elif isinstance(data, list):
                print(f"Lista con {len(data)} items")
                if data:
                    print(f"Primer item: {data[0]}")
        else:
            print(f"❌ Error {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {str(e)[:200]}")

print("="*80)
print("PRUEBA DE API BCRA v4.0")
print("="*80)

# Test 1: Principales variables v4
test_endpoint(
    f"{BASE_URL_V4}/principales",
    "Principales Variables (v4.0)"
)

# Test 2: Principales variables v2 (comparación)
test_endpoint(
    f"{BASE_URL_V2}/principales",
    "Principales Variables (v2.0 - antiguo)"
)

# Test 3: BADLAR con v4
hoy = date.today()
hace_30_dias = hoy - timedelta(days=30)

test_endpoint(
    f"{BASE_URL_V4}/datosvariable/7/{hace_30_dias.strftime('%Y-%m-%d')}/{hoy.strftime('%Y-%m-%d')}",
    "BADLAR últimos 30 días (v4.0)"
)

# Test 4: BADLAR con v2 (comparación)
test_endpoint(
    f"{BASE_URL_V2}/datosvariable/7/{hace_30_dias.strftime('%Y-%m-%d')}/{hoy.strftime('%Y-%m-%d')}",
    "BADLAR últimos 30 días (v2.0 - antiguo)"
)

# Test 5: Tipo de Cambio con v4
test_endpoint(
    f"{BASE_URL_V4}/datosvariable/1/{hace_30_dias.strftime('%Y-%m-%d')}/{hoy.strftime('%Y-%m-%d')}",
    "Tipo de Cambio últimos 30 días (v4.0)"
)

# Test 6: Últimos 7 días con v4
hace_7_dias = hoy - timedelta(days=7)

test_endpoint(
    f"{BASE_URL_V4}/datosvariable/7/{hace_7_dias.strftime('%Y-%m-%d')}/{hoy.strftime('%Y-%m-%d')}",
    "BADLAR últimos 7 días (v4.0)"
)

# Test 7: Probar endpoint sin fechas (último valor)
test_endpoint(
    f"{BASE_URL_V4}/datosvariable/7",
    "BADLAR - Último valor (v4.0)"
)

print("\n" + "="*80)
print("CONCLUSIÓN")
print("="*80)
print("""
Si v4.0 funciona:
  ✅ Actualizar BCRAClient para usar v4.0 en lugar de v2.0

Si v4.0 también falla:
  ⚠️  Problema temporal con la API del BCRA

Si v4.0 tiene estructura diferente:
  🔧 Adaptar el parser de respuestas
""")
