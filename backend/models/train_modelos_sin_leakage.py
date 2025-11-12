#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 7: Entrenamiento de Modelos SIN DATA LEAKAGE

Entrena SARIMAX y ElasticNet usando SOLO features válidas:
- Lags y rolling del target
- Ratios transaccionales LAGGED
- Proporciones LAGGED (no directas)
- Features temporales

EXCLUYE features con leakage:
- Proporciones directas (t)
- Variaciones directas (t)
- Componentes del target
- Operaciones por provincia/marca

Input: data/processed/dataset_forecasting_avanzado.parquet
Output:
  - models/sarimax_sin_leakage.pkl
  - models/elasticnet_sin_leakage.pkl
  - results/modelos_sin_leakage/comparison.json

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_modelos_sin_leakage.py
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
import warnings
from datetime import datetime

# Modelos
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.linear_model import ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

warnings.filterwarnings('ignore')

# Directorios
INPUT_FILE = 'data/processed/dataset_forecasting_avanzado.parquet'
OUTPUT_DIR_MODELS = 'models'
OUTPUT_DIR_RESULTS = 'results/modelos_sin_leakage'

os.makedirs(OUTPUT_DIR_MODELS, exist_ok=True)
os.makedirs(OUTPUT_DIR_RESULTS, exist_ok=True)


def cargar_datos():
    """Carga dataset de forecasting avanzado."""
    print("\n" + "="*80)
    print("CARGANDO DATOS")
    print("="*80)

    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: Archivo no encontrado: {INPUT_FILE}")
        return None

    df = pd.read_parquet(INPUT_FILE)

    print(f"\n✓ Dataset cargado:")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")
    print(f"   - Columnas totales: {len(df.columns)}")

    return df


def seleccionar_features_sin_leakage(df, target_col='total_operaciones'):
    """
    Selecciona SOLO features SIN data leakage.

    INCLUYE:
    - Lags y rolling del target
    - Ratios lagged
    - Proporciones lagged (solo con _lag)
    - Temporales

    EXCLUYE:
    - Componentes del target
    - Operaciones por provincia/marca
    - Proporciones/ratios/variaciones directas (sin _lag)
    """
    print("\n" + "="*80)
    print("SELECCIÓN DE FEATURES SIN LEAKAGE")
    print("="*80)

    # 1. Features autogresivas del target
    features_autogresivas = [col for col in df.columns if 'total_operaciones_' in col and ('lag' in col or 'rolling' in col)]

    # 2. Ratios lagged (INCLUIR solo los que tienen _lag)
    features_ratios_lag = [col for col in df.columns if 'ratio_' in col and '_lag' in col]

    # 3. Proporciones lagged (INCLUIR solo los que tienen _lag)
    features_prop_lag = [col for col in df.columns if col.startswith('prop_') and '_lag' in col]

    # 4. Variaciones de proporciones lagged (INCLUIR solo los que tienen _lag)
    features_deltaprop_lag = [col for col in df.columns if col.startswith('Δprop_') and '_lag' in col]

    # 5. Temporales
    features_temporales = [col for col in df.columns if col in ['mes', 'trimestre', 'anio', 'semestre']]

    # CONSOLIDAR features válidas
    features_validas = (
        features_autogresivas +
        features_ratios_lag +
        features_prop_lag +
        features_deltaprop_lag +
        features_temporales
    )

    print(f"\n📊 Features SIN leakage seleccionadas:")
    print(f"   - Autogresivas (lags/rolling):      {len(features_autogresivas)}")
    print(f"   - Ratios lagged:                    {len(features_ratios_lag)}")
    print(f"   - Proporciones lagged:              {len(features_prop_lag)}")
    print(f"   - Variaciones proporciones lagged:  {len(features_deltaprop_lag)}")
    print(f"   - Temporales:                       {len(features_temporales)}")
    print(f"   TOTAL: {len(features_validas)} features")

    print(f"\n❌ Features EXCLUIDAS (con leakage):")

    # Contar excluidas
    excluidas_componentes = ['total_inscripciones', 'total_transferencias', 'total_prendas']
    excluidas_operaciones = [col for col in df.columns if col.startswith('operaciones_')]
    excluidas_prop_directas = [col for col in df.columns if col.startswith('prop_') and '_lag' not in col]
    excluidas_deltaprop_directas = [col for col in df.columns if col.startswith('Δprop_') and '_lag' not in col]
    excluidas_ratios_directos = [col for col in df.columns if 'ratio_' in col and '_lag' not in col]

    print(f"   - Componentes del target:           {len(excluidas_componentes)}")
    print(f"   - Operaciones provincia/marca:      {len(excluidas_operaciones)}")
    print(f"   - Proporciones directas (t):        {len(excluidas_prop_directas)}")
    print(f"   - Variaciones directas (t):         {len(excluidas_deltaprop_directas)}")
    print(f"   - Ratios directos (t):              {len(excluidas_ratios_directos)}")
    print(f"   TOTAL EXCLUIDAS: {len(excluidas_componentes) + len(excluidas_operaciones) + len(excluidas_prop_directas) + len(excluidas_deltaprop_directas) + len(excluidas_ratios_directos)}")

    # Crear dataset limpio
    X = df[features_validas].copy()
    y = df[target_col].copy()

    # Limpieza
    print(f"\n🧹 Limpieza de datos:")

    # Remover columnas con todos NaN
    cols_all_nan = X.columns[X.isnull().all()].tolist()
    if cols_all_nan:
        print(f"   - Removiendo {len(cols_all_nan)} columnas con todos NaN")
        X = X.drop(columns=cols_all_nan)

    # Imputar NaN
    X = X.ffill().bfill()
    X = X.fillna(X.mean())
    X = X.fillna(0)

    # Remover columnas con varianza cero
    variance = X.var()
    zero_var_cols = variance[variance == 0].index.tolist()
    if zero_var_cols:
        print(f"   - Removiendo {len(zero_var_cols)} columnas con varianza 0")
        X = X.drop(columns=zero_var_cols)

    # Remover filas con NaN en y
    mask = ~y.isnull()
    X = X[mask]
    y = y[mask]

    print(f"\n✓ Dataset final:")
    print(f"   - Registros: {len(X):,}")
    print(f"   - Features: {len(X.columns)}")
    print(f"   - Ratio features/samples: {len(X.columns)/len(X):.2f}")

    return X, y, X.columns.tolist()


