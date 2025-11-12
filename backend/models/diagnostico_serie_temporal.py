#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico de la serie temporal.

Analiza:
- Estadísticas básicas
- Tendencia y estacionalidad
- Outliers
- Cambios estructurales
- Autocorrelación

Ejecutar desde: mercado_automotor/
Comando: python backend/models/diagnostico_serie_temporal.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración
INPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'

def analizar_serie_temporal():
    """Análisis completo de la serie temporal."""
    print("\n" + "="*80)
    print("DIAGNÓSTICO DE SERIE TEMPORAL")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Cargar datos
    print(f"\n📂 Cargando: {INPUT_FILE}")
    df = pd.read_parquet(INPUT_FILE)
    df_ts = df[['fecha', 'total_operaciones']].copy()
    df_ts = df_ts.sort_values('fecha').reset_index(drop=True)

    print(f"   ✓ {len(df_ts)} registros")
    print(f"   ✓ Período: {df_ts['fecha'].min()} a {df_ts['fecha'].max()}")

    # 1. ESTADÍSTICAS BÁSICAS
    print("\n" + "="*80)
    print("1. ESTADÍSTICAS BÁSICAS")
    print("="*80)

    stats = df_ts['total_operaciones'].describe()
    print(f"\n{'Estadística':<15} {'Valor':>15}")
    print("-"*32)
    for idx, val in stats.items():
        print(f"{idx:<15} {val:>15,.0f}")

    cv = stats['std'] / stats['mean']
    print(f"{'CV (std/mean)':<15} {cv:>15.4f}")

    # 2. VALORES EXTREMOS
    print("\n" + "="*80)
    print("2. DETECCIÓN DE OUTLIERS (IQR Method)")
    print("="*80)

    Q1 = df_ts['total_operaciones'].quantile(0.25)
    Q3 = df_ts['total_operaciones'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df_ts[(df_ts['total_operaciones'] < lower_bound) |
                     (df_ts['total_operaciones'] > upper_bound)]

    print(f"\nLímites IQR:")
    print(f"   Inferior: {lower_bound:,.0f}")
    print(f"   Superior: {upper_bound:,.0f}")
    print(f"\n{'Outliers detectados:':<25} {len(outliers)} registros ({len(outliers)/len(df_ts)*100:.1f}%)")

    if len(outliers) > 0:
        print(f"\n{'Fecha':<15} {'Valor':>15} {'% vs Media':>15}")
        print("-"*47)
        for _, row in outliers.head(10).iterrows():
            pct_diff = (row['total_operaciones'] - stats['mean']) / stats['mean'] * 100
            print(f"{str(row['fecha'])[:10]:<15} {row['total_operaciones']:>15,.0f} {pct_diff:>14.1f}%")

    # 3. TENDENCIA
    print("\n" + "="*80)
    print("3. ANÁLISIS DE TENDENCIA")
    print("="*80)

    # Calcular tendencia lineal simple
    x = np.arange(len(df_ts))
    y = df_ts['total_operaciones'].values
    coef = np.polyfit(x, y, 1)
    tendencia = coef[0]

    print(f"\nTendencia lineal: {tendencia:+,.2f} operaciones/mes")
    if tendencia > 0:
        print("   → Serie CRECIENTE")
    elif tendencia < 0:
        print("   → Serie DECRECIENTE")
    else:
        print("   → Serie ESTABLE")

    # Primeros 12 vs últimos 12 meses
    if len(df_ts) >= 24:
        primeros_12 = df_ts['total_operaciones'].head(12).mean()
        ultimos_12 = df_ts['total_operaciones'].tail(12).mean()
        cambio_pct = (ultimos_12 - primeros_12) / primeros_12 * 100

        print(f"\nPrimeros 12 meses: {primeros_12:,.0f} operaciones/mes")
        print(f"Últimos 12 meses:  {ultimos_12:,.0f} operaciones/mes")
        print(f"Cambio: {cambio_pct:+.1f}%")

    # 4. ESTACIONALIDAD
    print("\n" + "="*80)
    print("4. ANÁLISIS DE ESTACIONALIDAD")
    print("="*80)

    # Agregar columna de mes
    df_ts['mes'] = pd.to_datetime(df_ts['fecha']).dt.month

    # Promedio por mes
    estacionalidad = df_ts.groupby('mes')['total_operaciones'].agg(['mean', 'std', 'count'])
    estacionalidad['cv'] = estacionalidad['std'] / estacionalidad['mean']

    print(f"\n{'Mes':<5} {'Promedio':>12} {'Std':>12} {'CV':>8} {'N':>5}")
    print("-"*48)
    for mes, row in estacionalidad.iterrows():
        nombre_mes = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][mes-1]
        print(f"{nombre_mes:<5} {row['mean']:>12,.0f} {row['std']:>12,.0f} {row['cv']:>8.2f} {int(row['count']):>5}")

    # Detectar si hay estacionalidad clara
    max_mes = estacionalidad['mean'].idxmax()
    min_mes = estacionalidad['mean'].idxmin()
    dif_estacional = (estacionalidad['mean'].max() - estacionalidad['mean'].min()) / estacionalidad['mean'].mean() * 100

    print(f"\nMes más alto: {['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][max_mes-1]} ({estacionalidad['mean'].max():,.0f})")
    print(f"Mes más bajo: {['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][min_mes-1]} ({estacionalidad['mean'].min():,.0f})")
    print(f"Variación estacional: {dif_estacional:.1f}%")

    if dif_estacional > 20:
        print("   → Estacionalidad FUERTE detectada")
    elif dif_estacional > 10:
        print("   → Estacionalidad MODERADA detectada")
    else:
        print("   → Estacionalidad DÉBIL o ausente")

    # 5. AUTOCORRELACIÓN SIMPLE
    print("\n" + "="*80)
    print("5. AUTOCORRELACIÓN")
    print("="*80)

    # Calcular autocorrelación para lags 1, 3, 6, 12
    lags_test = [1, 3, 6, 12]
    print(f"\n{'Lag':<5} {'Correlación':>15}")
    print("-"*22)

    for lag in lags_test:
        if len(df_ts) > lag:
            corr = df_ts['total_operaciones'].autocorr(lag=lag)
            print(f"{lag:<5} {corr:>15.4f}")

    # 6. CAMBIOS ESTRUCTURALES (QUIEBRES)
    print("\n" + "="*80)
    print("6. DETECCIÓN DE CAMBIOS ESTRUCTURALES")
    print("="*80)

    # Buscar cambios grandes entre períodos consecutivos
    df_ts['cambio_pct'] = df_ts['total_operaciones'].pct_change() * 100

    cambios_grandes = df_ts[abs(df_ts['cambio_pct']) > 30]

    print(f"\nCambios >30% entre meses consecutivos: {len(cambios_grandes)}")

    if len(cambios_grandes) > 0:
        print(f"\n{'Fecha':<15} {'Valor':>15} {'Cambio %':>15}")
        print("-"*47)
        for _, row in cambios_grandes.head(10).iterrows():
            print(f"{str(row['fecha'])[:10]:<15} {row['total_operaciones']:>15,.0f} {row['cambio_pct']:>14.1f}%")

        print("\n⚠️  ATENCIÓN: Cambios grandes pueden indicar:")
        print("   - Eventos extraordinarios (pandemia, crisis)")
        print("   - Problemas de calidad de datos")
        print("   - Cambios en la metodología de medición")

    # 7. RECOMENDACIONES
    print("\n" + "="*80)
    print("7. RECOMENDACIONES PARA MODELADO")
    print("="*80)

    print("\n📊 Características del dataset:")
    print(f"   - Tamaño: {len(df_ts)} registros")
    print(f"   - Años completos: {len(df_ts)/12:.1f}")
    print(f"   - Tendencia: {'Sí' if abs(tendencia) > stats['mean']*0.01 else 'No'}")
    print(f"   - Estacionalidad: {'Sí' if dif_estacional > 10 else 'No'}")
    print(f"   - Outliers: {len(outliers)} ({len(outliers)/len(df_ts)*100:.1f}%)")
    print(f"   - Cambios estructurales: {len(cambios_grandes)}")

    print("\n💡 Modelos recomendados:")

    if len(df_ts) < 36:
        print("   ⚠️  Dataset MUY pequeño (<3 años)")
        print("   → Usar modelos simples: ARIMA sin componente estacional")
        print("   → Considerar usar promedios móviles o suavizado exponencial simple")
    elif len(df_ts) < 60:
        print("   ⚠️  Dataset pequeño (<5 años)")
        print("   → ARIMA(p,d,q) con p,d,q ≤ 1")
        print("   → Evitar SARIMA (requiere más datos)")
        print("   → Holt-Winters con restricciones")
    else:
        print("   ✓ Dataset suficiente para modelos estacionales")
        print("   → SARIMA(p,d,q)(P,D,Q,12) con parámetros bajos")
        print("   → Holt-Winters aditivo/multiplicativo")

    if len(cambios_grandes) > len(df_ts) * 0.1:
        print("\n   ⚠️  Muchos cambios estructurales detectados")
        print("   → Considerar análisis por sub-períodos")
        print("   → Evaluar si hay eventos externos que expliquen los cambios")

    if len(outliers) > len(df_ts) * 0.1:
        print("\n   ⚠️  Muchos outliers detectados")
        print("   → Revisar calidad de los datos")
        print("   → Considerar transformaciones (log, Box-Cox)")

    print("\n" + "="*80)
    print("✅ DIAGNÓSTICO COMPLETADO")
    print("="*80)

    return df_ts

if __name__ == "__main__":
    df_ts = analizar_serie_temporal()
