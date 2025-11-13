"""
Script para probar la API del BCRA con diferentes rangos y variables.
"""
import requests
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# Deshabilitar warnings SSL
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://api.bcra.gob.ar"

def test_principals():
    """Prueba el endpoint de principales variables."""
    url = f"{BASE_URL}/estadisticas/v2.0/principales"

    print("="*80)
    print("TEST 1: Principales Variables")
    print("="*80)

    try:
        response = requests.get(url, timeout=30, verify=False)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ OK - Obtenidas {len(data.get('results', []))} variables")

            # Mostrar algunas
            for var in data.get('results', [])[:5]:
                print(f"  - ID: {var.get('idVariable'):3d} | {var.get('descripcion')}")
        else:
            print(f"❌ Error {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print()

def test_variable_range(var_id, var_name, desde, hasta):
    """Prueba obtener una variable en un rango específico."""
    desde_str = desde.strftime('%Y-%m-%d')
    hasta_str = hasta.strftime('%Y-%m-%d')

    url = f"{BASE_URL}/estadisticas/v2.0/datosvariable/{var_id}/{desde_str}/{hasta_str}"

    dias = (hasta - desde).days
    print(f"TEST: {var_name} (ID {var_id})")
    print(f"  Rango: {desde_str} a {hasta_str} ({dias} días)")

    try:
        response = requests.get(url, timeout=30, verify=False)
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            resultados = data.get('results', [])
            print(f"  ✅ OK - {len(resultados)} registros")

            if resultados:
                print(f"  Primer valor: {resultados[0]}")
                print(f"  Último valor: {resultados[-1]}")
        else:
            print(f"  ❌ Error {response.status_code}: {response.text[:100]}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

print("="*80)
print("PRUEBA DE API BCRA - Diagnóstico")
print("="*80)
print()

# Test 1: Principales variables
test_principals()

# Definir hoy
hoy = date.today()

# Test 2: Último mes (30 días)
print("="*80)
print("TEST 2: BADLAR - Último mes (30 días)")
print("="*80)
desde = hoy - timedelta(days=30)
test_variable_range(7, "BADLAR", desde, hoy)

# Test 3: Última semana
print("="*80)
print("TEST 3: BADLAR - Última semana (7 días)")
print("="*80)
desde = hoy - timedelta(days=7)
test_variable_range(7, "BADLAR", desde, hoy)

# Test 4: Último trimestre (3 meses)
print("="*80)
print("TEST 4: BADLAR - Último trimestre (3 meses)")
print("="*80)
desde = hoy - relativedelta(months=3)
test_variable_range(7, "BADLAR", desde, hoy)

# Test 5: Último semestre (6 meses)
print("="*80)
print("TEST 5: BADLAR - Último semestre (6 meses)")
print("="*80)
desde = hoy - relativedelta(months=6)
test_variable_range(7, "BADLAR", desde, hoy)

# Test 6: Tipo de Cambio - Última semana
print("="*80)
print("TEST 6: Tipo de Cambio - Última semana")
print("="*80)
desde = hoy - timedelta(days=7)
test_variable_range(1, "Tipo de Cambio BNA", desde, hoy)

# Test 7: Año 2024 completo (rango histórico)
print("="*80)
print("TEST 7: BADLAR - Año 2024 completo")
print("="*80)
test_variable_range(7, "BADLAR", date(2024, 1, 1), date(2024, 12, 31))

print("="*80)
print("RESUMEN")
print("="*80)
print("""
Si todos los tests fallan:
  → La API del BCRA está caída o bloqueando las requests

Si funcionan los rangos cortos (7-30 días) pero fallan los largos:
  → Necesitamos chunks más pequeños (1 mes en lugar de 6)

Si solo falla el año completo:
  → El límite está entre 3-6 meses, ajustar chunk_months
""")
