#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 3: Unificación de Datasets para Forecasting

Este script unifica 3 fuentes de datos en un dataset mensual completo:
1. Dataset transaccional (inscripciones + transferencias + prendas) - agregado mensual
2. Datos BCRA (variables macroeconómicas)
3. Datos INDEC (actividad económica y mercado laboral)

Genera features avanzadas:
- Lags (1, 3, 6, 12 meses)
- Rolling means (3, 6, 12 meses)
- Ratios y tendencias
- Interacciones entre variables

Output: data/processed/dataset_forecasting_completo.parquet

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/07_unificar_datasets_forecasting.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path

# Archivos de entrada
DATASET_TRANSACCIONAL = 'data/processed/dataset_transaccional_unificado.parquet'
BCRA_MENSUAL = 'data/processed/bcra_datos_mensuales.parquet'
INDEC_MENSUAL = 'data/processed/indec_datos_mensuales.parquet'

# Archivo de salida
OUTPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'


def verificar_archivos_entrada():
    """
    Verifica que todos los archivos de entrada existan.

    Returns:
        True si todos existen, False si falta alguno
    """
    print("\n" + "="*80)
    print("VERIFICACIÓN DE ARCHIVOS DE ENTRADA")
    print("="*80)

    archivos = [
        ("Dataset Transaccional", DATASET_TRANSACCIONAL),
        ("Datos BCRA", BCRA_MENSUAL),
        ("Datos INDEC", INDEC_MENSUAL)
    ]

    todos_existen = True

    for nombre, path in archivos:
        existe = os.path.exists(path)
        icono = "✓" if existe else "❌"
        print(f"   {icono} {nombre}: {path}")

        if not existe:
            todos_existen = False

    if not todos_existen:
        print("\n❌ ERROR: Faltan archivos de entrada")
        print("\n📝 Ejecuta primero:")
        print("   1. python backend/data_processing/02_unir_datasets_v3.py")
        print("   2. python backend/data_processing/04_obtener_datos_bcra_v2.py")
        print("   3. python backend/data_processing/05_obtener_datos_indec.py")
        return False

    print("\n✅ Todos los archivos de entrada están disponibles")
    return True


