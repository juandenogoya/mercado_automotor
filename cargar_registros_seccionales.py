"""
Script para cargar catálogo de Registros Seccionales a PostgreSQL

EJECUCIÓN:
python cargar_registros_seccionales.py

Dataset: Listado de registros seccionales automotor (DNRPA)
"""

import os
import sys
import pandas as pd
import psycopg2
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

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

# Columnas esperadas
COLUMNAS_ESPERADAS = [
    'competencia',
    'codigo',
    'denominacion',
    'encargado',
    'encargado_cuit',
    'domicilio',
    'localidad',
    'provincia_nombre',
    'provincia_letra',
    'codigo_postal',
    'telefono',
    'horario_atencion',
    'provincia_id'
]


def conectar_db():
    """Conectar a PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        sys.exit(1)


def limpiar_datos(df, archivo_origen):
    """Limpiar y preparar datos para carga"""

    # Agregar metadata
    df['archivo_origen'] = Path(archivo_origen).name

    # Convertir codigo a int
    if 'codigo' in df.columns:
        df['codigo'] = pd.to_numeric(df['codigo'], errors='coerce').fillna(0).astype(int)

    # Limpiar strings vacíos
    df = df.fillna('')

    # Asegurar todas las columnas
    columnas_con_origen = COLUMNAS_ESPERADAS + ['archivo_origen']
    for col in columnas_con_origen:
        if col not in df.columns:
            df[col] = ''

    return df[columnas_con_origen]


def cargar_csv_a_tabla(archivo_csv):
    """Cargar CSV a PostgreSQL usando UPSERT"""

    try:
        # Leer CSV
        df = pd.read_csv(archivo_csv, low_memory=False)

        if len(df) == 0:
            return 0, 0, "Sin datos"

        # Limpiar datos
        df = limpiar_datos(df, archivo_csv)

        # Conectar a DB
        conn = conectar_db()
        cursor = conn.cursor()

        insertados = 0
        actualizados = 0

        # Insertar/actualizar registro por registro (UPSERT)
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO datos_gob_registros_seccionales
                    (competencia, codigo, denominacion, encargado, encargado_cuit,
                     domicilio, localidad, provincia_nombre, provincia_letra,
                     codigo_postal, telefono, horario_atencion, provincia_id, archivo_origen)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (codigo)
                    DO UPDATE SET
                        competencia = EXCLUDED.competencia,
                        denominacion = EXCLUDED.denominacion,
                        encargado = EXCLUDED.encargado,
                        encargado_cuit = EXCLUDED.encargado_cuit,
                        domicilio = EXCLUDED.domicilio,
                        localidad = EXCLUDED.localidad,
                        provincia_nombre = EXCLUDED.provincia_nombre,
                        provincia_letra = EXCLUDED.provincia_letra,
                        codigo_postal = EXCLUDED.codigo_postal,
                        telefono = EXCLUDED.telefono,
                        horario_atencion = EXCLUDED.horario_atencion,
                        provincia_id = EXCLUDED.provincia_id,
                        archivo_origen = EXCLUDED.archivo_origen,
                        fecha_actualizacion = CURRENT_TIMESTAMP
                    RETURNING (xmax = 0) AS inserted
                """, (
                    row['competencia'], row['codigo'], row['denominacion'],
                    row['encargado'], row['encargado_cuit'], row['domicilio'],
                    row['localidad'], row['provincia_nombre'], row['provincia_letra'],
                    row['codigo_postal'], row['telefono'], row['horario_atencion'],
                    row['provincia_id'], row['archivo_origen']
                ))

                fue_insert = cursor.fetchone()[0]
                if fue_insert:
                    insertados += 1
                else:
                    actualizados += 1

            except Exception as e:
                print(f"   ⚠️ Error en registro {row.get('codigo', 'N/A')}: {str(e)[:50]}")
                continue

        conn.commit()
        cursor.close()
        conn.close()

        return insertados, actualizados, "OK"

    except Exception as e:
        return 0, 0, str(e)


def main():
    """Función principal"""

    print("=" * 80)
    print("🚀 CARGA DE REGISTROS SECCIONALES A POSTGRESQL")
    print("=" * 80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Buscar archivos de registros seccionales
    input_dir = Path(__file__).parent / 'INPUT' / 'REGISTRO POR SECCIONAL'

    if not input_dir.exists():
        print(f"\n❌ No existe carpeta: {input_dir}")
        return

    archivos = list(input_dir.glob('**/*.csv'))

    if not archivos:
        print(f"\n⚠️ No se encontraron archivos CSV en {input_dir}")
        return

    print(f"\n📋 Archivos encontrados: {len(archivos)}")
    print("=" * 80)

    total_insertados = 0
    total_actualizados = 0

    for i, archivo in enumerate(archivos, 1):
        nombre = archivo.name
        print(f"\n[{i}/{len(archivos)}] {nombre}")
        print(f"   📥 Procesando...", end=' ', flush=True)

        insertados, actualizados, mensaje = cargar_csv_a_tabla(archivo)

        if mensaje == "OK":
            print(f"✅ {insertados} nuevos, {actualizados} actualizados")
            total_insertados += insertados
            total_actualizados += actualizados
        else:
            print(f"❌ Error: {mensaje[:100]}")

    # Verificar datos cargados
    print("\n" + "=" * 80)
    print("📊 VERIFICACIÓN DE CARGA")
    print("=" * 80)

    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM datos_gob_registros_seccionales")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT provincia_nombre, COUNT(*)
        FROM datos_gob_registros_seccionales
        GROUP BY provincia_nombre
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)
    top_provincias = cursor.fetchall()

    cursor.close()
    conn.close()

    print(f"\n✅ Total registros seccionales: {total:,}")
    print(f"   Insertados: {total_insertados}")
    print(f"   Actualizados: {total_actualizados}")

    print(f"\n📍 Top 5 provincias por cantidad de registros:")
    for prov, cant in top_provincias:
        print(f"   {prov}: {cant}")

    print("\n" + "=" * 80)
    print("✅ PROCESO COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
