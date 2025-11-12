#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 6: Comparación de Modelos para Series Temporales Cortas

Compara 3 modelos diseñados para datasets pequeños (79 registros):
1. Prophet (Facebook) - Diseñado para series temporales
2. SARIMAX (ARIMAX) - Modelo estadístico clásico
3. ElasticNet - Regresión regularizada con feature selection

Input: data/processed/dataset_forecasting_avanzado.parquet
Output:
  - models/prophet_model.pkl
  - models/sarimax_model.pkl
  - models/elasticnet_model.pkl
  - results/comparacion_modelos/comparison.json

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_comparacion_modelos.py
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
import warnings
from datetime import datetime
from pathlib import Path

# Modelos
from prophet import Prophet
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.linear_model import ElasticNet
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

warnings.filterwarnings('ignore')

# Directorios
INPUT_FILE = 'data/processed/dataset_forecasting_avanzado.parquet'
OUTPUT_DIR_MODELS = 'models'
OUTPUT_DIR_RESULTS = 'results/comparacion_modelos'

os.makedirs(OUTPUT_DIR_MODELS, exist_ok=True)
os.makedirs(OUTPUT_DIR_RESULTS, exist_ok=True)


def cargar_datos():
    """Carga dataset de forecasting avanzado."""
    print("\n" + "="*80)
    print("CARGANDO DATOS")
    print("="*80)

    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: Archivo no encontrado: {INPUT_FILE}")
        print(f"\n📝 Ejecuta primero:")
        print(f"   python backend/data_processing/09_feature_engineering_avanzado.py")
        return None

    df = pd.read_parquet(INPUT_FILE)

    print(f"\n✓ Dataset cargado:")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")
    print(f"   - Columnas: {len(df.columns)}")

    return df


def split_temporal(df, train_pct=0.75, val_pct=0.125):
    """Split temporal (NO aleatorio)."""
    print("\n" + "="*80)
    print("SPLIT TEMPORAL")
    print("="*80)

    n = len(df)
    train_size = int(n * train_pct)
    val_size = int(n * val_pct)

    df_train = df.iloc[:train_size].copy()
    df_val = df.iloc[train_size:train_size+val_size].copy()
    df_test = df.iloc[train_size+val_size:].copy()

    print(f"\n✓ Split completado:")
    print(f"   Train:      {len(df_train):3} registros ({train_pct*100:.1f}%)")
    print(f"   Validation: {len(df_val):3} registros ({val_pct*100:.1f}%)")
    print(f"   Test:       {len(df_test):3} registros ({(1-train_pct-val_pct)*100:.1f}%)")

    return df_train, df_val, df_test


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


def entrenar_prophet(df_train, df_val, df_test, target_col='total_operaciones'):
    """
    Entrena modelo Prophet.

    Prophet es robusto para series temporales cortas y maneja
    automáticamente tendencias y estacionalidad.
    """
    print("\n" + "="*80)
    print("MODELO 1: PROPHET (Facebook)")
    print("="*80)

    # Preparar datos para Prophet (necesita 'ds' y 'y')
    df_prophet_train = pd.DataFrame({
        'ds': df_train['fecha'],
        'y': df_train[target_col]
    })

    # Buscar features macro para usar como regresores
    macro_features = [col for col in df_train.columns if any(x in col.lower() for x in ['tipo_de_cambio', 'ipc', 'badlar'])]

    # Si no hay macro, usar lags del target como regresores
    if len(macro_features) == 0:
        print(f"\n⚠️  No hay features macro disponibles")
        print(f"   Usando lags del target como regresores")
        regressors = ['total_operaciones_lag1', 'total_operaciones_lag2', 'total_operaciones_lag3']
    else:
        print(f"\n✓ Usando {len(macro_features)} features macro como regresores")
        regressors = macro_features[:3]  # Máximo 3 regresores

    # Agregar regresores al dataframe
    for reg in regressors:
        if reg in df_train.columns:
            df_prophet_train[reg] = df_train[reg].values

    print(f"\n⚙️  Configuración Prophet:")
    print(f"   - Regresores: {len(regressors)}")
    for reg in regressors:
        print(f"      • {reg}")

    # Crear y configurar modelo
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05  # Menos flexible para evitar overfitting
    )

    # Agregar regresores
    for reg in regressors:
        if reg in df_prophet_train.columns:
            model.add_regressor(reg)

    # Entrenar
    print(f"\n🔄 Entrenando Prophet...")
    inicio = datetime.now()
    model.fit(df_prophet_train)
    tiempo = (datetime.now() - inicio).total_seconds()
    print(f"✓ Entrenamiento completado en {tiempo:.1f} segundos")

    # Predecir en cada conjunto
    resultados = {}

    for nombre, df_set in [('Train', df_train), ('Validation', df_val), ('Test', df_test)]:
        df_prophet_set = pd.DataFrame({'ds': df_set['fecha']})

        # Agregar regresores
        for reg in regressors:
            if reg in df_set.columns:
                df_prophet_set[reg] = df_set[reg].values

        forecast = model.predict(df_prophet_set)
        y_pred = forecast['yhat'].values
        y_true = df_set[target_col].values

        metricas = calcular_metricas(y_true, y_pred, 'Prophet')

        print(f"\n📊 {nombre}:")
        print(f"   RMSE: {metricas['RMSE']:,.2f}")
        print(f"   MAE:  {metricas['MAE']:,.2f}")
        print(f"   MAPE: {metricas['MAPE']:.2f}%")
        print(f"   R²:   {metricas['R2']:.4f}")

        resultados[nombre] = metricas

    return model, resultados


