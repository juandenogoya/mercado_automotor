#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 5: Modelo XGBoost AVANZADO con Feature Engineering Fundamentado

Entrena modelo XGBoost con features avanzadas:
- Lags y rolling means del target
- Variaciones macro (tipo cambio, inflación, etc.)
- Ratios transaccionales (prendas/inscripciones, etc.)
- Proporciones de market share (provincias/marcas)
- Features temporales

Sin data leakage y optimizado para evitar overfitting.

Input: data/processed/dataset_forecasting_avanzado.parquet
Output:
  - models/xgboost_avanzado_model.pkl
  - results/xgboost_avanzado/predictions.parquet
  - results/xgboost_avanzado/metrics.json

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_xgboost_avanzado.py
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
INPUT_FILE = 'data/processed/dataset_forecasting_avanzado.parquet'
OUTPUT_DIR_MODELS = 'models'
OUTPUT_DIR_RESULTS = 'results/xgboost_avanzado'

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
    print(f"   - Archivo: {INPUT_FILE}")
    print(f"   - Registros: {len(df):,}")
    print(f"   - Columnas: {len(df.columns)}")
    print(f"   - Período: {df['fecha'].min()} a {df['fecha'].max()}")

    if len(df) < 50:
        print(f"\n⚠️  ADVERTENCIA: Dataset pequeño ({len(df)} registros)")
        print(f"   Recomendación: Usar regularización alta para evitar overfitting")

    return df


def preparar_features(df, target_col='total_operaciones'):
    """
    Prepara features SIN DATA LEAKAGE.

    Excluye:
    - Componentes del target (total_inscripciones, total_prendas, etc.)
    - Operaciones por provincia/marca (son componentes del target)

    Incluye:
    - Lags y rolling del target
    - Variaciones macro (Δ)
    - Ratios transaccionales
    - Proporciones lagged (market share del mes anterior)
    - Features temporales
    """
    print("\n" + "="*80)
    print("PREPARACIÓN DE FEATURES (SIN LEAKAGE)")
    print("="*80)

    # Columnas a EXCLUIR (componentes del target y leakage)
    excluir = [
        'fecha',
        target_col,
        'total_inscripciones',
        'total_transferencias',
        'total_prendas',
    ]

    # TAMBIÉN excluir operaciones por provincia/marca (son componentes del target)
    cols_operaciones_provincia = [col for col in df.columns if col.startswith('operaciones_') and not col.startswith('operaciones_marca_')]
    cols_operaciones_marca = [col for col in df.columns if col.startswith('operaciones_marca_')]

    excluir.extend(cols_operaciones_provincia)
    excluir.extend(cols_operaciones_marca)

    print(f"\n🚫 Excluyendo {len(excluir)} columnas (leakage):")
    print(f"   - Target y componentes: 4")
    print(f"   - Operaciones provincia: {len(cols_operaciones_provincia)}")
    print(f"   - Operaciones marca: {len(cols_operaciones_marca)}")

    # Features candidatas (todo lo demás)
    feature_cols = [col for col in df.columns if col not in excluir]

    print(f"\n📋 Features candidatas: {len(feature_cols)}")

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Clasificar features por tipo
    features_autogresivas = [col for col in X.columns if 'total_operaciones_' in col and ('lag' in col or 'rolling' in col)]
    features_macro_var = [col for col in X.columns if col.startswith('Δ') and any(x in col for x in ['tipo_de_cambio', 'BADLAR', 'IPC', 'LELIQ', 'EMAE', 'reservas'])]
    features_ratios = [col for col in X.columns if 'ratio_' in col]
    features_proporciones = [col for col in X.columns if col.startswith('prop_') or col.startswith('Δprop_')]
    features_proporciones_lag = [col for col in features_proporciones if '_lag' in col]
    features_proporciones_directas = [col for col in features_proporciones if '_lag' not in col]
    features_temporales = [col for col in X.columns if col in ['mes', 'trimestre', 'anio', 'semestre']]

    print(f"\n📊 Features por categoría:")
    print(f"   - Autogresivas (lags/rolling del target): {len(features_autogresivas)}")
    print(f"   - Variaciones macro (Δ): {len(features_macro_var)}")
    print(f"   - Ratios transaccionales: {len(features_ratios)}")
    print(f"   - Proporciones (market share):")
    print(f"      • Directas (t): {len(features_proporciones_directas)}")
    print(f"      • Lagged (t-1, t-2, t-3): {len(features_proporciones_lag)}")
    print(f"   - Temporales: {len(features_temporales)}")

    # ESTRATEGIA: Excluir proporciones directas (t), mantener solo lagged
    print(f"\n🎯 Estrategia de selección:")
    print(f"   ✅ Incluir: Autogresivas, Macro, Ratios, Proporciones LAGGED, Temporales")
    print(f"   ❌ Excluir: Proporciones directas en t (pueden tener leakage sutil)")

    features_finales = (
        features_autogresivas +
        features_macro_var +
        features_ratios +
        features_proporciones_lag +  # Solo lagged, no directas
        features_temporales
    )

    print(f"\n✓ Features finales: {len(features_finales)}")
    print(f"   - Autogresivas: {len(features_autogresivas)}")
    print(f"   - Variaciones macro: {len(features_macro_var)}")
    print(f"   - Ratios: {len(features_ratios)}")
    print(f"   - Proporciones lagged: {len(features_proporciones_lag)}")
    print(f"   - Temporales: {len(features_temporales)}")

    # Filtrar X
    X_selected = X[features_finales].copy()

    # Limpieza
    print(f"\n🧹 Limpieza de datos:")

    # Remover columnas con todos NaN
    cols_all_nan = X_selected.columns[X_selected.isnull().all()].tolist()
    if cols_all_nan:
        print(f"   - Removiendo {len(cols_all_nan)} columnas con todos NaN")
        X_selected = X_selected.drop(columns=cols_all_nan)

    # Imputar NaN
    X_selected = X_selected.ffill().bfill()
    X_selected = X_selected.fillna(X_selected.mean())
    X_selected = X_selected.fillna(0)

    # Remover columnas con varianza cero
    variance = X_selected.var()
    zero_var_cols = variance[variance == 0].index.tolist()
    if zero_var_cols:
        print(f"   - Removiendo {len(zero_var_cols)} columnas con varianza 0")
        X_selected = X_selected.drop(columns=zero_var_cols)

    # Remover filas con NaN en y
    mask = ~y.isnull()
    X_selected = X_selected[mask]
    y = y[mask]

    print(f"\n✓ Datos limpios:")
    print(f"   - Registros: {len(X_selected):,}")
    print(f"   - Features: {len(X_selected.columns)}")

    return X_selected, y, X_selected.columns.tolist()


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


