#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script INCREMENTAL para actualizar datos del BCRA.

Diferencias con el script original:
- Detecta última fecha en el archivo Parquet
- Solo descarga datos nuevos desde esa fecha
- Hace APPEND al archivo existente (no sobrescribe)
- Si no existe archivo, descarga todo desde 2019-01-01

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/04_obtener_datos_bcra_incremental.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.external_apis.bcra_api_oficial import BCRAClientOficial

# Directorio de salida
OUTPUT_DIR = 'data/processed'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Archivos de salida
ARCHIVO_DIARIO = os.path.join(OUTPUT_DIR, 'bcra_datos_diarios.parquet')
ARCHIVO_MENSUAL = os.path.join(OUTPUT_DIR, 'bcra_datos_mensuales.parquet')


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


def descargar_datos_bcra_incremental(fecha_desde=None, fecha_hasta=None, modo='incremental'):
    """
    Descarga datos del BCRA de forma incremental.

    Args:
        fecha_desde: Fecha de inicio (YYYY-MM-DD), None = detectar automáticamente
        fecha_hasta: Fecha de fin (YYYY-MM-DD), None = hoy
        modo: 'incremental' (default) o 'full' (todo desde 2019)

    Returns:
        DataFrame con datos descargados
    """
    print("\n" + "="*80)
    print("ACTUALIZACIÓN INCREMENTAL DE DATOS BCRA")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Detectar última fecha si es modo incremental
    if modo == 'incremental' and fecha_desde is None:
        ultima_fecha = obtener_ultima_fecha(ARCHIVO_DIARIO)

        if ultima_fecha:
            # Agregar 1 día para no duplicar
            fecha_obj = datetime.strptime(ultima_fecha, '%Y-%m-%d') + timedelta(days=1)
            fecha_desde = fecha_obj.strftime('%Y-%m-%d')
            print(f"\n📅 Modo INCREMENTAL:")
            print(f"   - Última fecha en archivo: {ultima_fecha}")
            print(f"   - Descargando desde: {fecha_desde}")
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
    client = BCRAClientOficial(verify_ssl=False)

    # Variables a descargar
    variable_ids = [
        27,  # IPC mensual
        28,  # IPC interanual
        5,   # USD oficial
        7,   # BADLAR
        11,  # LELIQ
        1,   # Reservas
        15,  # Base monetaria
        16,  # Circulación monetaria
        19,  # Depósitos totales
        20,  # Depósitos sector privado
        21,  # Plazo fijo
    ]

    print(f"\n📋 Variables a descargar: {len(variable_ids)}")
    print(f"🔄 Iniciando descarga...\n")

    # Descargar datos
    df = client.get_multiple_variables(
        variable_ids=variable_ids,
        desde=fecha_desde,
        hasta=fecha_hasta,
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

    import numpy as np
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)

    print(f"   ✓ Features agregadas")

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

    df['fecha'] = pd.to_datetime(df['fecha'])
    df['anio_mes'] = df['fecha'].dt.to_period('M')

    cols_numericas = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    cols_a_agregar = [col for col in cols_numericas if col not in ['anio', 'mes', 'trimestre', 'dia_anio']]

    df_mensual = df.groupby('anio_mes')[cols_a_agregar].mean().reset_index()
    df_mensual['fecha'] = df_mensual['anio_mes'].dt.to_timestamp()
    df_mensual = df_mensual.drop('anio_mes', axis=1)

    df_mensual = agregar_features_temporales(df_mensual)

    print(f"   ✓ Datos agregados a nivel mensual")
    print(f"   - Registros mensuales: {len(df_mensual):,}")

    return df_mensual


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
    print(f"ACTUALIZACIÓN DATOS BCRA - Modo: {modo.upper()}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Descargar datos
        df_nuevo = descargar_datos_bcra_incremental(modo=modo)

        if df_nuevo is None or df_nuevo.empty:
            print("\n✅ No hay actualizaciones necesarias")
            return

        # 2. Agregar features temporales
        df_nuevo = agregar_features_temporales(df_nuevo)

        # 3. Append a archivo diario
        print(f"\n{'='*80}")
        print("ACTUALIZANDO ARCHIVO DIARIO")
        print('='*80)

        df_diario_final = append_a_parquet(df_nuevo, ARCHIVO_DIARIO)
        guardar_dataset(df_diario_final, ARCHIVO_DIARIO, "datos diarios")

        # 4. Recalcular agregación mensual (sobre todos los datos)
        print(f"\n{'='*80}")
        print("ACTUALIZANDO ARCHIVO MENSUAL")
        print('='*80)

        df_mensual = agregar_a_nivel_mensual(df_diario_final)
        guardar_dataset(df_mensual, ARCHIVO_MENSUAL, "datos mensuales")

        # Resumen final
        print(f"\n{'='*80}")
        print("✅ ACTUALIZACIÓN COMPLETADA EXITOSAMENTE")
        print('='*80)
        print(f"\n📁 Archivos actualizados:")
        print(f"   - {ARCHIVO_DIARIO}")
        print(f"   - {ARCHIVO_MENSUAL}")
        print(f"\n📊 Estadísticas:")
        print(f"   - Registros diarios: {len(df_diario_final):,}")
        print(f"   - Registros mensuales: {len(df_mensual):,}")
        print(f"   - Período: {df_diario_final['fecha'].min()} a {df_diario_final['fecha'].max()}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Actualizar datos BCRA')
    parser.add_argument('--full-refresh', action='store_true',
                       help='Descargar todo desde 2019 (ignorar datos existentes)')

    args = parser.parse_args()

    modo = 'full' if args.full_refresh else 'incremental'
    main(modo=modo)