def entrenar_sarimax(df_train, df_val, df_test, target_col='total_operaciones'):
    """
    Entrena modelo SARIMAX (ARIMAX con estacionalidad).

    SARIMAX es robusto para series temporales y permite features exógenas.
    """
    print("\n" + "="*80)
    print("MODELO 2: SARIMAX (ARIMAX)")
    print("="*80)

    # Seleccionar features exógenas (máximo 5 para evitar overfitting)
    excluir = ['fecha', target_col, 'total_inscripciones', 'total_transferencias', 'total_prendas']
    excluir += [col for col in df_train.columns if col.startswith('operaciones_')]

    feature_cols = [col for col in df_train.columns if col not in excluir]

    # Buscar mejores features usando correlación
    X_temp = df_train[feature_cols].copy()
    y_temp = df_train[target_col].copy()

    # Limpiar NaN
    X_temp = X_temp.ffill().bfill().fillna(0)

    # Calcular correlación absoluta
    correlaciones = {}
    for col in X_temp.columns:
        try:
            corr = abs(X_temp[col].corr(y_temp))
            correlaciones[col] = corr
        except:
            pass

    # Top 5 features
    top_features = sorted(correlaciones.items(), key=lambda x: x[1], reverse=True)[:5]
    selected_features = [f[0] for f in top_features]

    print(f"\n✓ Top 5 features seleccionadas (por correlación):")
    for feat, corr in top_features:
        print(f"   {feat:50} | {corr:.4f}")

    # Preparar datos
    y_train = df_train[target_col].values
    X_train = df_train[selected_features].ffill().bfill().fillna(0).values

    y_val = df_val[target_col].values
    X_val = df_val[selected_features].ffill().bfill().fillna(0).values

    y_test = df_test[target_col].values
    X_test = df_test[selected_features].ffill().bfill().fillna(0).values

    # SARIMAX con estacionalidad mensual
    print(f"\n⚙️  Configuración SARIMAX:")
    print(f"   - Order (p,d,q): (1,1,1)")
    print(f"   - Seasonal order: (1,1,1,12) [estacionalidad anual]")
    print(f"   - Features exógenas: {len(selected_features)}")

    print(f"\n🔄 Entrenando SARIMAX...")
    inicio = datetime.now()

    try:
        model = SARIMAX(
            y_train,
            exog=X_train,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 12),
            enforce_stationarity=False,
            enforce_invertibility=False
        )

        model_fit = model.fit(disp=False, maxiter=200)
        tiempo = (datetime.now() - inicio).total_seconds()
        print(f"✓ Entrenamiento completado en {tiempo:.1f} segundos")

    except Exception as e:
        print(f"⚠️  SARIMAX falló, usando ARIMA simple: {e}")
        # Fallback a ARIMA simple sin estacionalidad
        model = SARIMAX(
            y_train,
            exog=X_train,
            order=(1, 1, 1),
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        model_fit = model.fit(disp=False, maxiter=200)
        tiempo = (datetime.now() - inicio).total_seconds()
        print(f"✓ Entrenamiento completado en {tiempo:.1f} segundos")

    # Predecir
    resultados = {}

    # Train
    y_pred_train = model_fit.predict(start=0, end=len(y_train)-1, exog=X_train)
    metricas_train = calcular_metricas(y_train, y_pred_train, 'SARIMAX')
    resultados['Train'] = metricas_train

    print(f"\n📊 Train:")
    print(f"   RMSE: {metricas_train['RMSE']:,.2f}")
    print(f"   MAE:  {metricas_train['MAE']:,.2f}")
    print(f"   MAPE: {metricas_train['MAPE']:.2f}%")
    print(f"   R²:   {metricas_train['R2']:.4f}")

    # Validation
    y_pred_val = model_fit.forecast(steps=len(y_val), exog=X_val)
    metricas_val = calcular_metricas(y_val, y_pred_val, 'SARIMAX')
    resultados['Validation'] = metricas_val

    print(f"\n📊 Validation:")
    print(f"   RMSE: {metricas_val['RMSE']:,.2f}")
    print(f"   MAE:  {metricas_val['MAE']:,.2f}")
    print(f"   MAPE: {metricas_val['MAPE']:.2f}%")
    print(f"   R²:   {metricas_val['R2']:.4f}")

    # Test
    y_pred_test = model_fit.forecast(steps=len(y_val) + len(y_test), exog=np.vstack([X_val, X_test]))[-len(y_test):]
    metricas_test = calcular_metricas(y_test, y_pred_test, 'SARIMAX')
    resultados['Test'] = metricas_test

    print(f"\n📊 Test:")
    print(f"   RMSE: {metricas_test['RMSE']:,.2f}")
    print(f"   MAE:  {metricas_test['MAE']:,.2f}")
    print(f"   MAPE: {metricas_test['MAPE']:.2f}%")
    print(f"   R²:   {metricas_test['R2']:.4f}")

    return model_fit, resultados, selected_features


def entrenar_elasticnet(df_train, df_val, df_test, target_col='total_operaciones', n_features=15):
    """
    Entrena ElasticNet con selección de features.

    ElasticNet combina L1 y L2 regularization, ideal para datasets pequeños.
    """
    print("\n" + "="*80)
    print("MODELO 3: ELASTICNET (Regresión Regularizada)")
    print("="*80)

    # Preparar features
    excluir = ['fecha', target_col, 'total_inscripciones', 'total_transferencias', 'total_prendas']
    excluir += [col for col in df_train.columns if col.startswith('operaciones_')]

    feature_cols = [col for col in df_train.columns if col not in excluir]

    X_train = df_train[feature_cols].copy()
    y_train = df_train[target_col].values

    X_val = df_val[feature_cols].copy()
    y_val = df_val[target_col].values

    X_test = df_test[feature_cols].copy()
    y_test = df_test[target_col].values

    # Limpiar datos
    X_train = X_train.ffill().bfill().fillna(0)
    X_val = X_val.ffill().bfill().fillna(0)
    X_test = X_test.ffill().bfill().fillna(0)

    # Remover varianza cero
    variance = X_train.var()
    cols_nonzero = variance[variance > 0].index.tolist()
    X_train = X_train[cols_nonzero]
    X_val = X_val[cols_nonzero]
    X_test = X_test[cols_nonzero]

    print(f"\n📋 Features disponibles: {len(X_train.columns)}")

    # Feature selection: Top N features
    n_features = min(n_features, len(X_train.columns), len(y_train) // 3)  # Max features/samples = 1/3

    print(f"\n🔍 Seleccionando top {n_features} features...")

    selector = SelectKBest(score_func=f_regression, k=n_features)
    X_train_selected = selector.fit_transform(X_train, y_train)
    X_val_selected = selector.transform(X_val)
    X_test_selected = selector.transform(X_test)

    # Obtener nombres de features seleccionadas
    selected_mask = selector.get_support()
    selected_features = X_train.columns[selected_mask].tolist()

    print(f"\n✓ Top {n_features} features seleccionadas:")
    scores = selector.scores_[selected_mask]
    for feat, score in sorted(zip(selected_features, scores), key=lambda x: x[1], reverse=True):
        print(f"   {feat:50} | {score:.2f}")

    # Normalizar
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_selected)
    X_val_scaled = scaler.transform(X_val_selected)
    X_test_scaled = scaler.transform(X_test_selected)

    # Entrenar ElasticNet
    print(f"\n⚙️  Configuración ElasticNet:")
    print(f"   - alpha: 1.0 (regularización)")
    print(f"   - l1_ratio: 0.5 (50% L1, 50% L2)")

    print(f"\n🔄 Entrenando ElasticNet...")
    inicio = datetime.now()

    model = ElasticNet(
        alpha=1.0,
        l1_ratio=0.5,
        max_iter=5000,
        random_state=42
    )

    model.fit(X_train_scaled, y_train)
    tiempo = (datetime.now() - inicio).total_seconds()
    print(f"✓ Entrenamiento completado en {tiempo:.1f} segundos")

    # Evaluar
    resultados = {}

    for nombre, X_scaled, y_true in [
        ('Train', X_train_scaled, y_train),
        ('Validation', X_val_scaled, y_val),
        ('Test', X_test_scaled, y_test)
    ]:
        y_pred = model.predict(X_scaled)
        metricas = calcular_metricas(y_true, y_pred, 'ElasticNet')

        print(f"\n📊 {nombre}:")
        print(f"   RMSE: {metricas['RMSE']:,.2f}")
        print(f"   MAE:  {metricas['MAE']:,.2f}")
        print(f"   MAPE: {metricas['MAPE']:.2f}%")
        print(f"   R²:   {metricas['R2']:.4f}")

        resultados[nombre] = metricas

    return model, resultados, selector, scaler, selected_features


def comparar_modelos(resultados_prophet, resultados_sarimax, resultados_elasticnet):
    """Compara los tres modelos."""
    print("\n" + "="*80)
    print("COMPARACIÓN DE MODELOS")
    print("="*80)

    # Consolidar resultados
    comparacion = {
        'Prophet': resultados_prophet,
        'SARIMAX': resultados_sarimax,
        'ElasticNet': resultados_elasticnet
    }

    # Tabla comparativa en Test
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
    print(f"\n📈 Análisis de overfitting (Train R² - Test R²):")
    for modelo, resultados in comparacion.items():
        gap = resultados['Train']['R2'] - resultados['Test']['R2']
        status = "✅" if gap < 0.15 else ("⚠️" if gap < 0.30 else "❌")
        print(f"   {status} {modelo:<12}: {gap:>6.4f}")

    return comparacion, mejor_modelo


def guardar_resultados(comparacion, mejor_modelo):
    """Guarda resultados de comparación."""
    print("\n" + "="*80)
    print("GUARDANDO RESULTADOS")
    print("="*80)

    output_file = os.path.join(OUTPUT_DIR_RESULTS, 'comparison.json')

    resultados_json = {
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mejor_modelo': mejor_modelo,
        'modelos': comparacion
    }

    with open(output_file, 'w') as f:
        json.dump(resultados_json, f, indent=2)

    print(f"\n✓ Comparación guardada: {output_file}")


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("COMPARACIÓN DE MODELOS PARA SERIES TEMPORALES CORTAS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Cargar datos
        df = cargar_datos()
        if df is None:
            return

        # 2. Split temporal
        df_train, df_val, df_test = split_temporal(df)

        # 3. Entrenar Prophet
        model_prophet, resultados_prophet = entrenar_prophet(df_train, df_val, df_test)

        # 4. Entrenar SARIMAX
        model_sarimax, resultados_sarimax, features_sarimax = entrenar_sarimax(df_train, df_val, df_test)

        # 5. Entrenar ElasticNet
        model_elasticnet, resultados_elasticnet, selector, scaler, features_elasticnet = entrenar_elasticnet(
            df_train, df_val, df_test, n_features=15
        )

        # 6. Comparar modelos
        comparacion, mejor_modelo = comparar_modelos(resultados_prophet, resultados_sarimax, resultados_elasticnet)

        # 7. Guardar modelos
        print("\n" + "="*80)
        print("GUARDANDO MODELOS")
        print("="*80)

        with open(os.path.join(OUTPUT_DIR_MODELS, 'prophet_model.pkl'), 'wb') as f:
            pickle.dump(model_prophet, f)
        print(f"   ✓ Prophet guardado")

        with open(os.path.join(OUTPUT_DIR_MODELS, 'sarimax_model.pkl'), 'wb') as f:
            pickle.dump(model_sarimax, f)
        print(f"   ✓ SARIMAX guardado")

        with open(os.path.join(OUTPUT_DIR_MODELS, 'elasticnet_model.pkl'), 'wb') as f:
            pickle.dump({'model': model_elasticnet, 'selector': selector, 'scaler': scaler}, f)
        print(f"   ✓ ElasticNet guardado")

        # 8. Guardar resultados
        guardar_resultados(comparacion, mejor_modelo)

        # Resumen final
        print("\n" + "="*80)
        print("✅ COMPARACIÓN COMPLETADA")
        print("="*80)

        print(f"\n🏆 Mejor modelo: {mejor_modelo}")
        print(f"\n📁 Archivos generados:")
        print(f"   - models/prophet_model.pkl")
        print(f"   - models/sarimax_model.pkl")
        print(f"   - models/elasticnet_model.pkl")
        print(f"   - results/comparacion_modelos/comparison.json")

        print(f"\n💡 Recomendación:")
        test_r2 = comparacion[mejor_modelo]['Test']['R2']
        if test_r2 > 0.7:
            print(f"   ✅ {mejor_modelo} tiene excelente performance (R² > 0.7)")
        elif test_r2 > 0.5:
            print(f"   ⚠️  {mejor_modelo} tiene performance aceptable (R² > 0.5)")
        elif test_r2 > 0:
            print(f"   ⚠️  {mejor_modelo} tiene performance moderada (R² > 0)")
        else:
            print(f"   ❌ Todos los modelos tienen performance pobre (R² < 0)")
            print(f"   💡 Considera:")
            print(f"      - Obtener más datos (actualmente {len(df)} registros)")
            print(f"      - Agregar features macro (BCRA/INDEC)")
            print(f"      - Usar granularidad semanal en vez de mensual")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
