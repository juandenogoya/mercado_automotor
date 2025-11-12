#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 4B: Modelo XGBoost OPTIMIZADO para Forecasting

Versión optimizada que resuelve el problema de overfitting:
- Selección automática de top features
- Mayor regularización
- Menor complejidad del modelo
- Adaptado para datasets pequeños

Input: data/processed/dataset_forecasting_completo.parquet
Output:
  - models/xgboost_optimized_model.pkl
  - results/xgboost_optimized/predictions.parquet
  - results/xgboost_optimized/metrics.json

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_xgboost_optimizado.py
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
from datetime import datetime
from pathlib import Path

# XGBoost
import xgboost as xgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Directorios
# Auto-detectar si existe dataset semanal o mensual
INPUT_FILE_SEMANAL = 'data/processed/dataset_forecasting_completo_semanal.parquet'
INPUT_FILE_MENSUAL = 'data/processed/dataset_forecasting_completo.parquet'

# Preferir semanal si existe
if os.path.exists(INPUT_FILE_SEMANAL):
    INPUT_FILE = INPUT_FILE_SEMANAL
    GRANULARIDAD = 'semanal'
elif os.path.exists(INPUT_FILE_MENSUAL):
    INPUT_FILE = INPUT_FILE_MENSUAL
    GRANULARIDAD = 'mensual'
else:
    INPUT_FILE = INPUT_FILE_MENSUAL  # Default
    GRANULARIDAD = 'mensual'

OUTPUT_DIR_MODELS = 'models'
OUTPUT_DIR_RESULTS = 'results/xgboost_optimized'

os.makedirs(OUTPUT_DIR_MODELS, exist_ok=True)
os.makedirs(OUTPUT_DIR_RESULTS, exist_ok=True)


def cargar_datos():
    """Carga dataset de forecasting."""
    print("\n" + "="*80)
    print("CARGANDO DATOS")
    print("="*80)

    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: Archivo no encontrado: {INPUT_FILE}")
        print(f"\n💡 Archivos disponibles:")
        if os.path.exists(INPUT_FILE_SEMANAL):
            print(f"   ✓ Dataset semanal: {INPUT_FILE_SEMANAL}")
        if os.path.exists(INPUT_FILE_MENSUAL):
            print(f"   ✓ Dataset mensual: {INPUT_FILE_MENSUAL}")
        if not os.path.exists(INPUT_FILE_SEMANAL) and not os.path.exists(INPUT_FILE_MENSUAL):
            print(f"   ❌ Ningún dataset encontrado")
            print(f"\n📝 Ejecuta primero:")
            print(f"   python backend/data_processing/07b_unificar_datasets_forecasting_semanal.py")
        return None

    df = pd.read_parquet(INPUT_FILE)

    print(f"\n✓ Dataset cargado ({GRANULARIDAD.upper()}):")
    print(f"   - Archivo: {INPUT_FILE}")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")

    if GRANULARIDAD == 'mensual' and len(df) < 100:
        print(f"\n⚠️  ADVERTENCIA: Dataset mensual con solo {len(df)} registros")
        print(f"   💡 Recomendación: Usar dataset semanal para mejor generalización")
        print(f"   📝 Ejecutar: python backend/data_processing/07b_unificar_datasets_forecasting_semanal.py")

    return df


def preparar_features(df, target_col='total_operaciones', top_n_features=15):
    """
    Prepara features con SELECCIÓN AUTOMÁTICA de las más importantes.

    Args:
        df: DataFrame original
        target_col: Columna target
        top_n_features: Número de features a mantener

    Returns:
        X, y, lista de features seleccionadas
    """
    print("\n" + "="*80)
    print("PREPARACIÓN DE FEATURES (CON SELECCIÓN)")
    print("="*80)

    # Columnas a excluir
    excluir = [
        'fecha',
        target_col,
        'tramite_fecha',
        'total_inscripciones',
        'total_transferencias',
        'total_prendas',
    ]

    # Features candidatas
    feature_cols = [col for col in df.columns if col not in excluir]

    print(f"\n📋 Features candidatas: {len(feature_cols)}")

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Limpiar NaN y varianza cero
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

    print(f"\n✓ Datos limpios:")
    print(f"   - Registros: {len(X):,}")
    print(f"   - Features disponibles: {len(X.columns)}")

    # SELECCIÓN DE FEATURES: Entrenar modelo preliminar
    print(f"\n🔍 Selección de top {top_n_features} features...")

    # Split temporal simple para selección
    n = len(X)
    train_size = int(n * 0.75)
    X_temp = X.iloc[:train_size]
    y_temp = y.iloc[:train_size]

    # Modelo preliminar simple para obtener importancias
    model_temp = xgb.XGBRegressor(
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
        random_state=42
    )
    model_temp.fit(X_temp, y_temp)

    # Obtener importancias
    importancias = pd.DataFrame({
        'feature': X.columns,
        'importance': model_temp.feature_importances_
    }).sort_values('importance', ascending=False)

    # Seleccionar top N
    top_features = importancias.head(top_n_features)['feature'].tolist()

    print(f"\n📊 Top {top_n_features} features seleccionadas:")
    for i, row in importancias.head(top_n_features).iterrows():
        print(f"   {row['feature']:45} | {row['importance']:.4f}")

    # Filtrar X con solo top features
    X_selected = X[top_features].copy()

    print(f"\n✓ Features finales: {len(X_selected.columns)}")

    return X_selected, y, top_features


