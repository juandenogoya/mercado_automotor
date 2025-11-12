"""
Script para unir datasets de automóviles y crear features temporales.
VERSIÓN 2: Con fix para encoding en Windows.

Objetivo:
- Unir inscripciones + transferencias + prendas en un solo dataset
- Agregar columna 'tipo_operacion' para identificar origen
- Crear features temporales para forecasting
- Guardar dataset en formato Parquet (optimizado)

Dataset final incluirá:
- Todas las columnas originales comunes
- tipo_operacion: 'inscripcion', 'transferencia', 'prenda'
- Features temporales: año, mes, trimestre, día_semana, etc.

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/02_unir_datasets_v2.py
"""

# FIX CRÍTICO: Configurar encoding ANTES de cualquier import
import sys
import os

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    # Configurar variables de entorno ANTES de importar psycopg2
    os.environ['PGCLIENTENCODING'] = 'UTF8'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # Forzar encoding en stdout
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')

# Ahora sí, importar librerías
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración de conexión
DB_CONFIG = {
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432,
    'database': 'mercado_automotor'
}

# Crear URL de conexión con encoding explícito
connection_url = (
    f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    f"?client_encoding=utf8"
)

# Crear engine con configuración de encoding para Windows
engine = create_engine(
    connection_url,
    connect_args={
        'options': '-c client_encoding=UTF8'
    },
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Directorio de salida
OUTPUT_DIR = 'data/processed'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extraer_datos_tabla(tabla_nombre, tipo_operacion, limit=None):
    """
    Extrae datos de una tabla específica.

    Args:
        tabla_nombre: Nombre de la tabla en PostgreSQL
        tipo_operacion: 'inscripcion', 'transferencia', 'prenda'
        limit: Límite de registros (para testing, None = todos)

    Returns:
        DataFrame con datos de la tabla
    """
    print(f"\n📥 Extrayendo datos de: {tabla_nombre}")
    print(f"   Tipo operación: {tipo_operacion}")

    # Query base - seleccionar columnas comunes
    query = f"""
        SELECT
            tramite_fecha,
            registro_seccional_provincia,
            registro_seccional_descripcion,
            automotor_origen,
            automotor_marca_descripcion,
            automotor_tipo_descripcion,
            automotor_modelo_descripcion,
            automotor_uso,
            automotor_anio_modelo,
            '{tipo_operacion}' as tipo_operacion
        FROM {tabla_nombre}
        WHERE tramite_fecha IS NOT NULL
        ORDER BY tramite_fecha
        {f'LIMIT {limit}' if limit else ''}
    """

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
    except Exception as e:
        print(f"   ❌ Error al extraer datos: {e}")
        raise

    print(f"   ✓ Registros extraídos: {len(df):,}")

    return df


def crear_features_temporales(df):
    """
    Crea features temporales para forecasting.

    Args:
        df: DataFrame con columna 'tramite_fecha'

    Returns:
        DataFrame con nuevas columnas temporales
    """
    print(f"\n🛠️  Creando features temporales...")

    # Asegurar que tramite_fecha es datetime
    df['tramite_fecha'] = pd.to_datetime(df['tramite_fecha'])

    # Features básicas
    df['anio'] = df['tramite_fecha'].dt.year
    df['mes'] = df['tramite_fecha'].dt.month
    df['dia'] = df['tramite_fecha'].dt.day
    df['trimestre'] = df['tramite_fecha'].dt.quarter
    df['dia_semana'] = df['tramite_fecha'].dt.dayofweek  # 0=Lunes, 6=Domingo
    df['dia_semana_nombre'] = df['tramite_fecha'].dt.day_name()
    df['semana_anio'] = df['tramite_fecha'].dt.isocalendar().week
    df['mes_nombre'] = df['tramite_fecha'].dt.month_name()

    # Features de calendario
    df['es_fin_semana'] = df['dia_semana'].isin([5, 6]).astype(int)  # Sábado/Domingo
    df['es_inicio_mes'] = (df['dia'] <= 7).astype(int)
    df['es_fin_mes'] = (df['dia'] >= 25).astype(int)

    # Features cíclicas (para capturar estacionalidad)
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
    df['dia_semana_sin'] = np.sin(2 * np.pi * df['dia_semana'] / 7)
    df['dia_semana_cos'] = np.cos(2 * np.pi * df['dia_semana'] / 7)

    # Features de tiempo desde origen
    fecha_min = df['tramite_fecha'].min()
    df['dias_desde_origen'] = (df['tramite_fecha'] - fecha_min).dt.days

    print(f"   ✓ Features temporales creadas:")
    print(f"      - anio, mes, dia, trimestre")
    print(f"      - dia_semana, semana_anio")
    print(f"      - es_fin_semana, es_inicio_mes, es_fin_mes")
    print(f"      - features cíclicas (sin/cos)")
    print(f"      - dias_desde_origen")

    return df


def crear_features_agregadas(df):
    """
    Crea features agregadas por provincia y tipo.

    Args:
        df: DataFrame unificado

    Returns:
        DataFrame con nuevas features
    """
    print(f"\n🛠️  Creando features agregadas...")

    # Ordenar por fecha
    df = df.sort_values('tramite_fecha').reset_index(drop=True)

    # Feature: ID único secuencial
    df['operacion_id'] = range(1, len(df) + 1)

    # Categorizar marcas (Top 10 vs Otros)
    top_marcas = df['automotor_marca_descripcion'].value_counts().head(10).index
    df['marca_categoria'] = df['automotor_marca_descripcion'].apply(
        lambda x: x if x in top_marcas else 'OTROS'
    )

    # Categorizar tipos de vehículo (Top 10 vs Otros)
    top_tipos = df['automotor_tipo_descripcion'].value_counts().head(10).index
    df['tipo_categoria'] = df['automotor_tipo_descripcion'].apply(
        lambda x: x if x in top_tipos else 'OTROS'
    )

    print(f"   ✓ Features agregadas creadas:")
    print(f"      - operacion_id (ID secuencial)")
    print(f"      - marca_categoria (Top 10 + Otros)")
    print(f"      - tipo_categoria (Top 10 + Otros)")

    return df


def validar_dataset(df):
    """
    Valida calidad del dataset unificado.

    Args:
        df: DataFrame a validar
    """
    print(f"\n{'='*100}")
    print("VALIDACIÓN DE DATASET")
    print('='*100)

    # 1. Información general
    print(f"\n📊 INFORMACIÓN GENERAL:")
    print(f"   - Total registros: {len(df):,}")
    print(f"   - Total columnas: {len(df.columns)}")
    print(f"   - Memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # 2. Distribución por tipo de operación
    print(f"\n📋 DISTRIBUCIÓN POR TIPO DE OPERACIÓN:")
    tipo_dist = df['tipo_operacion'].value_counts()
    for tipo, count in tipo_dist.items():
        pct = 100 * count / len(df)
        print(f"   - {tipo:15} : {count:10,} ({pct:5.2f}%)")

    # 3. Rango temporal
    print(f"\n📅 RANGO TEMPORAL:")
    print(f"   - Fecha mínima: {df['tramite_fecha'].min()}")
    print(f"   - Fecha máxima: {df['tramite_fecha'].max()}")
    print(f"   - Días totales: {(df['tramite_fecha'].max() - df['tramite_fecha'].min()).days:,}")
    print(f"   - Años únicos: {df['anio'].nunique()}")

    # 4. Valores nulos
    print(f"\n🔍 VALORES NULOS (Top 10 columnas):")
    nulos = df.isnull().sum().sort_values(ascending=False).head(10)
    for col, count in nulos.items():
        if count > 0:
            pct = 100 * count / len(df)
            print(f"   - {col:40} : {count:10,} ({pct:5.2f}%)")

    # 5. Distribución por provincia (Top 10)
    print(f"\n📍 TOP 10 PROVINCIAS:")
    prov_dist = df['registro_seccional_provincia'].value_counts().head(10)
    for prov, count in prov_dist.items():
        pct = 100 * count / len(df)
        print(f"   - {prov:30} : {count:10,} ({pct:5.2f}%)")

    # 6. Distribución por marca (Top 10)
    print(f"\n🚗 TOP 10 MARCAS:")
    marca_dist = df['automotor_marca_descripcion'].value_counts().head(10)
    for marca, count in marca_dist.items():
        pct = 100 * count / len(df)
        print(f"   - {marca:30} : {count:10,} ({pct:5.2f}%)")

    # 7. Distribución temporal (registros por año)
    print(f"\n📈 REGISTROS POR AÑO:")
    anio_dist = df['anio'].value_counts().sort_index()
    for anio, count in anio_dist.items():
        pct = 100 * count / len(df)
        print(f"   - {anio} : {count:10,} ({pct:5.2f}%)")


def guardar_dataset(df, nombre_archivo):
    """
    Guarda dataset en formato Parquet.

    Args:
        df: DataFrame a guardar
        nombre_archivo: Nombre del archivo (sin extensión)
    """
    print(f"\n💾 Guardando dataset...")

    filepath = os.path.join(OUTPUT_DIR, f"{nombre_archivo}.parquet")

    # Guardar en Parquet (compresión snappy por defecto)
    df.to_parquet(filepath, index=False, engine='pyarrow', compression='snappy')

    # Verificar archivo creado
    size_mb = os.path.getsize(filepath) / 1024**2

    print(f"   ✓ Archivo guardado: {filepath}")
    print(f"   ✓ Tamaño: {size_mb:.2f} MB")

    # También guardar resumen en CSV (más fácil de inspeccionar)
    csv_path = os.path.join(OUTPUT_DIR, f"{nombre_archivo}_sample.csv")
    df.head(1000).to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"   ✓ Muestra guardada: {csv_path} (primeros 1000 registros)")


def main():
    """Función principal."""
    print("\n" + "="*100)
    print("UNIFICACIÓN DE DATASETS - FASE 1 (V2)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    try:
        # Verificar conexión
        print("\n🔌 Verificando conexión a PostgreSQL...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   ✓ Conectado: {version.split(',')[0]}")

        # Parámetros
        LIMIT = None  # None = todos los registros, usar número para testing (ej: 10000)

        # 1. Extraer datos de cada tabla
        df_inscripciones = extraer_datos_tabla('datos_gob_inscripciones', 'inscripcion', LIMIT)
        df_transferencias = extraer_datos_tabla('datos_gob_transferencias', 'transferencia', LIMIT)
        df_prendas = extraer_datos_tabla('datos_gob_prendas', 'prenda', LIMIT)

        # 2. Unir datasets
        print(f"\n🔗 Uniendo datasets...")
        df_unificado = pd.concat([df_inscripciones, df_transferencias, df_prendas], ignore_index=True)
        print(f"   ✓ Total registros unificados: {len(df_unificado):,}")

        # 3. Ordenar por fecha
        print(f"\n📅 Ordenando por fecha...")
        df_unificado = df_unificado.sort_values('tramite_fecha').reset_index(drop=True)
        print(f"   ✓ Dataset ordenado")

        # 4. Crear features temporales
        df_unificado = crear_features_temporales(df_unificado)

        # 5. Crear features agregadas
        df_unificado = crear_features_agregadas(df_unificado)

        # 6. Validar dataset
        validar_dataset(df_unificado)

        # 7. Guardar dataset
        guardar_dataset(df_unificado, 'dataset_transaccional_unificado')

        # Resumen final
        print(f"\n{'='*100}")
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print('='*100)
        print(f"\n📁 Archivos generados:")
        print(f"   - {OUTPUT_DIR}/dataset_transaccional_unificado.parquet")
        print(f"   - {OUTPUT_DIR}/dataset_transaccional_unificado_sample.csv")
        print(f"\n💡 Próximo paso:")
        print(f"   - Fase 2: Obtener datos macroeconómicos de APIs")
        print(f"   - Fase 3: Combinar datasets y crear features para forecasting")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
