#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 4A: Modelo XGBoost para Forecasting

XGBoost (Extreme Gradient Boosting) es un algoritmo de ensemble basado en árboles
de decisión que es muy efectivo con datos tabulares y múltiples features.

Características:
- Maneja múltiples features predictoras (~100 en nuestro caso)
- Captura relaciones no-lineales y complejas
- Feature importance para interpretabilidad
- Robusto y rápido de entrenar
- Muy utilizado en competencias de ML

Input: data/processed/dataset_forecasting_completo.parquet
Output:
  - models/xgboost_model.pkl
  - results/xgboost_predictions.parquet
  - results/xgboost_metrics.json
  - results/xgboost_feature_importance.png

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_xgboost.py
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
from datetime import datetime
from pathlib import Path

# Importar XGBoost
try:
    import xgboost as xgb
    from xgboost import XGBRegressor
except ImportError:
    print("❌ ERROR: XGBoost no está instalado")
    print("Instala con: pip install xgboost")
    exit(1)

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Directorios
INPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'
OUTPUT_DIR_MODELS = 'models'
OUTPUT_DIR_RESULTS = 'results/xgboost'

os.makedirs(OUTPUT_DIR_MODELS, exist_ok=True)
os.makedirs(OUTPUT_DIR_RESULTS, exist_ok=True)


def cargar_datos():
    """
    Carga dataset de forecasting.

    Returns:
        DataFrame con datos completos
    """
    print("\n" + "="*80)
    print("CARGANDO DATOS")
    print("="*80)

    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: Archivo no encontrado: {INPUT_FILE}")
        print("\n📝 Ejecuta primero:")
        print("   python backend/data_processing/ejecutar_pipeline_completa.py")
        return None

    df = pd.read_parquet(INPUT_FILE)

    print(f"\n✓ Dataset cargado:")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")

    return df


def preparar_features(df, target_col='total_operaciones'):
    """
    Prepara features y target para XGBoost.

    Args:
        df: DataFrame original
        target_col: Columna target

    Returns:
        X (features), y (target), feature_names
    """
    print("\n" + "="*80)
    print("PREPARANDO FEATURES PARA XGBOOST")
    print("="*80)

    # Columnas a excluir
    excluir = [
        'fecha',  # No es feature numérica
        target_col,  # Es el target
        'tramite_fecha',  # Si existe
        'total_inscripciones',  # No usar componentes del target
        'total_transferencias',  # No usar componentes del target
        'total_prendas',  # No usar componentes del target
    ]

    print(f"\n⚠️  Columnas excluidas (para evitar data leakage):")
    for col in excluir:
        if col in df.columns:
            print(f"   - {col}")

    # Columnas de features
    feature_cols = [col for col in df.columns if col not in excluir]

    # Filtrar solo columnas numéricas
    numericas = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    print(f"\n✓ Features seleccionadas: {len(numericas)}")

    # Categorías de features
    categorias = {
        'Operaciones': [c for c in numericas if 'total_' in c or 'operaciones_' in c],
        'Lags': [c for c in numericas if '_lag_' in c],
        'Rolling': [c for c in numericas if '_rolling_' in c],
        'BCRA': [c for c in numericas if any(x in c.lower() for x in ['ipc', 'tipo de cambio', 'badlar', 'leliq', 'reservas'])],
        'INDEC': [c for c in numericas if any(x in c.lower() for x in ['emae', 'desocupacion', 'actividad', 'empleo', 'ripte'])],
        'Temporales': [c for c in numericas if any(x in c for x in ['anio', 'mes', 'trimestre', 'sin', 'cos'])],
        'Avanzadas': [c for c in numericas if any(x in c for x in ['ratio', 'var_', 'tendencia', 'interaccion'])],
    }

    print(f"\n📊 Features por categoría:")
    for cat, cols in categorias.items():
        if cols:
            print(f"   {cat:15}: {len(cols):2} features")

    # Crear X y y
    X = df[numericas].copy()
    y = df[target_col].copy()

    # Imputar NaN en lugar de eliminar
    print(f"\n🔄 Manejando valores faltantes...")

    # Contar NaN antes
    nan_antes = X.isnull().sum().sum()
    print(f"   - Total NaN antes: {nan_antes:,}")

    # Identificar columnas con todos NaN
    cols_all_nan = X.columns[X.isnull().all()].tolist()
    if cols_all_nan:
        print(f"   ⚠️  Columnas completamente NaN (eliminando): {len(cols_all_nan)}")
        for col in cols_all_nan[:5]:  # Mostrar primeras 5
            print(f"      - {col}")
        X = X.drop(columns=cols_all_nan)
        numericas = [col for col in numericas if col not in cols_all_nan]

    # Imputar usando métodos actualizados (no deprecated)
    X = X.ffill().bfill()  # Forward fill y backward fill

    # Para columnas que aún tienen NaN (por ejemplo, todas eran NaN al inicio), usar media
    X = X.fillna(X.mean())

    # Si aún quedan NaN (columnas con varianza 0), usar 0
    X = X.fillna(0)

    # Verificar si quedaron NaN después de imputación
    nan_despues = X.isnull().sum().sum()

    # Eliminar solo filas donde el target es NaN
    mask = ~y.isnull()
    X = X[mask]
    y = y[mask]

    print(f"   - NaN imputados: {nan_antes:,}")
    print(f"   - NaN restantes: {nan_despues}")
    print(f"   - Filas con target NaN removidas: {(~mask).sum()}")

    # Verificar features con varianza cero
    variance = X.var()
    zero_var_cols = variance[variance == 0].index.tolist()
    if zero_var_cols:
        print(f"   ⚠️  Features con varianza cero (eliminando): {len(zero_var_cols)}")
        for col in zero_var_cols[:5]:
            print(f"      - {col}")
        X = X.drop(columns=zero_var_cols)
        numericas = [col for col in numericas if col not in zero_var_cols]

    print(f"\n✓ Dataset preparado:")
    print(f"   - Registros: {len(X):,}")
    print(f"   - Features: {len(numericas)}")

    return X, y, numericas


