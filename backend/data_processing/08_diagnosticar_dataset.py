#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico del dataset de forecasting.

Verifica:
- Valores NaN por columna
- Varianza de features
- Valores únicos
- Distribución del target

Ejecutar desde: mercado_automotor/
"""

import pandas as pd
import numpy as np

# Cargar dataset
df = pd.read_parquet('data/processed/dataset_forecasting_completo.parquet')

print("="*80)
print("DIAGNÓSTICO DEL DATASET")
print("="*80)

print(f"\n📊 Información general:")
print(f"   - Registros: {len(df)}")
print(f"   - Columnas: {len(df.columns)}")
print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")

# Ver primeras filas
print(f"\n🔍 Primeras 5 filas:")
print(df.head())

# Columnas
print(f"\n📋 Columnas ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"   {i:2}. {col}")

# Target
target = 'total_operaciones'
if target in df.columns:
    print(f"\n🎯 Target: {target}")
    print(f"   - Media: {df[target].mean():,.2f}")
    print(f"   - Std: {df[target].std():,.2f}")
    print(f"   - Min: {df[target].min():,.2f}")
    print(f"   - Max: {df[target].max():,.2f}")
    print(f"   - NaN: {df[target].isnull().sum()}")
    print(f"\n   Valores:")
    print(df[[target]].head(10))

# NaN por columna
print(f"\n⚠️  NaN por columna:")
nan_counts = df.isnull().sum()
nan_cols = nan_counts[nan_counts > 0].sort_values(ascending=False)
if len(nan_cols) > 0:
    for col, count in nan_cols.head(20).items():
        pct = (count / len(df)) * 100
        print(f"   {col:40} | {count:3} ({pct:5.1f}%)")
else:
    print("   ✓ No hay NaN")

# Varianza de features numéricas
print(f"\n📊 Varianza de features numéricas:")
numericas = df.select_dtypes(include=[np.number]).columns
variance = df[numericas].var().sort_values()

print(f"\n   Features con varianza CERO:")
zero_var = variance[variance == 0]
if len(zero_var) > 0:
    for col, var in zero_var.items():
        print(f"   {col:40} | {var}")

    # Mostrar valores de estas columnas
    print(f"\n   ⚠️  Valores de features con varianza 0:")
    for col in zero_var.index[:5]:
        unique_vals = df[col].unique()
        print(f"   {col}: {unique_vals}")
else:
    print("   ✓ Todas las features tienen varianza > 0")

print(f"\n   Features con MENOR varianza (top 10):")
for col, var in variance.head(10).items():
    print(f"   {col:40} | {var:.6f}")

# Lags y rolling específicamente
print(f"\n🔍 Verificación de LAGS:")
lag_cols = [col for col in df.columns if '_lag_' in col]
for col in lag_cols:
    unique = df[col].nunique()
    print(f"   {col:40} | Valores únicos: {unique}")
    if unique <= 5:
        print(f"      Valores: {df[col].unique()}")

print(f"\n🔍 Verificación de ROLLING MEANS:")
rolling_cols = [col for col in df.columns if '_rolling_' in col]
for col in rolling_cols:
    unique = df[col].nunique()
    print(f"   {col:40} | Valores únicos: {unique}")
    if unique <= 5:
        print(f"      Valores: {df[col].unique()}")

print("\n" + "="*80)
