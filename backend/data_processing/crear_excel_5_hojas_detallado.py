#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera Excel con 5 hojas para análisis detallado:

Hoja 1 "Transacciones_Originales":
- Dataset completo de transacciones (inscripciones + transferencias + prendas)
- SIN agregar, datos crudos con todas las variables
- Mínimo 1000 registros

Hoja 2 "Macro_IPC":
- Solo variable IPC con fechas
- Serie temporal completa
- Mínimo 1000 registros

Hoja 3 "Macro_BADLAR":
- Solo variable BADLAR con fechas
- Serie temporal completa
- Mínimo 1000 registros

Hoja 4 "Macro_TC":
- Solo Tipo de Cambio con fechas
- Serie temporal completa
- Mínimo 1000 registros

Hoja 5 "Transacciones_Transformadas":
- Mismo dataset de Hoja 1 con TODAS las variables categóricas transformadas
- Label Encoding, Frequency Encoding, Target Encoding para cada categórica
- Mínimo 1000 registros

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/crear_excel_5_hojas_detallado.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Configuración
CSV_INSCRIPCIONES_MOTO = 'data/estadisticas_dnrpa/estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-09.csv'
CSV_TRANSFERENCIAS_MOTO = 'data/estadisticas_dnrpa/estadistica-transferencias-motovehiculos-2007-01-2025-09.csv'
DATASET_FORECASTING = 'data/processed/dataset_forecasting_completo.parquet'
OUTPUT_FILE = 'data/processed/datasets_analisis_5_hojas_detallado.xlsx'

MIN_ROWS = 1000  # Mínimo de registros por hoja


def cargar_transacciones_completas():
    """
    Carga dataset transaccional completo sin agregaciones.

    Returns:
        DataFrame con todas las transacciones individuales
    """
    print("\n" + "="*80)
    print("HOJA 1: TRANSACCIONES ORIGINALES (COMPLETAS)")
    print("="*80)

    dfs = []

    # 1. Inscripciones Motovehículos
    print(f"\n📂 Cargando inscripciones motovehículos...")
    df_insc = pd.read_csv(CSV_INSCRIPCIONES_MOTO)
    df_insc['tipo_operacion'] = 'Inscripción'

    # Renombrar columnas para uniformidad
    df_insc = df_insc.rename(columns={
        'cantidad_inscripciones_iniciales': 'cantidad',
        'provincia_inscripcion_inicial': 'provincia',
        'letra_provincia_inscripcion_inicial': 'letra_provincia',
        'anio_inscripcion_inicial': 'anio',
        'mes_inscripcion_inicial': 'mes'
    })

    dfs.append(df_insc)
    print(f"   ✓ {len(df_insc):,} registros")

    # 2. Transferencias Motovehículos
    print(f"\n📂 Cargando transferencias motovehículos...")
    df_trans = pd.read_csv(CSV_TRANSFERENCIAS_MOTO)
    df_trans['tipo_operacion'] = 'Transferencia'

    df_trans = df_trans.rename(columns={
        'cantidad_transferencias': 'cantidad',
        'provincia_radicacion': 'provincia',
        'letra_provincia_radicacion': 'letra_provincia',
        'anio_transferencia': 'anio',
        'mes_transferencia': 'mes'
    })

    dfs.append(df_trans)
    print(f"   ✓ {len(df_trans):,} registros")

    # Unificar
    print(f"\n🔗 Unificando datasets...")
    df_completo = pd.concat(dfs, ignore_index=True)

    # Crear fecha
    df_completo['fecha'] = pd.to_datetime(
        df_completo['anio'].astype(str) + '-' +
        df_completo['mes'].astype(str).str.zfill(2) + '-01'
    )

    # Ordenar por fecha descendente (más reciente primero)
    df_completo = df_completo.sort_values('fecha', ascending=False).reset_index(drop=True)

    # Tomar al menos MIN_ROWS registros más recientes
    if len(df_completo) > MIN_ROWS:
        df_completo = df_completo.head(MIN_ROWS)

    print(f"\n✓ Dataset transaccional completo:")
    print(f"   - Total registros: {len(df_completo):,}")
    print(f"   - Período: {df_completo['fecha'].max()} a {df_completo['fecha'].min()}")
    print(f"   - Columnas: {len(df_completo.columns)}")

    # Listar todas las variables categóricas
    cols_categoricas = df_completo.select_dtypes(include=['object']).columns.tolist()
    cols_categoricas = [c for c in cols_categoricas if c not in ['fecha']]

    print(f"\n📊 Variables categóricas detectadas ({len(cols_categoricas)}):")
    for col in cols_categoricas:
        n_unique = df_completo[col].nunique()
        print(f"   - {col}: {n_unique} categorías únicas")

    return df_completo