def agregar_transaccional_mensual(df_transaccional):
    """
    Agrega dataset transaccional a nivel mensual.

    Args:
        df_transaccional: DataFrame con datos transaccionales diarios

    Returns:
        DataFrame agregado mensualmente con conteos por tipo de operación
    """
    print("\n" + "="*80)
    print("PASO 1: AGREGACIÓN MENSUAL DEL DATASET TRANSACCIONAL")
    print("="*80)

    print(f"\n📊 Dataset original:")
    print(f"   - Registros: {len(df_transaccional):,}")

    # Verificar qué columna de fecha existe
    fecha_col = None
    for col in ['tramite_fecha', 'fecha']:
        if col in df_transaccional.columns:
            fecha_col = col
            break

    if fecha_col is None:
        print("❌ ERROR: No se encontró columna de fecha")
        return None

    print(f"   - Columna de fecha: {fecha_col}")
    print(f"   - Período: {df_transaccional[fecha_col].min()} a {df_transaccional[fecha_col].max()}")

    # Convertir fecha a datetime
    df = df_transaccional.copy()
    df[fecha_col] = pd.to_datetime(df[fecha_col])

    # Crear columna de fecha mensual
    df['fecha'] = df[fecha_col].dt.to_period('M').dt.to_timestamp()

    print(f"\n🔄 Agregando por mes...")

    # VERIFICAR SI TIENE COLUMNA tipo_operacion O COLUMNAS DIRECTAS
    if 'tipo_operacion' in df.columns:
        print("   Método: Pivotar tipo_operacion")

        # Agrupar por mes y tipo_operacion
        df_mensual = df.groupby(['fecha', 'tipo_operacion']).size().reset_index(name='cantidad')

        # Pivotar para tener columnas por tipo de operación
        df_mensual = df_mensual.pivot(index='fecha', columns='tipo_operacion', values='cantidad')
        df_mensual = df_mensual.reset_index()

        # Rellenar NaN con 0
        df_mensual = df_mensual.fillna(0)

        # Limpiar nombre de columnas
        df_mensual.columns.name = None

        print(f"   Columnas después del pivot: {list(df_mensual.columns)}")

        # Renombrar columnas (buscar flexible)
        columnas_actuales = [col for col in df_mensual.columns if col != 'fecha']

        # Mapeo flexible de nombres
        columnas_rename = {}
        for col in columnas_actuales:
            col_lower = col.lower()
            if 'inscripc' in col_lower or 'inscripcion' in col_lower:
                columnas_rename[col] = 'total_inscripciones'
            elif 'transfer' in col_lower:
                columnas_rename[col] = 'total_transferencias'
            elif 'prenda' in col_lower:
                columnas_rename[col] = 'total_prendas'

        print(f"   Renombrando: {columnas_rename}")
        df_mensual = df_mensual.rename(columns=columnas_rename)
    else:
        print("   Método: Sumar columnas directas")

        # Sumar por mes (las columnas ya están separadas)
        df_mensual = df.groupby('fecha').agg({
            col: 'sum' for col in ['inscripcion', 'prenda', 'transferencia'] if col in df.columns
        }).reset_index()

        # Renombrar
        columnas_rename = {
            'inscripcion': 'total_inscripciones',
            'transferencia': 'total_transferencias',
            'prenda': 'total_prendas'
        }
        df_mensual = df_mensual.rename(columns=columnas_rename)

    # Calcular total general
    cols_totales = [col for col in df_mensual.columns if col.startswith('total_')]
    if cols_totales:
        df_mensual['total_operaciones'] = df_mensual[cols_totales].sum(axis=1)
    else:
        print("❌ ERROR: No se encontraron columnas de totales")
        return None

    print(f"\n✓ Agregación completada:")
    print(f"   - Meses únicos: {len(df_mensual):,}")
    print(f"   - Período: {df_mensual['fecha'].min()} a {df_mensual['fecha'].max()}")
    print(f"   - Columnas creadas: {list(df_mensual.columns)}")
    print(f"   - Total operaciones (primeras 5):")
    print(f"      {df_mensual[['fecha', 'total_operaciones']].head().to_string(index=False)}")

    return df_mensual


def agregar_features_provincia_marca(df_transaccional, df_mensual):
    """
    Agrega features de provincias y marcas más importantes.

    Args:
        df_transaccional: DataFrame transaccional original
        df_mensual: DataFrame mensual base

    Returns:
        DataFrame con features adicionales
    """
    print("\n" + "="*80)
    print("PASO 2: FEATURES DE PROVINCIAS Y MARCAS")
    print("="*80)

    df = df_transaccional.copy()
    df['tramite_fecha'] = pd.to_datetime(df['tramite_fecha'])
    df['fecha'] = df['tramite_fecha'].dt.to_period('M').dt.to_timestamp()

    # Top 5 provincias por volumen
    top_provincias = df['registro_seccional_provincia'].value_counts().head(5).index.tolist()
    print(f"\n🏙️  Top 5 provincias: {top_provincias}")

    for provincia in top_provincias:
        df_prov = df[df['registro_seccional_provincia'] == provincia]
        df_prov_mensual = df_prov.groupby('fecha').size().reset_index(name=f'operaciones_{provincia.lower().replace(" ", "_")}')
        df_mensual = df_mensual.merge(df_prov_mensual, on='fecha', how='left')

    # Top 5 marcas por volumen
    top_marcas = df['automotor_marca_descripcion'].value_counts().head(5).index.tolist()
    print(f"🚗 Top 5 marcas: {top_marcas}")

    for marca in top_marcas:
        df_marca = df[df['automotor_marca_descripcion'] == marca]
        df_marca_mensual = df_marca.groupby('fecha').size().reset_index(name=f'operaciones_{marca.lower().replace(" ", "_")}')
        df_mensual = df_mensual.merge(df_marca_mensual, on='fecha', how='left')

    # Rellenar NaN con 0
    df_mensual = df_mensual.fillna(0)

    print(f"\n✓ Features agregadas: {len(df_mensual.columns) - len(['fecha', 'total_inscripciones', 'total_transferencias', 'total_prendas', 'total_operaciones'])} nuevas columnas")

    return df_mensual


