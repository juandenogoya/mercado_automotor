#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar datos históricos de INDEC (datos.gob.ar).

Objetivo:
- Descargar series temporales de indicadores económicos y laborales
- Guardar en formato Parquet optimizado
- Crear dataset con frecuencia mensual para forecasting

Variables descargadas:
- EMAE: Estimador Mensual de Actividad Económica (mensual)
- Desocupación: Tasa de desempleo (trimestral)
- Tasa de Actividad (trimestral)
- Tasa de Empleo (trimestral)

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/05_obtener_datos_indec.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.external_apis.indec_client import INDECClient

# Directorio de salida
OUTPUT_DIR = 'data/processed'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def descargar_datos_indec(fecha_desde='2019-01-01', fecha_hasta=None):
    """
    Descarga datos de INDEC.

    Args:
        fecha_desde: Fecha de inicio (YYYY-MM-DD)
        fecha_hasta: Fecha de fin (YYYY-MM-DD), None = hoy

    Returns:
        DataFrame con datos descargados
    """
    print("\n" + "="*80)
    print("DESCARGA DE DATOS INDEC (datos.gob.ar)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Crear cliente
    client = INDECClient()

    # Series a descargar (priorizadas para forecasting automotor)
    series_keys = [
        # Mensuales (mejores para forecasting)
        'EMAE',  # Actividad económica mensual (MUY IMPORTANTE)

        # Trimestrales (mercado laboral)
        'DESOCUPACION',  # Tasa de desempleo
        'ACTIVIDAD',  # Tasa de actividad
        'EMPLEO',  # Tasa de empleo
    ]

    print(f"\n📋 Series a descargar: {len(series_keys)}")
    for series_key in series_keys:
        nombre = client.VARIABLE_NAMES.get(series_key, series_key)
        frecuencia = client.FRECUENCIAS.get(series_key, 'U')
        print(f"   {series_key:15} - {nombre:50} ({frecuencia})")

    print(f"\n⏱️  Período: {fecha_desde} a {fecha_hasta or 'hoy'}")
    print(f"\n🔄 Iniciando descarga...")

    # Descargar datos
    df = client.get_multiple_series(
        series_keys=series_keys,
        start_date=fecha_desde,
        end_date=fecha_hasta,
        format='wide'
    )

    if df.empty:
        print("\n❌ No se descargaron datos")
        return None

    print(f"\n✓ Descarga completada")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Fecha mínima: {df['fecha'].min()}")
    print(f"   - Fecha máxima: {df['fecha'].max()}")
    print(f"   - Columnas: {len(df.columns)}")

    return df


def interpolar_trimestrales(df):
    """
    Interpola series trimestrales a nivel mensual.

    Args:
        df: DataFrame con datos (algunas series trimestrales)

    Returns:
        DataFrame con todas las series a nivel mensual
    """
    print(f"\n🛠️  Interpolando series trimestrales a mensual...")

    # Asegurar que fecha es datetime
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Crear índice mensual completo
    fecha_min = df['fecha'].min()
    fecha_max = df['fecha'].max()

    # Generar rango mensual
    fechas_mensuales = pd.date_range(start=fecha_min, end=fecha_max, freq='MS')
    df_mensual = pd.DataFrame({'fecha': fechas_mensuales})

    # Hacer merge con datos originales
    df_mensual = df_mensual.merge(df, on='fecha', how='left')

    # Interpolar valores faltantes (para series trimestrales)
    columnas_numericas = df_mensual.select_dtypes(include=[np.number]).columns

    for col in columnas_numericas:
        # Interpolación lineal
        df_mensual[col] = df_mensual[col].interpolate(method='linear', limit_direction='both')

    print(f"   ✓ Series interpoladas a nivel mensual")
    print(f"   - Registros originales: {len(df):,}")
    print(f"   - Registros mensuales: {len(df_mensual):,}")

    return df_mensual


def agregar_features_temporales(df):
    """
    Agrega features temporales al dataset.

    Args:
        df: DataFrame con columna 'fecha'

    Returns:
        DataFrame con features temporales
    """
    print(f"\n🛠️  Agregando features temporales...")

    # Asegurar que fecha es datetime
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Features temporales
    df['anio'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['trimestre'] = df['fecha'].dt.quarter
    df['dia_anio'] = df['fecha'].dt.dayofyear

    # Features cíclicas (estacionalidad)
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)

    print(f"   ✓ Features agregadas: anio, mes, trimestre, mes_sin, mes_cos")

    return df


def validar_datos(df):
    """
    Valida calidad de los datos descargados.

    Args:
        df: DataFrame a validar
    """
    print(f"\n{'='*80}")
    print("VALIDACIÓN DE DATOS")
    print('='*80)

    # 1. Información general
    print(f"\n📊 INFORMACIÓN GENERAL:")
    print(f"   - Total registros: {len(df):,}")
    print(f"   - Total columnas: {len(df.columns)}")
    print(f"   - Memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # 2. Rango temporal
    print(f"\n📅 RANGO TEMPORAL:")
    print(f"   - Fecha mínima: {df['fecha'].min()}")
    print(f"   - Fecha máxima: {df['fecha'].max()}")
    print(f"   - Meses totales: {df['anio'].nunique() * 12 + df['mes'].nunique()}")

    # 3. Valores nulos
    print(f"\n🔍 VALORES NULOS:")
    nulos = df.isnull().sum()
    nulos_pct = 100 * nulos / len(df)

    for col in nulos.index:
        if nulos[col] > 0 and col not in ['anio', 'mes', 'trimestre', 'fecha']:
            print(f"   - {col:45} : {nulos[col]:5,} ({nulos_pct[col]:5.2f}%)")

    # 4. Estadísticas de variables clave
    print(f"\n📈 ESTADÍSTICAS DE VARIABLES CLAVE:")

    variables_clave = ['EMAE', 'DESOCUPACION', 'ACTIVIDAD', 'EMPLEO']

    for var in variables_clave:
        if var in df.columns:
            print(f"\n   {var}:")
            print(f"      Min: {df[var].min():.2f}")
            print(f"      Max: {df[var].max():.2f}")
            print(f"      Media: {df[var].mean():.2f}")
            print(f"      Mediana: {df[var].median():.2f}")


def guardar_dataset(df, nombre_archivo):
    """
    Guarda dataset en formato Parquet.

    Args:
        df: DataFrame a guardar
        nombre_archivo: Nombre del archivo (sin extensión)
    """
    print(f"\n💾 Guardando dataset...")

    # Parquet
    filepath_parquet = os.path.join(OUTPUT_DIR, f"{nombre_archivo}.parquet")
    df.to_parquet(filepath_parquet, index=False, engine='pyarrow', compression='snappy')

    size_mb = os.path.getsize(filepath_parquet) / 1024**2
    print(f"   ✓ Archivo Parquet guardado: {filepath_parquet}")
    print(f"   ✓ Tamaño: {size_mb:.2f} MB")

    # CSV (muestra)
    csv_path = os.path.join(OUTPUT_DIR, f"{nombre_archivo}_sample.csv")
    df.head(100).to_csv(csv_path, index=False, encoding='utf-8')
    print(f"   ✓ Muestra CSV guardada: {csv_path} (primeros 100 registros)")


def main():
    """Función principal."""
    print("="*80)
    print("OBTENCIÓN DE DATOS ECONÓMICOS - INDEC")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # Parámetros
        FECHA_DESDE = '2019-01-01'  # Coincidir con datos de autos y BCRA
        FECHA_HASTA = None  # Hasta hoy

        # 1. Descargar datos
        df = descargar_datos_indec(FECHA_DESDE, FECHA_HASTA)

        if df is None:
            return

        # 2. Interpolar trimestrales a mensual
        df_mensual = interpolar_trimestrales(df)

        # 3. Agregar features temporales
        df_mensual = agregar_features_temporales(df_mensual)

        # 4. Validar datos
        validar_datos(df_mensual)

        # 5. Guardar datasets
        print(f"\n{'='*80}")
        print("GUARDANDO DATASETS")
        print('='*80)

        # Guardar datos originales (con trimestrales)
        guardar_dataset(df, 'indec_datos_originales')

        # Guardar datos mensuales (interpolados)
        guardar_dataset(df_mensual, 'indec_datos_mensuales')

        # Resumen final
        print(f"\n{'='*80}")
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print('='*80)
        print(f"\n📁 Archivos generados:")
        print(f"   - {OUTPUT_DIR}/indec_datos_originales.parquet (datos sin interpolar)")
        print(f"   - {OUTPUT_DIR}/indec_datos_mensuales.parquet (interpolado mensual)")
        print(f"\n💡 Próximo paso:")
        print(f"   - Combinar BCRA + INDEC + datos transaccionales")
        print(f"   - Crear dataset final para forecasting")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
