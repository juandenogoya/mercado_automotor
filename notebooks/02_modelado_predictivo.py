"""
MODELADO PREDICTIVO - DEMANDA AUTOMOTRIZ
========================================

Este script entrena y evalúa múltiples modelos de ML para predecir la demanda
mensual de vehículos considerando variables macro-económicas.

MODELOS IMPLEMENTADOS:
----------------------
1. Regresión Lineal (baseline)
2. Random Forest Regressor
3. XGBoost Regressor
4. LightGBM Regressor
5. KNN Regressor

MÉTRICAS DE EVALUACIÓN:
-----------------------
- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² Score
- MAPE (Mean Absolute Percentage Error)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Modelos
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neighbors import KNeighborsRegressor
import xgboost as xgb
import lightgbm as lgb

# Configuración
INPUT_DIR = Path("data/processed/ml")
OUTPUT_DIR = Path("data/models")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def log(message):
    """Logger simple."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def cargar_datos():
    """
    Carga el dataset preparado.

    Returns:
        pd.DataFrame: Dataset ML
    """
    log("=" * 80)
    log("📥 CARGANDO DATOS")
    log("=" * 80)

    # Usar dataset de muestra para desarrollo rápido
    # Cambiar a dataset_ml_completo.parquet para producción
    file_path = INPUT_DIR / "dataset_ml_sample.parquet"

    if not file_path.exists():
        log(f"❌ ERROR: No se encuentra {file_path}")
        log("💡 Ejecuta primero: python notebooks/01_preparacion_datos_ml.py")
        sys.exit(1)

    df = pd.read_parquet(file_path)
    log(f"\n✓ Dataset cargado: {len(df):,} registros, {len(df.columns)} columnas")
    log(f"  Periodo: {df['fecha_mes'].min()} → {df['fecha_mes'].max()}")
    log(f"  Marcas únicas: {df['marca'].nunique()}")
    log(f"  Modelos únicos: {df['modelo'].nunique()}")

    return df


def identificar_tipos_columnas(df):
    """
    Identifica y clasifica columnas por tipo.

    Args:
        df: DataFrame

    Returns:
        dict: Diccionario con listas de columnas por tipo
    """
    log("\n" + "=" * 80)
    log("🔍 IDENTIFICANDO TIPOS DE COLUMNAS")
    log("=" * 80)

    # Target
    target = 'cantidad_transacciones'

    # Columnas a excluir (no son features)
    excluir = ['fecha_mes', 'fecha', target]

    # Columnas numéricas
    numericas = df.select_dtypes(include=[np.number]).columns.tolist()
    numericas = [col for col in numericas if col not in excluir]

    # Columnas categóricas
    categoricas = df.select_dtypes(include=['object', 'category']).columns.tolist()
    categoricas = [col for col in categoricas if col not in excluir]

    # Identificar columnas con alta cardinalidad (usar Label Encoding)
    alta_cardinalidad = []
    baja_cardinalidad = []

    for col in categoricas:
        n_unique = df[col].nunique()
        if n_unique > 50:
            alta_cardinalidad.append(col)
        else:
            baja_cardinalidad.append(col)

    tipos = {
        'target': target,
        'numericas': numericas,
        'cat_alta_card': alta_cardinalidad,  # Label Encoding
        'cat_baja_card': baja_cardinalidad,  # One-Hot Encoding
        'excluir': excluir
    }

    log(f"\n📊 Clasificación de columnas:")
    log(f"  Target: {target}")
    log(f"  Numéricas: {len(numericas)}")
    log(f"  Categóricas (alta cardinalidad): {len(alta_cardinalidad)} → Label Encoding")
    log(f"  Categóricas (baja cardinalidad): {len(baja_cardinalidad)} → One-Hot Encoding")

    for col in alta_cardinalidad:
        log(f"    - {col}: {df[col].nunique()} valores únicos")

    return tipos


