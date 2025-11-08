"""
Script para ejecutar desde PC LOCAL (IP residencial)
Scraping de DNRPA - Patentamientos por provincia

INSTRUCCIONES:
1. Instalar dependencias: pip install requests beautifulsoup4 pandas openpyxl
2. Ejecutar: python scraping_local_dnrpa.py
3. Los datos se guardarán en un archivo Excel: patentamientos_YYYY.xlsx
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
from datetime import datetime
import sys

# Deshabilitar warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("=" * 80)
print("🚗 SCRAPING DNRPA - PATENTAMIENTOS")
print("=" * 80)
print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"💻 Ejecutando desde: PC Local (IP residencial)")
print("=" * 80)

# Configurar año a scrapear
ANIO = 2024

print(f"\n📊 Obteniendo datos de patentamientos para el año {ANIO}...")

# URL y parámetros
url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"

# Datos del formulario POST (capturados del navegador)
data = {
    'anio': str(ANIO),
    'codigo_tipo': 'A',  # A = Autos
    'operacion': '1',  # ¡CRÍTICO!
    'origen': 'portal_dnrpa',
    'tipo_consulta': 'inscripciones',
    'boton': 'Aceptar'
}

# Crear sesión con headers de navegador real
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
})
session.verify = False

try:
    # PASO 1: Cargar página inicial para obtener cookies
    print("\n📥 Paso 1/3: Cargando página inicial para obtener cookies...")
    initial_url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php?origen=portal_dnrpa&tipo_consulta=inscripciones"
    initial_response = session.get(initial_url, timeout=30)

    if initial_response.status_code == 403:
        print("❌ ERROR: El servidor bloqueó la conexión con código 403")
        print("   Posibles causas:")
        print("   - Tu IP también está bloqueada")
        print("   - Necesitas VPN o proxy")
        print("   - El sitio requiere JavaScript/navegador real (Selenium)")
        sys.exit(1)

    print(f"   ✅ Status: {initial_response.status_code}")
    print(f"   🍪 Cookies recibidas: {len(session.cookies)}")

    # PASO 2: Enviar POST con datos del formulario
    print("\n📤 Paso 2/3: Enviando POST con datos del formulario...")
    session.headers.update({
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.dnrpa.gov.ar',
        'Referer': initial_url
    })

    response = session.post(url, data=data, timeout=30)
    print(f"   ✅ Status: {response.status_code}")

    if response.status_code != 200:
        print(f"❌ ERROR: Respuesta inesperada del servidor: {response.status_code}")
        sys.exit(1)

    # PASO 3: Parsear HTML y extraer datos
    print("\n🔍 Paso 3/3: Parseando datos...")
    soup = BeautifulSoup(response.content, 'html.parser')

    # Buscar enlaces de provincias
    provincia_links = soup.find_all('a', href=lambda x: x and 'tram_prov_' in x)
    print(f"   📍 Provincias encontradas: {len(provincia_links)}")

    if len(provincia_links) == 0:
        print("❌ ERROR: No se encontraron datos de provincias")
        print("   El servidor puede estar bloqueando o la estructura cambió")
        # Guardar HTML para debug
        with open('dnrpa_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("   💾 HTML guardado en: dnrpa_debug.html (para análisis)")
        sys.exit(1)

    # Buscar la tabla con datos
    tabla_datos = None
    for table in soup.find_all('table'):
        if table.find('a', href=lambda x: x and 'tram_prov_' in x):
            tabla_datos = table
            break

    if not tabla_datos:
        print("❌ ERROR: No se encontró la tabla con datos")
        sys.exit(1)

    # Extraer datos de la tabla
    print("\n📊 Extrayendo datos de la tabla...")

    # Headers
    header_row = tabla_datos.find('tr')
    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
    print(f"   📋 Columnas: {headers[:5]}...")  # Primeras 5

    # Datos
    rows_data = []
    for row in tabla_datos.find_all('tr')[1:]:  # Saltar header
        cells = row.find_all('td')
        if not cells:
            continue

        row_data = []
        for cell in cells:
            # Si tiene enlace, es provincia
            link = cell.find('a')
            if link:
                row_data.append(link.get_text(strip=True))
            else:
                # Es número
                text = cell.get_text(strip=True)
                # Limpiar formato argentino: 1.234 -> 1234
                text_clean = text.replace('.', '').replace(',', '.')
                try:
                    value = float(text_clean) if text_clean else 0
                    # Convertir a int si es entero
                    if value == int(value):
                        row_data.append(int(value))
                    else:
                        row_data.append(value)
                except ValueError:
                    row_data.append(text)

        if row_data:
            rows_data.append(row_data)

    print(f"   ✅ Filas extraídas: {len(rows_data)}")

    # Crear DataFrame
    df = pd.DataFrame(rows_data, columns=headers)

    print("\n📈 DATOS OBTENIDOS:")
    print("=" * 80)
    print(f"Forma del DataFrame: {df.shape}")
    print(f"\nPrimeras 5 provincias:")
    print(df.head(5).to_string())

    # Guardar a Excel
    filename = f"patentamientos_{ANIO}.xlsx"
    df.to_excel(filename, index=False, sheet_name=f'Autos_{ANIO}')
    print(f"\n💾 Datos guardados en: {filename}")

    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS:")
    print("=" * 80)
    total_col = 'Total' if 'Total' in df.columns else df.columns[-1]
    if total_col in df.columns:
        total_general = df[total_col].sum()
        print(f"Total de patentamientos {ANIO}: {total_general:,}")
        print(f"\nTop 5 provincias con más patentamientos:")
        top5 = df.nlargest(5, total_col)
        for idx, row in top5.iterrows():
            prov = row[df.columns[0]]
            total = row[total_col]
            print(f"  {idx+1}. {prov}: {total:,}")

    print("\n" + "=" * 80)
    print("✅ SCRAPING COMPLETADO EXITOSAMENTE")
    print("=" * 80)
    print("\nPróximos pasos:")
    print("1. Verificar el archivo Excel generado")
    print("2. Ejecutar script de carga a PostgreSQL (si existe)")
    print("3. Repetir para otros años si es necesario")

except requests.exceptions.Timeout:
    print("\n❌ ERROR: Timeout al conectar con DNRPA")
    print("   El servidor tardó demasiado en responder")
    sys.exit(1)

except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: No se pudo conectar con DNRPA")
    print("   Verificar conexión a internet")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR INESPERADO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
