#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para cargar estadísticas agregadas mensuales de DNRPA a PostgreSQL

Este script:
- Busca automáticamente los archivos CSV más recientes
- Maneja nombres de archivo dinámicos (ej: estadistica-*-2007-01-2025-09.csv)
- Carga datos a PostgreSQL de forma incremental (sin duplicados)
- Registra el archivo origen para auditoría

Uso:
    python cargar_estadisticas_agregadas.py

Estructura de tablas:
    - estadisticas_inscripciones: Datos agregados de inscripciones iniciales
    - estadisticas_transferencias: Datos agregados de transferencias
"""

import sys
import os
from pathlib import Path
import pandas as pd
import glob
from sqlalchemy import create_engine, text
from datetime import datetime

# Agregar backend al path
sys.path.append(str(Path(__file__).parent))
from backend.config.settings import settings


def encontrar_archivos_csv(directorio_base="data/estadisticas_dnrpa"):
    """
    Busca los archivos CSV más recientes en el directorio.
    Maneja nombres dinámicos como:
    - estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-09.csv
    - estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-10.csv (futuro)
    """
    base_path = Path(__file__).parent / directorio_base

    if not base_path.exists():
        print(f"❌ Error: Directorio no encontrado: {base_path}")
        return []

    # Patrones de búsqueda
    patrones = {
        'inscripciones_motovehiculos': 'estadistica-inscripciones-iniciales-motovehiculos-*.csv',
        'inscripciones_maquinarias': 'estadistica-inscripciones-iniciales-maquinarias-*.csv',
        'transferencias_motovehiculos': 'estadistica-transferencias-motovehiculos-*.csv',
        'transferencias_maquinarias': 'estadistica-transferencias-maquinarias-*.csv'
    }

    archivos_encontrados = {}

    for tipo, patron in patrones.items():
        archivos = list(base_path.glob(patron))

        if archivos:
            # Ordenar por fecha de modificación (más reciente primero)
            archivos_ordenados = sorted(archivos, key=lambda x: x.stat().st_mtime, reverse=True)
            archivo_mas_reciente = archivos_ordenados[0]
            archivos_encontrados[tipo] = archivo_mas_reciente
            print(f"✓ Encontrado ({tipo}): {archivo_mas_reciente.name}")
        else:
            print(f"⚠ No se encontró archivo para: {tipo}")

    return archivos_encontrados


def limpiar_bom(df):
    """
    Elimina BOM (Byte Order Mark) de los nombres de columnas.
    El BOM aparece como '\ufeff' al inicio del primer campo.
    """
    df.columns = df.columns.str.replace('\ufeff', '')
    return df


def cargar_csv_a_dataframe(archivo_path):
    """
    Carga un archivo CSV y lo prepara para inserción.
    """
    try:
        df = pd.read_csv(archivo_path, encoding='utf-8')
        df = limpiar_bom(df)

        # Agregar columna con nombre del archivo origen
        df['archivo_origen'] = archivo_path.name
        df['fecha_carga'] = datetime.now()

        return df
    except Exception as e:
        print(f"❌ Error al leer {archivo_path}: {e}")
        return None


def mapear_columnas_inscripciones(df):
    """
    Mapea las columnas del CSV a las columnas de la tabla PostgreSQL.
    """
    return df.rename(columns={
        'anio_inscripcion_inicial': 'anio',
        'mes_inscripcion_inicial': 'mes',
        'provincia_inscripcion_inicial': 'provincia',
        'letra_provincia_inscripcion_inicial': 'letra_provincia',
        'cantidad_inscripciones_iniciales': 'cantidad'
    })


def mapear_columnas_transferencias(df):
    """
    Mapea las columnas del CSV a las columnas de la tabla PostgreSQL.
    """
    return df.rename(columns={
        'anio_transferencia': 'anio',
        'mes_transferencia': 'mes',
        'provincia_transferencia': 'provincia',
        'letra_provincia_transferencia': 'letra_provincia',
        'cantidad_transferencias': 'cantidad'
    })


def cargar_a_postgresql(df, tabla, engine):
    """
    Carga datos a PostgreSQL de forma incremental.
    Solo inserta registros nuevos (evita duplicados).
    """
    try:
        with engine.connect() as conn:
            # Verificar si la tabla existe
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{tabla}'
                )
            """))
            tabla_existe = result.fetchone()[0]

            if not tabla_existe:
                print(f"⚠ Tabla {tabla} no existe. Ejecuta primero:")
                print(f"   psql -d mercado_automotor -f sql/crear_tablas_estadisticas_agregadas.sql")
                return False

            # Obtener registros existentes
            result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
            registros_antes = result.fetchone()[0]

            # Insertar solo registros nuevos (ON CONFLICT DO NOTHING)
            registros_insertados = 0

            for _, row in df.iterrows():
                try:
                    conn.execute(text(f"""
                        INSERT INTO {tabla}
                        (tipo_vehiculo, anio, mes, provincia, letra_provincia, provincia_id,
                         cantidad, archivo_origen, fecha_carga)
                        VALUES
                        (:tipo_vehiculo, :anio, :mes, :provincia, :letra_provincia, :provincia_id,
                         :cantidad, :archivo_origen, :fecha_carga)
                        ON CONFLICT (tipo_vehiculo, anio, mes, provincia)
                        DO UPDATE SET
                            cantidad = EXCLUDED.cantidad,
                            archivo_origen = EXCLUDED.archivo_origen,
                            fecha_carga = EXCLUDED.fecha_carga
                    """), {
                        'tipo_vehiculo': row['tipo_vehiculo'],
                        'anio': int(row['anio']),
                        'mes': int(row['mes']),
                        'provincia': row['provincia'],
                        'letra_provincia': row['letra_provincia'],
                        'provincia_id': row['provincia_id'],
                        'cantidad': int(row['cantidad']),
                        'archivo_origen': row['archivo_origen'],
                        'fecha_carga': row['fecha_carga']
                    })
                    registros_insertados += 1
                except Exception as e:
                    print(f"⚠ Error en registro: {e}")
                    continue

            conn.commit()

            # Verificar registros después
            result = conn.execute(text(f"SELECT COUNT(*) FROM {tabla}"))
            registros_despues = result.fetchone()[0]

            print(f"✓ Tabla {tabla}:")
            print(f"  - Registros antes: {registros_antes:,}")
            print(f"  - Registros procesados: {registros_insertados:,}")
            print(f"  - Registros después: {registros_despues:,}")
            print(f"  - Nuevos insertados/actualizados: {registros_despues - registros_antes:,}")

            return True

    except Exception as e:
        print(f"❌ Error al cargar datos a {tabla}: {e}")
        return False