def merge_con_bcra(df_base, df_bcra):
    """
    Hace merge con datos de BCRA.

    Args:
        df_base: DataFrame base mensual
        df_bcra: DataFrame con datos BCRA

    Returns:
        DataFrame combinado
    """
    print("\n" + "="*80)
    print("PASO 3: MERGE CON DATOS BCRA")
    print("="*80)

    print(f"\n📊 Datos BCRA:")
    print(f"   - Registros: {len(df_bcra):,}")
    print(f"   - Período: {df_bcra['fecha'].min()} a {df_bcra['fecha'].max()}")
    print(f"   - Variables: {list(df_bcra.columns)}")

    # Asegurar que fecha es datetime
    df_bcra['fecha'] = pd.to_datetime(df_bcra['fecha'])

    # Merge (left join para mantener todos los meses del dataset base)
    df_combined = df_base.merge(df_bcra, on='fecha', how='left')

    print(f"\n✓ Merge completado:")
    print(f"   - Registros resultantes: {len(df_combined):,}")
    print(f"   - Columnas totales: {len(df_combined.columns)}")

    # Reporte de valores faltantes en variables BCRA
    bcra_cols = [col for col in df_bcra.columns if col != 'fecha']
    nulls_info = []
    for col in bcra_cols:
        if col in df_combined.columns:
            nulls = df_combined[col].isnull().sum()
            if nulls > 0:
                nulls_info.append((col, nulls))

    if nulls_info:
        print(f"\n⚠️  Valores faltantes en variables BCRA:")
        for col, nulls in nulls_info[:5]:  # Mostrar primeras 5
            print(f"   - {col}: {nulls:,} ({(nulls/len(df_combined)*100):.1f}%)")

    return df_combined


def merge_con_indec(df_base, df_indec):
    """
    Hace merge con datos de INDEC.

    Args:
        df_base: DataFrame base mensual
        df_indec: DataFrame con datos INDEC

    Returns:
        DataFrame combinado
    """
    print("\n" + "="*80)
    print("PASO 4: MERGE CON DATOS INDEC")
    print("="*80)

    print(f"\n📊 Datos INDEC:")
    print(f"   - Registros: {len(df_indec):,}")
    print(f"   - Período: {df_indec['fecha'].min()} a {df_indec['fecha'].max()}")
    print(f"   - Variables: {list(df_indec.columns)}")

    # Asegurar que fecha es datetime
    df_indec['fecha'] = pd.to_datetime(df_indec['fecha'])

    # Eliminar columnas duplicadas de features temporales si existen
    cols_temporales = ['anio', 'mes', 'trimestre', 'dia_anio', 'mes_sin', 'mes_cos']
    df_indec_clean = df_indec.drop(columns=[col for col in cols_temporales if col in df_indec.columns], errors='ignore')

    # Merge (left join para mantener todos los meses del dataset base)
    df_combined = df_base.merge(df_indec_clean, on='fecha', how='left')

    print(f"\n✓ Merge completado:")
    print(f"   - Registros resultantes: {len(df_combined):,}")
    print(f"   - Columnas totales: {len(df_combined.columns)}")

    # Reporte de valores faltantes en variables INDEC
    indec_cols = [col for col in df_indec_clean.columns if col != 'fecha']
    nulls_info = []
    for col in indec_cols:
        if col in df_combined.columns:
            nulls = df_combined[col].isnull().sum()
            if nulls > 0:
                nulls_info.append((col, nulls))

    if nulls_info:
        print(f"\n⚠️  Valores faltantes en variables INDEC:")
        for col, nulls in nulls_info:
            print(f"   - {col}: {nulls:,} ({(nulls/len(df_combined)*100):.1f}%)")

    return df_combined