def split_temporal(X, y, train_pct=0.75, val_pct=0.125):
    """Split temporal de datos (NO aleatorio)."""
    print("\n" + "="*80)
    print("SPLIT TEMPORAL DE DATOS")
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


def entrenar_xgboost_optimizado(X_train, y_train, X_val, y_val):
    """
    Entrena XGBoost con PARÁMETROS OPTIMIZADOS para evitar overfitting.

    Mayor regularización y menor complejidad.
    """
    print("\n" + "="*80)
    print("ENTRENANDO XGBOOST OPTIMIZADO")
    print("="*80)

    # Parámetros OPTIMIZADOS para dataset pequeño
    params = {
        'objective': 'reg:squarederror',
        'n_estimators': 100,           # Menos árboles
        'max_depth': 3,                 # REDUCIDO (era 6) - menos profundidad
        'learning_rate': 0.05,          # REDUCIDO (era 0.1) - aprendizaje más lento
        'min_child_weight': 5,          # AUMENTADO (era 1) - más muestras por hoja
        'subsample': 0.7,               # REDUCIDO (era 0.8) - menos datos por árbol
        'colsample_bytree': 0.7,        # REDUCIDO (era 0.8) - menos features por árbol
        'reg_alpha': 1.0,               # AUMENTADO (era 0) - regularización L1
        'reg_lambda': 5.0,              # AUMENTADO (era 1) - regularización L2
        'random_state': 42,
        'early_stopping_rounds': 10,
    }

    print(f"\n⚙️  Parámetros optimizados (ANTI-OVERFITTING):")
    for key, val in params.items():
        if key != 'early_stopping_rounds':
            print(f"   - {key:20} = {val}")

    print(f"\n🔄 Entrenando modelo...")
    inicio = datetime.now()

    # Separar early_stopping_rounds
    early_stopping = params.pop('early_stopping_rounds')

    # Crear y entrenar modelo
    model = xgb.XGBRegressor(**params)

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False
    )

    tiempo = (datetime.now() - inicio).total_seconds()
    print(f"\n✓ Entrenamiento completado en {tiempo:.1f} segundos")

    # Mostrar mejor iteración (solo si se usó early stopping)
    try:
        print(f"   - Mejor iteración: {model.best_iteration}")
    except AttributeError:
        print(f"   - Iteraciones completadas: {model.n_estimators}")

    return model


