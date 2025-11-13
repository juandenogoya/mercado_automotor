"""
Test simple de API BCRA - Probando diferentes formatos y endpoints.
"""
import requests
import urllib3

# Deshabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_url(url, descripcion):
    """Prueba una URL específica."""
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
            print(f"Respuesta: {str(data)[:200]}...")
        else:
            print(f"❌ Error {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")

# Base URLs a probar
BASE_URLS = [
    "https://api.bcra.gob.ar",
    "https://api.estadisticasbcra.com",
]

print("="*80)
print("PRUEBA SIMPLE DE API BCRA")
print("="*80)

# Test 1: Principales variables con diferentes URLs
for base in BASE_URLS:
    test_url(f"{base}/estadisticas/v2.0/principales", f"Principales ({base})")
    test_url(f"{base}/estadisticas/v1.0/principales", f"Principales V1 ({base})")

# Test 2: Variable específica con diferentes formatos de fecha
print("\n" + "="*80)
print("PROBANDO DIFERENTES FORMATOS DE FECHA")
print("="*80)

base = "https://api.bcra.gob.ar"

# Formato 1: YYYY-MM-DD (actual)
test_url(
    f"{base}/estadisticas/v2.0/datosvariable/7/2024-11-01/2024-11-13",
    "Formato YYYY-MM-DD (últimos 13 días)"
)

# Formato 2: Sin guiones YYYYMMDD
test_url(
    f"{base}/estadisticas/v2.0/datosvariable/7/20241101/20241113",
    "Formato YYYYMMDD (sin guiones)"
)

# Test 3: Rango muy corto (3 días)
test_url(
    f"{base}/estadisticas/v2.0/datosvariable/7/2024-11-10/2024-11-13",
    "Rango corto (3 días)"
)

# Test 4: Solo un día
test_url(
    f"{base}/estadisticas/v2.0/datosvariable/7/2024-11-12/2024-11-12",
    "Un solo día"
)

# Test 5: Último dato disponible
test_url(
    f"{base}/estadisticas/v2.0/datosvariable/7/latest",
    "Último dato (latest)"
)

# Test 6: Probar con otra variable (tipo de cambio)
test_url(
    f"{base}/estadisticas/v2.0/datosvariable/1/2024-11-01/2024-11-13",
    "Tipo de Cambio (var 1) - últimos 13 días"
)

print("\n" + "="*80)
print("RECOMENDACIÓN")
print("="*80)
print("""
Si ninguna funciona:
  → La API del BCRA está temporalmente fuera de servicio
  → Usar fuente alternativa: https://api.estadisticasbcra.com

Si funciona algún formato específico:
  → Ajustar el cliente para usar ese formato

Si funciona con rangos muy cortos pero no largos:
  → Reducir chunks a 7 días máximo
""")
