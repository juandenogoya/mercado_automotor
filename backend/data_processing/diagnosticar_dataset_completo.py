#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Diagnóstico Completo de Dataset de Forecasting

Analiza el dataset unificado (Transacciones + BCRA + INDEC) y muestra:
1. Lista completa de variables
2. Tipo de dato de cada variable
3. Valores únicos para categóricas
4. Estadísticas para numéricas
5. Identificación de NaNs
6. Recomendaciones de transformación

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/diagnosticar_dataset_completo.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

# Archivos a analizar
FILES = {
    'semanal': 'data/processed/dataset_forecasting_completo_semanal.parquet',
    'mensual': 'data/processed/dataset_forecasting_completo.parquet'
}


def identificar_tipo_variable(serie):
    """
    Identifica el tipo de variable más apropiado.

    Returns:
        str: 'datetime', 'categorical', 'numeric_discrete', 'numeric_continuous', 'binary'
    """
    # Datetime
    if pd.api.types.is_datetime64_any_dtype(serie):
        return 'datetime'

    # Numérico
    if pd.api.types.is_numeric_dtype(serie):
        n_unique = serie.nunique()

        # Binary (0/1 o True/False)
        if n_unique == 2 and set(serie.dropna().unique()).issubset({0, 1, True, False}):
            return 'binary'

        # Discrete (pocos valores únicos)
        if n_unique < 20:
            return 'numeric_discrete'

        # Continuous
        return 'numeric_continuous'

    # Categórico (strings o objects)
    if pd.api.types.is_object_dtype(serie) or pd.api.types.is_categorical_dtype(serie):
        return 'categorical'

    return 'unknown'


def analizar_variable_categorica(serie):
    """Analiza una variable categórica."""
    info = {
        'valores_unicos': serie.nunique(),
        'top_5_valores': serie.value_counts().head(5).to_dict(),
        'nans': serie.isna().sum(),
        'pct_nans': (serie.isna().sum() / len(serie)) * 100
    }
    return info


def analizar_variable_numerica(serie):
    """Analiza una variable numérica."""
    info = {
        'min': serie.min(),
        'max': serie.max(),
        'mean': serie.mean(),
        'median': serie.median(),
        'std': serie.std(),
        'nans': serie.isna().sum(),
        'pct_nans': (serie.isna().sum() / len(serie)) * 100,
        'zeros': (serie == 0).sum(),
        'pct_zeros': ((serie == 0).sum() / len(serie)) * 100
    }
    return info


def recomendar_transformacion(col_name, tipo, info):
    """Recomienda transformación para la variable."""
    recomendaciones = []

    if tipo == 'categorical':
        n_unicos = info['valores_unicos']
        if n_unicos == 2:
            recomendaciones.append("✅ Binary → Label Encoding (0/1)")
        elif n_unicos <= 10:
            recomendaciones.append("✅ Categorical (pocos valores) → One-Hot Encoding")
        elif n_unicos <= 50:
            recomendaciones.append("⚠️ Categorical (muchos valores) → Target Encoding o eliminación")
        else:
            recomendaciones.append("❌ Demasiados valores únicos → Agrupar o eliminar")

        if info['pct_nans'] > 50:
            recomendaciones.append("⚠️ > 50% NaNs → Considerar eliminar columna")
        elif info['pct_nans'] > 0:
            recomendaciones.append("🔧 Imputar NaNs con moda o categoría 'desconocido'")

    elif tipo in ['numeric_continuous', 'numeric_discrete']:
        if info['pct_nans'] > 50:
            recomendaciones.append("⚠️ > 50% NaNs → Considerar eliminar columna")
        elif info['pct_nans'] > 0:
            recomendaciones.append("🔧 Imputar NaNs con media/mediana/forward-fill")

        if info['pct_zeros'] > 80:
            recomendaciones.append("⚠️ > 80% zeros → Poca varianza, considerar eliminar")

        # Detectar lags y rolling
        if '_lag_' in col_name or '_rolling_' in col_name:
            recomendaciones.append("✅ Feature autogresiva → Ya numérica, OK para modelo")

        if info['std'] == 0 or (info['max'] == info['min']):
            recomendaciones.append("❌ Varianza cero → Eliminar (no aporta información)")
        else:
            recomendaciones.append("✅ Variable numérica → OK para modelo")

    elif tipo == 'binary':
        recomendaciones.append("✅ Binaria → Ya está en formato 0/1, OK para modelo")
        if info['pct_nans'] > 0:
            recomendaciones.append("🔧 Imputar NaNs con 0 o moda")

    elif tipo == 'datetime':
        recomendaciones.append("🔧 Datetime → Extraer features: año, mes, día, día_semana, etc.")

    else:
        recomendaciones.append("❓ Tipo desconocido → Revisar manualmente")

    return recomendaciones


