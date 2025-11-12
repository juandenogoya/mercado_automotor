#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de análisis del dataset de forecasting avanzado.

Genera un reporte completo con:
- Lista de todas las columnas
- Tipos de datos
- Estadísticas descriptivas
- Primeros 20 registros
- Análisis de valores faltantes

Output: data/processed/dataset_analysis_report.txt

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/analizar_dataset.py
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Configuración
INPUT_FILE = 'data/processed/dataset_forecasting_avanzado.parquet'
OUTPUT_FILE = 'data/processed/dataset_analysis_report.txt'

def main():
    print("\n" + "="*80)
    print("ANÁLISIS DEL DATASET DE FORECASTING")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Cargar dataset
    print(f"\n📂 Cargando: {INPUT_FILE}")
    df = pd.read_parquet(INPUT_FILE)
    print(f"   ✓ {len(df)} registros, {len(df.columns)} columnas")

    # Crear reporte
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # Encabezado
        f.write("="*100 + "\n")
        f.write("REPORTE DE ANÁLISIS DEL DATASET DE FORECASTING AVANZADO\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*100 + "\n\n")

        # 1. INFORMACIÓN GENERAL
        f.write("1. INFORMACIÓN GENERAL\n")
        f.write("-"*100 + "\n")
        f.write(f"Archivo: {INPUT_FILE}\n")
        f.write(f"Registros: {len(df):,}\n")
        f.write(f"Columnas: {len(df.columns)}\n")
        f.write(f"Período: {df['fecha'].min()} a {df['fecha'].max()}\n")
        f.write(f"Memoria: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n\n")

        # 2. LISTA COMPLETA DE COLUMNAS
        f.write("2. LISTA COMPLETA DE COLUMNAS\n")
        f.write("-"*100 + "\n")
        f.write(f"{'#':<5} {'Nombre':<60} {'Tipo':<15} {'NaN':<10}\n")
        f.write("-"*100 + "\n")

        for idx, col in enumerate(df.columns, 1):
            dtype = str(df[col].dtype)
            nan_count = df[col].isnull().sum()
            nan_pct = (nan_count / len(df)) * 100 if nan_count > 0 else 0
            nan_str = f"{nan_count} ({nan_pct:.1f}%)" if nan_count > 0 else "0"
            f.write(f"{idx:<5} {col:<60} {dtype:<15} {nan_str:<10}\n")

        f.write("\n\n")

        # 3. COLUMNAS POR CATEGORÍA
        f.write("3. COLUMNAS POR CATEGORÍA\n")
        f.write("-"*100 + "\n")

        # Clasificar columnas
        col_target = ['total_operaciones']
        col_fecha = ['fecha']
        col_componentes_target = ['total_inscripciones', 'total_transferencias', 'total_prendas']
        col_operaciones_provincia = [col for col in df.columns if col.startswith('operaciones_') and not col.startswith('operaciones_marca_')]
        col_operaciones_marca = [col for col in df.columns if col.startswith('operaciones_marca_')]
        col_proporciones = [col for col in df.columns if col.startswith('prop_') and not col.startswith('Δprop_')]
        col_variaciones_prop = [col for col in df.columns if col.startswith('Δprop_')]
        col_ratios = [col for col in df.columns if 'ratio_' in col]
        col_lags_target = [col for col in df.columns if 'total_operaciones_' in col and ('lag' in col or 'rolling' in col)]
        col_temporales = [col for col in df.columns if col in ['mes', 'trimestre', 'anio', 'semestre']]
        col_macro = [col for col in df.columns if any(x in col.lower() for x in ['tipo_de_cambio', 'ipc', 'badlar', 'leliq', 'emae', 'reservas'])]

        categorias = [
            ("Target", col_target),
            ("Fecha", col_fecha),
            ("Componentes del Target", col_componentes_target),
            ("Operaciones por Provincia", col_operaciones_provincia),
            ("Operaciones por Marca", col_operaciones_marca),
            ("Proporciones (market share)", col_proporciones),
            ("Variaciones de Proporciones (Δ)", col_variaciones_prop),
            ("Ratios Transaccionales", col_ratios),
            ("Lags y Rolling del Target", col_lags_target),
            ("Features Temporales", col_temporales),
            ("Features Macro (BCRA/INDEC)", col_macro),
        ]

        for nombre_cat, columnas in categorias:
            f.write(f"\n{nombre_cat}: {len(columnas)} columnas\n")
            for col in columnas:
                f.write(f"   - {col}\n")

        f.write("\n\n")

        # 4. ESTADÍSTICAS DESCRIPTIVAS DEL TARGET
        f.write("4. ESTADÍSTICAS DEL TARGET (total_operaciones)\n")
        f.write("-"*100 + "\n")
        target_stats = df['total_operaciones'].describe()
        for stat, val in target_stats.items():
            f.write(f"{stat:15}: {val:,.2f}\n")
        f.write("\n\n")

        # 5. PRIMEROS 20 REGISTROS
        f.write("5. PRIMEROS 20 REGISTROS\n")
        f.write("-"*100 + "\n")
        f.write("NOTA: Solo se muestran las columnas más relevantes para legibilidad\n\n")

        # Seleccionar columnas clave para mostrar
        cols_mostrar = ['fecha', 'total_operaciones'] + \
                      col_componentes_target + \
                      col_ratios + \
                      col_lags_target[:3] + \
                      col_temporales

        cols_mostrar = [c for c in cols_mostrar if c in df.columns]

        df_head = df[cols_mostrar].head(20)
        f.write(df_head.to_string(index=False) + "\n\n")

        # 6. ANÁLISIS DE CORRELACIÓN CON EL TARGET
        f.write("6. TOP 20 FEATURES MÁS CORRELACIONADAS CON EL TARGET\n")
        f.write("-"*100 + "\n")

        # Calcular correlaciones (excluyendo fecha y target)
        cols_numericas = df.select_dtypes(include=[np.number]).columns.tolist()
        cols_numericas = [c for c in cols_numericas if c not in ['total_operaciones']]

        correlaciones = {}
        for col in cols_numericas:
            try:
                corr = df[col].corr(df['total_operaciones'])
                if not np.isnan(corr):
                    correlaciones[col] = abs(corr)
            except:
                pass

        top_correlaciones = sorted(correlaciones.items(), key=lambda x: x[1], reverse=True)[:20]

        f.write(f"{'Feature':<60} {'|Correlación|':<15}\n")
        f.write("-"*100 + "\n")
        for feat, corr in top_correlaciones:
            f.write(f"{feat:<60} {corr:<15.4f}\n")

        f.write("\n\n")

        # 7. DETECCIÓN DE DATA LEAKAGE
        f.write("7. ANÁLISIS DE DATA LEAKAGE\n")
        f.write("-"*100 + "\n")
        f.write("Columnas con ALTO RIESGO de data leakage (correlación > 0.9):\n\n")

        leakage_candidates = [(f, c) for f, c in top_correlaciones if c > 0.9]

        if leakage_candidates:
            for feat, corr in leakage_candidates:
                f.write(f"   ⚠️  {feat:<60} | {corr:.4f}\n")
            f.write("\nEstas features son muy probablemente COMPONENTES del target.\n")
            f.write("NO deben usarse para forecasting (causan overfitting).\n")
        else:
            f.write("   ✓ No se detectaron features con correlación extremadamente alta.\n")

        f.write("\n\n")

        # 8. FEATURES RECOMENDADAS
        f.write("8. FEATURES RECOMENDADAS PARA FORECASTING (SIN LEAKAGE)\n")
        f.write("-"*100 + "\n")

        features_recomendadas = col_lags_target + col_ratios + col_temporales + col_macro
        features_recomendadas = [f for f in features_recomendadas if f in df.columns]

        f.write(f"Total: {len(features_recomendadas)} features\n\n")
        f.write("Estas features NO tienen data leakage:\n")
        f.write("   - Lags del target: información del pasado\n")
        f.write("   - Ratios: relaciones entre componentes (no componentes directos)\n")
        f.write("   - Temporales: estacionalidad\n")
        f.write("   - Macro: información externa\n\n")

        for feat in features_recomendadas:
            corr = correlaciones.get(feat, 0)
            f.write(f"   ✓ {feat:<60} | Corr: {corr:.4f}\n")

        f.write("\n\n")

        # 9. VALORES COMPLETOS DE PRIMEROS 20 REGISTROS (TODAS LAS COLUMNAS)
        f.write("9. VALORES COMPLETOS - PRIMEROS 20 REGISTROS (TODAS LAS COLUMNAS)\n")
        f.write("-"*100 + "\n")
        f.write("NOTA: Valores transpuestos para mejor visualización\n\n")

        df_head_completo = df.head(20).T
        f.write(df_head_completo.to_string() + "\n\n")

        f.write("\n" + "="*100 + "\n")
        f.write("FIN DEL REPORTE\n")
        f.write("="*100 + "\n")

    print(f"\n✓ Reporte generado: {OUTPUT_FILE}")
    print(f"   Tamaño: {len(open(OUTPUT_FILE, 'r', encoding='utf-8').read())} caracteres")
    print(f"\n📝 Abre el archivo para ver el análisis completo:")
    print(f"   {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