def split_temporal(X, y, train_pct=0.75, val_pct=0.125):
    """Split temporal (NO aleatorio)."""
    print("\n" + "="*80)
    print("SPLIT TEMPORAL")
    print("="*80)

    n = len(X)
    train_size = int(n * train_pct)
    val_size = int(n * val_pct)

    X_train = X.iloc[:train_size]
    y_train = y.iloc[:train_size]

    X_val = X.iloc[train_size:train_size+val_size]
    y_val = y.iloc[train_size:train_size+val_size]

    X_test = X.iloc[train_size+val_size:]
    y_test = y.iloc[train_size+val_size:]

    print(f"\n✓ Split completado:")
    print(f"   Train:      {len(X_train):3} registros ({train_pct*100:.1f}%)")
    print(f"   Validation: {len(X_val):3} registros ({val_pct*100:.1f}%)")
    print(f"   Test:       {len(X_test):3} registros ({(1-train_pct-val_pct)*100:.1f}%)")

    return X_train, X_val, X_test, y_train, y_val, y_test


def calcular_metricas(y_true, y_pred, nombre_modelo):
    """Calcula métricas de evaluación."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)

    return {
        'modelo': nombre_modelo,
        'RMSE': float(rmse),
        'MAE': float(mae),
        'MAPE': float(mape),
        'R2': float(r2)
    }


def entrenar_sarimax(X_train, y_train, X_val, y_val, X_test, y_test):
    """Entrena SARIMAX con features sin leakage."""
    print("\n" + "="*80)
    print("MODELO 1: SARIMAX (SIN LEAKAGE)")
    print("="*80)

    # Seleccionar top 5 features por correlación
    correlaciones = {}
    for col in X_train.columns:
        try:
            corr = abs(X_train[col].corr(y_train))
            if not np.isnan(corr):
                correlaciones[col] = corr
        except:
            pass

    top_features = sorted(correlaciones.items(), key=lambda x: x[1], reverse=True)[:5]
    selected_features = [f[0] for f in top_features]

    print(f"\n✓ Top 5 features seleccionadas:")
    for feat, corr in top_features:
        print(f"   {feat:50} | {corr:.4f}")

    # Preparar datos
    X_train_sel = X_train[selected_features].values
    X_val_sel = X_val[selected_features].values
    X_test_sel = X_test[selected_features].values

    print(f"\n⚙️  Configuración SARIMAX:")
    print(f"   - Order (p,d,q): (1,1,1)")
    print(f"   - Seasonal order: (1,1,1,12)")
    print(f"   - Features exógenas: {len(selected_features)}")

    print(f"\n🔄 Entrenando...")
    inicio = datetime.now()

    try:
        model = SARIMAX(
            y_train.values,
            exog=X_train_sel,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        model_fit = model.fit(disp=False, maxiter=200)
    except Exception as e:
        print(f"⚠️  SARIMAX con estacionalidad falló: {e}")
        print(f"   Usando ARIMA simple...")
        model = SARIMAX(
            y_train.values,
            exog=X_train_sel,
            order=(1, 1, 1),
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        model_fit = model.fit(disp=False, maxiter=200)

    tiempo = (datetime.now() - inicio).total_seconds()
    print(f"✓ Completado en {tiempo:.1f}s")

    # Evaluar
    resultados = {}

    # Train
    y_pred_train = model_fit.predict(start=0, end=len(y_train)-1, exog=X_train_sel)
    metricas_train = calcular_metricas(y_train, y_pred_train, 'SARIMAX')
    resultados['Train'] = metricas_train
    print(f"\n📊 Train: R²={metricas_train['R2']:.4f}, MAPE={metricas_train['MAPE']:.2f}%")

    # Validation
    y_pred_val = model_fit.forecast(steps=len(y_val), exog=X_val_sel)
    metricas_val = calcular_metricas(y_val, y_pred_val, 'SARIMAX')
    resultados['Validation'] = metricas_val
    print(f"📊 Val:   R²={metricas_val['R2']:.4f}, MAPE={metricas_val['MAPE']:.2f}%")

    # Test
    y_pred_test = model_fit.forecast(steps=len(y_val) + len(y_test), exog=np.vstack([X_val_sel, X_test_sel]))[-len(y_test):]
    metricas_test = calcular_metricas(y_test, y_pred_test, 'SARIMAX')
    resultados['Test'] = metricas_test
    print(f"📊 Test:  R²={metricas_test['R2']:.4f}, MAPE={metricas_test['MAPE']:.2f}%")

    return model_fit, resultados, selected_features


def entrenar_elasticnet(X_train, y_train, X_val, y_val, X_test, y_test):
    """Entrena ElasticNet con features sin leakage."""
    print("\n" + "="*80)
    print("MODELO 2: ELASTICNET (SIN LEAKAGE)")
    print("="*80)

    # Usar todas las features (ya están filtradas)
    print(f"\n✓ Usando {len(X_train.columns)} features")

    # Normalizar
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    print(f"\n⚙️  Configuración ElasticNet:")
    print(f"   - alpha: 1.0")
    print(f"   - l1_ratio: 0.5")

    print(f"\n🔄 Entrenando...")
    inicio = datetime.now()

    model = ElasticNet(
        alpha=1.0,
        l1_ratio=0.5,
        max_iter=5000,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)

    tiempo = (datetime.now() - inicio).total_seconds()
    print(f"✓ Completado en {tiempo:.1f}s")

    # Evaluar
    resultados = {}

    for nombre, X_scaled, y_true in [
        ('Train', X_train_scaled, y_train),
        ('Validation', X_val_scaled, y_val),
        ('Test', X_test_scaled, y_test)
    ]:
        y_pred = model.predict(X_scaled)
        metricas = calcular_metricas(y_true, y_pred, 'ElasticNet')
        resultados[nombre] = metricas
        print(f"\n📊 {nombre}: R²={metricas['R2']:.4f}, MAPE={metricas['MAPE']:.2f}%")

    return model, resultados, scaler


def comparar_modelos(resultados_sarimax, resultados_elasticnet):
    """Compara los modelos."""
    print("\n" + "="*80)
    print("COMPARACIÓN DE MODELOS")
    print("="*80)

    comparacion = {
        'SARIMAX': resultados_sarimax,
        'ElasticNet': resultados_elasticnet
    }

    print(f"\n📊 Performance en TEST:")
    print(f"{'Modelo':<15} {'RMSE':>12} {'MAE':>12} {'MAPE':>8} {'R²':>8}")
    print(f"{'-'*60}")

    mejor_modelo = None
    mejor_r2 = -np.inf

    for modelo, resultados in comparacion.items():
        test_metrics = resultados['Test']
        print(f"{modelo:<15} {test_metrics['RMSE']:>12,.2f} {test_metrics['MAE']:>12,.2f} {test_metrics['MAPE']:>7.2f}% {test_metrics['R2']:>8.4f}")

        if test_metrics['R2'] > mejor_r2:
            mejor_r2 = test_metrics['R2']
            mejor_modelo = modelo

    print(f"\n🏆 MEJOR MODELO: {mejor_modelo} (R² = {mejor_r2:.4f})")

    # Análisis de overfitting
    print(f"\n📈 Análisis de overfitting:")
    for modelo, resultados in comparacion.items():
        gap = resultados['Train']['R2'] - resultados['Test']['R2']
        status = "✅" if gap < 0.15 else ("⚠️" if gap < 0.30 else "❌")
        print(f"   {status} {modelo:<12}: gap = {gap:.4f}")

    return comparacion, mejor_modelo


def guardar_resultados(comparacion, mejor_modelo):
    """Guarda resultados."""
    output_file = os.path.join(OUTPUT_DIR_RESULTS, 'comparison.json')

    resultados_json = {
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mejor_modelo': mejor_modelo,
        'modelos': comparacion
    }

    with open(output_file, 'w') as f:
        json.dump(resultados_json, f, indent=2)

    print(f"\n✓ Resultados guardados: {output_file}")


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("ENTRENAMIENTO DE MODELOS SIN DATA LEAKAGE")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Cargar datos
        df = cargar_datos()
        if df is None:
            return

        # 2. Seleccionar features SIN leakage
        X, y, feature_names = seleccionar_features_sin_leakage(df)

        # 3. Split temporal
        X_train, X_val, X_test, y_train, y_val, y_test = split_temporal(X, y)

        # 4. Entrenar SARIMAX
        model_sarimax, resultados_sarimax, features_sarimax = entrenar_sarimax(
            X_train, y_train, X_val, y_val, X_test, y_test
        )

        # 5. Entrenar ElasticNet
        model_elasticnet, resultados_elasticnet, scaler = entrenar_elasticnet(
            X_train, y_train, X_val, y_val, X_test, y_test
        )

        # 6. Comparar
        comparacion, mejor_modelo = comparar_modelos(resultados_sarimax, resultados_elasticnet)

        # 7. Guardar modelos
        print("\n" + "="*80)
        print("GUARDANDO MODELOS")
        print("="*80)

        with open(os.path.join(OUTPUT_DIR_MODELS, 'sarimax_sin_leakage.pkl'), 'wb') as f:
            pickle.dump(model_sarimax, f)
        print(f"   ✓ SARIMAX guardado")

        with open(os.path.join(OUTPUT_DIR_MODELS, 'elasticnet_sin_leakage.pkl'), 'wb') as f:
            pickle.dump({'model': model_elasticnet, 'scaler': scaler}, f)
        print(f"   ✓ ElasticNet guardado")

        # 8. Guardar resultados
        guardar_resultados(comparacion, mejor_modelo)

        # Resumen final
        print("\n" + "="*80)
        print("✅ ENTRENAMIENTO COMPLETADO")
        print("="*80)

        print(f"\n🏆 Mejor modelo: {mejor_modelo}")
        print(f"\n📁 Archivos:")
        print(f"   - models/sarimax_sin_leakage.pkl")
        print(f"   - models/elasticnet_sin_leakage.pkl")
        print(f"   - results/modelos_sin_leakage/comparison.json")

        test_r2 = comparacion[mejor_modelo]['Test']['R2']
        if test_r2 > 0.5:
            print(f"\n✅ Modelo con buena performance (R² > 0.5)")
        elif test_r2 > 0:
            print(f"\n⚠️  Modelo con performance moderada (R² > 0)")
        else:
            print(f"\n❌ Modelo con performance pobre (R² < 0)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