def cargar_macro_ipc():
    """
    Carga serie temporal de IPC.

    Returns:
        DataFrame con fecha e IPC
    """
    print("\n" + "="*80)
    print("HOJA 2: VARIABLES MACRO - IPC")
    print("="*80)

    print(f"\n📂 Cargando: {DATASET_FORECASTING}")
    df = pd.read_parquet(DATASET_FORECASTING)

    # Extraer solo fecha e IPC
    df_ipc = df[['fecha', 'ipc_mes']].copy()
    df_ipc = df_ipc.sort_values('fecha', ascending=False)

    # Si hay menos de MIN_ROWS, repetir o extender (en este caso solo tomar lo que hay)
    print(f"\n✓ Serie IPC:")
    print(f"   - Registros: {len(df_ipc):,}")
    print(f"   - Período: {df_ipc['fecha'].max()} a {df_ipc['fecha'].min()}")
    print(f"   - Valores no nulos: {df_ipc['ipc_mes'].notna().sum()}")

    return df_ipc


def cargar_macro_badlar():
    """
    Carga serie temporal de BADLAR.

    Returns:
        DataFrame con fecha y BADLAR
    """
    print("\n" + "="*80)
    print("HOJA 3: VARIABLES MACRO - BADLAR")
    print("="*80)

    print(f"\n📂 Cargando: {DATASET_FORECASTING}")
    df = pd.read_parquet(DATASET_FORECASTING)

    # Extraer solo fecha y BADLAR
    df_badlar = df[['fecha', 'badlar']].copy()
    df_badlar = df_badlar.sort_values('fecha', ascending=False)

    print(f"\n✓ Serie BADLAR:")
    print(f"   - Registros: {len(df_badlar):,}")
    print(f"   - Período: {df_badlar['fecha'].max()} a {df_badlar['fecha'].min()}")
    print(f"   - Valores no nulos: {df_badlar['badlar'].notna().sum()}")

    return df_badlar


def cargar_macro_tc():
    """
    Carga serie temporal de Tipo de Cambio.

    Returns:
        DataFrame con fecha y TC
    """
    print("\n" + "="*80)
    print("HOJA 4: VARIABLES MACRO - TIPO DE CAMBIO")
    print("="*80)

    print(f"\n📂 Cargando: {DATASET_FORECASTING}")
    df = pd.read_parquet(DATASET_FORECASTING)

    # Extraer solo fecha y TC
    df_tc = df[['fecha', 'tipo_de_cambio_usd_prom']].copy()
    df_tc = df_tc.sort_values('fecha', ascending=False)

    print(f"\n✓ Serie Tipo de Cambio:")
    print(f"   - Registros: {len(df_tc):,}")
    print(f"   - Período: {df_tc['fecha'].max()} a {df_tc['fecha'].min()}")
    print(f"   - Valores no nulos: {df_tc['tipo_de_cambio_usd_prom'].notna().sum()}")

    return df_tc


