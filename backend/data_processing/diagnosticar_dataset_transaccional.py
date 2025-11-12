#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Diagnóstico del Dataset TRANSACCIONAL Original

Analiza el dataset transaccional ANTES de cualquier agregación o merge
para identificar:
1. Todas las variables categóricas disponibles
2. Valores únicos de cada categórica
3. Distribución de valores
4. Recomendaciones de transformación

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/diagnosticar_dataset_transaccional.py
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

INPUT_FILE = 'data/processed/dataset_transaccional_unificado.parquet'


def analizar_columna_categorica(serie, nombre):
    """Analiza una columna categórica en detalle."""
    print(f"\n{'='*100}")
    print(f"📊 {nombre}")
    print(f"{'='*100}")

    n_total = len(serie)
    n_unicos = serie.nunique()
    n_nulos = serie.isna().sum()
    pct_nulos = (n_nulos / n_total) * 100

    print(f"\n📈 Estadísticas:")
    print(f"   - Total registros: {n_total:,}")
    print(f"   - Valores únicos: {n_unicos:,}")
    print(f"   - Valores nulos: {n_nulos:,} ({pct_nulos:.2f}%)")

    # Top valores
    print(f"\n🔝 Top 20 valores más frecuentes:")
    top_20 = serie.value_counts().head(20)
    for idx, (valor, count) in enumerate(top_20.items(), 1):
        pct = (count / n_total) * 100
        print(f"   {idx:2}. {str(valor):40} | {count:>10,} ({pct:>5.2f}%)")

    # Calcular % acumulado del top 10, 20, 50
    value_counts = serie.value_counts()
    total_ops = value_counts.sum()

    if len(value_counts) >= 10:
        top_10_pct = (value_counts.head(10).sum() / total_ops) * 100
        print(f"\n   💡 Top 10 valores representan: {top_10_pct:.2f}% del total")

    if len(value_counts) >= 20:
        top_20_pct = (value_counts.head(20).sum() / total_ops) * 100
        print(f"   💡 Top 20 valores representan: {top_20_pct:.2f}% del total")

    if len(value_counts) >= 50:
        top_50_pct = (value_counts.head(50).sum() / total_ops) * 100
        print(f"   💡 Top 50 valores representan: {top_50_pct:.2f}% del total")

    # Recomendaciones
    print(f"\n💡 Recomendaciones de transformación:")

    if n_unicos == 2:
        print(f"   ✅ BINARY → Label Encoding (0/1)")
        print(f"      Ejemplo: {list(serie.dropna().unique())}")
    elif n_unicos <= 5:
        print(f"   ✅ POCOS VALORES → One-Hot Encoding")
        print(f"      Creará {n_unicos} columnas binarias")
    elif n_unicos <= 25:
        print(f"   ✅ MODERADOS VALORES → One-Hot Encoding o Target Encoding")
        print(f"      One-Hot: {n_unicos} columnas")
        print(f"      Target Encoding: 1 columna numérica")
    elif n_unicos <= 100:
        print(f"   ⚠️  MUCHOS VALORES → Target Encoding o Agrupar")
        print(f"      Opción 1: Target Encoding (1 columna)")
        print(f"      Opción 2: Agrupar Top {min(20, n_unicos)} + 'otros'")
    else:
        print(f"   ❌ DEMASIADOS VALORES ({n_unicos:,}) → Agrupar o Eliminar")
        print(f"      Opción 1: Agrupar Top 20-50 + 'otros'")
        print(f"      Opción 2: Eliminar (demasiada cardinalidad)")

    # Estrategia de agregación temporal
    print(f"\n🔧 Estrategia para agregación temporal (semanal/mensual):")

    if n_unicos <= 25:
        print(f"   ✅ Crear una columna por valor:")
        print(f"      - operaciones_{nombre}_{valor1}")
        print(f"      - operaciones_{nombre}_{valor2}")
        print(f"      - etc.")
        print(f"   Resultado: {n_unicos} columnas numéricas (conteo de operaciones)")
    else:
        print(f"   ⚠️  Agrupar primero (demasiados valores):")
        print(f"      1. Identificar Top 20 valores")
        print(f"      2. Agrupar resto en 'otros'")
        print(f"      3. Crear columnas para Top 20 + 'otros'")
        print(f"   Resultado: 21 columnas numéricas")

    return {
        'n_unicos': n_unicos,
        'n_nulos': n_nulos,
        'pct_nulos': pct_nulos,
        'top_20': top_20.to_dict()
    }