def diagnosticar_dataset(filepath, nombre):
    """Diagnóstico completo del dataset."""
    print("\n" + "="*100)
    print(f"DIAGNÓSTICO COMPLETO: {nombre.upper()}")
    print("="*100)

    if not os.path.exists(filepath):
        print(f"\n❌ Archivo no encontrado: {filepath}")
        return

    # Cargar dataset
    df = pd.read_parquet(filepath)

    print(f"\n📊 INFORMACIÓN GENERAL")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Tamaño en memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    if 'fecha' in df.columns:
        print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")

    # Analizar cada columna
    resultados = []

    print(f"\n📋 ANÁLISIS POR VARIABLE")
    print("-" * 100)

    for col in df.columns:
        tipo = identificar_tipo_variable(df[col])

        if tipo == 'categorical':
            info = analizar_variable_categorica(df[col])
        elif tipo in ['numeric_continuous', 'numeric_discrete', 'binary']:
            info = analizar_variable_numerica(df[col])
        else:
            info = {'nans': df[col].isna().sum(), 'pct_nans': (df[col].isna().sum() / len(df)) * 100}

        recomendaciones = recomendar_transformacion(col, tipo, info)

        resultados.append({
            'columna': col,
            'tipo': tipo,
            'info': info,
            'recomendaciones': recomendaciones
        })

    # Agrupar por origen de los datos
    grupos = {
        'Target y Componentes': [],
        'Features Temporales': [],
        'Features Autogresivas (Lags/Rolling)': [],
        'Features de Transacciones (Provincias/Marcas)': [],
        'Features BCRA (Macroeconómicas)': [],
        'Features INDEC (Actividad Económica)': [],
        'Interacciones': [],
        'Otros': []
    }

    # Clasificar columnas
    for res in resultados:
        col = res['columna']

        if col in ['fecha', 'tramite_fecha']:
            continue  # Skip fecha

        if col in ['total_operaciones', 'total_inscripciones', 'total_transferencias', 'total_prendas']:
            grupos['Target y Componentes'].append(res)
        elif col in ['mes', 'trimestre', 'anio', 'semana_año', 'dia_del_anio']:
            grupos['Features Temporales'].append(res)
        elif '_lag_' in col or '_rolling_' in col or 'var_' in col:
            grupos['Features Autogresivas (Lags/Rolling)'].append(res)
        elif col.startswith('operaciones_'):
            grupos['Features de Transacciones (Provincias/Marcas)'].append(res)
        elif 'interaccion_' in col:
            grupos['Interacciones'].append(res)
        elif any(x in col.lower() for x in ['ipc', 'tipo_de_cambio', 'badlar', 'leliq', 'reservas', 'tasa']):
            grupos['Features BCRA (Macroeconómicas)'].append(res)
        elif any(x in col.lower() for x in ['emae', 'desocupacion', 'ripte', 'salario', 'empleo']):
            grupos['Features INDEC (Actividad Económica)'].append(res)
        else:
            grupos['Otros'].append(res)

    # Mostrar por grupo
    for grupo_nombre, grupo_cols in grupos.items():
        if not grupo_cols:
            continue

        print(f"\n{'='*100}")
        print(f"📦 {grupo_nombre.upper()} ({len(grupo_cols)} variables)")
        print(f"{'='*100}")

        for res in grupo_cols:
            col = res['columna']
            tipo = res['tipo']
            info = res['info']
            recomendaciones = res['recomendaciones']

            print(f"\n🔹 {col}")
            print(f"   Tipo: {tipo}")

            # Mostrar info según tipo
            if tipo == 'categorical':
                print(f"   Valores únicos: {info['valores_unicos']}")
                print(f"   NaNs: {info['nans']} ({info['pct_nans']:.1f}%)")
                if info['valores_unicos'] <= 10:
                    print(f"   Top valores: {info['top_5_valores']}")
            elif tipo in ['numeric_continuous', 'numeric_discrete', 'binary']:
                print(f"   Rango: [{info['min']:.2f}, {info['max']:.2f}]")
                print(f"   Media: {info['mean']:.2f} | Mediana: {info['median']:.2f} | Std: {info['std']:.2f}")
                print(f"   NaNs: {info['nans']} ({info['pct_nans']:.1f}%) | Zeros: {info['zeros']} ({info['pct_zeros']:.1f}%)")

            # Mostrar recomendaciones
            print(f"   Recomendaciones:")
            for rec in recomendaciones:
                print(f"      {rec}")

    # Resumen de problemas
    print(f"\n{'='*100}")
    print(f"⚠️  RESUMEN DE PROBLEMAS DETECTADOS")
    print(f"{'='*100}")

    # Contar problemas
    cols_varianza_cero = [r for r in resultados if any('Varianza cero' in rec for rec in r['recomendaciones'])]
    cols_muchos_nans = [r for r in resultados if r['info']['pct_nans'] > 50]
    cols_categoricas = [r for r in resultados if r['tipo'] == 'categorical']
    cols_muchos_zeros = [r for r in resultados if r['tipo'] in ['numeric_continuous', 'numeric_discrete'] and r['info'].get('pct_zeros', 0) > 80]

    print(f"\n❌ Varianza cero (eliminar): {len(cols_varianza_cero)}")
    for r in cols_varianza_cero:
        print(f"   - {r['columna']}")

    print(f"\n⚠️  > 50% NaNs (considerar eliminar): {len(cols_muchos_nans)}")
    for r in cols_muchos_nans:
        print(f"   - {r['columna']} ({r['info']['pct_nans']:.1f}% NaNs)")

    print(f"\n⚠️  > 80% Zeros (poca varianza): {len(cols_muchos_zeros)}")
    for r in cols_muchos_zeros:
        print(f"   - {r['columna']} ({r['info']['pct_zeros']:.1f}% zeros)")

    print(f"\n🔧 Variables categóricas (requieren transformación): {len(cols_categoricas)}")
    for r in cols_categoricas:
        print(f"   - {r['columna']} ({r['info']['valores_unicos']} valores únicos)")

    # Recomendaciones finales
    print(f"\n{'='*100}")
    print(f"💡 RECOMENDACIONES PARA MODELADO")
    print(f"{'='*100}")

    print(f"\n1. ELIMINAR inmediatamente:")
    print(f"   - Columnas con varianza cero: {len(cols_varianza_cero)}")
    print(f"   - Columnas con > 50% NaNs: {len(cols_muchos_nans)}")

    print(f"\n2. TRANSFORMAR variables categóricas:")
    for r in cols_categoricas:
        n_unicos = r['info']['valores_unicos']
        if n_unicos == 2:
            print(f"   - {r['columna']} → Label Encoding (0/1)")
        elif n_unicos <= 10:
            print(f"   - {r['columna']} → One-Hot Encoding")
        else:
            print(f"   - {r['columna']} → Target Encoding o agrupar")

    print(f"\n3. IMPUTAR NaNs en numéricas:")
    cols_con_nans = [r for r in resultados if r['tipo'] in ['numeric_continuous', 'numeric_discrete'] and r['info']['pct_nans'] > 0 and r['info']['pct_nans'] <= 50]
    for r in cols_con_nans:
        if '_lag_' in r['columna'] or '_rolling_' in r['columna']:
            print(f"   - {r['columna']} → Forward fill (feature autogresiva)")
        else:
            print(f"   - {r['columna']} → Media/mediana")

    print(f"\n4. CONSIDERAR eliminar por baja varianza:")
    for r in cols_muchos_zeros:
        print(f"   - {r['columna']} ({r['info']['pct_zeros']:.1f}% zeros)")

    # Guardar reporte
    output_file = filepath.replace('.parquet', '_diagnostico.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"DIAGNÓSTICO COMPLETO: {nombre.upper()}\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*100}\n\n")

        for grupo_nombre, grupo_cols in grupos.items():
            if not grupo_cols:
                continue
            f.write(f"\n{grupo_nombre.upper()} ({len(grupo_cols)} variables)\n")
            f.write(f"{'-'*100}\n")
            for res in grupo_cols:
                f.write(f"\n{res['columna']} | {res['tipo']}\n")
                for rec in res['recomendaciones']:
                    f.write(f"  {rec}\n")

    print(f"\n💾 Reporte guardado: {output_file}")


def main():
    """Función principal."""
    print("\n" + "="*100)
    print("DIAGNÓSTICO COMPLETO DE DATASETS DE FORECASTING")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    # Intentar analizar ambos datasets
    for nombre, filepath in FILES.items():
        if os.path.exists(filepath):
            diagnosticar_dataset(filepath, nombre)
        else:
            print(f"\n⚠️  Dataset {nombre} no encontrado: {filepath}")

    print("\n" + "="*100)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*100)
    print("\nRevisa los reportes generados (.txt) para detalles completos.")
    print("\n💡 Siguiente paso: Implementar transformaciones recomendadas en el script de unificación.")


if __name__ == "__main__":
    main()
