"""

Script para cargar datos CSV de datos.gob.ar a PostgreSQL

 

EJECUCIÓN:

python cargar_datos_gob_ar_postgresql.py

 

Requisitos:

- PostgreSQL corriendo (docker-compose up -d)

- Archivos CSV en carpeta INPUT/

- Variables de entorno en .env

 

Dataset: Estadística de trámites de automotores (Ministerio de Justicia/DNRPA)

"""

 

import os

import sys

import pandas as pd

import psycopg2

from pathlib import Path

from datetime import datetime

from dotenv import load_dotenv

import glob

 

# Cargar variables de entorno

load_dotenv()

 

# Configuración PostgreSQL

DB_CONFIG = {

    'host': os.getenv('DB_HOST', 'localhost'),

    'port': os.getenv('DB_PORT', '5432'),

    'database': os.getenv('DB_NAME', 'mercado_automotor'),

    'user': os.getenv('DB_USER', 'postgres'),

    'password': os.getenv('DB_PASSWORD', 'postgres')

}

 

# Mapeo de carpetas a tablas

MAPEO_TABLAS = {

    'INSCRIPCIONES': 'datos_gob_inscripciones',

    'TRANSFERENCIAS': 'datos_gob_transferencias',

    'PRENDAS': 'datos_gob_prendas'

}

 

# Columnas esperadas en los CSVs

COLUMNAS_ESPERADAS = [

    'tramite_tipo',

    'tramite_fecha',

    'fecha_inscripcion_inicial',

    'registro_seccional_codigo',

    'registro_seccional_descripcion',

    'registro_seccional_provincia',

    'automotor_origen',

    'automotor_anio_modelo',

    'automotor_tipo_codigo',

    'automotor_tipo_descripcion',

    'automotor_marca_codigo',

    'automotor_marca_descripcion',

    'automotor_modelo_codigo',

    'automotor_modelo_descripcion',

    'automotor_uso_codigo',

    'automotor_uso_descripcion',

    'titular_tipo_persona',

    'titular_domicilio_localidad',

    'titular_domicilio_provincia',

    'titular_genero',

    'titular_anio_nacimiento',

    'titular_pais_nacimiento',

    'titular_porcentaje_titularidad',

    'titular_domicilio_provincia_id',

    'titular_pais_nacimiento_id'

]

 

 

def conectar_db():

    """Conectar a PostgreSQL"""

    try:

        conn = psycopg2.connect(**DB_CONFIG)

        return conn

    except Exception as e:

        print(f"❌ Error conectando a PostgreSQL: {e}")

        print(f"   Configuración: {DB_CONFIG}")

        sys.exit(1)

 

 

def crear_tablas():

    """Crear tablas si no existen"""

    print("\n📋 Creando tablas en PostgreSQL...")

 

    sql_file = Path(__file__).parent / 'sql' / 'crear_tablas_datos_gob_ar.sql'

 

    if not sql_file.exists():

        print(f"❌ No se encontró {sql_file}")

        return False

 

    conn = conectar_db()

    cursor = conn.cursor()

 

    try:

        with open(sql_file, 'r', encoding='utf-8') as f:

            sql = f.read()

            cursor.execute(sql)

            conn.commit()

        print("✅ Tablas creadas exitosamente")

        return True

    except Exception as e:

        print(f"❌ Error creando tablas: {e}")

        conn.rollback()

        return False

    finally:

        cursor.close()

        conn.close()

 

 

def obtener_archivos_csv(categoria):

    """Obtener lista de archivos CSV de una categoría"""

    input_dir = Path(__file__).parent / 'INPUT' / categoria

 

    if not input_dir.exists():

        print(f"⚠️ No existe carpeta: {input_dir}")

        return []

 

    # Buscar todos los CSV recursivamente

    archivos = list(input_dir.glob('**/*.csv'))

    return sorted(archivos)

 

 

def limpiar_datos(df, archivo_origen):

    """Limpiar y preparar datos para carga"""

 

    # Agregar columna con nombre de archivo origen

    df['archivo_origen'] = Path(archivo_origen).name

 

    # Convertir fechas

    for col in ['tramite_fecha', 'fecha_inscripcion_inicial']:

        if col in df.columns:

            df[col] = pd.to_datetime(df[col], errors='coerce')

 

    # Convertir numéricos

    if 'registro_seccional_codigo' in df.columns:

        df['registro_seccional_codigo'] = pd.to_numeric(df['registro_seccional_codigo'], errors='coerce')

 

    if 'automotor_anio_modelo' in df.columns:

        df['automotor_anio_modelo'] = pd.to_numeric(df['automotor_anio_modelo'], errors='coerce')

 

    if 'titular_anio_nacimiento' in df.columns:

        df['titular_anio_nacimiento'] = pd.to_numeric(df['titular_anio_nacimiento'], errors='coerce')

 

    if 'titular_porcentaje_titularidad' in df.columns:

        df['titular_porcentaje_titularidad'] = pd.to_numeric(df['titular_porcentaje_titularidad'], errors='coerce')

 

    # Reemplazar valores vacíos

    df = df.fillna('')

 

    # Asegurar que tengamos todas las columnas esperadas

    columnas_con_origen = COLUMNAS_ESPERADAS + ['archivo_origen']

    for col in columnas_con_origen:

        if col not in df.columns:

            df[col] = ''

 

    return df[columnas_con_origen]

 

 