def main():
    print("=" * 80)
    print("CARGA DE ESTADÍSTICAS AGREGADAS MENSUALES DE DNRPA")
    print("=" * 80)
    print()

    # 1. Buscar archivos CSV
    print("1. Buscando archivos CSV...")
    archivos = encontrar_archivos_csv()

    if not archivos:
        print("❌ No se encontraron archivos CSV para cargar")
        return

    print()

    # 2. Conectar a PostgreSQL
    print("2. Conectando a PostgreSQL...")
    try:
        engine = create_engine(settings.get_database_url_sync())
        print("✓ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    print()

    # 3. Cargar Inscripciones
    print("3. Cargando datos de Inscripciones...")
    print("-" * 80)

    for tipo in ['inscripciones_motovehiculos', 'inscripciones_maquinarias']:
        if tipo in archivos:
            print(f"\nProcesando: {archivos[tipo].name}")
            df = cargar_csv_a_dataframe(archivos[tipo])
            if df is not None:
                df = mapear_columnas_inscripciones(df)
                cargar_a_postgresql(df, 'estadisticas_inscripciones', engine)

    print()

    # 4. Cargar Transferencias
    print("4. Cargando datos de Transferencias...")
    print("-" * 80)

    for tipo in ['transferencias_motovehiculos', 'transferencias_maquinarias']:
        if tipo in archivos:
            print(f"\nProcesando: {archivos[tipo].name}")
            df = cargar_csv_a_dataframe(archivos[tipo])
            if df is not None:
                df = mapear_columnas_transferencias(df)
                cargar_a_postgresql(df, 'estadisticas_transferencias', engine)

    print()
    print("=" * 80)
    print("✓ PROCESO COMPLETADO")
    print("=" * 80)
    print()
    print("Para verificar los datos:")
    print("  SELECT COUNT(*) FROM estadisticas_inscripciones;")
    print("  SELECT COUNT(*) FROM estadisticas_transferencias;")
    print()


if __name__ == "__main__":
    main()
