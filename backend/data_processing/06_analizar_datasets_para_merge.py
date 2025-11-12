#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar la estructura de los 3 datasets antes de unificarlos.

Analiza:
1. Dataset transaccional (inscripciones + transferencias + prendas)
2. Datos BCRA (mensuales)
3. Datos INDEC (mensuales)

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/06_analizar_datasets_para_merge.py
"""

import pandas as pd
import os
from datetime import datetime

# Archivos a analizar
DATASET_TRANSACCIONAL = 'data/processed/dataset_transaccional_unificado.parquet'
BCRA_MENSUAL = 'data/processed/bcra_datos_mensuales.parquet'
INDEC_MENSUAL = 'data/processed/indec_datos_mensuales.parquet'


def analizar_dataset(archivo_path, nombre):
    """
    Analiza un dataset y muestra su estructura.

    Args:
        archivo_path: Ruta al archivo Parquet
        nombre: Nombre descriptivo del dataset
    """
    print("\n" + "="*80)
    print(f"ANÁLISIS: {nombre}")
    print("="*80)

    if not os.path.exists(archivo_path):
        print(f"❌ Archivo no encontrado: {archivo_path}")
        return None

    # Leer dataset
    df = pd.read_parquet(archivo_path)

    print(f"\n📊 Información general:")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Tamaño en memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # Información de fechas
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])
        print(f"\n📅 Período:")
        print(f"   - Desde: {df['fecha'].min()}")
        print(f"   - Hasta: {df['fecha'].max()}")
        print(f"   - Días/Meses únicos: {df['fecha'].nunique():,}")

    # Listar columnas
    print(f"\n📋 Columnas ({len(df.columns)}):")
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        nulls = df[col].isnull().sum()
        null_pct = (nulls / len(df)) * 100
        print(f"   {i:2}. {col:40} | {str(dtype):15} | Nulls: {nulls:,} ({null_pct:.1f}%)")

    # Primeras filas
    print(f"\n🔍 Primeras 3 filas:")
    print(df.head(3).to_string())

    return df


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("ANÁLISIS DE DATASETS PARA UNIFICACIÓN - FASE 3")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Analizar cada dataset
    df_transaccional = analizar_dataset(DATASET_TRANSACCIONAL, "DATASET TRANSACCIONAL")
    df_bcra = analizar_dataset(BCRA_MENSUAL, "DATOS BCRA (MENSUALES)")
    df_indec = analizar_dataset(INDEC_MENSUAL, "DATOS INDEC (MENSUALES)")

    # Resumen comparativo
    print("\n" + "="*80)
    print("RESUMEN COMPARATIVO")
    print("="*80)

    datasets = [
        ("Transaccional", df_transaccional),
        ("BCRA", df_bcra),
        ("INDEC", df_indec)
    ]

    print(f"\n{'Dataset':<20} | {'Registros':>15} | {'Columnas':>10} | {'Período':<30}")
    print("-" * 80)

    for nombre, df in datasets:
        if df is not None:
            registros = f"{len(df):,}"
            columnas = len(df.columns)

            if 'fecha' in df.columns:
                df['fecha'] = pd.to_datetime(df['fecha'])
                periodo = f"{df['fecha'].min().strftime('%Y-%m-%d')} a {df['fecha'].max().strftime('%Y-%m-%d')}"
            else:
                periodo = "N/A"

            print(f"{nombre:<20} | {registros:>15} | {columnas:>10} | {periodo:<30}")

    # Estrategia de merge
    print("\n" + "="*80)
    print("ESTRATEGIA DE MERGE")
    print("="*80)

    print("""
Paso 1: Agregar dataset transaccional a nivel MENSUAL
   - Groupby por: anio + mes (o anio_mes)
   - Agregaciones:
     * Total inscripciones por mes
     * Total transferencias por mes
     * Total prendas por mes
     * Por provincia, marca, tipo, uso (top categorías)

Paso 2: Merge con BCRA (por fecha mensual)
   - Join type: LEFT (mantener todos los meses transaccionales)
   - On: fecha (año-mes)
   - Agregar variables macroeconómicas

Paso 3: Merge con INDEC (por fecha mensual)
   - Join type: LEFT (mantener todos los meses transaccionales)
   - On: fecha (año-mes)
   - Agregar variables de actividad económica

Paso 4: Feature Engineering Avanzado
   - Lags: 1, 3, 6, 12 meses
   - Rolling means: 3, 6, 12 meses
   - Ratios y tendencias
   - Interacciones entre variables

Paso 5: Guardar dataset final
   - Formato: Parquet con compresión
   - Ubicación: data/processed/dataset_forecasting_completo.parquet
    """)

    print("\n" + "="*80)
    print("✅ Análisis completado")
    print("="*80)


if __name__ == "__main__":
    main()