def agregar_features_temporales(df):
    """
    Agrega features temporales.

    Args:
        df: DataFrame con columna 'fecha'

    Returns:
        DataFrame con features temporales
    """
    print("\n" + "="*80)
    print("PASO 5: FEATURES TEMPORALES")
    print("="*80)

    df['anio'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['trimestre'] = df['fecha'].dt.quarter

    # Features cíclicas
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
    df['trimestre_sin'] = np.sin(2 * np.pi * df['trimestre'] / 4)
    df['trimestre_cos'] = np.cos(2 * np.pi * df['trimestre'] / 4)

    print(f"\n✓ Features temporales agregadas:")
    print(f"   - anio, mes, trimestre")
    print(f"   - mes_sin, mes_cos")
    print(f"   - trimestre_sin, trimestre_cos")

    return df


def agregar_features_lags(df, columnas, lags=[1, 3, 6, 12]):
    """
    Agrega features de lags para columnas específicas.

    Args:
        df: DataFrame
        columnas: Lista de columnas para las que crear lags
        lags: Lista de períodos de lag

    Returns:
        DataFrame con features de lag
    """
    print("\n" + "="*80)
    print("PASO 6: FEATURES DE LAGS")
    print("="*80)

    print(f"\n🔄 Creando lags para {len(columnas)} columnas...")
    print(f"   Períodos: {lags}")

    features_creadas = 0

    for col in columnas:
        if col in df.columns:
            for lag in lags:
                nombre_lag = f"{col}_lag_{lag}"
                df[nombre_lag] = df[col].shift(lag)
                features_creadas += 1

    print(f"\n✓ {features_creadas} features de lag creadas")

    return df


def agregar_features_rolling(df, columnas, ventanas=[3, 6, 12]):
    """
    Agrega features de rolling means.

    Args:
        df: DataFrame
        columnas: Lista de columnas para las que crear rolling means
        ventanas: Lista de tamaños de ventana

    Returns:
        DataFrame con features rolling
    """
    print("\n" + "="*80)
    print("PASO 7: FEATURES ROLLING MEANS")
    print("="*80)

    print(f"\n🔄 Creando rolling means para {len(columnas)} columnas...")
    print(f"   Ventanas: {ventanas}")

    features_creadas = 0

    for col in columnas:
        if col in df.columns:
            for ventana in ventanas:
                nombre_rolling = f"{col}_rolling_{ventana}"
                df[nombre_rolling] = df[col].rolling(window=ventana, min_periods=1).mean()
                features_creadas += 1

    print(f"\n✓ {features_creadas} features rolling creadas")

    return df


def agregar_features_avanzadas(df):
    """
    Agrega features avanzadas (ratios, tendencias, interacciones).

    Args:
        df: DataFrame

    Returns:
        DataFrame con features avanzadas
    """
    print("\n" + "="*80)
    print("PASO 8: FEATURES AVANZADAS")
    print("="*80)

    features_creadas = []

    # Ratio inscripciones/transferencias
    if 'total_inscripciones' in df.columns and 'total_transferencias' in df.columns:
        df['ratio_insc_transf'] = df['total_inscripciones'] / (df['total_transferencias'] + 1)
        features_creadas.append('ratio_insc_transf')

    # Variación mensual de operaciones
    if 'total_operaciones' in df.columns:
        df['var_mensual_operaciones'] = df['total_operaciones'].pct_change()
        df['var_mensual_operaciones_abs'] = df['total_operaciones'].diff()
        features_creadas.extend(['var_mensual_operaciones', 'var_mensual_operaciones_abs'])

    # Tendencia (diferencia con rolling mean de 12 meses)
    if 'total_operaciones' in df.columns:
        rolling_12 = df['total_operaciones'].rolling(window=12, min_periods=1).mean()
        df['tendencia_operaciones'] = df['total_operaciones'] - rolling_12
        features_creadas.append('tendencia_operaciones')

    # Interacción: Operaciones * EMAE (si existe)
    emae_col = [col for col in df.columns if 'EMAE' in col.upper() or 'emae' in col.lower()]
    if emae_col and 'total_operaciones' in df.columns:
        df['interaccion_operaciones_emae'] = df['total_operaciones'] * df[emae_col[0]]
        features_creadas.append('interaccion_operaciones_emae')

    print(f"\n✓ {len(features_creadas)} features avanzadas creadas:")
    for feat in features_creadas:
        print(f"   - {feat}")

    return df


def limpiar_datos_finales(df):
    """
    Limpia y prepara datos finales.

    Args:
        df: DataFrame

    Returns:
        DataFrame limpio
    """
    print("\n" + "="*80)
    print("PASO 9: LIMPIEZA Y PREPARACIÓN FINAL")
    print("="*80)

    # Ordenar por fecha
    df = df.sort_values('fecha').reset_index(drop=True)

    # Reporte de valores faltantes
    print(f"\n📊 Reporte de valores faltantes:")
    nulls_total = df.isnull().sum()
    nulls_cols = nulls_total[nulls_total > 0].sort_values(ascending=False)

    if len(nulls_cols) > 0:
        print(f"   Columnas con valores faltantes: {len(nulls_cols)}")
        for col, count in nulls_cols.head(10).items():
            print(f"   - {col}: {count:,} ({(count/len(df)*100):.1f}%)")
    else:
        print(f"   ✓ No hay valores faltantes")

    # Información del dataset final
    print(f"\n📊 Dataset final:")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")
    print(f"   - Tamaño en memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    return df


def guardar_dataset_final(df, output_path):
    """
    Guarda dataset final en formato Parquet.

    Args:
        df: DataFrame a guardar
        output_path: Ruta del archivo de salida
    """
    print("\n" + "="*80)
    print("PASO 10: GUARDANDO DATASET FINAL")
    print("="*80)

    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Guardar
    df.to_parquet(output_path, index=False, engine='pyarrow', compression='snappy')

    # Información del archivo
    size_mb = os.path.getsize(output_path) / 1024**2

    print(f"\n✅ Dataset guardado exitosamente:")
    print(f"   - Archivo: {output_path}")
    print(f"   - Tamaño: {size_mb:.2f} MB")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FASE 3: UNIFICACIÓN DE DATASETS PARA FORECASTING")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Verificar archivos de entrada
    if not verificar_archivos_entrada():
        return

    try:
        # Cargar datasets base
        print("\n" + "="*80)
        print("CARGANDO DATASETS BASE")
        print("="*80)

        print(f"\n📥 Cargando dataset transaccional...")
        df_transaccional = pd.read_parquet(DATASET_TRANSACCIONAL)
        print(f"   ✓ {len(df_transaccional):,} registros cargados")

        print(f"\n📥 Cargando datos BCRA...")
        df_bcra = pd.read_parquet(BCRA_MENSUAL)
        print(f"   ✓ {len(df_bcra):,} registros cargados")

        print(f"\n📥 Cargando datos INDEC...")
        df_indec = pd.read_parquet(INDEC_MENSUAL)
        print(f"   ✓ {len(df_indec):,} registros cargados")

        # PASO 1: Agregar transaccional a nivel mensual
        df_mensual = agregar_transaccional_mensual(df_transaccional)

        # PASO 2: Agregar features de provincias y marcas
        df_mensual = agregar_features_provincia_marca(df_transaccional, df_mensual)

        # PASO 3: Merge con BCRA
        df_combined = merge_con_bcra(df_mensual, df_bcra)

        # PASO 4: Merge con INDEC
        df_combined = merge_con_indec(df_combined, df_indec)

        # PASO 5: Features temporales
        df_combined = agregar_features_temporales(df_combined)

        # PASO 6: Features de lags
        columnas_para_lag = ['total_operaciones', 'total_inscripciones', 'total_transferencias']
        df_combined = agregar_features_lags(df_combined, columnas_para_lag, lags=[1, 3, 6, 12])

        # PASO 7: Features rolling
        columnas_para_rolling = ['total_operaciones', 'total_inscripciones', 'total_transferencias']
        df_combined = agregar_features_rolling(df_combined, columnas_para_rolling, ventanas=[3, 6, 12])

        # PASO 8: Features avanzadas
        df_combined = agregar_features_avanzadas(df_combined)

        # PASO 9: Limpieza final
        df_final = limpiar_datos_finales(df_combined)

        # PASO 10: Guardar
        guardar_dataset_final(df_final, OUTPUT_FILE)

        # Resumen final
        print("\n" + "="*80)
        print("✅ UNIFICACIÓN COMPLETADA EXITOSAMENTE")
        print("="*80)

        print(f"\n📁 Dataset final:")
        print(f"   {OUTPUT_FILE}")
        print(f"\n📊 Contenido:")
        print(f"   - {len(df_final):,} registros mensuales")
        print(f"   - {len(df_final.columns)} features")
        print(f"   - Período: {df_final['fecha'].min().strftime('%Y-%m')} a {df_final['fecha'].max().strftime('%Y-%m')}")
        print(f"\n🎯 Listo para entrenar modelos de forecasting!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