def main():
    """Función principal."""
    print("\n" + "="*100)
    print("DIAGNÓSTICO COMPLETO: DATASET TRANSACCIONAL ORIGINAL")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    # Verificar archivo
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: Archivo no encontrado: {INPUT_FILE}")
        print(f"\n📝 Ejecuta primero:")
        print(f"   python backend/data_processing/02_unir_datasets_v3.py")
        return

    # Cargar dataset (sample para análisis rápido)
    print(f"\n📂 Cargando dataset...")
    print(f"   Archivo: {INPUT_FILE}")

    # Leer solo primeras 100k filas para análisis rápido
    df = pd.read_parquet(INPUT_FILE)
    print(f"   ✓ Dataset completo cargado: {len(df):,} registros")

    # Si es muy grande, tomar sample
    if len(df) > 1_000_000:
        print(f"   ⚠️  Dataset grande, tomando sample de 1M registros para análisis...")
        df_sample = df.sample(n=1_000_000, random_state=42)
    else:
        df_sample = df

    print(f"\n📊 Información general:")
    print(f"   - Registros analizados: {len(df_sample):,}")
    print(f"   - Columnas totales: {len(df_sample.columns)}")

    if 'tramite_fecha' in df_sample.columns:
        print(f"   - Período: {df_sample['tramite_fecha'].min()} a {df_sample['tramite_fecha'].max()}")

    # Identificar columnas categóricas
    print(f"\n🔍 Identificando variables categóricas...")

    categoricas_detectadas = []
    numericas = []
    fechas = []

    for col in df_sample.columns:
        if pd.api.types.is_datetime64_any_dtype(df_sample[col]):
            fechas.append(col)
        elif pd.api.types.is_numeric_dtype(df_sample[col]):
            numericas.append(col)
        else:
            categoricas_detectadas.append(col)

    print(f"\n✓ Variables identificadas:")
    print(f"   - Categóricas: {len(categoricas_detectadas)}")
    print(f"   - Numéricas: {len(numericas)}")
    print(f"   - Fechas: {len(fechas)}")

    # Analizar cada categórica
    print(f"\n{'='*100}")
    print(f"ANÁLISIS DETALLADO DE VARIABLES CATEGÓRICAS")
    print(f"{'='*100}")

    resultados = {}

    # Buscar columnas específicas mencionadas por el usuario
    columnas_interes = {
        'provincia': ['provincia', 'provincia_normalized', 'provincia_nombre', 'domicilio_provincia'],
        'marca': ['marca', 'marca_normalized', 'marca_nombre'],
        'modelo': ['modelo', 'modelo_normalized', 'modelo_nombre'],
        'origen': ['origen', 'origen_vehiculo', 'pais_origen'],
        'genero': ['genero', 'sexo', 'genero_persona'],
        'tipo_persona': ['tipo_persona', 'persona_tipo', 'tipo_titular']
    }

    for nombre_concepto, posibles_nombres in columnas_interes.items():
        # Buscar la columna
        col_encontrada = None
        for nombre in posibles_nombres:
            if nombre in df_sample.columns:
                col_encontrada = nombre
                break

        if col_encontrada:
            print(f"\n✅ Encontrada: {nombre_concepto.upper()} → columna '{col_encontrada}'")
            resultados[nombre_concepto] = analizar_columna_categorica(
                df_sample[col_encontrada],
                nombre_concepto
            )
        else:
            print(f"\n❌ No encontrada: {nombre_concepto.upper()}")
            print(f"   Buscadas: {posibles_nombres}")
            print(f"   Disponibles: {[col for col in df_sample.columns if any(p in col.lower() for p in posibles_nombres)]}")

    # Analizar otras categóricas no identificadas
    otras_categoricas = [col for col in categoricas_detectadas
                         if not any(col in nombres for nombres in columnas_interes.values())]

    if otras_categoricas:
        print(f"\n{'='*100}")
        print(f"OTRAS VARIABLES CATEGÓRICAS ENCONTRADAS ({len(otras_categoricas)})")
        print(f"{'='*100}")

        for col in otras_categoricas:
            if col not in ['tramite_fecha', 'fecha']:  # Skip fechas
                print(f"\n🔹 {col}")
                n_unicos = df_sample[col].nunique()
                n_nulos = df_sample[col].isna().sum()
                print(f"   Valores únicos: {n_unicos:,}")
                print(f"   Nulos: {n_nulos:,} ({(n_nulos/len(df_sample))*100:.2f}%)")

                if n_unicos <= 50:
                    top_5 = df_sample[col].value_counts().head(5)
                    print(f"   Top 5: {top_5.to_dict()}")

    # Resumen final
    print(f"\n{'='*100}")
    print(f"📋 RESUMEN Y PLAN DE ACCIÓN")
    print(f"{'='*100}")

    print(f"\n✅ Variables categóricas identificadas:")
    for nombre_concepto, resultado in resultados.items():
        if resultado:
            print(f"   - {nombre_concepto:20} | {resultado['n_unicos']:>6,} valores únicos | {resultado['pct_nulos']:>5.2f}% NaNs")

    print(f"\n💡 Próximo paso:")
    print(f"   1. Crear script de transformación de categóricas")
    print(f"   2. Aplicar transformaciones (One-Hot, Target Encoding, Agrupación)")
    print(f"   3. Generar features agregadas por categoría")
    print(f"   4. LUEGO hacer agregación temporal (semanal)")
    print(f"   5. LUEGO merge con BCRA/INDEC")

    # Guardar reporte
    output_file = INPUT_FILE.replace('.parquet', '_diagnostico_categoricas.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"DIAGNÓSTICO: VARIABLES CATEGÓRICAS\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*100}\n\n")

        for nombre_concepto, resultado in resultados.items():
            if resultado:
                f.write(f"\n{nombre_concepto.upper()}\n")
                f.write(f"  Valores únicos: {resultado['n_unicos']:,}\n")
                f.write(f"  Nulos: {resultado['n_nulos']:,} ({resultado['pct_nulos']:.2f}%)\n")
                f.write(f"  Top 20:\n")
                for valor, count in resultado['top_20'].items():
                    f.write(f"    {valor}: {count:,}\n")

    print(f"\n💾 Reporte guardado: {output_file}")

    print("\n" + "="*100)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*100)


if __name__ == "__main__":
    main()
