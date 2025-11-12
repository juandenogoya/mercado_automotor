"""
Script para explorar la estructura de las tablas de automóviles en PostgreSQL.

Objetivo:
- Verificar columnas disponibles en cada tabla
- Validar tipos de datos
- Identificar columnas comunes entre tablas
- Contar registros totales

Tablas a analizar:
- datos_gob_inscripciones
- datos_gob_transferencias
- datos_gob_prendas

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/01_explorar_estructura_tablas.py
"""

from sqlalchemy import create_engine, text, inspect
import pandas as pd
from datetime import datetime

# Configuración de conexión
DB_CONFIG = {
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432,
    'database': 'mercado_automotor'
}

# Crear engine con configuración de encoding para Windows
engine = create_engine(
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
    connect_args={
        'client_encoding': 'utf8',
        'options': '-c client_encoding=utf8'
    },
    pool_pre_ping=True  # Verifica conexión antes de usarla
)

def explorar_tabla(tabla_nombre):
    """Explora estructura y datos de una tabla."""
    print(f"\n{'='*100}")
    print(f"TABLA: {tabla_nombre}")
    print('='*100)

    # 1. Obtener metadata de columnas
    inspector = inspect(engine)
    columnas = inspector.get_columns(tabla_nombre)

    print(f"\n📋 COLUMNAS ({len(columnas)} total):")
    print("-" * 100)

    df_columnas = pd.DataFrame([{
        'Columna': col['name'],
        'Tipo': str(col['type']),
        'Nullable': 'Sí' if col['nullable'] else 'No'
    } for col in columnas])

    print(df_columnas.to_string(index=False))

    # 2. Contar registros totales
    query_count = text(f"SELECT COUNT(*) as total FROM {tabla_nombre}")
    with engine.connect() as conn:
        total_registros = pd.read_sql(query_count, conn)['total'][0]

    print(f"\n📊 TOTAL REGISTROS: {total_registros:,}")

    # 3. Obtener rango de fechas
    query_fechas = text(f"""
        SELECT
            MIN(tramite_fecha) as fecha_min,
            MAX(tramite_fecha) as fecha_max,
            COUNT(DISTINCT EXTRACT(YEAR FROM tramite_fecha)) as anios_distintos
        FROM {tabla_nombre}
        WHERE tramite_fecha IS NOT NULL
    """)

    with engine.connect() as conn:
        df_fechas = pd.read_sql(query_fechas, conn)

    print(f"\n📅 RANGO TEMPORAL:")
    print(f"   - Fecha mínima: {df_fechas['fecha_min'][0]}")
    print(f"   - Fecha máxima: {df_fechas['fecha_max'][0]}")
    print(f"   - Años distintos: {df_fechas['anios_distintos'][0]}")

    # 4. Valores nulos por columna (solo columnas importantes)
    columnas_importantes = [
        'tramite_fecha',
        'registro_seccional_provincia',
        'automotor_marca_descripcion',
        'automotor_tipo_descripcion'
    ]

    print(f"\n🔍 VALORES NULOS (columnas clave):")
    print("-" * 100)

    for columna in columnas_importantes:
        # Verificar si la columna existe
        if columna in [col['name'] for col in columnas]:
            query_nulos = text(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT({columna}) as no_nulos,
                    COUNT(*) - COUNT({columna}) as nulos,
                    ROUND(100.0 * (COUNT(*) - COUNT({columna})) / COUNT(*), 2) as pct_nulos
                FROM {tabla_nombre}
            """)

            with engine.connect() as conn:
                df_nulos = pd.read_sql(query_nulos, conn)

            print(f"   {columna:40} -> Nulos: {df_nulos['nulos'][0]:10,} ({df_nulos['pct_nulos'][0]:6.2f}%)")

    # 5. Muestra de datos (primeros 3 registros)
    query_sample = text(f"""
        SELECT *
        FROM {tabla_nombre}
        WHERE tramite_fecha IS NOT NULL
        ORDER BY tramite_fecha DESC
        LIMIT 3
    """)

    with engine.connect() as conn:
        df_sample = pd.read_sql(query_sample, conn)

    print(f"\n📄 MUESTRA DE DATOS (últimos 3 registros):")
    print("-" * 100)
    print(df_sample.to_string(index=False))

    return [col['name'] for col in columnas]


def comparar_columnas(columnas_dict):
    """Compara columnas entre las 3 tablas."""
    print(f"\n{'='*100}")
    print("COMPARACIÓN DE COLUMNAS ENTRE TABLAS")
    print('='*100)

    # Encontrar columnas comunes
    columnas_inscripciones = set(columnas_dict['datos_gob_inscripciones'])
    columnas_transferencias = set(columnas_dict['datos_gob_transferencias'])
    columnas_prendas = set(columnas_dict['datos_gob_prendas'])

    columnas_comunes = columnas_inscripciones & columnas_transferencias & columnas_prendas

    print(f"\n✅ COLUMNAS COMUNES A LAS 3 TABLAS ({len(columnas_comunes)}):")
    print("-" * 100)
    for col in sorted(columnas_comunes):
        print(f"   - {col}")

    # Columnas únicas por tabla
    print(f"\n🔸 COLUMNAS ÚNICAS POR TABLA:")
    print("-" * 100)

    print(f"\n   Inscripciones ({len(columnas_inscripciones - columnas_comunes)}):")
    for col in sorted(columnas_inscripciones - columnas_comunes):
        print(f"      - {col}")

    print(f"\n   Transferencias ({len(columnas_transferencias - columnas_comunes)}):")
    for col in sorted(columnas_transferencias - columnas_comunes):
        print(f"      - {col}")

    print(f"\n   Prendas ({len(columnas_prendas - columnas_comunes)}):")
    for col in sorted(columnas_prendas - columnas_comunes):
        print(f"      - {col}")

    return sorted(columnas_comunes)


def main():
    """Función principal."""
    print("\n" + "="*100)
    print("EXPLORACIÓN DE ESTRUCTURA DE TABLAS - FASE 1")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    try:
        # Explorar cada tabla
        tablas = ['datos_gob_inscripciones', 'datos_gob_transferencias', 'datos_gob_prendas']
        columnas_dict = {}

        for tabla in tablas:
            columnas_dict[tabla] = explorar_tabla(tabla)

        # Comparar columnas
        columnas_comunes = comparar_columnas(columnas_dict)

        # Resumen final
        print(f"\n{'='*100}")
        print("RESUMEN Y RECOMENDACIONES")
        print('='*100)

        print(f"\n✅ Las 3 tablas tienen {len(columnas_comunes)} columnas en común.")
        print(f"✅ Estas columnas se pueden usar para unir los datasets.")
        print(f"\n📋 Columnas clave recomendadas para el dataset unificado:")

        columnas_clave = [
            'tramite_fecha',
            'registro_seccional_provincia',
            'automotor_marca_descripcion',
            'automotor_tipo_descripcion'
        ]

        for col in columnas_clave:
            if col in columnas_comunes:
                print(f"   ✓ {col}")
            else:
                print(f"   ✗ {col} (NO COMÚN - revisar)")

        print(f"\n💡 Próximo paso:")
        print(f"   Ejecutar: python backend/data_processing/02_unir_datasets.py")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
