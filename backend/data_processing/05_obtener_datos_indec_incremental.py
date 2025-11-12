#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script INCREMENTAL para actualizar datos de INDEC.

Diferencias con el script original:
- Detecta última fecha en el archivo Parquet
- Solo descarga datos nuevos desde esa fecha
- Hace APPEND al archivo existente (no sobrescribe)
- Si no existe archivo, descarga todo desde 2019-01-01

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/05_obtener_datos_indec_incremental.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.external_apis.indec_client import INDECClient

# Directorio de salida
OUTPUT_DIR = 'data/processed'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Archivos de salida
ARCHIVO_ORIGINAL = os.path.join(OUTPUT_DIR, 'indec_datos_originales.parquet')
ARCHIVO_MENSUAL = os.path.join(OUTPUT_DIR, 'indec_datos_mensuales.parquet')


def obtener_ultima_fecha(archivo_path):
    """
    Obtiene la última fecha disponible en un archivo Parquet.

    Args:
        archivo_path: Ruta al archivo Parquet

    Returns:
        Última fecha como string 'YYYY-MM-DD' o None si no existe
    """
    if not os.path.exists(archivo_path):
        return None

    try:
        df = pd.read_parquet(archivo_path)
        if df.empty:
            return None

        ultima_fecha = df['fecha'].max()
        return ultima_fecha.strftime('%Y-%m-%d')

    except Exception as e:
        print(f"⚠️  Error leyendo {archivo_path}: {e}")
        return None


def descargar_datos_indec_incremental(fecha_desde=None, fecha_hasta=None, modo='incremental'):
    """
    Descarga datos de INDEC de forma incremental.

    Args:
        fecha_desde: Fecha de inicio (YYYY-MM-DD), None = detectar automáticamente
        fecha_hasta: Fecha de fin (YYYY-MM-DD), None = hoy
        modo: 'incremental' (default) o 'full' (todo desde 2019)

    Returns:
        DataFrame con datos descargados
    """
    print("\n" + "="*80)
    print("ACTUALIZACIÓN INCREMENTAL DE DATOS INDEC")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Detectar última fecha si es modo incremental
    if modo == 'incremental' and fecha_desde is None:
        ultima_fecha = obtener_ultima_fecha(ARCHIVO_ORIGINAL)

        if ultima_fecha:
            # Para INDEC, restar 3 meses para asegurar actualizaciones trimestrales
            fecha_obj = datetime.strptime(ultima_fecha, '%Y-%m-%d') - timedelta(days=90)
            fecha_desde = fecha_obj.strftime('%Y-%m-%d')
            print(f"\n📅 Modo INCREMENTAL:")
            print(f"   - Última fecha en archivo: {ultima_fecha}")
            print(f"   - Descargando desde: {fecha_desde} (incluye 3 meses atrás para trimestrales)")
        else:
            # No existe archivo, descargar todo
            fecha_desde = '2019-01-01'
            print(f"\n📅 Modo INICIAL (archivo no existe):")
            print(f"   - Descargando todo desde: {fecha_desde}")
    elif modo == 'full':
        fecha_desde = '2019-01-01'
        print(f"\n📅 Modo FULL REFRESH:")
        print(f"   - Descargando todo desde: {fecha_desde}")

    # Fecha hasta
    if fecha_hasta is None:
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')

    print(f"   - Hasta: {fecha_hasta}")

    # Crear cliente
    client = INDECClient()

    # Series a descargar
    series_keys = [
        'EMAE',          # Mensual
        'DESOCUPACION',  # Trimestral
        'ACTIVIDAD',     # Trimestral
        'EMPLEO',        # Trimestral
        'SALARIOS',      # Mensual (RIPTE)
    ]

    print(f"\n📋 Series a descargar: {len(series_keys)}")
    for series_key in series_keys:
        nombre = client.VARIABLE_NAMES.get(series_key, series_key)
        frecuencia = client.FRECUENCIAS.get(series_key, 'U')
        print(f"   {series_key:15} - {nombre[:50]:50} ({frecuencia})")

    print(f"\n🔄 Iniciando descarga...\n")

    # Descargar datos
    df = client.get_multiple_series(
        series_keys=series_keys,
        start_date=fecha_desde,
        end_date=fecha_hasta,
        format='wide'
    )

    if df.empty:
        print("\n⚠️  No hay datos nuevos para descargar")
        return None

    print(f"\n✓ Descarga completada")
    print(f"   - Registros nuevos: {len(df):,}")
    print(f"   - Fecha mínima: {df['fecha'].min()}")
    print(f"   - Fecha máxima: {df['fecha'].max()}")

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

    df['fecha'] = pd.to_datetime(df['fecha'])

    fecha_min = df['fecha'].min()
    fecha_max = df['fecha'].max()

    fechas_mensuales = pd.date_range(start=fecha_min, end=fecha_max, freq='MS')
    df_mensual = pd.DataFrame({'fecha': fechas_mensuales})

    df_mensual = df_mensual.merge(df, on='fecha', how='left')

    columnas_numericas = df_mensual.select_dtypes(include=[np.number]).columns

    for col in columnas_numericas:
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

    df['fecha'] = pd.to_datetime(df['fecha'])

    df['anio'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month
    df['trimestre'] = df['fecha'].dt.quarter
    df['dia_anio'] = df['fecha'].dt.dayofyear

    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)

    print(f"   ✓ Features agregadas: anio, mes, trimestre, mes_sin, mes_cos")

    return df


