"""
Test DNRPA con método POST
"""
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"

# Configurar sesión
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/'
})
session.verify = False

print("=" * 80)
print("🧪 TEST DNRPA - Método POST")
print("=" * 80)

# Intentar POST
print("\n📤 Enviando POST con form data...")

data = {
    'anio': '2024',
    'codigo_tipo': 'A',
    'codigo_tramite': '3',
    'origen': 'portal_dnrpa',
    'tipo_consulta': 'inscripciones'
}

response = session.post(url, data=data, timeout=30)
print(f"✅ Respuesta: {response.status_code}")

soup = BeautifulSoup(response.content, 'html.parser')
tables = soup.find_all('table')
print(f"📊 Tablas encontradas: {len(tables)}")

for idx, table in enumerate(tables):
    print(f"\n{'=' * 80}")
    print(f"TABLA #{idx + 1}")
    print('=' * 80)

    rows = table.find_all('tr')
    print(f"Filas: {len(rows)}")

    # Mostrar primeras 5 filas
    for i, row in enumerate(rows[:5]):
        cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
        print(f"  Fila {i}: {cells[:10]}...")  # Primeras 10 celdas

print("\n" + "=" * 80)
print("✅ TEST POST COMPLETADO")
print("=" * 80)