def preparar_features(df, tipos):
    """
    Prepara features aplicando encoding apropiado.

    Args:
        df: DataFrame original
        tipos: Dict con tipos de columnas

    Returns:
        tuple: (X_encoded, y, encoders, feature_names)
    """
    log("\n" + "=" * 80)
    log("⚙️ PREPARANDO FEATURES")
    log("=" * 80)

    df_work = df.copy()

    # Eliminar filas con NaN en target
    df_work = df_work.dropna(subset=[tipos['target']])
    log(f"\n✓ Dataset limpio: {len(df_work):,} registros")

    # Target
    y = df_work[tipos['target']].values
    log(f"\n📈 Target: {tipos['target']}")
    log(f"  Min: {y.min():.0f}, Max: {y.max():.0f}, Media: {y.mean():.1f}")

    # Inicializar encoders
    encoders = {}

    # 1. Label Encoding para alta cardinalidad
    log("\n🏷️ Aplicando Label Encoding...")
    for col in tipos['cat_alta_card']:
        le = LabelEncoder()
        # Manejar NaN
        df_work[col] = df_work[col].fillna('UNKNOWN')
        df_work[f'{col}_encoded'] = le.fit_transform(df_work[col])
        encoders[col] = le
        log(f"  ✓ {col}: {len(le.classes_)} clases")

    # 2. One-Hot Encoding para baja cardinalidad
    log("\n🎯 Aplicando One-Hot Encoding...")
    if len(tipos['cat_baja_card']) > 0:
        df_work = pd.get_dummies(
            df_work,
            columns=tipos['cat_baja_card'],
            prefix=tipos['cat_baja_card'],
            drop_first=True  # Evitar multicolinealidad
        )
        log(f"  ✓ {len(tipos['cat_baja_card'])} columnas transformadas")

    # 3. Seleccionar features finales
    log("\n📋 Seleccionando features...")

    # Features numéricas originales
    features_numericas = tipos['numericas'].copy()

    # Features de label encoding
    features_encoded = [f'{col}_encoded' for col in tipos['cat_alta_card']]

    # Features de one-hot encoding
    features_ohe = [col for col in df_work.columns if any(prefix in col for prefix in tipos['cat_baja_card']) and col.endswith('_')]

    # Combinar todas las features
    feature_names = features_numericas + features_encoded + features_ohe

    # Filtrar solo las que existen en el dataframe
    feature_names = [f for f in feature_names if f in df_work.columns]

    # Crear X
    X = df_work[feature_names].copy()

    # Manejar NaN en features numéricas (imputar con mediana)
    log("\n🧹 Limpiando NaN en features...")
    for col in X.columns:
        if X[col].isnull().sum() > 0:
            if X[col].dtype in [np.float64, np.int64]:
                median_val = X[col].median()
                X[col].fillna(median_val, inplace=True)
                log(f"  ✓ {col}: {X[col].isnull().sum()} NaN → imputado con mediana ({median_val:.2f})")

    log(f"\n✅ Features preparados:")
    log(f"  Total features: {len(feature_names)}")
    log(f"  - Numéricas: {len(features_numericas)}")
    log(f"  - Label Encoded: {len(features_encoded)}")
    log(f"  - One-Hot Encoded: {len(features_ohe)}")
    log(f"  Shape final: {X.shape}")

    return X.values, y, encoders, feature_names


