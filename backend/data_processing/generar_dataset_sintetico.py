#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar dataset SINTÉTICO para demostración del modelo.

Genera datos simulados con:
- 120 meses de historia
- Variables económicas simuladas
- Target con estacionalidad y tendencia
- Features con correlaciones realistas

Output: data/processed/dataset_forecasting_completo.parquet
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# Configuración
np.random.seed(42)
OUTPUT_DIR = 'data/processed'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'dataset_forecasting_completo.parquet')

os.makedirs(OUTPUT_DIR, exist_ok=True)


def generar_serie_temporal(n_meses=120, tendencia=True, estacionalidad=True, ruido=0.1, base=50000.0):
    """Genera una serie temporal sintética."""
    t = np.arange(n_meses, dtype=float)

    serie = np.full(n_meses, base, dtype=float)  # Iniciar con valor base

    # Tendencia
    if tendencia:
        serie += 0.5 * t

    # Estacionalidad anual (12 meses)
    if estacionalidad:
        serie += 10000 * np.sin(2 * np.pi * t / 12)

    # Ruido
    std = ruido * base  # Usar base para escala del ruido
    serie += np.random.normal(0, std, n_meses)

    return serie


def generar_dataset_sintetico():
    """Genera dataset sintético completo."""
    print("\n" + "="*80)
    print("GENERANDO DATASET SINTÉTICO")
    print("="*80)

    # Fechas mensuales
    fecha_inicio = datetime(2014, 1, 1)
    n_meses = 120
    fechas = [fecha_inicio + timedelta(days=30*i) for i in range(n_meses)]

    # Target: total_operaciones
    total_operaciones = generar_serie_temporal(
        n_meses, tendencia=True, estacionalidad=True, ruido=0.15
    )
    total_operaciones = np.clip(total_operaciones, 30000, 150000).astype(int)

    # Componentes del target (para excluirlas como features)
    total_inscripciones = (total_operaciones * (0.4 + np.random.uniform(-0.05, 0.05, n_meses))).astype(int)
    total_transferencias = (total_operaciones * (0.45 + np.random.uniform(-0.05, 0.05, n_meses))).astype(int)
    total_prendas = (total_operaciones - total_inscripciones - total_transferencias)

    # Provincias (features importantes)
    operaciones_cordoba = (total_operaciones * (0.15 + np.random.uniform(-0.02, 0.02, n_meses))).astype(int)
    operaciones_buenos_aires = (total_operaciones * (0.40 + np.random.uniform(-0.02, 0.02, n_meses))).astype(int)
    operaciones_santa_fe = (total_operaciones * (0.12 + np.random.uniform(-0.02, 0.02, n_meses))).astype(int)
    operaciones_mendoza = (total_operaciones * (0.08 + np.random.uniform(-0.02, 0.02, n_meses))).astype(int)
    operaciones_cordoba_transferencias = (operaciones_cordoba * 0.6).astype(int)

    # Marcas (features importantes)
    operaciones_toyota = (total_operaciones * (0.12 + np.random.uniform(-0.02, 0.02, n_meses))).astype(int)
    operaciones_ford = (total_operaciones * (0.10 + np.random.uniform(-0.02, 0.02, n_meses))).astype(int)
    operaciones_chevrolet = (total_operaciones * (0.15 + np.random.uniform(-0.02, 0.02, n_meses))).astype(int)

    # Variables BCRA (macroeconómicas)
    ipc_mes = generar_serie_temporal(n_meses, tendencia=True, estacionalidad=False, ruido=0.3, base=3.0)
    ipc_mes = np.clip(ipc_mes, 0.5, 10.0)  # Inflación mensual 0.5-10%

    tipo_cambio = generar_serie_temporal(n_meses, tendencia=True, estacionalidad=False, ruido=0.1, base=100)
    tipo_cambio = np.clip(tipo_cambio, 10, 500)  # ARS/USD

    badlar = generar_serie_temporal(n_meses, tendencia=False, estacionalidad=False, ruido=0.2, base=30)
    badlar = np.clip(badlar, 5, 80)  # Tasa 5-80%

    leliq = badlar + np.random.uniform(-2, 5, n_meses)  # LELIQ similar a BADLAR

    reservas = generar_serie_temporal(n_meses, tendencia=False, estacionalidad=False, ruido=0.1, base=50000)
    reservas = np.clip(reservas, 20000, 80000)  # Millones USD

    # Variables INDEC (actividad económica)
    emae = generar_serie_temporal(n_meses, tendencia=True, estacionalidad=True, ruido=0.1, base=100)
    emae = np.clip(emae, 80, 120)  # Índice base 100

    desocupacion = generar_serie_temporal(n_meses, tendencia=False, estacionalidad=True, ruido=0.1, base=10)
    desocupacion = np.clip(desocupacion, 5, 15)  # %

    ripte = generar_serie_temporal(n_meses, tendencia=True, estacionalidad=False, ruido=0.15, base=80000)
    ripte = np.clip(ripte, 20000, 200000)  # Salario promedio

    # Features temporales
    mes = np.array([d.month for d in fechas])
    trimestre = np.array([(d.month - 1) // 3 + 1 for d in fechas])
    anio = np.array([d.year for d in fechas])

    # Lags del target
    lags = {}
    for lag in [1, 2, 3, 6, 12]:
        lags[f'total_operaciones_lag_{lag}'] = np.concatenate([
            np.full(lag, np.nan),
            total_operaciones[:-lag]
        ])

    # Rolling means
    window_sizes = [3, 6, 12]
    rolling = {}
    for window in window_sizes:
        rolling_vals = np.full(n_meses, np.nan)
        for i in range(window, n_meses):
            rolling_vals[i] = np.mean(total_operaciones[i-window:i])
        rolling[f'total_operaciones_rolling_mean_{window}'] = rolling_vals

    # Interacciones (correlacionadas con target)
    interaccion_operaciones_emae = (total_operaciones / 1000) * (emae / 100)
    interaccion_operaciones_ipc = total_operaciones * ipc_mes / 100

    # Construir DataFrame
    data = {
        'fecha': fechas,
        'total_operaciones': total_operaciones,
        'total_inscripciones': total_inscripciones,
        'total_transferencias': total_transferencias,
        'total_prendas': total_prendas,

        # Provincias
        'operaciones_córdoba': operaciones_cordoba,
        'operaciones_buenos_aires': operaciones_buenos_aires,
        'operaciones_santa_fe': operaciones_santa_fe,
        'operaciones_mendoza': operaciones_mendoza,
        'operaciones_córdoba_transferencias': operaciones_cordoba_transferencias,

        # Marcas
        'operaciones_toyota': operaciones_toyota,
        'operaciones_ford': operaciones_ford,
        'operaciones_chevrolet': operaciones_chevrolet,

        # BCRA
        'ipc_mes': ipc_mes,
        'tipo_de_cambio_usd_prom': tipo_cambio,
        'badlar': badlar,
        'leliq': leliq,
        'reservas_internacionales': reservas,

        # INDEC
        'emae': emae,
        'desocupacion': desocupacion,
        'ripte': ripte,

        # Temporales
        'mes': mes,
        'trimestre': trimestre,
        'anio': anio,

        # Interacciones
        'interaccion_operaciones_emae': interaccion_operaciones_emae,
        'interaccion_operaciones_ipc': interaccion_operaciones_ipc,
    }

    # Agregar lags
    data.update(lags)

    # Agregar rolling
    data.update(rolling)

    df = pd.DataFrame(data)

    print(f"\n✓ Dataset generado:")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")
    print(f"   - Target media: {df['total_operaciones'].mean():,.0f}")
    print(f"   - Target std: {df['total_operaciones'].std():,.0f}")

    # Guardar
    df.to_parquet(OUTPUT_FILE, index=False)
    size_mb = os.path.getsize(OUTPUT_FILE) / 1024**2

    print(f"\n💾 Archivo guardado:")
    print(f"   {OUTPUT_FILE}")
    print(f"   Tamaño: {size_mb:.2f} MB")

    # Mostrar primeras filas
    print(f"\n📊 Primeras 5 filas:")
    print(df[['fecha', 'total_operaciones', 'operaciones_córdoba', 'operaciones_buenos_aires', 'emae']].head())

    print("\n" + "="*80)
    print("✅ DATASET SINTÉTICO GENERADO")
    print("="*80)
    print("\n⚠️  NOTA: Este es un dataset SINTÉTICO para demostración")
    print("   Para producción, usa el dataset real generado con el pipeline completo.")

    return df


if __name__ == "__main__":
    generar_dataset_sintetico()
