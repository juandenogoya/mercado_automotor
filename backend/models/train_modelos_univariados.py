#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de entrenamiento de modelos UNIVARIADOS para forecasting.

Implementa modelos que SOLO usan la historia del target (0 features exógenas):
- ARIMA
- SARIMA (con estacionalidad mensual)
- Holt-Winters (Exponential Smoothing)
- Prophet (sin regressors)

Objetivo: Eliminar el problema de overfitting causado por el ratio features/samples.

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_modelos_univariados.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Modelos
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Intentar importar Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except:
    PROPHET_AVAILABLE = False
    print("⚠️  Prophet no disponible, se omitirá de la comparación")

# Configuración
INPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'
OUTPUT_DIR = 'models/saved/'

def load_data():
    """Carga el dataset y extrae solo fecha y target."""
    print(f"\n📂 Cargando: {INPUT_FILE}")
    df = pd.read_parquet(INPUT_FILE)

    # Extraer solo fecha y target
    df_ts = df[['fecha', 'total_operaciones']].copy()
    df_ts = df_ts.sort_values('fecha').reset_index(drop=True)

    print(f"   ✓ {len(df_ts)} registros")
    print(f"   ✓ Período: {df_ts['fecha'].min()} a {df_ts['fecha'].max()}")
    print(f"   ✓ Features exógenas: 0 (solo historia del target)")

    return df_ts

def temporal_split(df_ts, train_pct=0.75, val_pct=0.125):
    """Split temporal: train/val/test."""
    n = len(df_ts)
    n_train = int(n * train_pct)
    n_val = int(n * val_pct)

    train = df_ts.iloc[:n_train].copy()
    val = df_ts.iloc[n_train:n_train+n_val].copy()
    test = df_ts.iloc[n_train+n_val:].copy()

    print(f"\n📊 Split temporal:")
    print(f"   Train: {len(train)} registros ({train['fecha'].min()} a {train['fecha'].max()})")
    print(f"   Val:   {len(val)} registros ({val['fecha'].min()} a {val['fecha'].max()})")
    print(f"   Test:  {len(test)} registros ({test['fecha'].min()} a {test['fecha'].max()})")

    return train, val, test

