"""
ANÁLISIS PREDICTIVO - MERCADO AUTOMOTOR ARGENTINO
=================================================

Este script prepara los datos transaccionales (Inscripciones, Transferencias, Prendas)
y variables macro (IPC, BADLAR, Tipo de Cambio) para modelado predictivo.

OBJETIVO DEL ANÁLISIS:
---------------------
Predecir la DEMANDA MENSUAL por marca/modelo integrando variables macro-económicas
para evaluar cómo factores económicos afectan las transacciones automotrices.

TARGET VARIABLE:
- cantidad_transacciones: Volumen mensual de transacciones por marca/modelo/provincia/tipo

FEATURES:
- Variables categóricas: marca, modelo, provincia, tipo_vehiculo, genero, tipo_transaccion
- Variables temporales: año, mes, trimestre, día_semana
- Variables macro: IPC mensual, BADLAR, Tipo de Cambio, Tasa Real, TCR, Volatilidad
- Variables demográficas: edad_promedio_titular
- Variables calculadas: variación_intermensual, tendencia, estacionalidad

MODELOS A EVALUAR:
-----------------
1. Regresión Lineal (baseline)
2. Random Forest Regressor
3. Gradient Boosting (XGBoost, LightGBM)
4. KNN Regressor
5. Prophet (series temporales)
6. LSTM (deep learning para series temporales)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text

# Configuración
sys.path.append(str(Path(__file__).parent.parent))
from backend.config.settings import settings

# Constantes
OUTPUT_DIR = Path("data/processed/ml")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def log(message):
    """Logger simple."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def cargar_datos_transaccionales():
    """
    Carga y unifica los 3 datasets transaccionales.

    Returns:
        pd.DataFrame: Dataset unificado con columna 'tipo_transaccion'
    """
    log("=" * 80)
    log("📊 CARGANDO DATOS TRANSACCIONALES")
    log("=" * 80)

    engine = create_engine(settings.get_database_url_sync())

    datasets = {
        'inscripcion': 'datos_gob_inscripciones',
        'transferencia': 'datos_gob_transferencias',
        'prenda': 'datos_gob_prendas'
    }

    dfs = []

    for tipo, tabla in datasets.items():
        log(f"\n📥 Cargando {tipo.upper()}...")

        query = f"""
        SELECT
            EXTRACT(YEAR FROM tramite_fecha)::INTEGER as anio,
            EXTRACT(MONTH FROM tramite_fecha)::INTEGER as mes,
            EXTRACT(QUARTER FROM tramite_fecha)::INTEGER as trimestre,
            EXTRACT(DOW FROM tramite_fecha)::INTEGER as dia_semana,
            DATE_TRUNC('month', tramite_fecha) as fecha_mes,
            registro_seccional_provincia as provincia,
            automotor_marca_descripcion as marca,
            automotor_modelo_descripcion as modelo,
            automotor_tipo_descripcion as tipo_vehiculo,
            automotor_anio_modelo as anio_modelo,
            titular_genero as genero,
            EXTRACT(YEAR FROM tramite_fecha) - titular_anio_nacimiento as edad_titular,
            '{tipo}' as tipo_transaccion
        FROM {tabla}
        WHERE tramite_fecha IS NOT NULL
          AND tramite_fecha >= '2020-01-01'  -- Últimos años para análisis
          AND titular_anio_nacimiento IS NOT NULL
          AND automotor_marca_descripcion IS NOT NULL
          AND automotor_modelo_descripcion IS NOT NULL
          AND registro_seccional_provincia IS NOT NULL
        """

        df = pd.read_sql(query, engine)
        log(f"  ✓ {len(df):,} registros cargados")
        dfs.append(df)

    # Unificar datasets
    log("\n🔗 Unificando datasets...")
    df_unificado = pd.concat(dfs, ignore_index=True)
    log(f"  ✓ Dataset unificado: {len(df_unificado):,} registros")

    engine.dispose()
    return df_unificado


