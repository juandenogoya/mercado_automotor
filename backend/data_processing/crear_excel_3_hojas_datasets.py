#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera Excel con 3 hojas para análisis de datasets:

Hoja 1 "Transacciones Originales":
- Dataset transaccional de DNRPA (inscripciones + transferencias)
- Variables categóricas sin transformar
- Primeras 10,000 filas

Hoja 2 "Variables Macro":
- Variables macroeconómicas (BCRA/INDEC)
- IPC, Tipo de cambio, BADLAR, LELIQ, EMAE, etc.
- Serie temporal completa

Hoja 3 "Transacciones Transformadas":
- Mismo dataset de Hoja 1 con transformaciones a categóricas
- Label Encoding, Frequency Encoding, Target Encoding
- Muestra qué método se aplicó a cada variable

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/crear_excel_3_hojas_datasets.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import LabelEncoder

# Configuración
CSV_INSCRIPCIONES_MOTO = 'data/estadisticas_dnrpa/estadistica-inscripciones-iniciales-motovehiculos-2007-01-2025-09.csv'
CSV_TRANSFERENCIAS_MOTO = 'data/estadisticas_dnrpa/estadistica-transferencias-motovehiculos-2007-01-2025-09.csv'
CSV_INSCRIPCIONES_MAQ = 'data/estadisticas_dnrpa/estadistica-inscripciones-iniciales-maquinarias-2013-09-2025-09.csv'
CSV_TRANSFERENCIAS_MAQ = 'data/estadisticas_dnrpa/estadistica-transferencias-maquinarias-2013-09-2025-09.csv'
DATASET_FORECASTING = 'data/processed/dataset_forecasting_completo.parquet'
OUTPUT_FILE = 'data/processed/datasets_analisis_3_hojas.xlsx'

MAX_ROWS_TRANSACCIONES = 10000  # Límite para que Excel sea manejable


def cargar_dataset_transaccional():
    """
    Carga y unifica datasets transaccionales de DNRPA.

    Returns:
        DataFrame con transacciones unificadas
    """
    print("\n" + "="*80)
    print("HOJA 1: DATASET TRANSACCIONAL ORIGINAL")
    print("="*80)

    dfs = []

    # 1. Inscripciones Motovehículos
    print(f"\n📂 Cargando inscripciones motovehículos...")
    df_insc_moto = pd.read_csv(CSV_INSCRIPCIONES_MOTO)
    df_insc_moto['tipo_operacion'] = 'Inscripción'
    df_insc_moto = df_insc_moto.rename(columns={
        'cantidad_inscripciones_iniciales': 'cantidad',
        'provincia_inscripcion_inicial': 'provincia',
        'letra_provincia_inscripcion_inicial': 'letra_provincia',
        'anio_inscripcion_inicial': 'anio',
        'mes_inscripcion_inicial': 'mes'
    })
    dfs.append(df_insc_moto)
    print(f"   ✓ {len(df_insc_moto):,} registros")

    # 2. Transferencias Motovehículos
    print(f"\n📂 Cargando transferencias motovehículos...")
    df_trans_moto = pd.read_csv(CSV_TRANSFERENCIAS_MOTO)
    df_trans_moto['tipo_operacion'] = 'Transferencia'
    df_trans_moto = df_trans_moto.rename(columns={
        'cantidad_transferencias': 'cantidad',
        'provincia_radicacion': 'provincia',
        'letra_provincia_radicacion': 'letra_provincia',
        'anio_transferencia': 'anio',
        'mes_transferencia': 'mes'
    })
    dfs.append(df_trans_moto)
    print(f"   ✓ {len(df_trans_moto):,} registros")

    # 3. Inscripciones Maquinarias
    print(f"\n📂 Cargando inscripciones maquinarias...")
    df_insc_maq = pd.read_csv(CSV_INSCRIPCIONES_MAQ)
    df_insc_maq['tipo_operacion'] = 'Inscripción'
    df_insc_maq = df_insc_maq.rename(columns={
        'cantidad_inscripciones_iniciales': 'cantidad',
        'provincia_inscripcion_inicial': 'provincia',
        'letra_provincia_inscripcion_inicial': 'letra_provincia',
        'anio_inscripcion_inicial': 'anio',
        'mes_inscripcion_inicial': 'mes'
    })
    dfs.append(df_insc_maq)
    print(f"   ✓ {len(df_insc_maq):,} registros")

    # 4. Transferencias Maquinarias
    print(f"\n📂 Cargando transferencias maquinarias...")
    df_trans_maq = pd.read_csv(CSV_TRANSFERENCIAS_MAQ)
    df_trans_maq['tipo_operacion'] = 'Transferencia'
    df_trans_maq = df_trans_maq.rename(columns={
        'cantidad_transferencias': 'cantidad',
        'provincia_radicacion': 'provincia',
        'letra_provincia_radicacion': 'letra_provincia',
        'anio_transferencia': 'anio',
        'mes_transferencia': 'mes'
    })
    dfs.append(df_trans_maq)
    print(f"   ✓ {len(df_trans_maq):,} registros")

    # Unificar
    print(f"\n🔗 Unificando datasets...")
    df_unificado = pd.concat(dfs, ignore_index=True)

    # Seleccionar columnas comunes
    cols_comunes = ['tipo_vehiculo', 'anio', 'mes', 'provincia', 'letra_provincia',
                    'cantidad', 'provincia_id', 'tipo_operacion']
    df_unificado = df_unificado[[col for col in cols_comunes if col in df_unificado.columns]]

    # Crear fecha
    df_unificado['fecha'] = pd.to_datetime(
        df_unificado['anio'].astype(str) + '-' +
        df_unificado['mes'].astype(str).str.zfill(2) + '-01'
    )

    # Ordenar por fecha
    df_unificado = df_unificado.sort_values('fecha').reset_index(drop=True)

    print(f"\n✓ Dataset unificado:")
    print(f"   - Total registros: {len(df_unificado):,}")
    print(f"   - Período: {df_unificado['fecha'].min()} a {df_unificado['fecha'].max()}")
    print(f"   - Columnas: {len(df_unificado.columns)}")

    # Limitar a MAX_ROWS_TRANSACCIONES
    if len(df_unificado) > MAX_ROWS_TRANSACCIONES:
        print(f"\n   ⚠️  Limitando a primeras {MAX_ROWS_TRANSACCIONES:,} filas para Excel")
        df_unificado = df_unificado.head(MAX_ROWS_TRANSACCIONES)

    # Información de variables categóricas
    print(f"\n📊 Variables categóricas:")
    for col in ['tipo_vehiculo', 'tipo_operacion', 'provincia']:
        if col in df_unificado.columns:
            n_categorias = df_unificado[col].nunique()
            print(f"   - {col}: {n_categorias} categorías únicas")

    return df_unificado


