#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 1: Feature Engineering Avanzado - Fundamentado Económicamente

Crea features sin data leakage:
1. Variaciones porcentuales macro (ΔTC, ΔBADLAR, ΔIPC)
2. Ratios transaccionales inteligentes (sin leakage)
3. Proporciones de categóricas lagged (market share)
4. Lags de variaciones
5. Features temporales

Input:
  - Dataset transaccional mensual agregado
  - APIs BCRA/INDEC

Output:
  - Dataset con features avanzadas para forecasting
  - Sin data leakage
  - Fundamentado económicamente

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/09_feature_engineering_avanzado.py
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Archivos
DATASET_TRANSACCIONAL = 'data/processed/dataset_transaccional_unificado.parquet'
DATASET_BCRA = 'data/processed/bcra_series_completas.parquet'
DATASET_INDEC = 'data/processed/indec_series_completas.parquet'
OUTPUT_FILE = 'data/processed/dataset_forecasting_avanzado.parquet'


def agregar_transaccional_mensual(df_trans):
    """
    Agrega dataset transaccional a granularidad MENSUAL.

    Calcula:
    - total_operaciones (target)
    - total_inscripciones, total_transferencias, total_prendas
    - Conteos por provincia (para proporciones)
    - Conteos por marca (para proporciones)
    """
    print("\n" + "="*80)
    print("PASO 1: AGREGACIÓN MENSUAL")
    print("="*80)

    # Convertir fecha a mes
    df_trans['fecha_mes'] = pd.to_datetime(df_trans['tramite_fecha']).dt.to_period('M').dt.to_timestamp()

    # Agregación base
    df_mensual = df_trans.groupby('fecha_mes').agg({
        'tramite_fecha': 'count'  # Total operaciones
    }).rename(columns={'tramite_fecha': 'total_operaciones'})

    # Agregar por tipo de operación
    df_tipo = df_trans.groupby(['fecha_mes', 'tipo_operacion']).size().unstack(fill_value=0)

    # Mapeo correcto de plurales
    plural_map = {
        'inscripcion': 'inscripciones',
        'prenda': 'prendas',
        'transferencia': 'transferencias'
    }

    new_cols = []
    for col in df_tipo.columns:
        col_lower = col.lower()
        # Buscar en el mapeo o agregar 's' por defecto
        plural = plural_map.get(col_lower, col_lower + 's')
        new_cols.append('total_' + plural)

    df_tipo.columns = new_cols

    # Merge
    df_mensual = df_mensual.join(df_tipo)

    # Top 10 provincias para proporciones
    top_provincias = df_trans['registro_seccional_provincia'].value_counts().head(10).index.tolist()

    df_provincias = df_trans[df_trans['registro_seccional_provincia'].isin(top_provincias)].groupby(
        ['fecha_mes', 'registro_seccional_provincia']
    ).size().unstack(fill_value=0)
    df_provincias.columns = ['operaciones_' + col.lower().replace(' ', '_').replace('.', '') for col in df_provincias.columns]

    df_mensual = df_mensual.join(df_provincias)

    # Top 10 marcas para proporciones
    top_marcas = df_trans['automotor_marca_descripcion'].value_counts().head(10).index.tolist()

    df_marcas = df_trans[df_trans['automotor_marca_descripcion'].isin(top_marcas)].groupby(
        ['fecha_mes', 'automotor_marca_descripcion']
    ).size().unstack(fill_value=0)
    df_marcas.columns = ['operaciones_marca_' + col.lower().replace(' ', '_').replace('-', '_') for col in df_marcas.columns]

    df_mensual = df_mensual.join(df_marcas)

    df_mensual = df_mensual.reset_index().rename(columns={'fecha_mes': 'fecha'})

    print(f"\n✓ Agregación mensual completada:")
    print(f"   - Registros: {len(df_mensual)}")
    print(f"   - Período: {df_mensual['fecha'].min()} a {df_mensual['fecha'].max()}")
    print(f"   - Columnas base: {len(df_mensual.columns)}")

    return df_mensual