def split_temporal(X, y, train_pct=0.75, val_pct=0.125):
    """
    Split temporal de datos (NO aleatorio).

    Args:
        X: Features
        y: Target
        train_pct: % para train
        val_pct: % para validation

    Returns:
        X_train, X_val, X_test, y_train, y_val, y_test
    """
    print("\n" + "="*80)
    print("SPLIT TEMPORAL DE DATOS")
    print("="*80)

    n = len(X)
    train_size = int(n * train_pct)
    val_size = int(n * val_pct)

    X_train = X.iloc[:train_size]
    X_val = X.iloc[train_size:train_size+val_size]
    X_test = X.iloc[train_size+val_size:]

    y_train = y.iloc[:train_size]
    y_val = y.iloc[train_size:train_size+val_size]
    y_test = y.iloc[train_size+val_size:]

    print(f"\n✓ Split completado:")
    print(f"   Train:      {len(X_train):3} registros")
    print(f"   Validation: {len(X_val):3} registros")
    print(f"   Test:       {len(X_test):3} registros")
    print(f"\n   Proporción: {train_pct*100:.1f}% / {val_pct*100:.1f}% / {(1-train_pct-val_pct)*100:.1f}%")

    return X_train, X_val, X_test, y_train, y_val, y_test


def entrenar_xgboost(X_train, y_train, X_val, y_val, **kwargs):
    """
    Entrena modelo XGBoost con early stopping.

    Args:
        X_train, y_train: Datos de entrenamiento
        X_val, y_val: Datos de validación
        **kwargs: Parámetros adicionales para XGBoost

    Returns:
        Modelo XGBoost entrenado
    """
    print("\n" + "="*80)
    print("ENTRENANDO MODELO XGBOOST")
    print("="*80)

    # Configuración por defecto
    config = {
        'n_estimators': 1000,
        'max_depth': 6,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 3,
        'gamma': 0,
        'reg_alpha': 0.1,  # L1 regularization
        'reg_lambda': 1.0,  # L2 regularization
        'random_state': 42,
        'n_jobs': -1,
        'objective': 'reg:squarederror',
    }

    config.update(kwargs)

    print(f"\n⚙️  Configuración:")
    for key, val in config.items():
        print(f"   - {key}: {val}")

    # Crear modelo
    model = XGBRegressor(**config)

    # Entrenar con early stopping
    print(f"\n🔄 Entrenando modelo con early stopping...")
    inicio = datetime.now()

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        eval_metric='rmse',
        early_stopping_rounds=50,
        verbose=False
    )

    tiempo = (datetime.now() - inicio).total_seconds()

    print(f"\n✓ Entrenamiento completado en {tiempo:.1f} segundos")
    print(f"   - Mejor iteración: {model.best_iteration}")
    print(f"   - Score train: {model.best_score:.4f}")

    return model