def cargar_variables_macro():
    """
    Carga variables macroeconómicas del dataset de forecasting.

    Returns:
        DataFrame con variables macro
    """
    print("\n" + "="*80)
    print("HOJA 2: VARIABLES MACROECONÓMICAS")
    print("="*80)

    print(f"\n📂 Cargando: {DATASET_FORECASTING}")
    df_forecasting = pd.read_parquet(DATASET_FORECASTING)

    # Seleccionar solo variables macro + fecha
    cols_macro = ['fecha', 'ipc_mes', 'tipo_de_cambio_usd_prom', 'badlar', 'leliq',
                  'reservas_internacionales', 'emae', 'desocupacion', 'ripte']

    cols_disponibles = [col for col in cols_macro if col in df_forecasting.columns]
    df_macro = df_forecasting[cols_disponibles].copy()

    print(f"\n✓ Variables macro extraídas:")
    print(f"   - Registros: {len(df_macro):,}")
    print(f"   - Período: {df_macro['fecha'].min()} a {df_macro['fecha'].max()}")
    print(f"   - Variables: {len(df_macro.columns) - 1}")

    print(f"\n📊 Variables incluidas:")
    for col in df_macro.columns:
        if col != 'fecha':
            non_null = df_macro[col].notna().sum()
            pct = (non_null / len(df_macro)) * 100
            print(f"   - {col}: {non_null}/{len(df_macro)} valores ({pct:.1f}%)")

    return df_macro


