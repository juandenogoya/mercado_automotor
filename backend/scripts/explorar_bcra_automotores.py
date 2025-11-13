"""
Script para explorar endpoints disponibles en BCRA API v4.0.

Investiga qué datos del sector automotor están disponibles.

Uso:
    python backend/scripts/explorar_bcra_automotores.py
"""
import requests
import urllib3
from datetime import date, timedelta

# Deshabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("="*80)
print("EXPLORADOR DE DATASETS BCRA - SECTOR AUTOMOTOR")
print("="*80)

# Base URL BCRA v4.0
base_url = "https://api.bcra.gob.ar/estadisticas/v4.0"

session = requests.Session()
session.verify = False
session.headers.update({'Accept': 'application/json'})

# 1. Explorar endpoint de estadísticas
print("\n1. EXPLORANDO ENDPOINTS DISPONIBLES:")
print("-" * 80)

endpoints_a_probar = [
    "/estadisticas",
    "/monetarias",
    "/series",
    "/automotores",
    "/prendarios",
    "/creditos",
]

for endpoint in endpoints_a_probar:
    url = f"{base_url}{endpoint}"
    try:
        response = session.get(url, timeout=10)
        print(f"  {endpoint:30s} - Status: {response.status_code}")
        if response.status_code == 200:
            print(f"    ✓ DISPONIBLE")
            # Mostrar primeras líneas de respuesta
            try:
                data = response.json()
                print(f"    Keys: {list(data.keys())[:5]}")
            except:
                print(f"    Content-Type: {response.headers.get('content-type', 'N/A')}")
    except Exception as e:
        print(f"  {endpoint:30s} - ERROR: {e}")

# 2. Buscar variables monetarias relacionadas con automotores
print("\n\n2. BUSCANDO VARIABLES RELACIONADAS CON AUTOMOTORES:")
print("-" * 80)

# Intentar obtener catálogo de variables (si existe)
catalogos_a_probar = [
    "/catalogo",
    "/variables",
    "/monetarias/catalogo",
]

for catalogo_url in catalogos_a_probar:
    url = f"{base_url}{catalogo_url}"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            print(f"\n  ✓ Encontrado catálogo en: {catalogo_url}")
            data = response.json()
            print(f"    Keys disponibles: {list(data.keys())}")

            # Buscar en resultados si hay algo relacionado con automotores
            if 'results' in data:
                print(f"    Total variables: {len(data['results'])}")
                # Buscar keywords relevantes
                keywords = ['auto', 'motor', 'vehiculo', 'prenda', 'credito', 'transferencia']
                for item in data['results']:
                    descripcion = str(item).lower()
                    for keyword in keywords:
                        if keyword in descripcion:
                            print(f"    MATCH: {item}")
                            break
    except Exception as e:
        pass

# 3. Probar IDs conocidos de variables monetarias (exploratorio)
print("\n\n3. PROBANDO IDs DE VARIABLES (EXPLORATORIO):")
print("-" * 80)

# Probar un rango de IDs para ver qué variables existen
fecha_desde = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
fecha_hasta = date.today().strftime('%Y-%m-%d')

print(f"\n  Probando IDs 1-50 con datos recientes ({fecha_desde} a {fecha_hasta}):")
print()

variables_encontradas = []

for id_var in range(1, 51):
    url = f"{base_url}/monetarias/{id_var}"
    params = {'desde': fecha_desde, 'hasta': fecha_hasta, 'limit': 10}

    try:
        response = session.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                nombre = data['results'][0].get('descripcion', 'Sin descripción')
                count = len(data['results'][0].get('detalle', []))
                variables_encontradas.append({
                    'id': id_var,
                    'nombre': nombre,
                    'registros': count
                })
                print(f"  ID {id_var:3d}: {nombre[:60]:60s} ({count} registros)")
    except:
        pass

# 4. Verificar endpoint de prendarios (CSV mencionado en código)
print("\n\n4. VERIFICANDO ENDPOINT DE CRÉDITOS PRENDARIOS:")
print("-" * 80)

prendarios_urls = [
    "https://api.bcra.gob.ar/pdfs/BCRAyVos/PRENDARIOS.CSV",
    "https://www.bcra.gob.ar/pdfs/BCRAyVos/PRENDARIOS.CSV",
    f"{base_url}/prendarios",
    f"{base_url}/creditos/prendarios",
]

for url in prendarios_urls:
    try:
        response = session.get(url, timeout=10)
        print(f"\n  {url}")
        print(f"    Status: {response.status_code}")
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            print(f"    Content-Type: {content_type}")

            if 'csv' in content_type.lower() or 'text' in content_type.lower():
                # Mostrar primeras líneas
                lines = response.text.split('\n')[:10]
                print(f"    ✓ CSV ENCONTRADO - Primeras líneas:")
                for line in lines:
                    print(f"      {line}")
    except Exception as e:
        print(f"    ERROR: {e}")

# 5. Resumen
print("\n\n" + "="*80)
print("RESUMEN DE DATASETS ENCONTRADOS PARA AUTOMOTORES")
print("="*80)

print(f"\nVariables monetarias encontradas: {len(variables_encontradas)}")

# Filtrar variables que puedan ser relevantes para automotores
keywords_relevantes = ['crédito', 'préstamo', 'prenda', 'auto', 'vehículo', 'consumo']

print("\nVariables potencialmente relevantes:")
for var in variables_encontradas:
    descripcion_lower = var['nombre'].lower()
    for keyword in keywords_relevantes:
        if keyword in descripcion_lower:
            print(f"  ID {var['id']:3d}: {var['nombre']}")
            break

print("\n" + "="*80)
print("\n💡 PRÓXIMOS PASOS:")
print("  1. Verificar qué IDs corresponden a automotores")
print("  2. Crear modelos para automotores (prendas, inscripciones, transferencias)")
print("  3. Agregar funciones al BCRAClient para sincronizar estos datos")
print("  4. Integrar con análisis existente")
print("\n" + "="*80)
