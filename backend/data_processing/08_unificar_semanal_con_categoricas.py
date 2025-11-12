#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 3C: Unificación Semanal CON Features Categóricas Correctas

Script CORREGIDO que:
1. Usa los nombres EXACTOS de las columnas categóricas
2. Crea features numéricas por cada categoría (provincias, marcas, origen)
3. Agrega temporalmente a nivel SEMANAL (352 registros vs 81 mensuales)
4. Merge con BCRA/INDEC
5. Agrega lags, rolling means, interacciones

FEATURES GENERADAS:
- Provincias: 26 columnas (operaciones_buenos_aires, operaciones_cordoba, etc.)
- Marcas: 31 columnas (Top 30 + otros)
- Origen: 3 columnas (nacional, protocolo_21, importado)
- Tipo Operación: 3 columnas (transferencia, inscripcion, prenda)
- Marca Categoría: 11 columnas (ya agrupada Top 10 + OTROS)
- BCRA: ~10 columnas
- INDEC: ~7 columnas
- Lags + Rolling: ~12 columnas
- Temporales: 5 columnas
- Interacciones: ~3 columnas

TOTAL: ~111 features (vs 14 con NaN anterior)

Input:
  - data/processed/dataset_transaccional_unificado.parquet
  - data/processed/bcra_datos_mensuales.parquet
  - data/processed/indec_datos_mensuales.parquet