def aplicar_transformaciones_categoricas(df_original):
    """
    Aplica transformaciones a variables categóricas.

    Métodos:
    1. Label Encoding: para variables ordinales o con pocas categorías
    2. Frequency Encoding: % de apariciones de cada categoría
    3. Target Encoding: promedio del target por categoría

    Returns:
        DataFrame transformado + diccionario de métodos aplicados
    """
    print("\n" + "="*80)
    print("HOJA 3: TRANSACCIONES CON TRANSFORMACIONES")
    print("="*80)

    df_transformed = df_original.copy()

    # Diccionario para documentar transformaciones
    transformaciones = []

    # 1. LABEL ENCODING: tipo_operacion (2 categorías: Inscripción, Transferencia)
    if 'tipo_operacion' in df_transformed.columns:
        print(f"\n🔢 Aplicando Label Encoding a 'tipo_operacion'...")
        le_tipo = LabelEncoder()
        df_transformed['tipo_operacion_encoded'] = le_tipo.fit_transform(df_transformed['tipo_operacion'])

        mapping = dict(zip(le_tipo.classes_, le_tipo.transform(le_tipo.classes_)))
        print(f"   Mapeo: {mapping}")

        transformaciones.append({
            'Variable': 'tipo_operacion',
            'Método': 'Label Encoding',
            'Nueva Variable': 'tipo_operacion_encoded',
            'Descripción': 'Codificación ordinal: ' + str(mapping),
            'Categorías': len(le_tipo.classes_),
            'Razón': 'Variable binaria (2 categorías)'
        })

    # 2. LABEL ENCODING: tipo_vehiculo (2 categorías: Motovehículos, Maquinarias)
    if 'tipo_vehiculo' in df_transformed.columns:
        print(f"\n🔢 Aplicando Label Encoding a 'tipo_vehiculo'...")
        le_vehiculo = LabelEncoder()
        df_transformed['tipo_vehiculo_encoded'] = le_vehiculo.fit_transform(df_transformed['tipo_vehiculo'])

        mapping = dict(zip(le_vehiculo.classes_, le_vehiculo.transform(le_vehiculo.classes_)))
        print(f"   Mapeo: {mapping}")

        transformaciones.append({
            'Variable': 'tipo_vehiculo',
            'Método': 'Label Encoding',
            'Nueva Variable': 'tipo_vehiculo_encoded',
            'Descripción': 'Codificación ordinal: ' + str(mapping),
            'Categorías': len(le_vehiculo.classes_),
            'Razón': 'Variable binaria (2 categorías)'
        })

    # 3. FREQUENCY ENCODING: provincia (muchas categorías)
    if 'provincia' in df_transformed.columns:
        print(f"\n📊 Aplicando Frequency Encoding a 'provincia'...")
        freq_map = df_transformed['provincia'].value_counts(normalize=True).to_dict()
        df_transformed['provincia_frequency'] = df_transformed['provincia'].map(freq_map)

        n_provincias = df_transformed['provincia'].nunique()
        print(f"   ✓ {n_provincias} provincias codificadas")
        print(f"   Ejemplo: {list(freq_map.items())[:3]}")

        transformaciones.append({
            'Variable': 'provincia',
            'Método': 'Frequency Encoding',
            'Nueva Variable': 'provincia_frequency',
            'Descripción': 'Frecuencia relativa (% de apariciones)',
            'Categorías': n_provincias,
            'Razón': 'Muchas categorías, preserva importancia relativa'
        })

    # 4. TARGET ENCODING: provincia (promedio de cantidad por provincia)
    if 'provincia' in df_transformed.columns and 'cantidad' in df_transformed.columns:
        print(f"\n🎯 Aplicando Target Encoding a 'provincia'...")
        target_map = df_transformed.groupby('provincia')['cantidad'].mean().to_dict()
        df_transformed['provincia_target_mean'] = df_transformed['provincia'].map(target_map)

        print(f"   ✓ Promedio de 'cantidad' por provincia calculado")
        print(f"   Ejemplo: {dict(list(target_map.items())[:3])}")

        transformaciones.append({
            'Variable': 'provincia',
            'Método': 'Target Encoding',
            'Nueva Variable': 'provincia_target_mean',
            'Descripción': 'Promedio del target (cantidad) por provincia',
            'Categorías': len(target_map),
            'Razón': 'Captura relación con variable objetivo'
        })

    # 5. ONE-HOT ENCODING: letra_provincia (como ejemplo, aunque no es ideal para Excel)
    if 'letra_provincia' in df_transformed.columns:
        # Solo para las 5 provincias más frecuentes (para no explotar Excel)
        top_letras = df_transformed['letra_provincia'].value_counts().head(5).index

        print(f"\n🔥 Aplicando One-Hot Encoding a 'letra_provincia' (top 5)...")

        for letra in top_letras:
            col_name = f'letra_provincia_{letra}'
            df_transformed[col_name] = (df_transformed['letra_provincia'] == letra).astype(int)

        print(f"   ✓ {len(top_letras)} columnas dummy creadas")

        transformaciones.append({
            'Variable': 'letra_provincia',
            'Método': 'One-Hot Encoding (top 5)',
            'Nueva Variable': 'letra_provincia_X (múltiples columnas)',
            'Descripción': f'Columnas binarias para top 5 letras: {list(top_letras)}',
            'Categorías': len(top_letras),
            'Razón': 'Variables dummy para categorías sin orden'
        })

    # Resumen
    print(f"\n✅ Transformaciones aplicadas: {len(transformaciones)}")
    print(f"   Dataset original: {df_original.shape[1]} columnas")
    print(f"   Dataset transformado: {df_transformed.shape[1]} columnas")
    print(f"   Nuevas columnas: {df_transformed.shape[1] - df_original.shape[1]}")

    # Crear DataFrame de documentación
    df_transformaciones = pd.DataFrame(transformaciones)

    return df_transformed, df_transformaciones


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("GENERACIÓN DE EXCEL CON 3 HOJAS DE DATASETS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 1. Cargar dataset transaccional original
    df_transacciones = cargar_dataset_transaccional()

    # 2. Cargar variables macro
    df_macro = cargar_variables_macro()

    # 3. Aplicar transformaciones a categóricas
    df_transacciones_transformed, df_transformaciones = aplicar_transformaciones_categoricas(df_transacciones)

    # 4. Exportar a Excel con 3 hojas
    print("\n" + "="*80)
    print("EXPORTANDO A EXCEL")
    print("="*80)

    print(f"\n💾 Guardando: {OUTPUT_FILE}")

    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        # Hoja 1: Transacciones Originales
        df_transacciones.to_excel(writer, sheet_name='1_Transacciones_Originales', index=False)
        print(f"   ✓ Hoja '1_Transacciones_Originales': {df_transacciones.shape}")

        # Hoja 2: Variables Macro
        df_macro.to_excel(writer, sheet_name='2_Variables_Macro', index=False)
        print(f"   ✓ Hoja '2_Variables_Macro': {df_macro.shape}")

        # Hoja 3: Transacciones Transformadas
        df_transacciones_transformed.to_excel(writer, sheet_name='3_Transacciones_Transformadas', index=False)
        print(f"   ✓ Hoja '3_Transacciones_Transformadas': {df_transacciones_transformed.shape}")

        # Hoja 4: Documentación de Transformaciones
        df_transformaciones.to_excel(writer, sheet_name='4_Doc_Transformaciones', index=False)
        print(f"   ✓ Hoja '4_Doc_Transformaciones': {df_transformaciones.shape}")

    # Resumen final
    print("\n" + "="*80)
    print("✅ EXCEL GENERADO EXITOSAMENTE")
    print("="*80)

    print(f"\n📄 Archivo: {OUTPUT_FILE}")
    print(f"\n📊 Contenido:")
    print(f"\n   Hoja 1 - Transacciones Originales:")
    print(f"      • Dataset transaccional de DNRPA sin transformar")
    print(f"      • {df_transacciones.shape[0]:,} registros × {df_transacciones.shape[1]} columnas")
    print(f"      • Variables categóricas: tipo_vehiculo, tipo_operacion, provincia")

    print(f"\n   Hoja 2 - Variables Macro:")
    print(f"      • Variables macroeconómicas (BCRA/INDEC)")
    print(f"      • {df_macro.shape[0]:,} registros × {df_macro.shape[1]} columnas")
    print(f"      • Variables: IPC, TC, BADLAR, LELIQ, EMAE, etc.")

    print(f"\n   Hoja 3 - Transacciones Transformadas:")
    print(f"      • Mismo dataset de Hoja 1 con transformaciones aplicadas")
    print(f"      • {df_transacciones_transformed.shape[0]:,} registros × {df_transacciones_transformed.shape[1]} columnas")
    print(f"      • Nuevas columnas: {df_transacciones_transformed.shape[1] - df_transacciones.shape[1]}")

    print(f"\n   Hoja 4 - Documentación Transformaciones:")
    print(f"      • Descripción de cada transformación aplicada")
    print(f"      • Método, razón y mapeos utilizados")
    print(f"      • {len(df_transformaciones)} transformaciones documentadas")

    print(f"\n💡 Métodos de transformación aplicados:")
    print(f"   • Label Encoding: Variables binarias (tipo_operacion, tipo_vehiculo)")
    print(f"   • Frequency Encoding: Provincias (% de apariciones)")
    print(f"   • Target Encoding: Provincias (promedio de cantidad)")
    print(f"   • One-Hot Encoding: Top 5 letras de provincia")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
