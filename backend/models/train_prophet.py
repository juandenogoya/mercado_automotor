#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 4A: Modelo Prophet para Forecasting

Prophet (desarrollado por Facebook/Meta) es un modelo diseñado específicamente
para series temporales de negocios con estacionalidad fuerte.

Características:
- Maneja estacionalidad automáticamente (mensual, anual)
- Robusto a valores faltantes y outliers
- Interpreta componentes: tendencia, estacionalidad, holidays
- Puede incluir regresores externos (variables BCRA/INDEC)

Input: data/processed/dataset_forecasting_completo.parquet
Output:
  - models/prophet_model.pkl
  - results/prophet_predictions.parquet
  - results/prophet_metrics.json

Ejecutar desde: mercado_automotor/
Comando: python backend/models/train_prophet.py
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
from datetime import datetime
from pathlib import Path

# Importar Prophet
try:
    from prophet import Prophet
except ImportError:
    print("❌ ERROR: Prophet no está instalado")
    print("Instala con: pip install prophet")
    exit(1)

# Directorios
INPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'
OUTPUT_DIR_MODELS = 'models'
OUTPUT_DIR_RESULTS = 'results/prophet'

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


def preparar_datos_prophet(df, target_col='total_operaciones', include_regressors=True):
    """
    Prepara datos en formato Prophet (ds, y).

    Args:
        df: DataFrame original
        target_col: Columna target
        include_regressors: Si incluir regresores externos

    Returns:
        DataFrame en formato Prophet
    """
    print("\n" + "="*80)
    print("PREPARANDO DATOS PARA PROPHET")
    print("="*80)

    # Formato Prophet: 'ds' (date) y 'y' (target)
    df_prophet = pd.DataFrame({
        'ds': df['fecha'],
        'y': df[target_col]
    })

    # Agregar regresores externos (variables BCRA/INDEC)
    if include_regressors:
        regresores = []

        # Variables BCRA
        bcra_vars = [col for col in df.columns if any(x in col.lower() for x in
                     ['ipc', 'tipo de cambio', 'badlar', 'leliq', 'reservas', 'base monetaria'])]

        # Variables INDEC
        indec_vars = [col for col in df.columns if any(x in col.lower() for x in
                      ['emae', 'desocupacion', 'actividad', 'empleo', 'ripte', 'salarios'])]

        regresores.extend(bcra_vars[:5])  # Top 5 BCRA
        regresores.extend(indec_vars[:3])  # Top 3 INDEC

        for col in regresores:
            if col in df.columns:
                df_prophet[col] = df[col]

        print(f"\n✓ Regresores agregados ({len(regresores)}):")
        for reg in regresores:
            print(f"   - {reg}")

    # Remover NaN
    df_prophet = df_prophet.dropna()

    print(f"\n✓ Dataset preparado:")
    print(f"   - Registros: {len(df_prophet):,}")
    print(f"   - Columnas: {list(df_prophet.columns)}")

    return df_prophet, regresores if include_regressors else []


def split_temporal(df, train_pct=0.75, val_pct=0.125):
    """
    Split temporal de datos (NO aleatorio).

    Args:
        df: DataFrame con datos
        train_pct: % para train
        val_pct: % para validation

    Returns:
        train, validation, test DataFrames
    """
    print("\n" + "="*80)
    print("SPLIT TEMPORAL DE DATOS")
    print("="*80)

    n = len(df)
    train_size = int(n * train_pct)
    val_size = int(n * val_pct)

    train = df.iloc[:train_size].copy()
    val = df.iloc[train_size:train_size+val_size].copy()
    test = df.iloc[train_size+val_size:].copy()

    print(f"\n✓ Split completado:")
    print(f"   Train:      {len(train):3} registros ({train['ds'].min()} a {train['ds'].max()})")
    print(f"   Validation: {len(val):3} registros ({val['ds'].min()} a {val['ds'].max()})")
    print(f"   Test:       {len(test):3} registros ({test['ds'].min()} a {test['ds'].max()})")
    print(f"\n   Proporción: {train_pct*100:.1f}% / {val_pct*100:.1f}% / {(1-train_pct-val_pct)*100:.1f}%")

    return train, val, test


def entrenar_prophet(train, regresores=[], **kwargs):
    """
    Entrena modelo Prophet.

    Args:
        train: DataFrame de entrenamiento
        regresores: Lista de nombres de regresores
        **kwargs: Parámetros adicionales para Prophet

    Returns:
        Modelo Prophet entrenado
    """
    print("\n" + "="*80)
    print("ENTRENANDO MODELO PROPHET")
    print("="*80)

    # Configuración por defecto
    config = {
        'seasonality_mode': 'multiplicative',  # o 'additive'
        'yearly_seasonality': True,
        'weekly_seasonality': False,  # Datos mensuales
        'daily_seasonality': False,   # Datos mensuales
        'changepoint_prior_scale': 0.05,  # Flexibilidad de tendencia
    }

    config.update(kwargs)

    print(f"\n⚙️  Configuración:")
    for key, val in config.items():
        print(f"   - {key}: {val}")

    # Crear modelo
    model = Prophet(**config)

    # Agregar regresores
    for reg in regresores:
        if reg in train.columns:
            model.add_regressor(reg)
            print(f"   + Regresor agregado: {reg}")

    # Entrenar
    print(f"\n🔄 Entrenando modelo...")
    inicio = datetime.now()

    model.fit(train)

    tiempo = (datetime.now() - inicio).total_seconds()

    print(f"\n✓ Entrenamiento completado en {tiempo:.1f} segundos")

    return model


