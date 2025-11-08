"""
Scraping histórico de DNRPA - Nivel Provincial
Obtiene datos de patentamientos por provincia para múltiples años

EJECUCIÓN:
python scraping_provincial_historico.py --anio-inicio 2020 --anio-fin 2024
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

# Configuración
TIPOS_VEHICULO = {
    'A': 'Autos',
    'M': 'Motos',
    'C': 'Camiones',
    'O': 'Otros'
}

def scrapear_provincia_anio(anio, codigo_tipo='A'):
    """
    Scrapea datos de provincias para un año y tipo de vehículo específico

    Returns:
        DataFrame con datos o None si falla
    """
    url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php"

    data = {
        'anio': str(anio),
        'codigo_tipo': codigo_tipo,
        'operacion': '1',
        'origen': 'portal_dnrpa',
        'tipo_consulta': 'inscripciones',
        'boton': 'Aceptar'
    }

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'es-AR,es;q=0.9,en;q=0.8',
        'DNT': '1',
        'Connection': 'keep-alive'
    })
    session.verify = False

    try:
        # Obtener cookies
        initial_url = "https://www.dnrpa.gov.ar/portal_dnrpa/estadisticas/rrss_tramites/tram_prov.php?origen=portal_dnrpa&tipo_consulta=inscripciones"
        initial_response = session.get(initial_url, timeout=30)

        if initial_response.status_code == 403:
            print(f"   ❌ Error 403 al obtener cookies para {anio}")
            return None

        # POST con datos
        session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.dnrpa.gov.ar',
            'Referer': initial_url
        })

        response = session.post(url, data=data, timeout=30)

        if response.status_code != 200:
            print(f"   ❌ Error {response.status_code} para {anio}")
            return None

        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar tabla con datos
        tabla_datos = None
        for table in soup.find_all('table'):
            if table.find('a', href=lambda x: x and 'tram_prov_' in x):
                tabla_datos = table
                break

        if not tabla_datos:
            print(f"   ❌ No se encontró tabla de datos para {anio}")
            return None

        # Extraer datos
        header_row = tabla_datos.find('tr')
        headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]

        rows_data = []
        for row in tabla_datos.find_all('tr')[1:]:
            cells = row.find_all('td')
            if not cells:
                continue

            row_data = []
            for cell in cells:
                link = cell.find('a')
                if link:
                    row_data.append(link.get_text(strip=True))
                else:
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

        if not rows_data:
            print(f"   ❌ No se extrajeron datos para {anio}")
            return None

        # Crear DataFrame
        df = pd.DataFrame(rows_data, columns=headers)

        # Agregar columnas de metadata
        df['anio'] = anio
        df['tipo_vehiculo'] = TIPOS_VEHICULO[codigo_tipo]
        df['fecha_scraping'] = datetime.now()

        print(f"   ✅ {anio}: {len(df)} provincias obtenidas")
        return df

    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout para {anio}")
        return None
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Error de conexión para {anio}")
        return None
    except Exception as e:
        print(f"   ❌ Error inesperado para {anio}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Scraping histórico DNRPA - Nivel Provincial')
    parser.add_argument('--anio-inicio', type=int, default=2020, help='Año inicial (default: 2020)')
    parser.add_argument('--anio-fin', type=int, default=2024, help='Año final (default: 2024)')
    parser.add_argument('--tipo-vehiculo', type=str, default='A', choices=['A', 'M', 'C', 'O'],
                        help='Tipo de vehículo: A=Autos, M=Motos, C=Camiones, O=Otros (default: A)')
    parser.add_argument('--delay', type=int, default=3, help='Segundos de espera entre requests (default: 3)')

    args = parser.parse_args()

    print("=" * 80)
    print("🚗 SCRAPING HISTÓRICO DNRPA - NIVEL PROVINCIAL")
    print("=" * 80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Años: {args.anio_inicio} - {args.anio_fin}")
    print(f"🚙 Tipo vehículo: {TIPOS_VEHICULO[args.tipo_vehiculo]}")
    print(f"⏱️  Delay entre requests: {args.delay}s")
    print("=" * 80)

    # Lista para almacenar todos los DataFrames
    dfs_historicos = []

    # Iterar por cada año
    for anio in range(args.anio_inicio, args.anio_fin + 1):
        print(f"\n📥 Scrapeando año {anio}...")

        df = scrapear_provincia_anio(anio, args.tipo_vehiculo)

        if df is not None:
            dfs_historicos.append(df)

            # Checkpoint: guardar progreso cada 3 años
            if len(dfs_historicos) % 3 == 0:
                df_temp = pd.concat(dfs_historicos, ignore_index=True)
                checkpoint_file = f'checkpoint_provincial_{args.anio_inicio}_{anio}.xlsx'
                df_temp.to_excel(checkpoint_file, index=False)
                print(f"   💾 Checkpoint guardado: {checkpoint_file}")

        # Esperar antes del siguiente request (rate limiting)
        if anio < args.anio_fin:
            print(f"   ⏳ Esperando {args.delay}s antes del siguiente request...")
            time.sleep(args.delay)

    # Verificar si se obtuvieron datos
    if not dfs_historicos:
        print("\n❌ ERROR: No se obtuvieron datos para ningún año")
        sys.exit(1)

    # Combinar todos los DataFrames
    print(f"\n📊 Combinando datos de {len(dfs_historicos)} años...")
    df_final = pd.concat(dfs_historicos, ignore_index=True)

    # Guardar archivo final
    output_file = f"patentamientos_provincial_{args.anio_inicio}_{args.anio_fin}_{TIPOS_VEHICULO[args.tipo_vehiculo]}.xlsx"
    df_final.to_excel(output_file, index=False, sheet_name='Datos')

    print("\n" + "=" * 80)
    print("✅ SCRAPING COMPLETADO")
    print("=" * 80)
    print(f"💾 Archivo generado: {output_file}")
    print(f"📊 Total de registros: {len(df_final)}")
    print(f"📅 Años incluidos: {df_final['anio'].unique().tolist()}")
    print(f"📍 Provincias únicas: {df_final[df_final.columns[0]].nunique()}")

    # Estadísticas por año
    print("\n📈 ESTADÍSTICAS POR AÑO:")
    print("-" * 80)
    for anio in sorted(df_final['anio'].unique()):
        df_anio = df_final[df_final['anio'] == anio]
        total_col = 'Total' if 'Total' in df_anio.columns else df_anio.columns[-4]  # -4 porque últimas 3 son metadata
        if total_col in df_anio.columns:
            total = df_anio[total_col].sum()
            print(f"  {anio}: {total:>10,} patentamientos")

    print("\n" + "=" * 80)
    print("🎯 Próximos pasos:")
    print("  1. Verificar el archivo Excel generado")
    print("  2. Ejecutar para otros tipos de vehículos si es necesario")
    print("  3. Cargar datos a PostgreSQL con: python cargar_datos_postgresql.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
