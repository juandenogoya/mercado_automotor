#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 3B: UNIFICACIÓN DE DATASETS PARA FORECASTING - GRANULARIDAD SEMANAL

Similar al script mensual, pero agrega por SEMANA en lugar de por MES.
Esto aumenta los registros de ~81 a ~350, mejorando el entrenamiento ML.

Input:
  - data/processed/dataset_transaccional_unificado.parquet
  - data/processed/bcra_datos_mensuales.parquet
  - data/processed/indec_datos_mensuales.parquet

Output:
  - data/processed/dataset_forecasting_completo_semanal.parquet

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/07b_unificar_datasets_forecasting_semanal.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# Configuración
DATASET_TRANSACCIONAL = 'data/processed/dataset_transaccional_unificado.parquet'
DATOS_BCRA = 'data/processed/bcra_datos_mensuales.parquet'
DATOS_INDEC = 'data/processed/indec_datos_mensuales.parquet'

OUTPUT_FILE = 'data/processed/dataset_forecasting_completo_semanal.parquet'
OUTPUT_DIR = os.path.dirname(OUTPUT_FILE)

os.makedirs(OUTPUT_DIR, exist_ok=True)


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

    if not todos_ok:
        print(f"\n❌ ERROR: Faltan archivos de entrada")
        print(f"\n📝 Ejecuta primero:")
        print(f"   1. python backend/data_processing/02_unir_datasets_v3.py")
        print(f"   2. python backend/data_processing/04_obtener_datos_bcra_v2.py")
        print(f"   3. python backend/data_processing/05_obtener_datos_indec.py")
        return False

    return True


def agregar_datos_semanales(df):
    """
    Agrega datos transaccionales por SEMANA.

    Args:
        df: DataFrame con transacciones individuales

    Returns:
        DataFrame agregado por semana
    """
    print("\n" + "="*80)
    print("AGREGACIÓN SEMANAL DE DATOS TRANSACCIONALES")
    print("="*80)

    # Convertir fecha a datetime si no lo es
    if not pd.api.types.is_datetime64_any_dtype(df['tramite_fecha']):
        df['tramite_fecha'] = pd.to_datetime(df['tramite_fecha'])

    # Crear columna de semana (inicio de semana = lunes)
    df['fecha_semana'] = df['tramite_fecha'].dt.to_period('W-MON').dt.start_time

    print(f"\n📅 Período de datos:")
    print(f"   Desde: {df['tramite_fecha'].min()}")
    print(f"   Hasta: {df['tramite_fecha'].max()}")

    # VERIFICAR SI TIENE COLUMNA tipo_operacion O COLUMNAS DIRECTAS
    if 'tipo_operacion' in df.columns:
        print("   Método: Pivotar tipo_operacion por semana")

        # Agrupar por semana y tipo_operacion
        df_semanal = df.groupby(['fecha_semana', 'tipo_operacion']).size().reset_index(name='cantidad')
        df_semanal = df_semanal.pivot(index='fecha_semana', columns='tipo_operacion', values='cantidad')

        # Flexible column renaming
        columnas_actuales = [col for col in df_semanal.columns if col != 'fecha_semana']
        columnas_rename = {}
        for col in columnas_actuales:
            col_lower = col.lower()
            if 'inscripc' in col_lower or 'inscripcion' in col_lower:
                columnas_rename[col] = 'total_inscripciones'
            elif 'transfer' in col_lower:
                columnas_rename[col] = 'total_transferencias'
            elif 'prenda' in col_lower:
                columnas_rename[col] = 'total_prendas'

        df_semanal = df_semanal.rename(columns=columnas_rename)
        df_semanal = df_semanal.reset_index()

    else:
        print("   Método: Columnas directas por semana")

        # Agrupar directamente por semana
        agg_dict = {}
        if 'total_inscripciones' in df.columns:
            agg_dict['total_inscripciones'] = 'sum'
        if 'total_transferencias' in df.columns:
            agg_dict['total_transferencias'] = 'sum'
        if 'total_prendas' in df.columns:
            agg_dict['total_prendas'] = 'sum'

        df_semanal = df.groupby('fecha_semana').agg(agg_dict).reset_index()

    # Renombrar fecha_semana a fecha
    df_semanal = df_semanal.rename(columns={'fecha_semana': 'fecha'})

    # Rellenar NaN con 0
    cols_totales = [col for col in df_semanal.columns if col.startswith('total_')]
    if cols_totales:
        df_semanal[cols_totales] = df_semanal[cols_totales].fillna(0)

        # Calcular total_operaciones
        df_semanal['total_operaciones'] = df_semanal[cols_totales].sum(axis=1)
    else:
        print("❌ ERROR: No se encontraron columnas de totales")
        return None

    print(f"\n✓ Agregación semanal completada:")
    print(f"   - Semanas: {len(df_semanal):,}")
    print(f"   - Período: {df_semanal['fecha'].min()} a {df_semanal['fecha'].max()}")
    print(f"   - Total operaciones media: {df_semanal['total_operaciones'].mean():,.0f}")

    # Agregar features de provincias por semana
    if 'provincia_normalized' in df.columns:
        print(f"\n📊 Agregando features de provincias...")
        prov_semanal = df.groupby(['fecha_semana', 'provincia_normalized']).size().reset_index(name='cantidad')
        prov_semanal = prov_semanal.pivot(index='fecha_semana', columns='provincia_normalized', values='cantidad')
        prov_semanal.columns = [f'operaciones_{col.lower()}' for col in prov_semanal.columns]
        prov_semanal = prov_semanal.reset_index()
        prov_semanal = prov_semanal.rename(columns={'fecha_semana': 'fecha'})

        df_semanal = df_semanal.merge(prov_semanal, on='fecha', how='left')
        print(f"   ✓ {len(prov_semanal.columns) - 1} provincias agregadas")

    # Agregar features de marcas por semana
    if 'marca_normalized' in df.columns:
        print(f"\n📊 Agregando features de marcas...")
        marca_semanal = df.groupby(['fecha_semana', 'marca_normalized']).size().reset_index(name='cantidad')
        marca_semanal = marca_semanal.pivot(index='fecha_semana', columns='marca_normalized', values='cantidad')
        marca_semanal.columns = [f'operaciones_{col.lower()}' for col in marca_semanal.columns]
        marca_semanal = marca_semanal.reset_index()
        marca_semanal = marca_semanal.rename(columns={'fecha_semana': 'fecha'})

        df_semanal = df_semanal.merge(marca_semanal, on='fecha', how='left')
        print(f"   ✓ {len(marca_semanal.columns) - 1} marcas agregadas")

    return df_semanal


