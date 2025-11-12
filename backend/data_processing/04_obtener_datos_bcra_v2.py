#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar datos históricos del BCRA (API oficial v4.0).

Objetivo:
- Descargar series temporales macroeconómicas del BCRA
- Guardar en formato Parquet optimizado
- Crear dataset con frecuencia mensual para forecasting

Variables descargadas:
- IPC (inflación mensual e interanual)
- Tipo de cambio mayorista
- Tasas de interés (BADLAR, LELIQ)
- Reservas internacionales
- Base monetaria

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/04_obtener_datos_bcra_v2.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.external_apis.bcra_api_oficial import BCRAClientOficial

# Directorio de salida
OUTPUT_DIR = 'data/processed'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def descargar_datos_bcra(fecha_desde='2019-01-01', fecha_hasta=None):
    """
    Descarga datos del BCRA.

    Args:
        fecha_desde: Fecha de inicio (YYYY-MM-DD)
        fecha_hasta: Fecha de fin (YYYY-MM-DD), None = hoy

    Returns:
        DataFrame con datos descargados
    """
    print("\n" + "="*80)
    print("DESCARGA DE DATOS BCRA (API OFICIAL V4.0)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Crear cliente
    client = BCRAClientOficial()

    # Variables a descargar (priorizadas para forecasting automotor)
    variable_ids = [
        # Inflación (muy importante)
        27,  # IPC Nivel General - Variación mensual
        28,  # IPC Nivel General - Variación interanual

        # Tipo de cambio (importante)
        5,   # Tipo de cambio mayorista (USD/ARS)

        # Tasas de interés (importante para financiamiento)
        7,   # BADLAR bancos privados
        11,  # LELIQ

        # Agregados monetarios (contexto macro)
        1,   # Reservas internacionales
        15,  # Base monetaria
        16,  # Circulación monetaria

        # Depósitos (poder adquisitivo)
        19,  # Depósitos en cuenta corriente
        20,  # Depósitos en caja de ahorro
        21   # Depósitos a plazo fijo
    ]

    print(f"\n📋 Variables a descargar: {len(variable_ids)}")
    for variable_id in variable_ids:
        nombre = client.get_variable_name(variable_id)
        print(f"   {variable_id:3} - {nombre}")

    print(f"\n⏱️  Período: {fecha_desde} a {fecha_hasta or 'hoy'}")
    print(f"\n🔄 Iniciando descarga...")

    # Descargar datos
    df = client.get_multiple_variables(
        variable_ids=variable_ids,
        desde=fecha_desde,
        hasta=fecha_hasta,
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


def agregar_a_nivel_mensual(df):
    """
    Agrega datos a nivel mensual (promedio por mes).

    Args:
        df: DataFrame con datos diarios

    Returns:
        DataFrame agregado mensualmente
    """
    print(f"\n📊 Agregando a nivel mensual...")

    # Asegurar que fecha es datetime
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Crear columna año-mes
    df['anio_mes'] = df['fecha'].dt.to_period('M')

    # Columnas numéricas a agregar
    cols_numericas = df.select_dtypes(include=['float64', 'int64']).columns.tolist()

    # Excluir columnas de tiempo
    cols_a_agregar = [col for col in cols_numericas if col not in ['anio', 'mes', 'trimestre', 'dia_anio']]

    # Agrupar por mes y calcular promedio
    df_mensual = df.groupby('anio_mes')[cols_a_agregar].mean().reset_index()

    # Convertir period a timestamp
    df_mensual['fecha'] = df_mensual['anio_mes'].dt.to_timestamp()
    df_mensual = df_mensual.drop('anio_mes', axis=1)

    # Agregar features temporales
    df_mensual = agregar_features_temporales(df_mensual)

    print(f"   ✓ Datos agregados a nivel mensual")
    print(f"   - Registros originales: {len(df):,}")
    print(f"   - Registros mensuales: {len(df_mensual):,}")

    return df_mensual


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

    variables_clave = [
        'IPC Nivel General - Variación mensual',
        'Tipo de cambio mayorista (USD/ARS)',
        'BADLAR bancos privados',
        'Reservas internacionales'
    ]

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
    print("OBTENCIÓN DE DATOS MACROECONÓMICOS - BCRA (API OFICIAL)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # Parámetros
        FECHA_DESDE = '2019-01-01'  # Coincidir con datos de autos
        FECHA_HASTA = None  # Hasta hoy

        # 1. Descargar datos
        df = descargar_datos_bcra(FECHA_DESDE, FECHA_HASTA)

        if df is None:
            return

        # 2. Agregar features temporales
        df = agregar_features_temporales(df)

        # 3. Agregar a nivel mensual
        df_mensual = agregar_a_nivel_mensual(df)

        # 4. Validar datos
        validar_datos(df_mensual)

        # 5. Guardar datasets
        print(f"\n{'='*80}")
        print("GUARDANDO DATASETS")
        print('='*80)

        # Guardar datos diarios
        guardar_dataset(df, 'bcra_datos_diarios')

        # Guardar datos mensuales
        guardar_dataset(df_mensual, 'bcra_datos_mensuales')

        # Resumen final
        print(f"\n{'='*80}")
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print('='*80)
        print(f"\n📁 Archivos generados:")
        print(f"   - {OUTPUT_DIR}/bcra_datos_diarios.parquet (datos originales)")
        print(f"   - {OUTPUT_DIR}/bcra_datos_mensuales.parquet (agregado mensual)")
        print(f"\n💡 Próximo paso:")
        print(f"   - Descargar datos de INDEC")
        print(f"   - Combinar con dataset transaccional para forecasting")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
