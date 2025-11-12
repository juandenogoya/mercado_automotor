#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 4C: Modelo XGBoost ULTRA SIMPLIFICADO para Datasets Pequeños

Versión extremadamente simplificada para datasets con < 100 registros:
- Solo TOP 5 features más importantes
- Regularización MUY alta
- Modelo MUY simple (max_depth=2, learning_rate=0.01)
- Enfoque: PREVENIR overfitting a toda costa

Input: data/processed/dataset_forecasting_completo.parquet
Output:
  - models/xgboost_ultra_simple_model.pkl
  - results/xgboost_ultra_simple/predictions.parquet
  - results/xgboost_ultra_simple/metrics.json

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_xgboost_ultra_simple.py
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
INPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'
OUTPUT_DIR_MODELS = 'models'
OUTPUT_DIR_RESULTS = 'results/xgboost_ultra_simple'

os.makedirs(OUTPUT_DIR_MODELS, exist_ok=True)
os.makedirs(OUTPUT_DIR_RESULTS, exist_ok=True)


def cargar_datos():
    """Carga dataset de forecasting."""
    print("\n" + "="*80)
    print("CARGANDO DATOS")
    print("="*80)

    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: Archivo no encontrado: {INPUT_FILE}")
        return None

    df = pd.read_parquet(INPUT_FILE)

    print(f"\n✓ Dataset cargado:")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")

    return df