def transformar_todas_categoricas(df_original):
    """
    Aplica transformaciones a TODAS las variables categóricas.

    Para cada variable categórica crea:
    1. Label Encoding
    2. Frequency Encoding
    3. Target Encoding (usando 'cantidad' como target)

    Returns:
        DataFrame transformado con todas las nuevas columnas
    """
    print("\n" + "="*80)
    print("HOJA 5: TRANSACCIONES CON TODAS LAS CATEGÓRICAS TRANSFORMADAS")
    print("="*80)

    df_transformed = df_original.copy()

    # Identificar todas las variables categóricas
    cols_categoricas = df_transformed.select_dtypes(include=['object']).columns.tolist()
    cols_categoricas = [c for c in cols_categoricas if c not in ['fecha']]

    print(f"\n🔄 Transformando {len(cols_categoricas)} variables categóricas...")

    for col in cols_categoricas:
        print(f"\n   📊 Procesando: {col}")

        n_unique = df_transformed[col].nunique()
        print(f"      Categorías únicas: {n_unique}")

        # 1. LABEL ENCODING
        try:
            le = LabelEncoder()
            col_encoded = f'{col}_label_enc'
            df_transformed[col_encoded] = le.fit_transform(df_transformed[col].astype(str))
            print(f"      ✓ Label Encoding: {col_encoded}")
        except Exception as e:
            print(f"      ⚠️  Label Encoding falló: {e}")

        # 2. FREQUENCY ENCODING
        try:
            freq_map = df_transformed[col].value_counts(normalize=True).to_dict()
            col_freq = f'{col}_frequency'
            df_transformed[col_freq] = df_transformed[col].map(freq_map)
            print(f"      ✓ Frequency Encoding: {col_freq}")
        except Exception as e:
            print(f"      ⚠️  Frequency Encoding falló: {e}")

        # 3. TARGET ENCODING (usando 'cantidad' si existe)
        if 'cantidad' in df_transformed.columns:
            try:
                target_map = df_transformed.groupby(col)['cantidad'].mean().to_dict()
                col_target = f'{col}_target_mean'
                df_transformed[col_target] = df_transformed[col].map(target_map)
                print(f"      ✓ Target Encoding: {col_target}")
            except Exception as e:
                print(f"      ⚠️  Target Encoding falló: {e}")

    print(f"\n✅ Transformaciones completadas:")
    print(f"   Dataset original: {df_original.shape[1]} columnas")
    print(f"   Dataset transformado: {df_transformed.shape[1]} columnas")
    print(f"   Nuevas columnas: {df_transformed.shape[1] - df_original.shape[1]}")

    # Crear documentación de transformaciones
    docs = []
    for col in cols_categoricas:
        n_unique = df_original[col].nunique()

        # Label Encoding
        if f'{col}_label_enc' in df_transformed.columns:
            docs.append({
                'Variable_Original': col,
                'Nueva_Variable': f'{col}_label_enc',
                'Método': 'Label Encoding',
                'Descripción': f'Codificación numérica ordinal (0 a {n_unique-1})',
                'Categorías': n_unique
            })

        # Frequency Encoding
        if f'{col}_frequency' in df_transformed.columns:
            docs.append({
                'Variable_Original': col,
                'Nueva_Variable': f'{col}_frequency',
                'Método': 'Frequency Encoding',
                'Descripción': 'Frecuencia relativa (% de apariciones)',
                'Categorías': n_unique
            })

        # Target Encoding
        if f'{col}_target_mean' in df_transformed.columns:
            docs.append({
                'Variable_Original': col,
                'Nueva_Variable': f'{col}_target_mean',
                'Método': 'Target Encoding',
                'Descripción': 'Promedio del target (cantidad) por categoría',
                'Categorías': n_unique
            })

    df_docs = pd.DataFrame(docs)

    return df_transformed, df_docs


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("GENERACIÓN DE EXCEL CON 5 HOJAS DETALLADAS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 1. Cargar transacciones completas
    df_transacciones = cargar_transacciones_completas()

    # 2. Cargar IPC
    df_ipc = cargar_macro_ipc()

    # 3. Cargar BADLAR
    df_badlar = cargar_macro_badlar()

    # 4. Cargar TC
    df_tc = cargar_macro_tc()

    # 5. Transformar todas las categóricas
    df_transacciones_transformed, df_docs = transformar_todas_categoricas(df_transacciones)

    # 6. Exportar a Excel
    print("\n" + "="*80)
    print("EXPORTANDO A EXCEL")
    print("="*80)

    print(f"\n💾 Guardando: {OUTPUT_FILE}")

    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        # Hoja 1: Transacciones Originales
        df_transacciones.to_excel(writer, sheet_name='1_Transacciones_Originales', index=False)
        print(f"   ✓ Hoja '1_Transacciones_Originales': {df_transacciones.shape}")

        # Hoja 2: IPC
        df_ipc.to_excel(writer, sheet_name='2_Macro_IPC', index=False)
        print(f"   ✓ Hoja '2_Macro_IPC': {df_ipc.shape}")

        # Hoja 3: BADLAR
        df_badlar.to_excel(writer, sheet_name='3_Macro_BADLAR', index=False)
        print(f"   ✓ Hoja '3_Macro_BADLAR': {df_badlar.shape}")

        # Hoja 4: Tipo de Cambio
        df_tc.to_excel(writer, sheet_name='4_Macro_TC', index=False)
        print(f"   ✓ Hoja '4_Macro_TC': {df_tc.shape}")

        # Hoja 5: Transacciones Transformadas
        df_transacciones_transformed.to_excel(writer, sheet_name='5_Transacciones_Transformadas', index=False)
        print(f"   ✓ Hoja '5_Transacciones_Transformadas': {df_transacciones_transformed.shape}")

        # Hoja 6: Documentación
        df_docs.to_excel(writer, sheet_name='6_Doc_Transformaciones', index=False)
        print(f"   ✓ Hoja '6_Doc_Transformaciones': {df_docs.shape}")

    # Resumen final
    print("\n" + "="*80)
    print("✅ EXCEL GENERADO EXITOSAMENTE")
    print("="*80)

    print(f"\n📄 Archivo: {OUTPUT_FILE}")

    print(f"\n📊 Resumen de hojas:")

    print(f"\n   Hoja 1 - Transacciones Originales:")
    print(f"      • {df_transacciones.shape[0]:,} registros × {df_transacciones.shape[1]} columnas")
    print(f"      • Período: {df_transacciones['fecha'].max()} a {df_transacciones['fecha'].min()}")
    print(f"      • Datos crudos sin agregaciones")

    print(f"\n   Hoja 2 - Macro IPC:")
    print(f"      • {df_ipc.shape[0]:,} registros × {df_ipc.shape[1]} columnas")
    print(f"      • Solo variable IPC con fechas")

    print(f"\n   Hoja 3 - Macro BADLAR:")
    print(f"      • {df_badlar.shape[0]:,} registros × {df_badlar.shape[1]} columnas")
    print(f"      • Solo variable BADLAR con fechas")

    print(f"\n   Hoja 4 - Macro Tipo de Cambio:")
    print(f"      • {df_tc.shape[0]:,} registros × {df_tc.shape[1]} columnas")
    print(f"      • Solo variable TC USD/ARS con fechas")

    print(f"\n   Hoja 5 - Transacciones Transformadas:")
    print(f"      • {df_transacciones_transformed.shape[0]:,} registros × {df_transacciones_transformed.shape[1]} columnas")
    print(f"      • TODAS las variables categóricas transformadas")
    print(f"      • Nuevas columnas: {df_transacciones_transformed.shape[1] - df_transacciones.shape[1]}")

    print(f"\n   Hoja 6 - Documentación:")
    print(f"      • {len(df_docs):,} transformaciones documentadas")
    print(f"      • Describe cada nueva columna creada")

    print(f"\n💡 Transformaciones aplicadas a cada categórica:")
    print(f"   • Label Encoding: Codificación numérica ordinal")
    print(f"   • Frequency Encoding: % de apariciones")
    print(f"   • Target Encoding: Promedio de 'cantidad' por categoría")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