def cargar_variables_macro():
    """
    Carga variables macro-económicas mensuales.

    Returns:
        pd.DataFrame: Variables macro agregadas por mes
    """
    log("\n" + "=" * 80)
    log("📈 CARGANDO VARIABLES MACRO")
    log("=" * 80)

    engine = create_engine(settings.get_database_url_sync())

    # IPC mensual
    log("\n💰 Cargando IPC...")
    query_ipc = """
    SELECT
        fecha,
        nivel_general as ipc_nivel,
        variacion_mensual as ipc_var_mensual,
        variacion_interanual as ipc_var_interanual,
        variacion_acumulada as ipc_var_acumulada
    FROM ipc
    WHERE fecha >= '2020-01-01'
    ORDER BY fecha
    """
    df_ipc = pd.read_sql(query_ipc, engine)
    df_ipc['fecha'] = pd.to_datetime(df_ipc['fecha'])
    df_ipc['fecha_mes'] = df_ipc['fecha'].dt.to_period('M').dt.to_timestamp()
    df_ipc = df_ipc.groupby('fecha_mes').last().reset_index()
    log(f"  ✓ IPC: {len(df_ipc)} meses")

    # BADLAR promedio mensual
    log("\n💵 Cargando BADLAR...")
    query_badlar = """
    SELECT
        DATE_TRUNC('month', fecha) as fecha_mes,
        AVG(tasa) as badlar_promedio,
        STDDEV(tasa) as badlar_volatilidad
    FROM badlar
    WHERE fecha >= '2020-01-01'
    GROUP BY DATE_TRUNC('month', fecha)
    ORDER BY fecha_mes
    """
    df_badlar = pd.read_sql(query_badlar, engine)
    log(f"  ✓ BADLAR: {len(df_badlar)} meses")

    # Tipo de Cambio promedio mensual
    log("\n💱 Cargando Tipo de Cambio...")
    query_tc = """
    SELECT
        DATE_TRUNC('month', fecha) as fecha_mes,
        AVG(promedio) as tc_promedio,
        STDDEV(promedio) as tc_volatilidad
    FROM tipo_cambio
    WHERE fecha >= '2020-01-01'
    GROUP BY DATE_TRUNC('month', fecha)
    ORDER BY fecha_mes
    """
    df_tc = pd.read_sql(query_tc, engine)
    log(f"  ✓ Tipo Cambio: {len(df_tc)} meses")

    # Indicadores calculados (pivotear de formato largo a ancho)
    log("\n📊 Cargando Indicadores Calculados...")
    query_ind = """
    SELECT
        DATE_TRUNC('month', fecha) as fecha_mes,
        indicador,
        AVG(valor) as valor_promedio
    FROM indicadores_calculados
    WHERE fecha >= '2020-01-01'
      AND indicador IN ('tasa_real', 'tcr', 'accesibilidad', 'volatilidad')
    GROUP BY DATE_TRUNC('month', fecha), indicador
    ORDER BY fecha_mes, indicador
    """
    df_ind_raw = pd.read_sql(query_ind, engine)

    # Pivotear de largo a ancho
    if not df_ind_raw.empty:
        df_ind = df_ind_raw.pivot(index='fecha_mes', columns='indicador', values='valor_promedio').reset_index()
        df_ind.columns = ['fecha_mes'] + [f'{col}_promedio' for col in df_ind.columns[1:]]
        log(f"  ✓ Indicadores: {len(df_ind)} meses, {len(df_ind.columns)-1} indicadores")
    else:
        log("  ⚠️ No hay indicadores calculados, creando DataFrame vacío")
        df_ind = pd.DataFrame({'fecha_mes': []})

    # Merge de todas las variables macro
    log("\n🔗 Unificando variables macro...")
    df_macro = df_ipc.merge(df_badlar, on='fecha_mes', how='outer')
    df_macro = df_macro.merge(df_tc, on='fecha_mes', how='outer')
    df_macro = df_macro.merge(df_ind, on='fecha_mes', how='outer')

    # Ordenar y forward fill para missing values
    df_macro = df_macro.sort_values('fecha_mes').fillna(method='ffill')

    log(f"  ✓ Variables macro unificadas: {len(df_macro)} meses, {len(df_macro.columns)} variables")

    engine.dispose()
    return df_macro