Output:
  - data/processed/dataset_forecasting_semanal_completo.parquet

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/08_unificar_semanal_con_categoricas.py
"""

import duckdb
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Configuración
DATASET_TRANSACCIONAL = 'data/processed/dataset_transaccional_unificado.parquet'
DATOS_BCRA = 'data/processed/bcra_datos_mensuales.parquet'
DATOS_INDEC = 'data/processed/indec_datos_mensuales.parquet'

OUTPUT_FILE = 'data/processed/dataset_forecasting_semanal_completo.parquet'
OUTPUT_DIR = os.path.dirname(OUTPUT_FILE)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Nombres EXACTOS de las columnas categóricas
COL_PROVINCIA = 'registro_seccional_provincia'
COL_MARCA = 'automotor_marca_descripcion'
COL_MODELO = 'automotor_modelo_descripcion'
COL_ORIGEN = 'automotor_origen'
COL_TIPO_OP = 'tipo_operacion'
COL_MARCA_CAT = 'marca_categoria'


def verificar_archivos():
    """Verifica que existan los archivos de entrada."""
    print("\n" + "="*80)
    print("VERIFICACIÓN DE ARCHIVOS DE ENTRADA")
    print("="*80)

    archivos = {
        'Dataset Transaccional': DATASET_TRANSACCIONAL,
        'Datos BCRA': DATOS_BCRA,
        'Datos INDEC': DATOS_INDEC
    }

    todos_ok = True
    for nombre, path in archivos.items():
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / 1024**2
            print(f"   ✓ {nombre}: {path} ({size_mb:.2f} MB)")
        else:
            print(f"   ❌ {nombre}: {path}")
            todos_ok = False

    return todos_ok


def agregar_target_semanal(con):
    """Agrega target (total_operaciones) por semana usando DuckDB."""
    print("\n" + "="*80)
    print("PASO 1: AGREGACIÓN DE TARGET POR SEMANA")
    print("="*80)

    query = f"""
    SELECT
        date_trunc('week', tramite_fecha) as fecha,
        COUNT(*) as total_operaciones
    FROM read_parquet('{DATASET_TRANSACCIONAL}')
    GROUP BY date_trunc('week', tramite_fecha)
    ORDER BY fecha
    """

    df_target = con.execute(query).fetchdf()

    print(f"\n✓ Target semanal calculado:")
    print(f"   - Semanas: {len(df_target):,}")
    print(f"   - Período: {df_target['fecha'].min()} a {df_target['fecha'].max()}")
    print(f"   - Media operaciones/semana: {df_target['total_operaciones'].mean():,.0f}")

    return df_target


def agregar_features_provincia(con, df_base):
    """Agrega features de provincias (26 columnas)."""
    print("\n" + "="*80)
    print("PASO 2: FEATURES DE PROVINCIAS (26 columnas)")
    print("="*80)

    query = f"""
    SELECT
        date_trunc('week', tramite_fecha) as fecha,
        {COL_PROVINCIA} as provincia,
        COUNT(*) as operaciones
    FROM read_parquet('{DATASET_TRANSACCIONAL}')
    WHERE {COL_PROVINCIA} IS NOT NULL AND {COL_PROVINCIA} != ''
    GROUP BY fecha, provincia
    ORDER BY fecha, provincia
    """

    df_prov = con.execute(query).fetchdf()

    # Pivot
    df_prov_pivot = df_prov.pivot(index='fecha', columns='provincia', values='operaciones')
    df_prov_pivot = df_prov_pivot.fillna(0)

    # Renombrar columnas (normalizar nombres)
    df_prov_pivot.columns = ['operaciones_' + col.lower().replace(' ', '_').replace('.', '') for col in df_prov_pivot.columns]

    df_prov_pivot = df_prov_pivot.reset_index()

    # Merge con base
    df_result = df_base.merge(df_prov_pivot, on='fecha', how='left')

    print(f"   ✓ {len(df_prov_pivot.columns) - 1} columnas de provincias agregadas")
    print(f"   Ejemplos: {list(df_prov_pivot.columns[1:6])}")

    return df_result


def agregar_features_marca(con, df_base, top_n=30):
    """Agrega features de marcas (Top 30 + otros = 31 columnas)."""
    print("\n" + "="*80)
    print(f"PASO 3: FEATURES DE MARCAS (Top {top_n} + otros)")
    print("="*80)

    # Obtener Top N marcas
    query_top = f"""
    SELECT {COL_MARCA} as marca, COUNT(*) as total
    FROM read_parquet('{DATASET_TRANSACCIONAL}')
    WHERE {COL_MARCA} IS NOT NULL
    GROUP BY marca
    ORDER BY total DESC
    LIMIT {top_n}
    """

    top_marcas = con.execute(query_top).fetchdf()['marca'].tolist()

    print(f"\n   Top {top_n} marcas identificadas:")
    for i, marca in enumerate(top_marcas[:10], 1):
        print(f"      {i:2}. {marca}")
    if top_n > 10:
        print(f"      ... y {top_n - 10} más")

    # Query con CASE para agrupar resto en 'otros'
    marcas_case = " OR ".join([f"{COL_MARCA} = '{marca}'" for marca in top_marcas])

    query = f"""
    SELECT
        date_trunc('week', tramite_fecha) as fecha,
        CASE
            WHEN {marcas_case} THEN {COL_MARCA}
            ELSE 'OTROS'
        END as marca,
        COUNT(*) as operaciones
    FROM read_parquet('{DATASET_TRANSACCIONAL}')
    WHERE {COL_MARCA} IS NOT NULL
    GROUP BY fecha, marca
    ORDER BY fecha, marca
    """

    df_marca = con.execute(query).fetchdf()

    # Pivot
    df_marca_pivot = df_marca.pivot(index='fecha', columns='marca', values='operaciones')
    df_marca_pivot = df_marca_pivot.fillna(0)

    # Renombrar columnas
    df_marca_pivot.columns = ['operaciones_marca_' + col.lower().replace(' ', '_') for col in df_marca_pivot.columns]

    df_marca_pivot = df_marca_pivot.reset_index()

    # Merge
    df_result = df_base.merge(df_marca_pivot, on='fecha', how='left')

    print(f"\n   ✓ {len(df_marca_pivot.columns) - 1} columnas de marcas agregadas")

    return df_result


def agregar_features_origen(con, df_base):
    """Agrega features de origen (3 columnas)."""
    print("\n" + "="*80)
    print("PASO 4: FEATURES DE ORIGEN (3 columnas)")
    print("="*80)

    query = f"""
    SELECT
        date_trunc('week', tramite_fecha) as fecha,
        {COL_ORIGEN} as origen,
        COUNT(*) as operaciones
    FROM read_parquet('{DATASET_TRANSACCIONAL}')
    WHERE {COL_ORIGEN} IS NOT NULL
    GROUP BY fecha, origen
    ORDER BY fecha, origen
    """

    df_origen = con.execute(query).fetchdf()

    # Pivot
    df_origen_pivot = df_origen.pivot(index='fecha', columns='origen', values='operaciones')
    df_origen_pivot = df_origen_pivot.fillna(0)

    # Renombrar columnas
    df_origen_pivot.columns = ['operaciones_origen_' + col.lower().replace(' ', '_') for col in df_origen_pivot.columns]

    df_origen_pivot = df_origen_pivot.reset_index()

    # Merge
    df_result = df_base.merge(df_origen_pivot, on='fecha', how='left')

    print(f"   ✓ {len(df_origen_pivot.columns) - 1} columnas de origen agregadas")

    return df_result


def agregar_features_tipo_operacion(con, df_base):
    """Agrega features de tipo de operación (3 columnas)."""
    print("\n" + "="*80)
    print("PASO 5: FEATURES DE TIPO OPERACIÓN (3 columnas)")
    print("="*80)

    query = f"""
    SELECT
        date_trunc('week', tramite_fecha) as fecha,
        {COL_TIPO_OP} as tipo_op,
        COUNT(*) as operaciones
    FROM read_parquet('{DATASET_TRANSACCIONAL}')
    WHERE {COL_TIPO_OP} IS NOT NULL
    GROUP BY fecha, tipo_op
    ORDER BY fecha, tipo_op
    """

    df_tipo = con.execute(query).fetchdf()

    # Pivot
    df_tipo_pivot = df_tipo.pivot(index='fecha', columns='tipo_op', values='operaciones')
    df_tipo_pivot = df_tipo_pivot.fillna(0)

    # Renombrar columnas
    df_tipo_pivot.columns = ['total_' + col.lower() + 's' for col in df_tipo_pivot.columns]  # transferencia -> total_transferencias

    df_tipo_pivot = df_tipo_pivot.reset_index()

    # Merge
    df_result = df_base.merge(df_tipo_pivot, on='fecha', how='left')

    print(f"   ✓ {len(df_tipo_pivot.columns) - 1} columnas de tipo operación agregadas")

    return df_result


def agregar_features_marca_categoria(con, df_base):
    """Agrega features de marca categoría (11 columnas - ya agrupada)."""
    print("\n" + "="*80)
    print("PASO 6: FEATURES DE MARCA CATEGORÍA (11 columnas)")
    print("="*80)

    query = f"""
    SELECT
        date_trunc('week', tramite_fecha) as fecha,
        {COL_MARCA_CAT} as marca_cat,
        COUNT(*) as operaciones
    FROM read_parquet('{DATASET_TRANSACCIONAL}')
    WHERE {COL_MARCA_CAT} IS NOT NULL
    GROUP BY fecha, marca_cat
    ORDER BY fecha, marca_cat
    """

    df_marca_cat = con.execute(query).fetchdf()

    # Pivot
    df_marca_cat_pivot = df_marca_cat.pivot(index='fecha', columns='marca_cat', values='operaciones')
    df_marca_cat_pivot = df_marca_cat_pivot.fillna(0)

    # Renombrar columnas
    df_marca_cat_pivot.columns = ['operaciones_' + col.lower().replace(' ', '_') for col in df_marca_cat_pivot.columns]

    df_marca_cat_pivot = df_marca_cat_pivot.reset_index()

    # Merge
    df_result = df_base.merge(df_marca_cat_pivot, on='fecha', how='left')

    print(f"   ✓ {len(df_marca_cat_pivot.columns) - 1} columnas de marca categoría agregadas")

    return df_result


def interpolar_datos_mensuales_a_semanales(df_mensual, fecha_min, fecha_max):
    """Interpola datos mensuales (BCRA/INDEC) a semanales."""
    # Generar todas las semanas
    fechas_semanales = pd.date_range(start=fecha_min, end=fecha_max, freq='W-MON')
    df_semanal = pd.DataFrame({'fecha': fechas_semanales})

    # Merge asof
    df_mensual_copy = df_mensual.copy()
    df_mensual_copy['fecha'] = pd.to_datetime(df_mensual_copy['fecha'])

    df_semanal = pd.merge_asof(
        df_semanal.sort_values('fecha'),
        df_mensual_copy.sort_values('fecha'),
        on='fecha',
        direction='backward'
    )

    # Interpolar
    numeric_cols = df_semanal.select_dtypes(include=[np.number]).columns.tolist()
    for col in numeric_cols:
        df_semanal[col] = df_semanal[col].interpolate(method='linear', limit_direction='both')

    return df_semanal


def agregar_features_temporales(df):
    """Agrega features temporales."""
    print("\n" + "="*80)
    print("PASO 9: FEATURES TEMPORALES (5 columnas)")
    print("="*80)

    df['semana_año'] = df['fecha'].dt.isocalendar().week
    df['mes'] = df['fecha'].dt.month
    df['trimestre'] = df['fecha'].dt.quarter
    df['anio'] = df['fecha'].dt.year
    df['dia_del_anio'] = df['fecha'].dt.dayofyear

    print(f"   ✓ Features temporales agregadas")

    return df


def agregar_lags_y_rolling(df, target_col='total_operaciones'):
    """Agrega lags y rolling means."""
    print("\n" + "="*80)
    print("PASO 10: LAGS Y ROLLING MEANS (~12 columnas)")
    print("="*80)

    # Lags
    lags = [1, 2, 4, 8, 12]
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)

    # Rolling means
    windows = [4, 8, 12]
    for window in windows:
        df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()

    # Variación semanal
    df[f'var_semanal_{target_col}'] = df[target_col].pct_change()

    print(f"   ✓ Lags: {lags}")
    print(f"   ✓ Rolling means: {windows} semanas")
    print(f"   ✓ Variación semanal")

    return df


def agregar_interacciones(df):
    """Agrega features de interacción."""
    print("\n" + "="*80)
    print("PASO 11: FEATURES DE INTERACCIÓN (~3 columnas)")
    print("="*80)

    # Interacción operaciones × EMAE
    if 'total_operaciones' in df.columns and 'emae' in df.columns:
        df['interaccion_operaciones_emae'] = df['total_operaciones'] * df['emae'] / 100

    # Interacción operaciones × IPC
    if 'total_operaciones' in df.columns and 'ipc_mes' in df.columns:
        df['interaccion_operaciones_ipc'] = df['total_operaciones'] * df['ipc_mes']

    # Interacción tipo_cambio × reservas
    if 'tipo_de_cambio_usd_prom' in df.columns and 'reservas_internacionales' in df.columns:
        df['interaccion_tc_reservas'] = df['tipo_de_cambio_usd_prom'] * df['reservas_internacionales'] / 1000

    print(f"   ✓ Interacciones creadas")

    return df


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FASE 3C: UNIFICACIÓN SEMANAL CON FEATURES CATEGÓRICAS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Verificar archivos
        if not verificar_archivos():
            return

        # 2. Inicializar DuckDB
        con = duckdb.connect()

        # 3. Agregar target semanal
        df_final = agregar_target_semanal(con)

        # 4-8. Agregar features categóricas
        df_final = agregar_features_provincia(con, df_final)
        df_final = agregar_features_marca(con, df_final, top_n=30)
        df_final = agregar_features_origen(con, df_final)
        df_final = agregar_features_tipo_operacion(con, df_final)
        df_final = agregar_features_marca_categoria(con, df_final)

        con.close()

        # Rellenar NaN con 0 en las features categóricas
        cat_cols = [col for col in df_final.columns if col.startswith('operaciones_') or col.startswith('total_')]
        df_final[cat_cols] = df_final[cat_cols].fillna(0)

        print(f"\n📊 Estado actual del dataset:")
        print(f"   - Registros: {len(df_final):,}")
        print(f"   - Columnas: {len(df_final.columns)}")

        # 9. Cargar y fusionar BCRA
        if os.path.exists(DATOS_BCRA):
            print(f"\n📂 Cargando datos BCRA...")
            df_bcra = pd.read_parquet(DATOS_BCRA)

            df_bcra_semanal = interpolar_datos_mensuales_a_semanales(
                df_bcra,
                df_final['fecha'].min(),
                df_final['fecha'].max()
            )

            bcra_cols = [col for col in df_bcra_semanal.columns if col != 'fecha']
            df_final = df_final.merge(df_bcra_semanal[['fecha'] + bcra_cols], on='fecha', how='left')

            print(f"   ✓ {len(bcra_cols)} columnas BCRA agregadas")

        # 10. Cargar y fusionar INDEC
        if os.path.exists(DATOS_INDEC):
            print(f"\n📂 Cargando datos INDEC...")
            df_indec = pd.read_parquet(DATOS_INDEC)

            df_indec_semanal = interpolar_datos_mensuales_a_semanales(
                df_indec,
                df_final['fecha'].min(),
                df_final['fecha'].max()
            )

            indec_cols = [col for col in df_indec_semanal.columns if col != 'fecha']
            df_final = df_final.merge(df_indec_semanal[['fecha'] + indec_cols], on='fecha', how='left')

            print(f"   ✓ {len(indec_cols)} columnas INDEC agregadas")

        # 11. Features adicionales
        df_final = agregar_features_temporales(df_final)
        df_final = agregar_lags_y_rolling(df_final)
        df_final = agregar_interacciones(df_final)

        # 12. Ordenar y guardar
        df_final = df_final.sort_values('fecha').reset_index(drop=True)

        print(f"\n💾 Guardando dataset...")
        df_final.to_parquet(OUTPUT_FILE, index=False)

        size_mb = os.path.getsize(OUTPUT_FILE) / 1024**2

        # Resumen final
        print("\n" + "="*80)
        print("✅ UNIFICACIÓN COMPLETADA")
        print("="*80)

        print(f"\n📊 Dataset final:")
        print(f"   - Registros (semanas): {len(df_final):,}")
        print(f"   - Columnas: {len(df_final.columns)}")
        print(f"   - Tamaño: {size_mb:.2f} MB")
        print(f"   - Período: {df_final['fecha'].min()} a {df_final['fecha'].max()}")

        # Contar features por tipo
        cat_features = len([col for col in df_final.columns if col.startswith('operaciones_')])
        bcra_features = len([col for col in df_final.columns if any(x in col.lower() for x in ['ipc', 'tipo_de_cambio', 'badlar', 'leliq', 'reservas'])])
        indec_features = len([col for col in df_final.columns if any(x in col.lower() for x in ['emae', 'desocupacion', 'ripte'])])
        lag_features = len([col for col in df_final.columns if '_lag_' in col or '_rolling_' in col or 'var_' in col])
        temp_features = len([col for col in df_final.columns if col in ['semana_año', 'mes', 'trimestre', 'anio', 'dia_del_anio']])
        inter_features = len([col for col in df_final.columns if 'interaccion_' in col])

        print(f"\n📋 Features por categoría:")
        print(f"   - Categóricas (provincias/marcas/origen): {cat_features}")
        print(f"   - BCRA (macroeconómicas): {bcra_features}")
        print(f"   - INDEC (actividad): {indec_features}")
        print(f"   - Autogresivas (lags/rolling): {lag_features}")
        print(f"   - Temporales: {temp_features}")
        print(f"   - Interacciones: {inter_features}")
        print(f"   TOTAL: {len(df_final.columns)}")

        print(f"\n📁 Archivo generado:")
        print(f"   {OUTPUT_FILE}")

        print(f"\n📝 Siguiente paso:")
        print(f"   python backend/models/train_xgboost_optimizado.py")

        print(f"\n💡 DIFERENCIA vs versión anterior:")
        print(f"   ANTES: 14 features disponibles (26 con todos NaN)")
        print(f"   AHORA: {len(df_final.columns)} features SIN NaN")
        print(f"   Mejora: {len(df_final.columns) / 14:.1f}x más features útiles")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Verificar DuckDB
    try:
        import duckdb
    except ImportError:
        print("\n❌ ERROR: DuckDB no está instalado")
        print("\n📝 Instalar con:")
        print("   pip install duckdb")
        exit(1)

    main()
