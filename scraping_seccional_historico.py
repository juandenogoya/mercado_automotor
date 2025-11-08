"""
Scraping histórico DNRPA - Nivel Seccional
Obtiene datos de seccionales para múltiples años y provincias

ADVERTENCIA: Este script puede tomar MUCHO tiempo
- 24 provincias × 5 años × delay 3s = ~6 minutos (sin contar tiempo de scraping)
- Se recomienda ejecutar de noche o con delay largo para evitar bloqueos

EJECUCIÓN:
# Scrapear todas las provincias, todos los años
python scraping_seccional_historico.py --anio-inicio 2020 --anio-fin 2024

# Solo algunas provincias (códigos separados por coma)
python scraping_seccional_historico.py --anio-inicio 2020 --anio-fin 2024 --provincias 01,02,04

# Con delay mayor para evitar bloqueos
python scraping_seccional_historico.py --anio-inicio 2020 --anio-fin 2024 --delay 5
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
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Mapeo de provincias (se actualizará dinámicamente)
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
    """Obtiene lista dinámica de provincias desde DNRPA"""
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

        provincia_links = soup.find_all('a', href=lambda x: x and 'tram_prov_' in x)

        provincias = {}
        for link in provincia_links:
            href = link.get('href')
            nombre = link.get_text(strip=True)

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
    """Scrapea seccionales para una provincia y año específicos"""
    # La URL siempre es tram_prov_01.php, el código de provincia va como parámetro
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
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')

        if not tables:
            print(f"      [DEBUG] No se encontraron tablas")
            return None

        print(f"      [DEBUG] {len(tables)} tablas encontradas")
        tabla_datos = max(tables, key=lambda t: len(t.find_all('tr')))
        print(f"      [DEBUG] Tabla más grande tiene {len(tabla_datos.find_all('tr'))} filas")

        if len(tabla_datos.find_all('tr')) < 2:
            print(f"      [DEBUG] Tabla tiene menos de 2 filas")
            return None

        # Extraer headers
        header_row = tabla_datos.find('tr')
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        print(f"      [DEBUG] Headers: {headers[:5]}...")  # Primeros 5

        # Extraer datos
        rows_data = []
        for row in tabla_datos.find_all('tr')[1:]:
            cells = row.find_all('td')
            if not cells:
                continue

            row_data = []
            for cell in cells:
                text = cell.get_text(strip=True)
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

        print(f"      [DEBUG] {len(rows_data)} filas de datos extraídas")

        if not rows_data:
            print(f"      [DEBUG] rows_data está vacío")
            return None

        df = pd.DataFrame(rows_data, columns=headers)

        # Agregar metadata
        df['provincia_codigo'] = codigo_provincia
        df['anio'] = anio
        df['tipo_vehiculo'] = 'Autos' if codigo_tipo == 'A' else codigo_tipo
        df['fecha_scraping'] = datetime.now()

        return df

    except Exception as e:
        return None


def guardar_checkpoint(data, checkpoint_file):
    """Guarda checkpoint con información de progreso"""
    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)


def cargar_checkpoint(checkpoint_file):
    """Carga checkpoint si existe"""
    try:
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def main():
    parser = argparse.ArgumentParser(description='Scraping histórico DNRPA - Nivel Seccional')
    parser.add_argument('--anio-inicio', type=int, default=2020, help='Año inicial (default: 2020)')
    parser.add_argument('--anio-fin', type=int, default=2024, help='Año final (default: 2024)')
    parser.add_argument('--provincias', type=str, default=None,
                        help='Códigos de provincias separados por coma (ej: 01,02,04). Si no se especifica, scrapea todas')
    parser.add_argument('--tipo-vehiculo', type=str, default='A', choices=['A', 'M', 'C', 'O'],
                        help='Tipo de vehículo: A=Autos, M=Motos, C=Camiones, O=Otros')
    parser.add_argument('--delay', type=int, default=3,
                        help='Segundos de espera entre requests (default: 3, recomendado: 5)')
    parser.add_argument('--output-dir', type=str, default='datos_seccionales',
                        help='Directorio de salida (default: datos_seccionales)')
    parser.add_argument('--continuar', action='store_true',
                        help='Continuar desde el último checkpoint')

    args = parser.parse_args()

    print("=" * 80)
    print("🚗 SCRAPING HISTÓRICO DNRPA - NIVEL SECCIONAL")
    print("=" * 80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Años: {args.anio_inicio} - {args.anio_fin}")
    print(f"🚙 Tipo vehículo: {args.tipo_vehiculo}")
    print(f"⏱️  Delay: {args.delay}s")
    print("=" * 80)

    # Crear directorio de salida
    output_path = Path(args.output_dir)
    output_path.mkdir(exist_ok=True)

    # Obtener provincias
    print("\n📥 Obteniendo lista de provincias...")
    provincias = obtener_provincias_con_codigos()

    # Filtrar provincias si se especificaron
    if args.provincias:
        # Normalizar códigos a 2 dígitos con cero inicial
        codigos_filtro = [c.strip().zfill(2) for c in args.provincias.split(',')]
        # Normalizar claves del diccionario también
        provincias_normalizadas = {k.zfill(2): v for k, v in provincias.items()}
        provincias = {k: v for k, v in provincias_normalizadas.items() if k in codigos_filtro}

        if not provincias:
            print(f"❌ ERROR: No se encontraron las provincias especificadas: {args.provincias}")
            print(f"   Provincias disponibles: {', '.join(sorted(provincias_normalizadas.keys()))}")
            sys.exit(1)

        print(f"🎯 Filtrando {len(provincias)} provincias: {', '.join(provincias.values())}")
    else:
        # Normalizar todas las claves a 2 dígitos
        provincias = {k.zfill(2): v for k, v in provincias.items()}
        print(f"✅ {len(provincias)} provincias encontradas")

    # Checkpoint
    checkpoint_file = output_path / 'checkpoint_seccional.json'
    checkpoint = cargar_checkpoint(checkpoint_file) if args.continuar else None

    if checkpoint:
        print(f"\n♻️  Continuando desde checkpoint: Año {checkpoint['ultimo_anio']}, Provincia {checkpoint['ultima_provincia']}")

    # Calcular total de requests
    total_años = args.anio_fin - args.anio_inicio + 1
    total_provincias = len(provincias)
    total_requests = total_años * total_provincias
    tiempo_estimado = (total_requests * args.delay) / 60

    print(f"\n⚠️  ADVERTENCIA:")
    print(f"   Total de requests: {total_requests} ({total_años} años × {total_provincias} provincias)")
    print(f"   Tiempo estimado: ~{tiempo_estimado:.1f} minutos (solo delays)")
    print(f"   Se recomienda ejecutar con --delay 5 o mayor para evitar bloqueos")

    input("\n   Presiona ENTER para continuar o Ctrl+C para cancelar...")

    # Variables de progreso
    dfs_todos = []
    stats = {
        'exitosos': 0,
        'fallidos': 0,
        'total_seccionales': 0
    }

    # Iterar por años y provincias
    for anio in range(args.anio_inicio, args.anio_fin + 1):
        # Saltar si ya se procesó en checkpoint
        if checkpoint and anio < checkpoint.get('ultimo_anio', 0):
            continue

        print(f"\n{'=' * 80}")
        print(f"📅 AÑO {anio}")
        print('=' * 80)

        for codigo, nombre in provincias.items():
            # Saltar si ya se procesó en checkpoint
            if checkpoint and anio == checkpoint.get('ultimo_anio', 0) and codigo <= checkpoint.get('ultima_provincia', '00'):
                continue

            print(f"\n   📍 {nombre} ({codigo})...", end=' ')

            df = scrapear_seccional_provincia(codigo, anio, args.tipo_vehiculo)

            if df is not None and not df.empty:
                dfs_todos.append(df)
                stats['exitosos'] += 1
                stats['total_seccionales'] += len(df)
                print(f"✅ {len(df)} seccionales")
            else:
                stats['fallidos'] += 1
                print("❌ Sin datos")

            # Guardar checkpoint cada 5 provincias
            if stats['exitosos'] % 5 == 0:
                checkpoint_data = {
                    'ultimo_anio': anio,
                    'ultima_provincia': codigo,
                    'stats': stats,
                    'timestamp': datetime.now().isoformat()
                }
                guardar_checkpoint(checkpoint_data, checkpoint_file)

                # Guardar checkpoint de datos también
                if dfs_todos:
                    df_temp = pd.concat(dfs_todos, ignore_index=True)
                    checkpoint_excel = output_path / f'checkpoint_datos_{anio}_{codigo}.xlsx'
                    df_temp.to_excel(checkpoint_excel, index=False)
                    print(f"      💾 Checkpoint guardado ({len(dfs_todos)} provincias)")

            # Delay entre requests
            time.sleep(args.delay)

        print(f"\n   ✅ Año {anio} completado: {stats['exitosos']} exitosos, {stats['fallidos']} fallidos")

    # Verificar si se obtuvieron datos
    if not dfs_todos:
        print("\n❌ ERROR: No se obtuvieron datos")
        sys.exit(1)

    # Combinar todos los datos
    print(f"\n📊 Combinando datos de {len(dfs_todos)} scrapes...")
    df_final = pd.concat(dfs_todos, ignore_index=True)

    # Guardar archivo final
    output_file = output_path / f"patentamientos_seccional_{args.anio_inicio}_{args.anio_fin}_consolidado.xlsx"
    df_final.to_excel(output_file, index=False, sheet_name='Todos')

    # Eliminar checkpoint al finalizar exitosamente
    if checkpoint_file.exists():
        checkpoint_file.unlink()

    print("\n" + "=" * 80)
    print("✅ SCRAPING HISTÓRICO COMPLETADO")
    print("=" * 80)
    print(f"💾 Archivo: {output_file}")
    print(f"📊 Total de seccionales: {len(df_final)}")
    print(f"📅 Años: {sorted(df_final['anio'].unique())}")
    print(f"📍 Provincias: {len(df_final['provincia_codigo'].unique())}")
    print(f"✅ Exitosos: {stats['exitosos']}")
    print(f"❌ Fallidos: {stats['fallidos']}")

    # Estadísticas por año
    print("\n📈 SECCIONALES POR AÑO:")
    print("-" * 80)
    for anio in sorted(df_final['anio'].unique()):
        df_anio = df_final[df_final['anio'] == anio]
        count = len(df_anio)
        provincias_count = df_anio['provincia_codigo'].nunique()
        print(f"  {anio}: {count:>4} seccionales ({provincias_count} provincias)")

    # Estadísticas por provincia
    print("\n📍 TOP 10 PROVINCIAS POR CANTIDAD DE SECCIONALES:")
    print("-" * 80)
    top_provincias = df_final.groupby('provincia_codigo').size().sort_values(ascending=False).head(10)
    for codigo, count in top_provincias.items():
        nombre_prov = provincias.get(codigo, codigo)
        # Contar seccionales únicos (por nombre de primera columna)
        seccionales_unicos = df_final[df_final['provincia_codigo'] == codigo][df_final.columns[0]].nunique()
        print(f"  {nombre_prov}: {seccionales_unicos} seccionales únicos ({count} registros)")

    print("\n" + "=" * 80)
    print("🎯 Próximos pasos:")
    print("  1. Verificar archivo Excel generado")
    print("  2. Crear esquema de BD: psql < backend/models/schema_patentamientos.sql")
    print("  3. Cargar datos a PostgreSQL")
    print("  4. Actualizar dashboard Streamlit")
    print("=" * 80)


if __name__ == "__main__":
    main()