def calcular_metricas(y_true, y_pred):
    """Calcula métricas de evaluación."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    r2 = r2_score(y_true, y_pred)

    return {
        'RMSE': float(rmse),
        'MAE': float(mae),
        'MAPE': float(mape),
        'R2': float(r2)
    }


def evaluar_modelo(model, X_train, X_val, X_test, y_train, y_val, y_test):
    """Evalúa modelo en train, validation y test."""
    print("\n" + "="*80)
    print("EVALUANDO MODELO")
    print("="*80)

    resultados = {}

    for nombre, X, y in [
        ('Train', X_train, y_train),
        ('Validation', X_val, y_val),
        ('Test', X_test, y_test)
    ]:
        y_pred = model.predict(X)
        metricas = calcular_metricas(y, y_pred)
        resultados[nombre] = metricas

        print(f"\n📊 {nombre}:")
        print(f"   RMSE:  {metricas['RMSE']:,.2f}")
        print(f"   MAE:   {metricas['MAE']:,.2f}")
        print(f"   MAPE:  {metricas['MAPE']:.2f}%")
        print(f"   R²:    {metricas['R2']:.4f}")

    # Análisis de overfitting
    print("\n" + "="*80)
    print("ANÁLISIS DE OVERFITTING")
    print("="*80)

    r2_train = resultados['Train']['R2']
    r2_val = resultados['Validation']['R2']
    r2_test = resultados['Test']['R2']

    gap_train_val = r2_train - r2_val
    gap_train_test = r2_train - r2_test

    print(f"\n📈 Diferencia de R²:")
    print(f"   Train vs Validation: {gap_train_val:.4f}")
    print(f"   Train vs Test:       {gap_train_test:.4f}")

    if gap_train_test < 0.15:
        print(f"\n✅ Modelo bien generalizado (gap < 0.15)")
    elif gap_train_test < 0.30:
        print(f"\n⚠️  Overfitting leve (gap 0.15-0.30)")
    else:
        print(f"\n❌ Overfitting severo (gap > 0.30)")

    return resultados


def obtener_feature_importance(model, feature_names):
    """Obtiene feature importance del modelo."""
    print("\n" + "="*80)
    print("IMPORTANCIA DE FEATURES")
    print("="*80)

    importancias = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n🔝 Top 10 features más importantes:")
    for idx, row in importancias.head(10).iterrows():
        print(f"   {row['feature']:45} | {row['importance']:.4f}")

    # Acumulado
    total_acum = importancias['importance'].cumsum()
    top_5_pct = total_acum.iloc[4] * 100 if len(total_acum) >= 5 else 0

    print(f"\n📊 Top 5 features explican: {top_5_pct:.2f}% de la importancia")

    return importancias


def guardar_modelo(model, filepath):
    """Guarda modelo XGBoost."""
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)

    size_mb = os.path.getsize(filepath) / 1024**2
    print(f"\n💾 Modelo guardado: {filepath} ({size_mb:.2f} MB)")


def guardar_resultados(y_test, y_pred, metricas, importancias, output_dir):
    """Guarda predicciones, métricas e importancias."""
    print("\n" + "="*80)
    print("GUARDANDO RESULTADOS")
    print("="*80)

    # Predicciones
    pred_file = os.path.join(output_dir, 'predictions.parquet')
    df_pred = pd.DataFrame({
        'real': y_test.values,
        'prediccion': y_pred,
        'error': y_test.values - y_pred,
        'error_pct': ((y_test.values - y_pred) / y_test.values) * 100
    })
    df_pred.to_parquet(pred_file, index=False)
    print(f"   ✓ Predicciones: {pred_file}")

    # Métricas
    metrics_file = os.path.join(output_dir, 'metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(metricas, f, indent=2)
    print(f"   ✓ Métricas: {metrics_file}")

    # Feature importance
    importance_file = os.path.join(output_dir, 'feature_importance.csv')
    importancias.to_csv(importance_file, index=False)
    print(f"   ✓ Feature importance: {importance_file}")


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FASE 4B: XGBOOST OPTIMIZADO - ANTI-OVERFITTING")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Cargar datos
        df = cargar_datos()
        if df is None:
            return

        # 2. Preparar features con SELECCIÓN
        X, y, feature_names = preparar_features(df, top_n_features=15)

        # 3. Split temporal
        X_train, X_val, X_test, y_train, y_val, y_test = split_temporal(
            X, y, train_pct=0.75, val_pct=0.125
        )

        # 4. Entrenar modelo OPTIMIZADO
        model = entrenar_xgboost_optimizado(X_train, y_train, X_val, y_val)

        # 5. Evaluar
        metricas = evaluar_modelo(model, X_train, X_val, X_test, y_train, y_val, y_test)

        # 6. Feature importance
        importancias = obtener_feature_importance(model, feature_names)

        # 7. Predicciones finales en test
        y_pred_test = model.predict(X_test)

        # 8. Guardar modelo
        model_file = os.path.join(OUTPUT_DIR_MODELS, 'xgboost_optimized_model.pkl')
        guardar_modelo(model, model_file)

        # 9. Guardar resultados
        guardar_resultados(y_test, y_pred_test, metricas, importancias, OUTPUT_DIR_RESULTS)

        # Resumen final
        print("\n" + "="*80)
        print("✅ ENTRENAMIENTO COMPLETADO")
        print("="*80)

        print(f"\n📁 Archivos generados:")
        print(f"   - Modelo: {model_file}")
        print(f"   - Resultados: {OUTPUT_DIR_RESULTS}/")

        print(f"\n🎯 Performance final (Test):")
        test_metrics = metricas['Test']
        print(f"   RMSE: {test_metrics['RMSE']:,.2f}")
        print(f"   MAE:  {test_metrics['MAE']:,.2f}")
        print(f"   MAPE: {test_metrics['MAPE']:.2f}%")
        print(f"   R²:   {test_metrics['R2']:.4f}")

        # Comparación con versión original
        print(f"\n💡 Mejoras vs versión original:")
        print(f"   - Features reducidas: 58 → 15")
        print(f"   - Regularización aumentada (L1=1.0, L2=5.0)")
        print(f"   - Complejidad reducida (max_depth: 6→3)")
        print(f"   - Objetivo: Mejor generalización, menos overfitting")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