def interpolar_datos_mensuales_a_semanales(df_mensual, fecha_min, fecha_max):
    """
    Interpola datos mensuales a semanales.

    Args:
        df_mensual: DataFrame con datos mensuales (BCRA/INDEC)
        fecha_min: Fecha mínima semanal
        fecha_max: Fecha máxima semanal

    Returns:
        DataFrame interpolado a semanas
    """
    # Generar todas las semanas en el rango
    fechas_semanales = pd.date_range(start=fecha_min, end=fecha_max, freq='W-MON')
    df_semanal = pd.DataFrame({'fecha': fechas_semanales})

    # Merge con datos mensuales (usando merge_asof para unir por fecha más cercana)
    df_mensual_copy = df_mensual.copy()
    df_mensual_copy['fecha'] = pd.to_datetime(df_mensual_copy['fecha'])

    df_semanal = pd.merge_asof(
        df_semanal.sort_values('fecha'),
        df_mensual_copy.sort_values('fecha'),
        on='fecha',
        direction='backward'
    )

    # Interpolar linealmente valores faltantes
    numeric_cols = df_semanal.select_dtypes(include=[np.number]).columns.tolist()
    if 'fecha' in numeric_cols:
        numeric_cols.remove('fecha')

    for col in numeric_cols:
        df_semanal[col] = df_semanal[col].interpolate(method='linear', limit_direction='both')

    return df_semanal


def agregar_features_temporales(df):
    """Agrega features temporales (semana del año, mes, trimestre, etc.)."""
    print("\n" + "="*80)
    print("AGREGANDO FEATURES TEMPORALES")
    print("="*80)

    df['semana_año'] = df['fecha'].dt.isocalendar().week
    df['mes'] = df['fecha'].dt.month
    df['trimestre'] = df['fecha'].dt.quarter
    df['anio'] = df['fecha'].dt.year
    df['dia_del_anio'] = df['fecha'].dt.dayofyear

    print(f"   ✓ Features temporales agregadas: semana_año, mes, trimestre, anio, dia_del_anio")

    return df


def agregar_lags_y_rolling(df, target_col='total_operaciones'):
    """Agrega lags y rolling means del target."""
    print("\n" + "="*80)
    print("AGREGANDO LAGS Y ROLLING MEANS")
    print("="*80)

    # Lags semanales (ajustados para granularidad semanal)
    lags = [1, 2, 4, 8, 12]  # 1, 2, 4, 8, 12 semanas atrás
    for lag in lags:
        df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)

    print(f"   ✓ Lags agregados: {lags}")

    # Rolling means semanales
    windows = [4, 8, 12]  # 4, 8, 12 semanas (aprox 1, 2, 3 meses)
    for window in windows:
        df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window=window).mean()

    print(f"   ✓ Rolling means agregados: {windows} semanas")

    # Variación semanal
    df[f'var_semanal_{target_col}'] = df[target_col].pct_change()

    print(f"   ✓ Variación semanal agregada")

    return df