def cargar_csv_a_tabla(archivo_csv, tabla):

    """Cargar un archivo CSV a PostgreSQL"""

 

    try:

        # Leer CSV

        df = pd.read_csv(archivo_csv, low_memory=False)

 

        if len(df) == 0:

            return 0, "Sin datos"

 

        # Limpiar datos

        df = limpiar_datos(df, archivo_csv)

 

        # Conectar a DB

        conn = conectar_db()

        cursor = conn.cursor()

 

        # Insertar datos usando copy_from (más rápido)

        from io import StringIO

 

        buffer = StringIO()

        df.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')

        buffer.seek(0)

 

        columnas = COLUMNAS_ESPERADAS + ['archivo_origen']

 

        cursor.copy_from(

            buffer,

            tabla,

            columns=columnas,

            sep='\t',

            null='\\N'

        )

 

        conn.commit()

        filas_cargadas = len(df)

 

        cursor.close()

        conn.close()

 

        return filas_cargadas, "OK"

 

    except Exception as e:

        return 0, str(e)

 

 

def procesar_categoria(categoria):

    """Procesar todos los CSVs de una categoría"""

 

    print(f"\n{'=' * 80}")

    print(f"📂 PROCESANDO: {categoria}")

    print(f"{'=' * 80}")

 

    tabla = MAPEO_TABLAS.get(categoria)

    if not tabla:

        print(f"⚠️ Categoría {categoria} no mapeada a tabla")

        return

 

    archivos = obtener_archivos_csv(categoria)

 

    if not archivos:

        print(f"⚠️ No se encontraron archivos CSV en INPUT/{categoria}")

        return

 

    print(f"📋 Archivos encontrados: {len(archivos)}")

    print(f"🎯 Tabla destino: {tabla}")

 

    total_filas = 0

    archivos_ok = 0

    archivos_error = 0

 

    for i, archivo in enumerate(archivos, 1):

        nombre = archivo.name

        print(f"\n[{i}/{len(archivos)}] {nombre}")

        print(f"   📥 Cargando...", end=' ', flush=True)

 

        filas, mensaje = cargar_csv_a_tabla(archivo, tabla)

 

        if mensaje == "OK":

            print(f"✅ {filas:,} filas")

            total_filas += filas

            archivos_ok += 1

        else:

            print(f"❌ Error: {mensaje[:100]}")

            archivos_error += 1

 

    print(f"\n{'=' * 80}")

    print(f"📊 RESUMEN {categoria}")

    print(f"{'=' * 80}")

    print(f"✅ Archivos OK: {archivos_ok}")

    print(f"❌ Archivos con error: {archivos_error}")

    print(f"📊 Total filas cargadas: {total_filas:,}")

    print(f"{'=' * 80}")

 

 

def verificar_carga():

    """Verificar datos cargados"""

    print(f"\n{'=' * 80}")

    print("📊 VERIFICACIÓN DE CARGA")

    print(f"{'=' * 80}")

 

    conn = conectar_db()

    cursor = conn.cursor()

 

    for categoria, tabla in MAPEO_TABLAS.items():

        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")

        count = cursor.fetchone()[0]

 

        if count > 0:

            cursor.execute(f"""

                SELECT

                    MIN(tramite_fecha) as fecha_min,

                    MAX(tramite_fecha) as fecha_max,

                    COUNT(DISTINCT registro_seccional_provincia) as provincias

                FROM {tabla}

            """)

            fecha_min, fecha_max, provincias = cursor.fetchone()

 

            print(f"\n✅ {tabla}")

            print(f"   Registros: {count:,}")

            print(f"   Período: {fecha_min} a {fecha_max}")

            print(f"   Provincias: {provincias}")

        else:

            print(f"\n⚠️ {tabla}: Sin datos")

 

    cursor.close()

    conn.close()

    print(f"\n{'=' * 80}")

 

 

def main():

    """Función principal"""

 

    print("=" * 80)

    print("🚀 CARGA DE DATOS datos.gob.ar A POSTGRESQL")

    print("=" * 80)

    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("=" * 80)

 

    # 1. Crear tablas

    if not crear_tablas():

        print("❌ Error creando tablas. Abortando.")

        return

 

    # 2. Procesar cada categoría

    for categoria in MAPEO_TABLAS.keys():

        procesar_categoria(categoria)

 

    # 3. Verificar carga

    verificar_carga()

 

    print("\n" + "=" * 80)

    print("✅ PROCESO COMPLETADO")

    print("=" * 80)

    print("\n🎯 Próximos pasos:")

    print("   1. Revisar dashboard actualizado")

    print("   2. Crear visualizaciones con los nuevos datos")

    print("   3. Explorar análisis por provincia, marca, período")

    print("=" * 80)

 

 

if __name__ == "__main__":

    main()