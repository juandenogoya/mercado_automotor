"""
Test acceso directo a datos DNRPA
Probando diferentes combinaciones de parámetros
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9'
})
session.verify = False

print("=" * 80)
print("🧪 TEST DNRPA - Acceso Directo a Datos")
print("=" * 80)

# OPCIÓN 1: Sin parámetros extra
print("\n🔬 OPCIÓN 1: URL base con parámetros mínimos")
print("-" * 80)

url1 = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"
params1 = {
    'anio': 2024,
    'codigo_tipo': 'A',
    'codigo_tramite': 3
}

response1 = session.get(url1, params=params1)
print(f"URL completa: {response1.url}")
print(f"Status: {response1.status_code}")

soup1 = BeautifulSoup(response1.content, 'html.parser')
tables1 = soup1.find_all('table')
print(f"Tablas encontradas: {len(tables1)}")

if tables1:
    # Buscar tabla con datos (no formulario)
    for idx, table in enumerate(tables1):
        rows = table.find_all('tr')
        if len(rows) > 5:  # Tabla con contenido sustancial
            print(f"\n✅ Tabla #{idx+1} tiene {len(rows)} filas (posiblemente datos)")

            # Mostrar estructura
            first_row = rows[0].find_all(['th', 'td'])
            print(f"   Primera fila: {[c.get_text(strip=True) for c in first_row[:5]]}")

            if len(rows) > 1:
                second_row = rows[1].find_all(['th', 'td'])
                print(f"   Segunda fila: {[c.get_text(strip=True) for c in second_row[:5]]}")

# OPCIÓN 2: Simular click en "Aceptar" del formulario
print("\n\n🔬 OPCIÓN 2: Simulando submit de formulario")
print("-" * 80)

# Primero cargar la página del formulario
response_form = session.get("https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php")

# Ahora hacer la consulta
url2 = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"

# Probar sin origen ni tipo_consulta
params2 = {
    'c_provincia': '',  # Vacío para resumen
    'anio': '2024',
    'codigo_tipo': 'A',
    'codigo_tramite': '3'
}

response2 = session.get(url2, params=params2)
print(f"URL completa: {response2.url}")
print(f"Status: {response2.status_code}")

soup2 = BeautifulSoup(response2.content, 'html.parser')
tables2 = soup2.find_all('table')
print(f"Tablas encontradas: {len(tables2)}")

# OPCIÓN 3: Buscar si hay iframe o JavaScript que carga datos
print("\n\n🔬 OPCIÓN 3: Buscando iframes o scripts")
print("-" * 80)

iframes = soup1.find_all('iframe')
scripts = soup1.find_all('script')
print(f"iframes: {len(iframes)}")
print(f"scripts: {len(scripts)}")

if scripts:
    print("\nScripts encontrados:")
    for idx, script in enumerate(scripts[:3]):
        script_text = script.get_text()[:200] if script.get_text() else script.get('src', 'inline')
        print(f"  Script {idx+1}: {script_text}...")

# OPCIÓN 4: Guardar HTML completo para inspección
print("\n\n📄 Guardando HTML para inspección...")
with open('dnrpa_response.html', 'w', encoding='utf-8') as f:
    f.write(soup1.prettify())
print("✅ Guardado en: dnrpa_response.html")

print("\n" + "=" * 80)
print("💡 PRÓXIMO PASO:")
print("   Abrí dnrpa_response.html en un navegador y comparalo")
print("   con lo que ves cuando accedes manualmente a DNRPA")
print("=" * 80)