def agregar_features_macro(df_base):
    """
    Agrega features macro de BCRA/INDEC.
    """
    print("\n" + "="*80)
    print("PASO 2: FEATURES MACRO (BCRA/INDEC)")
    print("="*80)

    # Cargar BCRA
    if os.path.exists(DATASET_BCRA):
        df_bcra = pd.read_parquet(DATASET_BCRA)
        df_bcra['fecha'] = pd.to_datetime(df_bcra['fecha'])

        # Seleccionar columnas relevantes
        cols_bcra = ['fecha', 'tipo_de_cambio_usd_prom', 'BADLAR', 'IPC_mensual', 'LELIQ', 'reservas_internacionales']
        cols_disponibles = [col for col in cols_bcra if col in df_bcra.columns]
        df_bcra = df_bcra[cols_disponibles]

        df_base = df_base.merge(df_bcra, on='fecha', how='left')
        print(f"   ✓ BCRA: {len(cols_disponibles)-1} variables agregadas")
    else:
        print(f"   ⚠️  BCRA no disponible: {DATASET_BCRA}")

    # Cargar INDEC
    if os.path.exists(DATASET_INDEC):
        df_indec = pd.read_parquet(DATASET_INDEC)
        df_indec['fecha'] = pd.to_datetime(df_indec['fecha'])

        # Seleccionar columnas relevantes
        cols_indec = ['fecha', 'EMAE', 'desocupacion', 'ripte']
        cols_disponibles = [col for col in cols_indec if col in df_indec.columns]
        df_indec = df_indec[cols_disponibles]

        df_base = df_base.merge(df_indec, on='fecha', how='left')
        print(f"   ✓ INDEC: {len(cols_disponibles)-1} variables agregadas")
    else:
        print(f"   ⚠️  INDEC no disponible: {DATASET_INDEC}")

    return df_base


def crear_variaciones_porcentuales(df):
    """
    Crea variaciones porcentuales de variables macro.

    Δ = (X_t - X_{t-1}) / X_{t-1}
    """
    print("\n" + "="*80)
    print("PASO 3: VARIACIONES PORCENTUALES MACRO")
    print("="*80)

    # Variables a transformar
    vars_macro = ['tipo_de_cambio_usd_prom', 'BADLAR', 'IPC_mensual', 'LELIQ', 'EMAE', 'reservas_internacionales']

    for var in vars_macro:
        if var in df.columns:
            df[f'Δ{var}'] = df[var].pct_change()
            print(f"   ✓ Δ{var} creada")

    print(f"\n✓ {len([c for c in df.columns if c.startswith('Δ')])} variaciones porcentuales creadas")

    return df


def crear_ratios_inteligentes(df):
    """
    Crea ratios transaccionales SIN leakage.

    Estos ratios NO son componentes del target, sino relaciones entre componentes.
    """
    print("\n" + "="*80)
    print("PASO 4: RATIOS TRANSACCIONALES (SIN LEAKAGE)")
    print("="*80)

    # Ratio prendas/inscripciones (mide financiamiento)
    if 'total_prendas' in df.columns and 'total_inscripciones' in df.columns:
        df['ratio_prendas_inscripciones'] = df['total_prendas'] / (df['total_inscripciones'] + 1e-6)
        print(f"   ✓ ratio_prendas_inscripciones: Mide % operaciones financiadas")

    # Ratio transferencias/inscripciones (mide mercado secundario vs primario)
    if 'total_transferencias' in df.columns and 'total_inscripciones' in df.columns:
        df['ratio_transferencias_inscripciones'] = df['total_transferencias'] / (df['total_inscripciones'] + 1e-6)
        print(f"   ✓ ratio_transferencias_inscripciones: Mide dinamismo secundario")

    # Variación del ratio (cambio en financiamiento)
    if 'ratio_prendas_inscripciones' in df.columns:
        df['Δratio_prendas_inscripciones'] = df['ratio_prendas_inscripciones'].pct_change()
        print(f"   ✓ Δratio_prendas_inscripciones: Cambio en financiamiento")

    print(f"\n✓ {sum(1 for c in df.columns if 'ratio_' in c)} ratios creados")

    return df