def predecir(model, test):
    """
    Genera predicciones con modelo Prophet.

    Args:
        model: Modelo Prophet entrenado
        test: DataFrame de test

    Returns:
        DataFrame con predicciones
    """
    print("\n" + "="*80)
    print("GENERANDO PREDICCIONES")
    print("="*80)

    # Predecir
    forecast = model.predict(test)

    print(f"\n✓ Predicciones generadas:")
    print(f"   - Registros: {len(forecast)}")
    print(f"   - Columnas: {list(forecast.columns[:5])}...")

    return forecast


def calcular_metricas(y_true, y_pred):
    """
    Calcula métricas de evaluación.

    Args:
        y_true: Valores reales
        y_pred: Valores predichos

    Returns:
        Dict con métricas
    """
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

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


def evaluar_modelo(model, train, val, test):
    """
    Evalúa modelo en train, validation y test.

    Args:
        model: Modelo Prophet
        train, val, test: DataFrames

    Returns:
        Dict con métricas por split
    """
    print("\n" + "="*80)
    print("EVALUANDO MODELO")
    print("="*80)

    resultados = {}

    for nombre, data in [('Train', train), ('Validation', val), ('Test', test)]:
        # Predecir
        forecast = model.predict(data)
        y_pred = forecast['yhat'].values
        y_true = data['y'].values

        # Calcular métricas
        metricas = calcular_metricas(y_true, y_pred)

        resultados[nombre] = metricas

        # Mostrar
        print(f"\n📊 {nombre}:")
        print(f"   RMSE:  {metricas['RMSE']:,.2f}")
        print(f"   MAE:   {metricas['MAE']:,.2f}")
        print(f"   MAPE:  {metricas['MAPE']:.2f}%")
        print(f"   R²:    {metricas['R2']:.4f}")

    return resultados


def guardar_modelo(model, filepath):
    """
    Guarda modelo Prophet.

    Args:
        model: Modelo Prophet
        filepath: Ruta del archivo
    """
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)

    size_mb = os.path.getsize(filepath) / 1024**2
    print(f"\n💾 Modelo guardado: {filepath} ({size_mb:.2f} MB)")


def guardar_resultados(forecast, test, metricas, output_dir):
    """
    Guarda predicciones y métricas.

    Args:
        forecast: Predicciones Prophet
        test: Datos de test
        metricas: Dict con métricas
        output_dir: Directorio de salida
    """
    print("\n" + "="*80)
    print("GUARDANDO RESULTADOS")
    print("="*80)

    # Predicciones
    pred_file = os.path.join(output_dir, 'predictions.parquet')
    df_pred = pd.DataFrame({
        'fecha': test['ds'].values,
        'real': test['y'].values,
        'prediccion': forecast['yhat'].values,
        'lower_bound': forecast['yhat_lower'].values,
        'upper_bound': forecast['yhat_upper'].values
    })
    df_pred.to_parquet(pred_file, index=False)
    print(f"   ✓ Predicciones: {pred_file}")

    # Métricas
    metrics_file = os.path.join(output_dir, 'metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(metricas, f, indent=2)
    print(f"   ✓ Métricas: {metrics_file}")

    # Componentes
    components_file = os.path.join(output_dir, 'components.parquet')
    forecast.to_parquet(components_file, index=False)
    print(f"   ✓ Componentes: {components_file}")


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FASE 4A: MODELO PROPHET PARA FORECASTING")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # 1. Cargar datos
        df = cargar_datos()
        if df is None:
            return

        # 2. Preparar datos
        df_prophet, regresores = preparar_datos_prophet(df, include_regressors=True)

        # 3. Split temporal
        train, val, test = split_temporal(df_prophet, train_pct=0.75, val_pct=0.125)

        # 4. Entrenar modelo
        model = entrenar_prophet(train, regresores=regresores)

        # 5. Evaluar
        metricas = evaluar_modelo(model, train, val, test)

        # 6. Predicciones finales en test
        forecast_test = predecir(model, test)

        # 7. Guardar modelo
        model_file = os.path.join(OUTPUT_DIR_MODELS, 'prophet_model.pkl')
        guardar_modelo(model, model_file)

        # 8. Guardar resultados
        guardar_resultados(forecast_test, test, metricas, OUTPUT_DIR_RESULTS)

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