def agregar_y_preparar_datos(df_transaccional, df_macro):
    """
    Agrega transacciones a nivel mensual y merge con variables macro.

    Args:
        df_transaccional: DataFrame con datos transaccionales
        df_macro: DataFrame con variables macro

    Returns:
        pd.DataFrame: Dataset preparado para ML
    """
    log("\n" + "=" * 80)
    log("🔧 AGREGACIÓN Y PREPARACIÓN DE DATOS")
    log("=" * 80)

    # Agregar transacciones por mes/marca/modelo/provincia/tipo
    log("\n📊 Agregando transacciones...")
    df_agg = df_transaccional.groupby([
        'fecha_mes', 'anio', 'mes', 'trimestre',
        'marca', 'modelo', 'provincia', 'tipo_vehiculo',
        'tipo_transaccion', 'genero'
    ]).agg({
        'anio': 'count',  # cantidad de transacciones
        'edad_titular': 'mean',  # edad promedio
        'anio_modelo': 'mean'  # año modelo promedio
    }).rename(columns={'anio': 'cantidad_transacciones'}).reset_index()

    log(f"  ✓ Agregación completada: {len(df_agg):,} grupos")

    # Merge con variables macro
    log("\n🔗 Integrando variables macro...")
    df_ml = df_agg.merge(df_macro, on='fecha_mes', how='left')
    log(f"  ✓ Merge completado: {len(df_ml):,} registros, {len(df_ml.columns)} columnas")

    # Feature Engineering
    log("\n⚙️ Feature Engineering...")

    # 1. Variables temporales adicionales
    df_ml['es_primer_semestre'] = (df_ml['mes'] <= 6).astype(int)
    df_ml['es_fin_anio'] = (df_ml['mes'] >= 11).astype(int)

    # 2. Lag features (valores del mes anterior)
    log("  - Creando lag features...")
    df_ml = df_ml.sort_values(['marca', 'modelo', 'provincia', 'tipo_transaccion', 'fecha_mes'])

    for col in ['cantidad_transacciones', 'ipc_var_mensual', 'badlar_promedio', 'tc_promedio']:
        df_ml[f'{col}_lag1'] = df_ml.groupby(['marca', 'modelo', 'provincia', 'tipo_transaccion'])[col].shift(1)
        df_ml[f'{col}_lag3'] = df_ml.groupby(['marca', 'modelo', 'provincia', 'tipo_transaccion'])[col].shift(3)

    # 3. Rolling features (promedios móviles)
    log("  - Creando rolling features...")
    df_ml['cantidad_ma3'] = df_ml.groupby(['marca', 'modelo', 'provincia', 'tipo_transaccion'])['cantidad_transacciones'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    df_ml['cantidad_ma6'] = df_ml.groupby(['marca', 'modelo', 'provincia', 'tipo_transaccion'])['cantidad_transacciones'].transform(
        lambda x: x.rolling(window=6, min_periods=1).mean()
    )

    # 4. Variación intermensual de cantidad
    df_ml['cantidad_var_mensual'] = df_ml.groupby(['marca', 'modelo', 'provincia', 'tipo_transaccion'])['cantidad_transacciones'].pct_change() * 100

    # 5. Categorización de edad titular
    df_ml['rango_edad'] = pd.cut(
        df_ml['edad_titular'],
        bins=[0, 25, 35, 45, 55, 65, 100],
        labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    )

    log(f"  ✓ Features creados: {len(df_ml.columns)} columnas totales")

    # Eliminar filas con NaN en target
    log("\n🧹 Limpieza de datos...")
    inicial = len(df_ml)
    df_ml = df_ml.dropna(subset=['cantidad_transacciones'])
    log(f"  ✓ Eliminadas {inicial - len(df_ml):,} filas con target NaN")

    return df_ml


def guardar_datasets(df_ml):
    """
    Guarda datasets procesados para ML.

    Args:
        df_ml: DataFrame preparado para ML
    """
    log("\n" + "=" * 80)
    log("💾 GUARDANDO DATASETS")
    log("=" * 80)

    # Dataset completo
    file_completo = OUTPUT_DIR / "dataset_ml_completo.parquet"
    df_ml.to_parquet(file_completo, index=False)
    log(f"\n✓ Dataset completo guardado: {file_completo}")
    log(f"  Registros: {len(df_ml):,}")
    log(f"  Columnas: {len(df_ml.columns)}")
    log(f"  Tamaño: {file_completo.stat().st_size / 1024 / 1024:.2f} MB")

    # Dataset de muestra (top 20 marcas para desarrollo rápido)
    log("\n📦 Creando dataset de muestra (top 20 marcas)...")
    top_marcas = df_ml.groupby('marca')['cantidad_transacciones'].sum().nlargest(20).index
    df_sample = df_ml[df_ml['marca'].isin(top_marcas)]

    file_sample = OUTPUT_DIR / "dataset_ml_sample.parquet"
    df_sample.to_parquet(file_sample, index=False)
    log(f"✓ Dataset muestra guardado: {file_sample}")
    log(f"  Registros: {len(df_sample):,}")
    log(f"  Tamaño: {file_sample.stat().st_size / 1024 / 1024:.2f} MB")

    # Guardar info de columnas
    log("\n📋 Guardando metadatos...")
    columnas_info = pd.DataFrame({
        'columna': df_ml.columns,
        'tipo': df_ml.dtypes.astype(str),
        'no_nulos': df_ml.count(),
        'nulos': df_ml.isnull().sum(),
        'valores_unicos': df_ml.nunique()
    })

    file_meta = OUTPUT_DIR / "dataset_ml_metadata.csv"
    columnas_info.to_csv(file_meta, index=False)
    log(f"✓ Metadatos guardados: {file_meta}")


def main():
    """Función principal del pipeline de preparación."""
    log("=" * 80)
    log("🚀 PIPELINE DE PREPARACIÓN DE DATOS PARA ML")
    log("=" * 80)
    log(f"\nInicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Cargar datos transaccionales
    df_transaccional = cargar_datos_transaccionales()

    # 2. Cargar variables macro
    df_macro = cargar_variables_macro()

    # 3. Agregar y preparar datos
    df_ml = agregar_y_preparar_datos(df_transaccional, df_macro)

    # 4. Guardar datasets
    guardar_datasets(df_ml)

    # Resumen final
    log("\n" + "=" * 80)
    log("✅ PREPARACIÓN COMPLETADA")
    log("=" * 80)
    log(f"\nDataset final:")
    log(f"  - Registros: {len(df_ml):,}")
    log(f"  - Features: {len(df_ml.columns)}")
    log(f"  - Periodo: {df_ml['fecha_mes'].min()} → {df_ml['fecha_mes'].max()}")
    log(f"  - Marcas: {df_ml['marca'].nunique()}")
    log(f"  - Modelos: {df_ml['modelo'].nunique()}")
    log(f"\nArchivos generados en: {OUTPUT_DIR}")
    log("\n💡 Siguiente paso: Ejecutar 02_modelado_predictivo.py")
    log("=" * 80)


if __name__ == "__main__":
    main()