def evaluate_model(y_true, y_pred, model_name, dataset_name):
    """Calcula métricas de evaluación."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

    return {
        'model': model_name,
        'dataset': dataset_name,
        'MAE': mae,
        'RMSE': rmse,
        'R²': r2,
        'MAPE': mape
    }

def train_arima(train, val, test):
    """Entrena modelo ARIMA(p,d,q)."""
    print("\n" + "="*80)
    print("1. ARIMA")
    print("="*80)

    try:
        # Configuración: ARIMA(2,1,2) - valores razonables para series económicas
        order = (2, 1, 2)
        print(f"   Configuración: order={order}")

        # Entrenar
        print("   Entrenando...")
        model = ARIMA(train['total_operaciones'], order=order)
        fitted = model.fit()

        # Predicciones
        print("   Prediciendo...")

        # Train predictions (in-sample)
        train_pred = fitted.fittedvalues

        # Val predictions (out-of-sample)
        val_pred = fitted.forecast(steps=len(val))

        # Test predictions (out-of-sample, después de val)
        # Re-entrenar con train+val para predecir test
        model_full = ARIMA(
            pd.concat([train['total_operaciones'], val['total_operaciones']]),
            order=order
        )
        fitted_full = model_full.fit()
        test_pred = fitted_full.forecast(steps=len(test))

        # Evaluar
        results = []
        results.append(evaluate_model(train['total_operaciones'], train_pred, 'ARIMA', 'Train'))
        results.append(evaluate_model(val['total_operaciones'].values, val_pred.values, 'ARIMA', 'Val'))
        results.append(evaluate_model(test['total_operaciones'].values, test_pred.values, 'ARIMA', 'Test'))

        # Mostrar resultados
        print("\n   Resultados:")
        for r in results:
            print(f"   {r['dataset']:6} - R²: {r['R²']:7.4f} | MAE: {r['MAE']:10.2f} | MAPE: {r['MAPE']:6.2f}%")

        return results, fitted

    except Exception as e:
        print(f"   ❌ Error en ARIMA: {e}")
        return [], None

def train_sarima(train, val, test):
    """Entrena modelo SARIMA con estacionalidad mensual."""
    print("\n" + "="*80)
    print("2. SARIMA")
    print("="*80)

    try:
        # Configuración: SARIMA(1,1,1)x(1,1,1,12) - estacionalidad mensual
        order = (1, 1, 1)
        seasonal_order = (1, 1, 1, 12)
        print(f"   Configuración: order={order}, seasonal_order={seasonal_order}")

        # Entrenar
        print("   Entrenando...")
        model = SARIMAX(
            train['total_operaciones'],
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        fitted = model.fit(disp=False)

        # Predicciones
        print("   Prediciendo...")

        # Train predictions
        train_pred = fitted.fittedvalues

        # Val predictions
        val_pred = fitted.forecast(steps=len(val))

        # Test predictions (re-entrenar con train+val)
        model_full = SARIMAX(
            pd.concat([train['total_operaciones'], val['total_operaciones']]),
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        fitted_full = model_full.fit(disp=False)
        test_pred = fitted_full.forecast(steps=len(test))

        # Evaluar
        results = []
        results.append(evaluate_model(train['total_operaciones'], train_pred, 'SARIMA', 'Train'))
        results.append(evaluate_model(val['total_operaciones'].values, val_pred.values, 'SARIMA', 'Val'))
        results.append(evaluate_model(test['total_operaciones'].values, test_pred.values, 'SARIMA', 'Test'))

        # Mostrar resultados
        print("\n   Resultados:")
        for r in results:
            print(f"   {r['dataset']:6} - R²: {r['R²']:7.4f} | MAE: {r['MAE']:10.2f} | MAPE: {r['MAPE']:6.2f}%")

        return results, fitted_full

    except Exception as e:
        print(f"   ❌ Error en SARIMA: {e}")
        return [], None

def train_holtwinters(train, val, test):
    """Entrena modelo Holt-Winters (Exponential Smoothing)."""
    print("\n" + "="*80)
    print("3. HOLT-WINTERS (Exponential Smoothing)")
    print("="*80)

    try:
        # Configuración: seasonal='add', seasonal_periods=12 (mensual)
        seasonal = 'add'
        seasonal_periods = 12
        print(f"   Configuración: seasonal={seasonal}, seasonal_periods={seasonal_periods}")

        # Entrenar
        print("   Entrenando...")
        model = ExponentialSmoothing(
            train['total_operaciones'],
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
            trend='add'
        )
        fitted = model.fit()

        # Predicciones
        print("   Prediciendo...")

        # Train predictions
        train_pred = fitted.fittedvalues

        # Val predictions
        val_pred = fitted.forecast(steps=len(val))

        # Test predictions (re-entrenar con train+val)
        model_full = ExponentialSmoothing(
            pd.concat([train['total_operaciones'], val['total_operaciones']]),
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
            trend='add'
        )
        fitted_full = model_full.fit()
        test_pred = fitted_full.forecast(steps=len(test))

        # Evaluar
        results = []
        results.append(evaluate_model(train['total_operaciones'], train_pred, 'Holt-Winters', 'Train'))
        results.append(evaluate_model(val['total_operaciones'].values, val_pred.values, 'Holt-Winters', 'Val'))
        results.append(evaluate_model(test['total_operaciones'].values, test_pred.values, 'Holt-Winters', 'Test'))

        # Mostrar resultados
        print("\n   Resultados:")
        for r in results:
            print(f"   {r['dataset']:6} - R²: {r['R²']:7.4f} | MAE: {r['MAE']:10.2f} | MAPE: {r['MAPE']:6.2f}%")

        return results, fitted_full

    except Exception as e:
        print(f"   ❌ Error en Holt-Winters: {e}")
        return [], None

def train_prophet(train, val, test):
    """Entrena modelo Prophet sin regressors."""
    if not PROPHET_AVAILABLE:
        return [], None

    print("\n" + "="*80)
    print("4. PROPHET (sin regressors)")
    print("="*80)

    try:
        # Preparar datos para Prophet
        df_train = train[['fecha', 'total_operaciones']].copy()
        df_train.columns = ['ds', 'y']

        # Entrenar
        print("   Entrenando...")
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False
        )
        model.fit(df_train)

        # Predicciones
        print("   Prediciendo...")

        # Train predictions
        train_pred = model.predict(df_train)['yhat'].values

        # Val predictions
        df_val = val[['fecha', 'total_operaciones']].copy()
        df_val.columns = ['ds', 'y']
        val_pred = model.predict(df_val)['yhat'].values

        # Test predictions (re-entrenar con train+val)
        df_trainval = pd.concat([
            train[['fecha', 'total_operaciones']],
            val[['fecha', 'total_operaciones']]
        ])
        df_trainval.columns = ['ds', 'y']

        model_full = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False
        )
        model_full.fit(df_trainval)

        df_test = test[['fecha', 'total_operaciones']].copy()
        df_test.columns = ['ds', 'y']
        test_pred = model_full.predict(df_test)['yhat'].values

        # Evaluar
        results = []
        results.append(evaluate_model(train['total_operaciones'].values, train_pred, 'Prophet', 'Train'))
        results.append(evaluate_model(val['total_operaciones'].values, val_pred, 'Prophet', 'Val'))
        results.append(evaluate_model(test['total_operaciones'].values, test_pred, 'Prophet', 'Test'))

        # Mostrar resultados
        print("\n   Resultados:")
        for r in results:
            print(f"   {r['dataset']:6} - R²: {r['R²']:7.4f} | MAE: {r['MAE']:10.2f} | MAPE: {r['MAPE']:6.2f}%")

        return results, model_full

    except Exception as e:
        print(f"   ❌ Error en Prophet: {e}")
        return [], None

def main():
    print("\n" + "="*80)
    print("ENTRENAMIENTO DE MODELOS UNIVARIADOS (0 Features Exógenas)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Cargar datos
    df_ts = load_data()

    # Split temporal
    train, val, test = temporal_split(df_ts)

    # Entrenar modelos
    all_results = []

    # ARIMA
    results_arima, model_arima = train_arima(train, val, test)
    all_results.extend(results_arima)

    # SARIMA
    results_sarima, model_sarima = train_sarima(train, val, test)
    all_results.extend(results_sarima)

    # Holt-Winters
    results_hw, model_hw = train_holtwinters(train, val, test)
    all_results.extend(results_hw)

    # Prophet
    results_prophet, model_prophet = train_prophet(train, val, test)
    all_results.extend(results_prophet)

    # Resumen comparativo
    print("\n" + "="*80)
    print("RESUMEN COMPARATIVO - PERFORMANCE EN TEST SET")
    print("="*80)

    df_results = pd.DataFrame(all_results)
    df_test = df_results[df_results['dataset'] == 'Test'].copy()
    df_test = df_test.sort_values('R²', ascending=False)

    print("\n" + df_test.to_string(index=False))

    # Mejor modelo
    if len(df_test) > 0:
        best_model = df_test.iloc[0]
        print(f"\n🏆 MEJOR MODELO: {best_model['model']}")
        print(f"   R² Test: {best_model['R²']:.4f}")
        print(f"   MAE Test: {best_model['MAE']:.2f}")
        print(f"   MAPE Test: {best_model['MAPE']:.2f}%")

    print("\n" + "="*80)
    print("VENTAJAS DE LOS MODELOS UNIVARIADOS:")
    print("="*80)
    print("✓ 0 features exógenas → elimina problema de ratio features/samples")
    print("✓ Solo usa historia del target → no hay data leakage")
    print("✓ Modelos apropiados para datasets pequeños (79 registros)")
    print("✓ Captura estacionalidad y tendencia automáticamente")
    print("="*80)

    print("\n✅ Entrenamiento completado")

    return df_results

if __name__ == "__main__":
    results = main()