def calcular_metricas(y_true, y_pred):
    """
    Calcula métricas de evaluación.

    Args:
        y_true: Valores reales
        y_pred: Valores predichos

    Returns:
        Dict con métricas
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)

    metricas = {
        'RMSE': float(rmse),
        'MAE': float(mae),
        'MAPE': float(mape),
        'R2': float(r2)
    }

    return metricas


def evaluar_modelo(model, X_train, X_val, X_test, y_train, y_val, y_test):
    """
    Evalúa modelo en train, validation y test.

    Args:
        model: Modelo XGBoost
        X_train, X_val, X_test: Features
        y_train, y_val, y_test: Targets

    Returns:
        Dict con métricas por split
    """
    print("\n" + "="*80)
    print("EVALUANDO MODELO")
    print("="*80)

    resultados = {}

    for nombre, X, y in [('Train', X_train, y_train),
                          ('Validation', X_val, y_val),
                          ('Test', X_test, y_test)]:
        # Predecir
        y_pred = model.predict(X)

        # Calcular métricas
        metricas = calcular_metricas(y, y_pred)

        resultados[nombre] = metricas

        # Mostrar
        print(f"\n📊 {nombre}:")
        print(f"   RMSE:  {metricas['RMSE']:,.2f}")
        print(f"   MAE:   {metricas['MAE']:,.2f}")
        print(f"   MAPE:  {metricas['MAPE']:.2f}%")
        print(f"   R²:    {metricas['R2']:.4f}")

    return resultados


def analizar_feature_importance(model, feature_names, top_n=20):
    """
    Analiza importancia de features.

    Args:
        model: Modelo XGBoost
        feature_names: Nombres de features
        top_n: Top N features a mostrar

    Returns:
        DataFrame con feature importance
    """
    print("\n" + "="*80)
    print(f"FEATURE IMPORTANCE (TOP {top_n})")
    print("="*80)

    # Obtener importancia
    importance = model.feature_importances_

    # Crear DataFrame
    df_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    })

    # Ordenar
    df_importance = df_importance.sort_values('importance', ascending=False).reset_index(drop=True)

    # Mostrar top
    print(f"\n📊 Top {top_n} features más importantes:")
    for i, row in df_importance.head(top_n).iterrows():
        print(f"   {i+1:2}. {row['feature']:40} | {row['importance']:.4f}")

    return df_importance


def guardar_modelo(model, filepath):
    """
    Guarda modelo XGBoost.

    Args:
        model: Modelo XGBoost
        filepath: Ruta del archivo
    """
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)

    size_mb = os.path.getsize(filepath) / 1024**2
    print(f"\n💾 Modelo guardado: {filepath} ({size_mb:.2f} MB)")


def guardar_resultados(y_test, y_pred, fechas_test, metricas, df_importance, output_dir):
    """
    Guarda predicciones, métricas y feature importance.

    Args:
        y_test: Valores reales
        y_pred: Predicciones
        fechas_test: Fechas de test
        metricas: Dict con métricas
        df_importance: DataFrame con importancia
        output_dir: Directorio de salida
    """
    print("\n" + "="*80)
    print("GUARDANDO RESULTADOS")
    print("="*80)

    # Predicciones
    pred_file = os.path.join(output_dir, 'predictions.parquet')
    df_pred = pd.DataFrame({
        'fecha': fechas_test,
        'real': y_test,
        'prediccion': y_pred
    })
    df_pred.to_parquet(pred_file, index=False)
    print(f"   ✓ Predicciones: {pred_file}")

    # Métricas
    metrics_file = os.path.join(output_dir, 'metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(metricas, f, indent=2)
    print(f"   ✓ Métricas: {metrics_file}")

    # Feature importance
    importance_file = os.path.join(output_dir, 'feature_importance.parquet')
    df_importance.to_parquet(importance_file, index=False)
    print(f"   ✓ Feature importance: {importance_file}")


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FASE 4A: MODELO XGBOOST PARA FORECASTING")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Cargar datos
        df = cargar_datos()
        if df is None:
            return

        # Guardar fechas para después
        fechas = df['fecha'].copy()

        # 2. Preparar features
        X, y, feature_names = preparar_features(df)

        # Ajustar fechas al mismo índice
        fechas = fechas[X.index]

        # 3. Split temporal
        X_train, X_val, X_test, y_train, y_val, y_test = split_temporal(X, y, train_pct=0.75, val_pct=0.125)

        # Fechas de test
        fechas_test = fechas.iloc[len(X_train) + len(X_val):].values

        # 4. Entrenar modelo
        model = entrenar_xgboost(X_train, y_train, X_val, y_val)

        # 5. Evaluar
        metricas = evaluar_modelo(model, X_train, X_val, X_test, y_train, y_val, y_test)

        # 6. Feature importance
        df_importance = analizar_feature_importance(model, feature_names, top_n=20)

        # 7. Predicciones finales en test
        y_pred_test = model.predict(X_test)

        # 8. Guardar modelo
        model_file = os.path.join(OUTPUT_DIR_MODELS, 'xgboost_model.pkl')
        guardar_modelo(model, model_file)

        # 9. Guardar resultados
        guardar_resultados(y_test.values, y_pred_test, fechas_test, metricas, df_importance, OUTPUT_DIR_RESULTS)

        # Resumen final
        print("\n" + "="*80)
        print("✅ ENTRENAMIENTO COMPLETADO")
        print("="*80)

        print(f"\n📁 Archivos generados:")
        print(f"   - Modelo: {model_file}")
        print(f"   - Resultados: {OUTPUT_DIR_RESULTS}/")

        print(f"\n🎯 Mejor performance (Test):")
        test_metrics = metricas['Test']
        print(f"   RMSE: {test_metrics['RMSE']:,.2f}")
        print(f"   MAE:  {test_metrics['MAE']:,.2f}")
        print(f"   MAPE: {test_metrics['MAPE']:.2f}%")
        print(f"   R²:   {test_metrics['R2']:.4f}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
