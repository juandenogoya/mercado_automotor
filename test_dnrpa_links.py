"""
Test DNRPA - Buscar tabla correcta con enlaces de provincias
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"

# Usar POST como el navegador real (capturado con cURL)
data = {
    'anio': '2024',
    'codigo_tipo': 'A',
    'operacion': '1',  # ¡CRÍTICO!
    'origen': 'portal_dnrpa',
    'tipo_consulta': 'inscripciones',
    'boton': 'Aceptar'
}

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
})
session.verify = False

print("=" * 80)
print("🔍 DNRPA - Buscando tabla con enlaces de provincias")
print("=" * 80)

# PASO 1: Primero cargar la página inicial para obtener cookies
print("📥 Paso 1: Cargando página inicial para obtener cookies...")
initial_url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php?origen=portal_dnrpa&tipo_consulta=inscripciones"
initial_response = session.get(initial_url)
print(f"   Status: {initial_response.status_code}")
print(f"   Cookies: {len(session.cookies)} cookies recibidas")

# PASO 2: Ahora hacer el POST con las cookies
print("\n📤 Paso 2: Enviando POST con datos del formulario")
print(f"   Data: {data}")

# Actualizar headers para el POST
session.headers.update({
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://www.dnrpa.gov.ar',
    'Referer': initial_url
})

response = session.post(url, data=data)
print(f"✅ Respuesta: {response.status_code}")

soup = BeautifulSoup(response.content, 'html.parser')

# Buscar TODOS los enlaces que contengan "tram_prov_"
print("\n🔗 Buscando enlaces de provincias...")
provincia_links = soup.find_all('a', href=lambda x: x and 'tram_prov_' in x)
print(f"✅ Encontrados {len(provincia_links)} enlaces de provincias")

if provincia_links:
    print("\n📋 Primeros 5 enlaces:")
    for link in provincia_links[:5]:
        provincia = link.get_text(strip=True)
        href = link.get('href')
        print(f"  • {provincia}: {href}")

# Buscar la tabla que contiene estos enlaces
print("\n\n📊 Buscando tabla que contiene los enlaces...")
tables = soup.find_all('table')
print(f"Total de tablas: {len(tables)}")

for idx, table in enumerate(tables):
    # Ver si esta tabla tiene enlaces de provincias
    links_in_table = table.find_all('a', href=lambda x: x and 'tram_prov_' in x)

    if links_in_table:
        print(f"\n{'=' * 80}")
        print(f"✅ TABLA #{idx + 1} - CONTIENE {len(links_in_table)} ENLACES DE PROVINCIAS")
        print('=' * 80)

        # Analizar estructura
        rows = table.find_all('tr')
        print(f"\nFilas totales: {len(rows)}")

        # Buscar fila de headers (probablemente la primera)
        print("\n📋 ESTRUCTURA DE LA TABLA:")
        for row_idx, row in enumerate(rows[:3]):  # Primeras 3 filas
            cells = row.find_all(['th', 'td'])
            print(f"\n  Fila {row_idx}:")
            print(f"    Tipo de celdas: {[cell.name for cell in cells]}")
            print(f"    Cantidad: {len(cells)}")

            # Extraer contenido
            cell_contents = []
            for cell in cells:
                # Si tiene enlace, extraer texto del enlace
                link = cell.find('a')
                if link:
                    cell_contents.append(f"[LINK: {link.get_text(strip=True)}]")
                else:
                    cell_contents.append(cell.get_text(strip=True))

            print(f"    Contenido: {cell_contents[:15]}")  # Primeras 15 celdas

        # Intentar parsear con pandas
        print("\n\n🐼 Parseando tabla con pandas...")
        try:
            # Convertir tabla a string y parsear
            from io import StringIO
            df = pd.read_html(StringIO(str(table)))[0]

            print(f"  ✅ Forma del DataFrame: {df.shape}")
            print(f"  📋 Columnas: {list(df.columns)}")
            print(f"\n  📊 Primeras 3 filas:")
            print(df.head(3).to_string())

        except Exception as e:
            print(f"  ❌ Error con pandas: {e}")

        # Extraer manualmente los datos
        print("\n\n🔧 EXTRACCIÓN MANUAL:")
        print("-" * 80)

        data_rows = []
        for row in rows[1:]:  # Saltar header
            cells = row.find_all('td')
            if not cells:
                continue

            row_data = []
            for cell in cells:
                link = cell.find('a')
                if link:
                    # Es provincia (con enlace)
                    row_data.append(link.get_text(strip=True))
                else:
                    # Es número
                    text = cell.get_text(strip=True)
                    # Limpiar separadores de miles
                    text_clean = text.replace('.', '').replace(',', '.')
                    try:
                        row_data.append(int(float(text_clean)) if text_clean else 0)
                    except:
                        row_data.append(text)

            if row_data:
                data_rows.append(row_data)

        print(f"Filas extraídas: {len(data_rows)}")
        if data_rows:
            print("\nPrimeras 3 provincias:")
            for i, row in enumerate(data_rows[:3]):
                print(f"  {i+1}. {row[:5]}...")  # Primeros 5 valores

print("\n" + "=" * 80)
print("✅ ANÁLISIS COMPLETADO")
print("=" * 80)