def agregar_interacciones(df):
    """Agrega features de interacción entre variables."""
    print("\n" + "="*80)
    print("AGREGANDO FEATURES DE INTERACCIÓN")
    print("="*80)

    interacciones_creadas = []

    # Interacción operaciones × EMAE
    if 'total_operaciones' in df.columns and 'emae' in df.columns:
        df['interaccion_operaciones_emae'] = df['total_operaciones'] * df['emae'] / 100
        interacciones_creadas.append('operaciones × EMAE')

    # Interacción operaciones × IPC
    if 'total_operaciones' in df.columns and 'ipc_mes' in df.columns:
        df['interaccion_operaciones_ipc'] = df['total_operaciones'] * df['ipc_mes']
        interacciones_creadas.append('operaciones × IPC')

    # Interacción tipo_cambio × reservas
    if 'tipo_de_cambio_usd_prom' in df.columns and 'reservas_internacionales' in df.columns:
        df['interaccion_tc_reservas'] = df['tipo_de_cambio_usd_prom'] * df['reservas_internacionales'] / 1000
        interacciones_creadas.append('tipo_cambio × reservas')

    print(f"   ✓ Interacciones creadas: {', '.join(interacciones_creadas)}")

    return df


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FASE 3B: UNIFICACIÓN SEMANAL PARA FORECASTING")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Verificar archivos
        if not verificar_archivos():
            return

        # 2. Cargar dataset transaccional
        print(f"\n📂 Cargando dataset transaccional...")
        df_trans = pd.read_parquet(DATASET_TRANSACCIONAL)
        print(f"   ✓ {len(df_trans):,} registros cargados")

        # 3. Agregar por semana
        df_semanal = agregar_datos_semanales(df_trans)
        if df_semanal is None:
            return

        # 4. Cargar y procesar datos BCRA
        print(f"\n📂 Cargando datos BCRA...")
        df_bcra = pd.read_parquet(DATOS_BCRA)
        print(f"   ✓ {len(df_bcra):,} registros mensuales cargados")

        # Interpolar BCRA a semanal
        print(f"\n🔄 Interpolando BCRA a granularidad semanal...")
        df_bcra_semanal = interpolar_datos_mensuales_a_semanales(
            df_bcra,
            df_semanal['fecha'].min(),
            df_semanal['fecha'].max()
        )
        print(f"   ✓ {len(df_bcra_semanal):,} registros semanales interpolados")

        # 5. Cargar y procesar datos INDEC
        print(f"\n📂 Cargando datos INDEC...")
        df_indec = pd.read_parquet(DATOS_INDEC)
        print(f"   ✓ {len(df_indec):,} registros mensuales cargados")

        # Interpolar INDEC a semanal
        print(f"\n🔄 Interpolando INDEC a granularidad semanal...")
        df_indec_semanal = interpolar_datos_mensuales_a_semanales(
            df_indec,
            df_semanal['fecha'].min(),
            df_semanal['fecha'].max()
        )
        print(f"   ✓ {len(df_indec_semanal):,} registros semanales interpolados")

        # 6. Unificar todos los datasets
        print(f"\n🔗 Unificando datasets...")
        df_final = df_semanal.copy()

        # Merge con BCRA (sin columna fecha duplicada)
        bcra_cols = [col for col in df_bcra_semanal.columns if col != 'fecha']
        df_final = df_final.merge(
            df_bcra_semanal[['fecha'] + bcra_cols],
            on='fecha',
            how='left'
        )

        # Merge con INDEC (sin columna fecha duplicada)
        indec_cols = [col for col in df_indec_semanal.columns if col != 'fecha']
        df_final = df_final.merge(
            df_indec_semanal[['fecha'] + indec_cols],
            on='fecha',
            how='left'
        )

        print(f"   ✓ Datasets unificados: {len(df_final):,} semanas, {len(df_final.columns)} columnas")

        # 7. Agregar features adicionales
        df_final = agregar_features_temporales(df_final)
        df_final = agregar_lags_y_rolling(df_final)
        df_final = agregar_interacciones(df_final)

        # 8. Ordenar por fecha
        df_final = df_final.sort_values('fecha').reset_index(drop=True)

        # 9. Guardar
        print(f"\n💾 Guardando dataset unificado...")
        df_final.to_parquet(OUTPUT_FILE, index=False)

        size_mb = os.path.getsize(OUTPUT_FILE) / 1024**2
        print(f"   ✓ Archivo guardado: {OUTPUT_FILE} ({size_mb:.2f} MB)")

        # Resumen final
        print("\n" + "="*80)
        print("✅ UNIFICACIÓN SEMANAL COMPLETADA")
        print("="*80)

        print(f"\n📊 Dataset final:")
        print(f"   - Registros (semanas): {len(df_final):,}")
        print(f"   - Columnas: {len(df_final.columns)}")
        print(f"   - Período: {df_final['fecha'].min()} a {df_final['fecha'].max()}")
        print(f"   - Target media: {df_final['total_operaciones'].mean():,.0f}")
        print(f"   - Target std: {df_final['total_operaciones'].std():,.0f}")

        print(f"\n📁 Archivo generado:")
        print(f"   {OUTPUT_FILE}")

        print(f"\n📝 Siguiente paso:")
        print(f"   python backend/models/train_xgboost_optimizado.py")
        print(f"   (Modificar INPUT_FILE para usar dataset semanal)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