def entrenar_xgboost(X_train, y_train, X_val, y_val):
    """
    Entrena XGBoost con parámetros OPTIMIZADOS para evitar overfitting.
    """
    print("\n" + "="*80)
    print("ENTRENANDO XGBOOST AVANZADO")
    print("="*80)

    # Parámetros OPTIMIZADOS para dataset pequeño
    params = {
        'objective': 'reg:squarederror',
        'n_estimators': 100,           # Moderado
        'max_depth': 3,                 # Baja profundidad para evitar overfitting
        'learning_rate': 0.05,          # Aprendizaje lento
        'min_child_weight': 5,          # Muestras mínimas por hoja
        'subsample': 0.7,               # Bootstrap de datos
        'colsample_bytree': 0.7,        # Bootstrap de features
        'reg_alpha': 1.0,               # Regularización L1
        'reg_lambda': 5.0,              # Regularización L2 (alta)
        'random_state': 42,
    }

    print(f"\n⚙️  Parámetros optimizados (ANTI-OVERFITTING):")
    for key, val in params.items():
        print(f"   - {key:20} = {val}")

    print(f"\n🔄 Entrenando modelo...")
    inicio = datetime.now()

    model = xgb.XGBRegressor(**params)

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False
    )

    tiempo = (datetime.now() - inicio).total_seconds()
    print(f"\n✓ Entrenamiento completado en {tiempo:.1f} segundos")

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

    print(f"\n🔝 Top 15 features más importantes:")
    for idx, row in importancias.head(15).iterrows():
        print(f"   {row['feature']:50} | {row['importance']:.4f}")

    # Acumulado
    total_acum = importancias['importance'].cumsum()
    top_10_pct = total_acum.iloc[9] * 100 if len(total_acum) >= 10 else 0

    print(f"\n📊 Top 10 features explican: {top_10_pct:.2f}% de la importancia")

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
    print("FASE 5: XGBOOST AVANZADO CON FEATURE ENGINEERING FUNDAMENTADO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Cargar datos
        df = cargar_datos()
        if df is None:
            return

        # 2. Preparar features SIN LEAKAGE
        X, y, feature_names = preparar_features(df)

        # 3. Split temporal
        X_train, X_val, X_test, y_train, y_val, y_test = split_temporal(
            X, y, train_pct=0.75, val_pct=0.125
        )

        # 4. Entrenar modelo
        model = entrenar_xgboost(X_train, y_train, X_val, y_val)

        # 5. Evaluar
        metricas = evaluar_modelo(model, X_train, X_val, X_test, y_train, y_val, y_test)

        # 6. Feature importance
        importancias = obtener_feature_importance(model, feature_names)

        # 7. Predicciones finales en test
        y_pred_test = model.predict(X_test)

        # 8. Guardar modelo
        model_file = os.path.join(OUTPUT_DIR_MODELS, 'xgboost_avanzado_model.pkl')
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

        print(f"\n💡 Features utilizadas:")
        print(f"   - Total: {len(feature_names)}")
        print(f"   - Sin data leakage (componentes del target excluidos)")
        print(f"   - Fundamentadas económicamente")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
