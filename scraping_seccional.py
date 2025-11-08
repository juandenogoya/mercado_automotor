"""
Scraping DNRPA - Nivel Seccional
Obtiene datos de patentamientos por registro seccional dentro de cada provincia

EJECUCIÓN:
# Scrapear todas las provincias para un año
python scraping_seccional.py --anio 2024

# Scrapear solo una provincia
python scraping_seccional.py --anio 2024 --provincia 01

# Con delay mayor para evitar bloqueos
python scraping_seccional.py --anio 2024 --delay 5
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib3
from datetime import datetime
import sys
import time
import argparse
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Mapeo de códigos de provincia (se actualizará al scrapear)
CODIGOS_PROVINCIA = {
    '01': 'BUENOS AIRES',
    '02': 'C.AUTONOMA DE BS.AS',
    '03': 'CATAMARCA',
    '04': 'CORDOBA',
    '05': 'CORRIENTES',
    '06': 'CHACO',
    '07': 'CHUBUT',
    '08': 'ENTRE RIOS',
    '09': 'FORMOSA',
    '10': 'JUJUY',
    '11': 'LA PAMPA',
    '12': 'LA RIOJA',
    '13': 'MENDOZA',
    '14': 'MISIONES',
    '15': 'NEUQUEN',
    '16': 'RIO NEGRO',
    '17': 'SALTA',
    '18': 'SAN JUAN',
    '19': 'SAN LUIS',
    '20': 'SANTA CRUZ',
    '21': 'SANTA FE',
    '22': 'SANTIAGO DEL ESTERO',
    '23': 'TIERRA DEL FUEGO',
    '24': 'TUCUMAN'
}

def obtener_provincias_con_codigos():
    """
    Obtiene la lista de provincias con sus códigos desde DNRPA

    Returns:
        dict: {codigo: nombre_provincia}
    """
    url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"

    data = {
        'anio': '2024',
        'codigo_tipo': 'A',
        'operacion': '1',
        'origen': 'portal_dnrpa',
        'tipo_consulta': 'inscripciones',
        'boton': 'Aceptar'
    }

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9',
        'DNT': '1'
    })
    session.verify = False

    try:
        initial_url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php?origen=portal_dnrpa&tipo_consulta=inscripciones"
        initial_response = session.get(initial_url, timeout=30)

        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.dnrpa.gov.ar',
            'Referer': initial_url
        })

        response = session.post(url, data=data, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar enlaces de provincias
        provincia_links = soup.find_all('a', href=lambda x: x and 'tram_prov_' in x)

        provincias = {}
        for link in provincia_links:
            href = link.get('href')
            nombre = link.get_text(strip=True)

            # Extraer código de provincia del href
            # Ejemplo: tram_prov_01.php?c_provincia=01&...
            if 'c_provincia=' in href:
                codigo = href.split('c_provincia=')[1].split('&')[0]
                provincias[codigo] = nombre

        # Si no se encontraron provincias, usar predefinidas
        if not provincias:
            print(f"⚠️ No se encontraron provincias dinámicamente")
            print("   Usando lista predefinida")
            return CODIGOS_PROVINCIA

        return provincias

    except Exception as e:
        print(f"⚠️ Error al obtener provincias: {e}")
        print("   Usando lista predefinida")
        return CODIGOS_PROVINCIA


def scrapear_seccional_provincia(codigo_provincia, anio, codigo_tipo='A'):
    """
    Scrapea datos de seccionales para una provincia específica

    Args:
        codigo_provincia: Código de 2 dígitos (ej: '01', '02')
        anio: Año a scrapear
        codigo_tipo: Tipo de vehículo (A=Autos, M=Motos, etc.)

    Returns:
        DataFrame con datos o None si falla
    """
    # URL para nivel seccional (siempre es tram_prov_01.php, el código va como parámetro)
    url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov_01.php"

    params = {
        'c_provincia': codigo_provincia,
        'codigo_tipo': codigo_tipo,
        'anio': str(anio),
        'codigo_tramite': '3',  # 3 = Inscripciones (dato del cURL real)
        'provincia': codigo_provincia,  # También se envía como 'provincia'
        'origen': 'portal_dnrpa'
    }

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Referer': 'https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    })
    session.verify = False

    try:
        # Primero obtener cookies de la página principal
        initial_url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php?origen=portal_dnrpa&tipo_consulta=inscripciones"
        try:
            session.get(initial_url, timeout=10)
        except:
            pass  # Continuar aunque falle la obtención de cookies

        # Ahora hacer el request de seccional
        response = session.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"   ❌ Error {response.status_code}")
            if response.status_code == 404:
                print(f"   URL intentada: {response.url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar tabla con datos de seccionales
        tables = soup.find_all('table')

        if not tables:
            print(f"   ⚠️ No se encontraron tablas")
            return None

        print(f"   [DEBUG] {len(tables)} tablas encontradas")
        # La tabla con datos suele ser la que tiene más filas
        tabla_datos = max(tables, key=lambda t: len(t.find_all('tr')))
        print(f"   [DEBUG] Tabla más grande tiene {len(tabla_datos.find_all('tr'))} filas")

        if len(tabla_datos.find_all('tr')) < 2:
            print(f"   ⚠️ Tabla vacía o sin datos")
            return None

        # Extraer headers
        header_row = tabla_datos.find('tr')
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        print(f"   [DEBUG] Headers: {headers[:5]}...")  # Primeros 5

        # Extraer datos
        rows_data = []
        for row in tabla_datos.find_all('tr')[1:]:
            cells = row.find_all('td')
            if not cells:
                continue

            row_data = []
            for cell in cells:
                text = cell.get_text(strip=True)
                # Limpiar formato argentino: 1.234 -> 1234
                text_clean = text.replace('.', '').replace(',', '.')
                try:
                    value = float(text_clean) if text_clean else 0
                    if value == int(value):
                        row_data.append(int(value))
                    else:
                        row_data.append(value)
                except ValueError:
                    row_data.append(text)

            if row_data:
                rows_data.append(row_data)

        print(f"   [DEBUG] {len(rows_data)} filas de datos extraídas")

        if not rows_data:
            print(f"   ⚠️ No se extrajeron datos")
            return None

        # Crear DataFrame
        df = pd.DataFrame(rows_data, columns=headers)

        # Agregar metadata
        df['provincia_codigo'] = codigo_provincia
        df['anio'] = anio
        df['tipo_vehiculo'] = 'Autos' if codigo_tipo == 'A' else codigo_tipo
        df['fecha_scraping'] = datetime.now()

        print(f"   ✅ {len(df)} seccionales obtenidas")
        return df

    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Scraping DNRPA - Nivel Seccional')
    parser.add_argument('--anio', type=int, required=True, help='Año a scrapear')
    parser.add_argument('--provincia', type=str, default=None,
                        help='Código de provincia (01-24). Si no se especifica, scrapea todas')
    parser.add_argument('--tipo-vehiculo', type=str, default='A', choices=['A', 'M', 'C', 'O'],
                        help='Tipo de vehículo: A=Autos, M=Motos, C=Camiones, O=Otros')
    parser.add_argument('--delay', type=int, default=3,
                        help='Segundos de espera entre requests (default: 3)')
    parser.add_argument('--output-dir', type=str, default='.',
                        help='Directorio de salida para archivos (default: directorio actual)')

    args = parser.parse_args()

    print("=" * 80)
    print("🚗 SCRAPING DNRPA - NIVEL SECCIONAL")
    print("=" * 80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Año: {args.anio}")
    print(f"🚙 Tipo vehículo: {args.tipo_vehiculo}")
    print(f"⏱️  Delay entre requests: {args.delay}s")
    print("=" * 80)

    # Obtener lista de provincias
    print("\n📥 Obteniendo lista de provincias...")
    provincias = obtener_provincias_con_codigos()
    print(f"✅ {len(provincias)} provincias encontradas")

    # Filtrar si se especificó una provincia
    if args.provincia:
        if args.provincia in provincias:
            provincias = {args.provincia: provincias[args.provincia]}
            print(f"🎯 Filtrando solo: {provincias[args.provincia]}")
        else:
            print(f"❌ Código de provincia inválido: {args.provincia}")
            sys.exit(1)

    # Crear directorio de salida
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    # Scrapear cada provincia
    dfs_todas_provincias = []
    provincias_exitosas = 0
    provincias_fallidas = 0

    for codigo, nombre in provincias.items():
        print(f"\n📍 Provincia: {nombre} ({codigo})")

        df = scrapear_seccional_provincia(codigo, args.anio, args.tipo_vehiculo)

        if df is not None and not df.empty:
            dfs_todas_provincias.append(df)
            provincias_exitosas += 1

            # Guardar archivo individual por provincia
            filename = f"seccional_{nombre.replace(' ', '_')}_{args.anio}.xlsx"
            filepath = output_path / filename
            df.to_excel(filepath, index=False)
            print(f"   💾 Guardado: {filename}")
        else:
            provincias_fallidas += 1

        # Delay entre provincias
        if codigo != list(provincias.keys())[-1]:  # No esperar después de la última
            print(f"   ⏳ Esperando {args.delay}s...")
            time.sleep(args.delay)

    # Combinar todos los datos
    if dfs_todas_provincias:
        print(f"\n📊 Combinando datos de {len(dfs_todas_provincias)} provincias...")
        df_final = pd.concat(dfs_todas_provincias, ignore_index=True)

        # Guardar archivo consolidado
        output_file = output_path / f"patentamientos_seccional_{args.anio}_consolidado.xlsx"
        df_final.to_excel(output_file, index=False, sheet_name='Todos')

        print("\n" + "=" * 80)
        print("✅ SCRAPING COMPLETADO")
        print("=" * 80)
        print(f"💾 Archivo consolidado: {output_file}")
        print(f"📊 Total de seccionales: {len(df_final)}")
        print(f"✅ Provincias exitosas: {provincias_exitosas}")
        print(f"❌ Provincias fallidas: {provincias_fallidas}")

        # Estadísticas por provincia
        print("\n📈 SECCIONALES POR PROVINCIA:")
        print("-" * 80)
        for codigo in sorted(df_final['provincia_codigo'].unique()):
            df_prov = df_final[df_final['provincia_codigo'] == codigo]
            nombre_prov = provincias.get(codigo, codigo)
            count = len(df_prov)
            print(f"  {nombre_prov}: {count} seccionales")

        print("\n" + "=" * 80)
        print("🎯 Próximos pasos:")
        print("  1. Verificar archivos Excel generados")
        print("  2. Repetir para otros años si es necesario")
        print("  3. Cargar datos a PostgreSQL")
        print("=" * 80)

    else:
        print("\n❌ ERROR: No se obtuvieron datos de ninguna provincia")
        sys.exit(1)


if __name__ == "__main__":
    main()