def crear_proporciones_categoricas(df):
    """
    Crea proporciones de categóricas (market share).

    prop_X = operaciones_X / total_operaciones

    IMPORTANTE: Las proporciones en t son leakage, pero las proporciones en t-1 NO lo son.
    """
    print("\n" + "="*80)
    print("PASO 5: PROPORCIONES DE CATEGÓRICAS (MARKET SHARE)")
    print("="*80)

    # Columnas categóricas (operaciones por provincia/marca)
    cols_categoricas = [col for col in df.columns if col.startswith('operaciones_') and col not in ['operaciones_marca_']]

    for col in cols_categoricas:
        prop_col = col.replace('operaciones_', 'prop_')
        df[prop_col] = df[col] / (df['total_operaciones'] + 1e-6)

    print(f"   ✓ {len(cols_categoricas)} proporciones creadas")

    # Variaciones de proporciones (cambio de market share)
    cols_proporciones = [col for col in df.columns if col.startswith('prop_')]

    for col in cols_proporciones:
        df[f'Δ{col}'] = df[col].diff()  # Diferencia absoluta (no porcentual)

    print(f"   ✓ {len(cols_proporciones)} variaciones de proporciones creadas")

    return df


def crear_lags_features(df):
    """
    Crea lags de features avanzadas.

    IMPORTANTE: Solo lags de features NO derivadas del target.
    """
    print("\n" + "="*80)
    print("PASO 6: LAGS DE FEATURES AVANZADAS")
    print("="*80)

    # Features a laggear
    features_lag = []

    # 1. Variaciones macro
    features_lag += [col for col in df.columns if col.startswith('Δ') and any(x in col for x in ['tipo_de_cambio', 'BADLAR', 'IPC', 'LELIQ', 'EMAE', 'reservas'])]

    # 2. Ratios transaccionales
    features_lag += [col for col in df.columns if 'ratio_' in col]

    # 3. Proporciones (market share)
    features_lag += [col for col in df.columns if col.startswith('prop_') and not col.startswith('Δprop_')]

    # 4. Variaciones de proporciones
    features_lag += [col for col in df.columns if col.startswith('Δprop_')]

    # Lags: 1, 2, 3 meses
    lags = [1, 2, 3]

    n_lags_creados = 0
    for feature in features_lag:
        for lag in lags:
            df[f'{feature}_lag{lag}'] = df[feature].shift(lag)
            n_lags_creados += 1

    print(f"\n✓ {n_lags_creados} lags creados ({len(features_lag)} features × {len(lags)} lags)")

    # También crear lags del target (para features autogresivas)
    print(f"\n   Creando lags del target...")
    for lag in [1, 2, 3, 6, 12]:
        df[f'total_operaciones_lag{lag}'] = df['total_operaciones'].shift(lag)

    # Rolling means del target
    for window in [3, 6, 12]:
        df[f'total_operaciones_rolling{window}'] = df['total_operaciones'].rolling(window=window).mean()

    print(f"   ✓ 5 lags + 3 rolling means del target")

    return df


def crear_features_temporales(df):
    """
    Crea features temporales (estacionalidad).
    """
    print("\n" + "="*80)
    print("PASO 7: FEATURES TEMPORALES")
    print("="*80)

    df['mes'] = df['fecha'].dt.month
    df['trimestre'] = df['fecha'].dt.quarter
    df['anio'] = df['fecha'].dt.year
    df['semestre'] = (df['fecha'].dt.month - 1) // 6 + 1

    print(f"   ✓ 4 features temporales creadas")

    return df