def append_a_parquet(df_nuevo, archivo_path):
    """
    Agrega datos nuevos a un archivo Parquet existente.

    Args:
        df_nuevo: DataFrame con datos nuevos
        archivo_path: Ruta al archivo Parquet
    """
    if os.path.exists(archivo_path):
        # Leer datos existentes
        df_existente = pd.read_parquet(archivo_path)

        # Combinar y eliminar duplicados
        df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
        df_combinado = df_combinado.drop_duplicates(subset=['fecha'], keep='last')
        df_combinado = df_combinado.sort_values('fecha').reset_index(drop=True)

        print(f"   - Registros existentes: {len(df_existente):,}")
        print(f"   - Registros nuevos: {len(df_nuevo):,}")
        print(f"   - Total final: {len(df_combinado):,}")

        return df_combinado
    else:
        print(f"   - Archivo nuevo, creando...")
        return df_nuevo


def guardar_dataset(df, archivo_path, nombre):
    """
    Guarda dataset en formato Parquet.

    Args:
        df: DataFrame a guardar
        archivo_path: Ruta completa del archivo
        nombre: Nombre descriptivo para mensajes
    """
    print(f"\n💾 Guardando {nombre}...")

    df.to_parquet(archivo_path, index=False, engine='pyarrow', compression='snappy')

    size_mb = os.path.getsize(archivo_path) / 1024**2
    print(f"   ✓ Archivo guardado: {archivo_path}")
    print(f"   ✓ Tamaño: {size_mb:.2f} MB")


def main(modo='incremental'):
    """
    Función principal.

    Args:
        modo: 'incremental' (default) o 'full'
    """
    print("="*80)
    print(f"ACTUALIZACIÓN DATOS INDEC - Modo: {modo.upper()}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Descargar datos
        df_nuevo = descargar_datos_indec_incremental(modo=modo)

        if df_nuevo is None or df_nuevo.empty:
            print("\n✅ No hay actualizaciones necesarias")
            return

        # 2. Append a archivo original
        print(f"\n{'='*80}")
        print("ACTUALIZANDO ARCHIVO ORIGINAL")
        print('='*80)

        df_original_final = append_a_parquet(df_nuevo, ARCHIVO_ORIGINAL)
        guardar_dataset(df_original_final, ARCHIVO_ORIGINAL, "datos originales")

        # 3. Recalcular interpolación mensual (sobre todos los datos)
        print(f"\n{'='*80}")
        print("ACTUALIZANDO ARCHIVO MENSUAL")
        print('='*80)

        df_mensual = interpolar_trimestrales(df_original_final)
        df_mensual = agregar_features_temporales(df_mensual)
        guardar_dataset(df_mensual, ARCHIVO_MENSUAL, "datos mensuales")

        # Resumen final
        print(f"\n{'='*80}")
        print("✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
        print('='*80)
        print(f"\n📁 Archivos actualizados:")
        print(f"   - {ARCHIVO_ORIGINAL}")
        print(f"   - {ARCHIVO_MENSUAL}")
        print(f"\n📊 Estadísticas:")
        print(f"   - Registros originales: {len(df_original_final):,}")
        print(f"   - Registros mensuales: {len(df_mensual):,}")
        print(f"   - Período: {df_original_final['fecha'].min()} a {df_original_final['fecha'].max()}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Actualizar datos INDEC')
    parser.add_argument('--full-refresh', action='store_true',
                       help='Descargar todo desde 2019 (ignorar datos existentes)')

    args = parser.parse_args()

    modo = 'full' if args.full_refresh else 'incremental'
    main(modo=modo)
