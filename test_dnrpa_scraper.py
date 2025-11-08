"""
Test simple de DNRPA scraper
Para diagnosticar problemas de parsing HTML
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Configuración
url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"
params = {
    'origen': 'portal_dnrpa',
    'tipo_consulta': 'inscripciones',
    'anio': 2024,
    'codigo_tipo': 'A',  # Autos
    'codigo_tramite': 3   # Inscripciones
}

print("=" * 80)
print("🧪 TEST DNRPA SCRAPER")
print("=" * 80)
print(f"\n📥 Descargando: {url}")
print(f"   Parámetros: {params}")

# Hacer request
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
})
session.verify = False
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

response = session.get(url, params=params, timeout=30)
response.raise_for_status()

print(f"\n✅ Respuesta recibida: {response.status_code}")
print(f"   Content-Type: {response.headers.get('Content-Type')}")
print(f"   Tamaño: {len(response.content)} bytes")

# Parsear HTML
soup = BeautifulSoup(response.content, 'html.parser')

# Buscar todas las tablas
tables = soup.find_all('table')
print(f"\n📊 Tablas encontradas: {len(tables)}")

# Analizar cada tabla
for idx, table in enumerate(tables):
    print(f"\n{'=' * 80}")
    print(f"TABLA #{idx + 1}")
    print('=' * 80)

    # Buscar headers
    thead = table.find('thead')
    if thead:
        print("\n📋 THEAD encontrado:")
        headers = [th.get_text(strip=True) for th in thead.find_all(['th', 'td'])]
        print(f"   Headers: {headers}")

    # Buscar primera fila (puede ser header)
    first_row = table.find('tr')
    if first_row:
        print("\n📋 Primera fila:")
        cells = [cell.get_text(strip=True) for cell in first_row.find_all(['th', 'td'])]
        print(f"   Celdas: {cells}")

    # Buscar tbody
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"\n📊 TBODY con {len(rows)} filas")
    else:
        rows = table.find_all('tr')
        print(f"\n📊 Tabla sin TBODY, {len(rows)} filas totales")

    # Mostrar primeras 3 filas de datos
    print("\n🔍 Primeras 3 filas de datos:")
    data_rows = rows[1:4] if len(rows) > 1 else rows[:3]  # Saltar header

    for row_idx, row in enumerate(data_rows):
        cells = row.find_all('td')
        if cells:
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            print(f"   Fila {row_idx + 1}: {cell_texts}")

    # Intentar parsear con pandas
    print("\n🐼 Intentando parsear con pandas...")
    try:
        df = pd.read_html(str(table))[0]
        print(f"   ✅ Pandas parseó exitosamente:")
        print(f"      Forma: {df.shape}")
        print(f"      Columnas: {list(df.columns)}")
        print(f"\n   Muestra de datos:")
        print(df.head(3))
    except Exception as e:
        print(f"   ❌ Pandas falló: {e}")

print("\n" + "=" * 80)
print("📝 HTML COMPLETO DE LA PRIMERA TABLA (primeros 2000 caracteres):")
print("=" * 80)
if tables:
    html_str = str(tables[0])
    print(html_str[:2000])
    if len(html_str) > 2000:
        print(f"\n... ({len(html_str) - 2000} caracteres más)")

print("\n" + "=" * 80)
print("✅ TEST COMPLETADO")
print("=" * 80)