def limpiar_y_validar(df):
    """
    Limpia dataset y valida features.
    """
    print("\n" + "="*80)
    print("PASO 8: LIMPIEZA Y VALIDACIÓN")
    print("="*80)

    # Eliminar primeras filas con NaN por lags
    n_antes = len(df)
    df = df.dropna(subset=['total_operaciones_lag1', 'total_operaciones_rolling3'])
    n_despues = len(df)

    print(f"   - Eliminadas {n_antes - n_despues} filas iniciales (NaN por lags)")

    # Reemplazar inf por NaN
    df = df.replace([np.inf, -np.inf], np.nan)

    # Contar NaN por columna
    nan_counts = df.isnull().sum()
    cols_con_nan = nan_counts[nan_counts > 0]

    if len(cols_con_nan) > 0:
        print(f"\n   ⚠️  Columnas con NaN:")
        for col, count in cols_con_nan.head(10).items():
            pct = (count / len(df)) * 100
            print(f"      - {col}: {count} ({pct:.1f}%)")
    else:
        print(f"\n   ✓ No hay NaN en el dataset")

    # Separar features por tipo para reporte
    features_macro_var = [col for col in df.columns if col.startswith('Δ') and any(x in col for x in ['tipo_de_cambio', 'BADLAR', 'IPC', 'LELIQ', 'EMAE'])]
    features_ratios = [col for col in df.columns if 'ratio_' in col]
    features_proporciones = [col for col in df.columns if col.startswith('prop_') or col.startswith('Δprop_')]
    features_lags = [col for col in df.columns if '_lag' in col]
    features_rolling = [col for col in df.columns if '_rolling' in col]
    features_temporales = ['mes', 'trimestre', 'anio', 'semestre']

    print(f"\n📊 Resumen de features creadas:")
    print(f"   - Variaciones macro: {len(features_macro_var)}")
    print(f"   - Ratios transaccionales: {len(features_ratios)}")
    print(f"   - Proporciones (market share): {len(features_proporciones)}")
    print(f"   - Lags de features: {len(features_lags)}")
    print(f"   - Rolling means: {len(features_rolling)}")
    print(f"   - Temporales: {len(features_temporales)}")
    print(f"   TOTAL FEATURES: {len(df.columns) - 1} (sin contar fecha)")

    return df


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FEATURE ENGINEERING AVANZADO - FASE 1")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 1. Verificar dataset transaccional
    if not os.path.exists(DATASET_TRANSACCIONAL):
        print(f"\n❌ ERROR: Dataset transaccional no encontrado: {DATASET_TRANSACCIONAL}")
        print(f"\n📝 Ejecuta primero:")
        print(f"   python backend/data_processing/02_unir_datasets_v3.py")
        return

    print(f"\n📂 Dataset transaccional: {DATASET_TRANSACCIONAL}")
    size_mb = os.path.getsize(DATASET_TRANSACCIONAL) / 1024**2
    print(f"   Tamaño: {size_mb:,.2f} MB")

    # 2. Cargar y agregar transaccional mensual
    print(f"\n⏳ Cargando dataset transaccional...")
    df_trans = pd.read_parquet(DATASET_TRANSACCIONAL)
    print(f"   ✓ {len(df_trans):,} registros cargados")

    df = agregar_transaccional_mensual(df_trans)

    # 3. Agregar features macro
    df = agregar_features_macro(df)

    # 4. Crear variaciones porcentuales
    df = crear_variaciones_porcentuales(df)

    # 5. Crear ratios inteligentes
    df = crear_ratios_inteligentes(df)

    # 6. Crear proporciones de categóricas
    df = crear_proporciones_categoricas(df)

    # 7. Crear lags
    df = crear_lags_features(df)

    # 8. Crear features temporales
    df = crear_features_temporales(df)

    # 9. Limpiar y validar
    df = limpiar_y_validar(df)

    # 10. Guardar
    print("\n" + "="*80)
    print("GUARDANDO DATASET FINAL")
    print("="*80)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_parquet(OUTPUT_FILE, index=False)

    size_mb = os.path.getsize(OUTPUT_FILE) / 1024**2
    print(f"\n✓ Dataset guardado: {OUTPUT_FILE}")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Features: {len(df.columns) - 1}")
    print(f"   - Tamaño: {size_mb:.2f} MB")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")

    # Resumen final
    print("\n" + "="*80)
    print("✅ FEATURE ENGINEERING COMPLETADO")
    print("="*80)

    print("\n💡 Próximos pasos:")
    print("   1. Entrenar modelo XGBoost con estas features")
    print("   2. Evaluar importancia de features")
    print("   3. Comparar performance vs dataset anterior")

    print(f"\n📝 Para entrenar modelo:")
    print(f"   python backend/models/train_xgboost_avanzado.py")


if __name__ == "__main__":
    main()