def preparar_features(df, target_col='total_operaciones', top_n_features=5):
    """
    Prepara features con SELECCIÓN ULTRA AGRESIVA.

    Para datasets < 100 registros, usar SOLO las top 5 features.
    """
    print("\n" + "="*80)
    print(f"PREPARACIÓN DE FEATURES (TOP {top_n_features} SOLAMENTE)")
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

    # SELECCIÓN ULTRA AGRESIVA: Solo top N features
    print(f"\n🔍 Selección ULTRA AGRESIVA: top {top_n_features} features...")

    # Split temporal simple para selección
    n = len(X)
    train_size = int(n * 0.75)
    X_temp = X.iloc[:train_size]
    y_temp = y.iloc[:train_size]

    # Modelo preliminar MUY simple para obtener importancias
    model_temp = xgb.XGBRegressor(
        n_estimators=30,
        max_depth=2,
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

    # Calcular % explicado
    total_importance = importancias['importance'].sum()
    top_importance = importancias.head(top_n_features)['importance'].sum()
    pct_explained = (top_importance / total_importance) * 100

    print(f"\n   💡 Top {top_n_features} explican: {pct_explained:.2f}% de la importancia")

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


def entrenar_xgboost_ultra_simple(X_train, y_train, X_val, y_val):
    """
    Entrena XGBoost con parámetros ULTRA CONSERVADORES.

    Para datasets < 100 registros:
    - max_depth = 2 (árboles MUY poco profundos)
    - learning_rate = 0.01 (aprendizaje MUY lento)
    - n_estimators = 50 (pocos árboles)
    - Regularización MUY alta (L1=5, L2=10)
    """
    print("\n" + "="*80)
    print("ENTRENANDO XGBOOST ULTRA SIMPLIFICADO")
    print("="*80)

    # Parámetros ULTRA CONSERVADORES para datasets pequeños
    params = {
        'objective': 'reg:squarederror',
        'n_estimators': 50,             # MUY REDUCIDO (era 100)
        'max_depth': 2,                 # MUY REDUCIDO (era 3) - árboles muy simples
        'learning_rate': 0.01,          # MUY REDUCIDO (era 0.05) - aprendizaje muy lento
        'min_child_weight': 10,         # MUY AUMENTADO (era 5) - muchas muestras por hoja
        'subsample': 0.6,               # MUY REDUCIDO (era 0.7) - menos datos por árbol
        'colsample_bytree': 0.6,        # MUY REDUCIDO (era 0.7) - menos features por árbol
        'reg_alpha': 5.0,               # MUY AUMENTADO (era 1.0) - regularización L1 alta
        'reg_lambda': 10.0,             # MUY AUMENTADO (era 5.0) - regularización L2 muy alta
        'random_state': 42,
    }

    print(f"\n⚙️  Parámetros ULTRA CONSERVADORES:")
    for key, val in params.items():
        print(f"   - {key:20} = {val}")

    print(f"\n🔄 Entrenando modelo...")
    inicio = datetime.now()

    # Crear y entrenar modelo
    model = xgb.XGBRegressor(**params)

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False
    )

    tiempo = (datetime.now() - inicio).total_seconds()
    print(f"\n✓ Entrenamiento completado en {tiempo:.1f} segundos")
    print(f"   - Árboles entrenados: {model.n_estimators}")

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
    elif gap_train_test < 0.50:
        print(f"\n❌ Overfitting moderado (gap 0.30-0.50)")
    else:
        print(f"\n❌ Overfitting severo (gap > 0.50)")

    # Advertencia si test es negativo
    if r2_test < 0:
        print(f"\n⚠️  ADVERTENCIA: R² Test negativo ({r2_test:.4f})")
        print(f"   El modelo predice PEOR que simplemente usar la media.")
        print(f"   Considerar:")
        print(f"   - Usar regresión lineal simple en lugar de XGBoost")
        print(f"   - Reducir aún más features (< 5)")
        print(f"   - Recolectar más datos (mínimo 200-300 registros)")

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

    print(f"\n🔝 Features y su importancia:")
    for idx, row in importancias.iterrows():
        print(f"   {row['feature']:45} | {row['importance']:.4f}")

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
    print("FASE 4C: XGBOOST ULTRA SIMPLIFICADO - DATASETS PEQUEÑOS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Cargar datos
        df = cargar_datos()
        if df is None:
            return

        # Determinar número de features según tamaño del dataset
        n_registros = len(df)
        if n_registros < 50:
            top_n = 3
            print(f"\n⚠️  Dataset MUY pequeño ({n_registros} registros)")
            print(f"   Usando solo {top_n} features")
        elif n_registros < 100:
            top_n = 5
            print(f"\n⚠️  Dataset pequeño ({n_registros} registros)")
            print(f"   Usando solo {top_n} features")
        else:
            top_n = 10
            print(f"\n✓ Dataset aceptable ({n_registros} registros)")
            print(f"   Usando {top_n} features")

        # 2. Preparar features con SELECCIÓN ULTRA AGRESIVA
        X, y, feature_names = preparar_features(df, top_n_features=top_n)

        # 3. Split temporal
        X_train, X_val, X_test, y_train, y_val, y_test = split_temporal(
            X, y, train_pct=0.75, val_pct=0.125
        )

        # 4. Entrenar modelo ULTRA SIMPLIFICADO
        model = entrenar_xgboost_ultra_simple(X_train, y_train, X_val, y_val)

        # 5. Evaluar
        metricas = evaluar_modelo(model, X_train, X_val, X_test, y_train, y_val, y_test)

        # 6. Feature importance
        importancias = obtener_feature_importance(model, feature_names)

        # 7. Predicciones finales en test
        y_pred_test = model.predict(X_test)

        # 8. Guardar modelo
        model_file = os.path.join(OUTPUT_DIR_MODELS, 'xgboost_ultra_simple_model.pkl')
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

        # Comparación con versión optimizada
        print(f"\n💡 Cambios vs versión optimizada:")
        print(f"   - Features: 15 → {top_n}")
        print(f"   - max_depth: 3 → 2")
        print(f"   - learning_rate: 0.05 → 0.01")
        print(f"   - n_estimators: 100 → 50")
        print(f"   - Regularización: L1=1→5, L2=5→10")
        print(f"   - Objetivo: Máxima simplicidad para dataset pequeño")

        # Recomendaciones finales
        if test_metrics['R2'] < 0:
            print(f"\n📌 RECOMENDACIONES:")
            print(f"   1. Con {n_registros} registros, XGBoost puede no ser apropiado")
            print(f"   2. Considerar regresión lineal con Ridge/Lasso")
            print(f"   3. O simplemente usar promedio móvil / ARIMA")
            print(f"   4. Ideal: Recolectar más datos (mínimo 200-300 registros)")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