def crear_modelos():
    """
    Define modelos a entrenar.

    Returns:
        dict: Diccionario con modelos
    """
    log("\n" + "=" * 80)
    log("🤖 DEFINIENDO MODELOS")
    log("=" * 80)

    modelos = {
        'Regresion_Lineal': {
            'modelo': LinearRegression(),
            'params': {}
        },
        'Ridge': {
            'modelo': Ridge(),
            'params': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        },
        'Lasso': {
            'modelo': Lasso(),
            'params': {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        },
        'Random_Forest': {
            'modelo': RandomForestRegressor(random_state=42, n_jobs=-1),
            'params': {
                'n_estimators': [100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5],
                'min_samples_leaf': [1, 2]
            }
        },
        'XGBoost': {
            'modelo': xgb.XGBRegressor(random_state=42, n_jobs=-1),
            'params': {
                'n_estimators': [100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'subsample': [0.8, 1.0]
            }
        },
        'LightGBM': {
            'modelo': lgb.LGBMRegressor(random_state=42, n_jobs=-1, verbose=-1),
            'params': {
                'n_estimators': [100, 200],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.3],
                'num_leaves': [31, 50]
            }
        },
        'KNN': {
            'modelo': KNeighborsRegressor(n_jobs=-1),
            'params': {
                'n_neighbors': [3, 5, 7, 10],
                'weights': ['uniform', 'distance'],
                'metric': ['euclidean', 'manhattan']
            }
        }
    }

    log(f"\n✓ {len(modelos)} modelos definidos:")
    for nombre in modelos.keys():
        log(f"  - {nombre}")

    return modelos


def calcular_metricas(y_true, y_pred):
    """
    Calcula múltiples métricas de evaluación.

    Args:
        y_true: Valores reales
        y_pred: Valores predichos

    Returns:
        dict: Métricas calculadas
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)

    # MAPE (evitar división por cero)
    mape = np.mean(np.abs((y_true - y_pred) / np.where(y_true == 0, 1, y_true))) * 100

    return {
        'MAE': mae,
        'RMSE': rmse,
        'R2': r2,
        'MAPE': mape
    }


def entrenar_y_evaluar(X_train, X_test, y_train, y_test, modelos, usar_grid_search=True):
    """
    Entrena y evalúa todos los modelos.

    Args:
        X_train, X_test, y_train, y_test: Datos de entrenamiento y prueba
        modelos: Diccionario de modelos
        usar_grid_search: Si usar GridSearchCV para optimización

    Returns:
        dict: Resultados de todos los modelos
    """
    log("\n" + "=" * 80)
    log("🎯 ENTRENAMIENTO Y EVALUACIÓN")
    log("=" * 80)

    resultados = []
    modelos_entrenados = {}

    for nombre, config in modelos.items():
        log(f"\n{'='*80}")
        log(f"📊 {nombre}")
        log(f"{'='*80}")

        modelo = config['modelo']
        params = config['params']

        inicio = datetime.now()

        # Entrenar con o sin GridSearch
        if usar_grid_search and len(params) > 0:
            log(f"\n🔍 Optimizando hiperparámetros con GridSearchCV...")
            log(f"  Combinaciones a probar: {np.prod([len(v) for v in params.values()])}")

            grid = GridSearchCV(
                modelo,
                params,
                cv=3,
                scoring='neg_mean_absolute_error',
                n_jobs=-1,
                verbose=0
            )
            grid.fit(X_train, y_train)

            mejor_modelo = grid.best_estimator_
            log(f"  ✓ Mejores parámetros: {grid.best_params_}")
        else:
            log(f"\n⚡ Entrenando con parámetros por defecto...")
            mejor_modelo = modelo
            mejor_modelo.fit(X_train, y_train)

        duracion = (datetime.now() - inicio).total_seconds()

        # Predicciones
        log(f"\n📈 Evaluando modelo...")
        y_train_pred = mejor_modelo.predict(X_train)
        y_test_pred = mejor_modelo.predict(X_test)

        # Métricas
        metricas_train = calcular_metricas(y_train, y_train_pred)
        metricas_test = calcular_metricas(y_test, y_test_pred)

        log(f"\n  📊 Resultados:")
        log(f"  {'Métrica':<10} {'Train':<15} {'Test':<15}")
        log(f"  {'-'*40}")
        log(f"  {'MAE':<10} {metricas_train['MAE']:<15.2f} {metricas_test['MAE']:<15.2f}")
        log(f"  {'RMSE':<10} {metricas_train['RMSE']:<15.2f} {metricas_test['RMSE']:<15.2f}")
        log(f"  {'R²':<10} {metricas_train['R2']:<15.4f} {metricas_test['R2']:<15.4f}")
        log(f"  {'MAPE':<10} {metricas_train['MAPE']:<15.2f}% {metricas_test['MAPE']:<15.2f}%")
        log(f"\n  ⏱️ Tiempo de entrenamiento: {duracion:.2f}s")

        # Guardar resultados
        resultados.append({
            'modelo': nombre,
            'mae_train': metricas_train['MAE'],
            'mae_test': metricas_test['MAE'],
            'rmse_train': metricas_train['RMSE'],
            'rmse_test': metricas_test['RMSE'],
            'r2_train': metricas_train['R2'],
            'r2_test': metricas_test['R2'],
            'mape_train': metricas_train['MAPE'],
            'mape_test': metricas_test['MAPE'],
            'tiempo_entrenamiento': duracion
        })

        modelos_entrenados[nombre] = mejor_modelo

    return resultados, modelos_entrenados


def comparar_modelos(resultados):
    """
    Compara y rankea modelos.

    Args:
        resultados: Lista de resultados de modelos

    Returns:
        pd.DataFrame: Comparación de modelos
    """
    log("\n" + "=" * 80)
    log("🏆 COMPARACIÓN DE MODELOS")
    log("=" * 80)

    df_resultados = pd.DataFrame(resultados)

    # Ordenar por R² Test (descendente)
    df_resultados = df_resultados.sort_values('r2_test', ascending=False).reset_index(drop=True)
    df_resultados['rank'] = range(1, len(df_resultados) + 1)

    # Mostrar tabla
    log("\n" + "=" * 120)
    log(f"{'Rank':<6} {'Modelo':<20} {'MAE Test':<12} {'RMSE Test':<12} {'R² Test':<12} {'MAPE Test':<12} {'Tiempo (s)':<12}")
    log("=" * 120)

    for _, row in df_resultados.iterrows():
        log(f"{row['rank']:<6} {row['modelo']:<20} {row['mae_test']:<12.2f} {row['rmse_test']:<12.2f} {row['r2_test']:<12.4f} {row['mape_test']:<12.2f}% {row['tiempo_entrenamiento']:<12.2f}")

    log("=" * 120)

    # Mejor modelo
    mejor = df_resultados.iloc[0]
    log(f"\n🥇 MEJOR MODELO: {mejor['modelo']}")
    log(f"   R² Test: {mejor['r2_test']:.4f}")
    log(f"   MAE Test: {mejor['mae_test']:.2f}")
    log(f"   RMSE Test: {mejor['rmse_test']:.2f}")
    log(f"   MAPE Test: {mejor['mape_test']:.2f}%")

    return df_resultados


def guardar_resultados(df_resultados, modelos_entrenados, encoders, feature_names):
    """
    Guarda modelos y resultados.

    Args:
        df_resultados: DataFrame con resultados
        modelos_entrenados: Modelos entrenados
        encoders: Encoders de variables categóricas
        feature_names: Nombres de features
    """
    log("\n" + "=" * 80)
    log("💾 GUARDANDO RESULTADOS")
    log("=" * 80)

    # 1. Guardar resultados CSV
    file_resultados = RESULTS_DIR / f"comparacion_modelos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_resultados.to_csv(file_resultados, index=False)
    log(f"\n✓ Resultados guardados: {file_resultados}")

    # 2. Guardar mejor modelo
    mejor_nombre = df_resultados.iloc[0]['modelo']
    mejor_modelo = modelos_entrenados[mejor_nombre]

    file_modelo = OUTPUT_DIR / f"mejor_modelo_{mejor_nombre}.pkl"
    with open(file_modelo, 'wb') as f:
        pickle.dump(mejor_modelo, f)
    log(f"✓ Mejor modelo guardado: {file_modelo}")

    # 3. Guardar todos los modelos
    file_todos = OUTPUT_DIR / f"todos_modelos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
    with open(file_todos, 'wb') as f:
        pickle.dump(modelos_entrenados, f)
    log(f"✓ Todos los modelos guardados: {file_todos}")

    # 4. Guardar encoders
    file_encoders = OUTPUT_DIR / "encoders.pkl"
    with open(file_encoders, 'wb') as f:
        pickle.dump(encoders, f)
    log(f"✓ Encoders guardados: {file_encoders}")

    # 5. Guardar feature names
    file_features = OUTPUT_DIR / "feature_names.pkl"
    with open(file_features, 'wb') as f:
        pickle.dump(feature_names, f)
    log(f"✓ Feature names guardados: {file_features}")

    # 6. Feature importance (si es Random Forest o similar)
    if hasattr(mejor_modelo, 'feature_importances_'):
        log(f"\n📊 Feature Importance (Top 20):")
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': mejor_modelo.feature_importances_
        }).sort_values('importance', ascending=False).head(20)

        for idx, row in importance_df.iterrows():
            log(f"  {row['feature']:<40} {row['importance']:.6f}")

        file_importance = RESULTS_DIR / f"feature_importance_{mejor_nombre}.csv"
        importance_df.to_csv(file_importance, index=False)
        log(f"\n✓ Feature importance guardado: {file_importance}")


def main():
    """Pipeline completo de modelado."""
    log("=" * 80)
    log("🚀 PIPELINE DE MODELADO PREDICTIVO")
    log("=" * 80)
    log(f"\nInicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Cargar datos
    df = cargar_datos()

    # 2. Identificar tipos de columnas
    tipos = identificar_tipos_columnas(df)

    # 3. Preparar features
    X, y, encoders, feature_names = preparar_features(df, tipos)

    # 4. Split train/test
    log("\n" + "=" * 80)
    log("✂️ SPLIT TRAIN/TEST")
    log("=" * 80)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    log(f"\n✓ Split completado:")
    log(f"  Train: {len(X_train):,} registros ({len(X_train)/len(X)*100:.1f}%)")
    log(f"  Test:  {len(X_test):,} registros ({len(X_test)/len(X)*100:.1f}%)")

    # 5. Crear modelos
    modelos = crear_modelos()

    # 6. Entrenar y evaluar
    resultados, modelos_entrenados = entrenar_y_evaluar(
        X_train, X_test, y_train, y_test, modelos, usar_grid_search=True
    )

    # 7. Comparar modelos
    df_resultados = comparar_modelos(resultados)

    # 8. Guardar resultados
    guardar_resultados(df_resultados, modelos_entrenados, encoders, feature_names)

    # Resumen final
    log("\n" + "=" * 80)
    log("✅ MODELADO COMPLETADO")
    log("=" * 80)
    log(f"\nModelos entrenados: {len(modelos)}")
    log(f"Features utilizados: {len(feature_names)}")
    log(f"Mejor modelo: {df_resultados.iloc[0]['modelo']}")
    log(f"R² Test: {df_resultados.iloc[0]['r2_test']:.4f}")
    log(f"\nArchivos generados en:")
    log(f"  - Modelos: {OUTPUT_DIR}")
    log(f"  - Resultados: {RESULTS_DIR}")
    log("=" * 80)


if __name__ == "__main__":
    main()
