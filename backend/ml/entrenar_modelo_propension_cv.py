#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Entrenamiento con Cross-Validation - Modelo de Propensión a Compra

Este script implementa validación cruzada robusta:
- Stratified K-Fold Cross-Validation (5 folds)
- Comparación de múltiples modelos
- Métricas con media ± desviación estándar
- GridSearchCV opcional para optimización de hiperparámetros
- Análisis estadístico de comparación entre modelos

Uso:
    # Básico con cross-validation
    python backend/ml/entrenar_modelo_propension_cv.py --input data/ml/

    # Con optimización de hiperparámetros
    python backend/ml/entrenar_modelo_propension_cv.py --input data/ml/ --grid-search
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import pickle
import json
from datetime import datetime
import time

# ML libraries
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate, GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    make_scorer, top_k_accuracy_score
)
import warnings
warnings.filterwarnings('ignore')

# Intentar importar XGBoost (opcional)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


def cargar_datasets(input_dir):
    """
    Carga los datasets preparados
    """
    print("\n" + "="*60)
    print("📥 CARGANDO DATASETS")
    print("="*60)

    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {input_path}")

    # Cargar arrays
    X_train = np.load(input_path / 'X_train.npy')
    X_test = np.load(input_path / 'X_test.npy')
    y_train = np.load(input_path / 'y_train.npy')
    y_test = np.load(input_path / 'y_test.npy')

    # Cargar encoders y feature names
    with open(input_path / 'encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)

    with open(input_path / 'feature_names.pkl', 'rb') as f:
        feature_names = pickle.load(f)

    # Cargar metadata
    with open(input_path / 'metadata.json', 'r') as f:
        metadata = json.load(f)

    print(f"✅ Datasets cargados:")
    print(f"   - X_train: {X_train.shape}")
    print(f"   - X_test: {X_test.shape}")
    print(f"   - Features: {len(feature_names)}")
    print(f"   - Clases: {metadata['n_clases']}")

    return X_train, X_test, y_train, y_test, encoders, feature_names, metadata


def crear_scoring_dict(encoders):
    """
    Crea diccionario de scorers para cross-validation

    NOTA: No pasamos 'labels' a top_k_accuracy_score porque cada fold
    puede tener diferentes clases presentes. Sklearn lo maneja automáticamente.
    """
    scoring = {
        'accuracy': 'accuracy',
        'precision_weighted': make_scorer(precision_score, average='weighted', zero_division=0),
        'recall_weighted': make_scorer(recall_score, average='weighted', zero_division=0),
        'f1_weighted': make_scorer(f1_score, average='weighted', zero_division=0),
        'top3_accuracy': make_scorer(top_k_accuracy_score, k=3, needs_proba=True),
        'top5_accuracy': make_scorer(top_k_accuracy_score, k=5, needs_proba=True)
    }

    return scoring


def cross_validate_model(model, X, y, model_name, cv, scoring):
    """
    Realiza cross-validation de un modelo

    Args:
        model: Modelo de sklearn
        X: Features
        y: Target
        model_name: Nombre del modelo
        cv: Cross-validator (StratifiedKFold)
        scoring: Dict de scorers

    Returns:
        Dict con resultados de CV
    """
    print(f"\n🔄 Cross-validating {model_name}...")
    print(f"   Folds: {cv.get_n_splits()}")

    inicio = time.time()

    # Realizar cross-validation
    cv_results = cross_validate(
        model, X, y,
        cv=cv,
        scoring=scoring,
        return_train_score=True,
        n_jobs=-1,
        verbose=0
    )

    duracion = time.time() - inicio

    # Calcular estadísticas
    resultados = {
        'tiempo_total': duracion,
        'tiempo_promedio_fold': duracion / cv.get_n_splits(),
        'metricas': {}
    }

    for metric_name in scoring.keys():
        test_scores = cv_results[f'test_{metric_name}']
        train_scores = cv_results[f'train_{metric_name}']

        resultados['metricas'][metric_name] = {
            'test_mean': test_scores.mean(),
            'test_std': test_scores.std(),
            'train_mean': train_scores.mean(),
            'train_std': train_scores.std(),
            'test_scores': test_scores.tolist(),
            'train_scores': train_scores.tolist()
        }

    # Mostrar resultados
    print(f"\n   ✅ Completado en {duracion:.2f}s")
    print(f"\n   📊 Resultados ({cv.get_n_splits()}-Fold CV):")
    print(f"   {'Métrica':<20} {'Test Mean':<12} {'Test Std':<12} {'Train Mean':<12}")
    print(f"   {'-'*60}")

    for metric_name, valores in resultados['metricas'].items():
        metric_display = metric_name.replace('_', ' ').title()
        print(f"   {metric_display:<20} {valores['test_mean']:>10.4f}  "
              f"{valores['test_std']:>10.4f}  {valores['train_mean']:>10.4f}")

    return resultados


def entrenar_modelo_final(model, X_train, y_train, X_test, y_test, encoders):
    """
    Entrena el modelo final con todos los datos de train y evalúa en test
    """
    print(f"\n   🎯 Entrenando modelo final con todos los datos de train...")

    inicio = time.time()
    model.fit(X_train, y_train)
    duracion = time.time() - inicio

    # Evaluar en test set
    y_pred = model.predict(X_test)
    y_pred_proba_raw = model.predict_proba(X_test)

    # El modelo solo predice para las clases que vio en entrenamiento (ej. 96 de 100)
    # Necesitamos expandir y_pred_proba para incluir TODAS las clases posibles
    # Pondremos probabilidad 0 para las clases que el modelo nunca vio

    n_samples = X_test.shape[0]
    n_all_classes = len(encoders['target'].classes_)

    # Crear array de probabilidades con todas las clases (inicializado en 0)
    y_pred_proba_full = np.zeros((n_samples, n_all_classes))

    # Llenar las probabilidades para las clases que el modelo conoce
    for i, class_label in enumerate(model.classes_):
        y_pred_proba_full[:, class_label] = y_pred_proba_raw[:, i]

    # Ahora podemos usar todas las clases del encoder
    all_labels = np.arange(n_all_classes)

    metricas_test = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
        'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
        'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0),
        'top3_accuracy': top_k_accuracy_score(y_test, y_pred_proba_full, k=3, labels=all_labels),
        'top5_accuracy': top_k_accuracy_score(y_test, y_pred_proba_full, k=5, labels=all_labels)
    }

    print(f"   ✅ Modelo entrenado en {duracion:.2f}s")
    print(f"\n   📊 Rendimiento en Test Set (holdout):")
    print(f"   {'Métrica':<20} {'Valor':<12}")
    print(f"   {'-'*35}")
    for metric_name, valor in metricas_test.items():
        metric_display = metric_name.replace('_', ' ').title()
        print(f"   {metric_display:<20} {valor:>10.4f}")

    return model, metricas_test, duracion


def grid_search_optimization(X, y, model_type, cv, scoring_primary='f1_weighted'):
    """
    Optimiza hiperparámetros usando GridSearchCV

    Args:
        X: Features
        y: Target
        model_type: 'rf' o 'xgb'
        cv: Cross-validator
        scoring_primary: Métrica principal para optimización

    Returns:
        Mejor modelo y parámetros
    """
    print(f"\n🔍 Optimizando hiperparámetros con GridSearchCV...")
    print(f"   Métrica de optimización: {scoring_primary}")

    if model_type == 'rf':
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [10, 20, 30],
            'min_samples_split': [2, 5],
            'min_samples_leaf': [1, 2]
        }
        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)

    elif model_type == 'xgb':
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.1, 0.3],
            'subsample': [0.8, 1.0]
        }
        base_model = xgb.XGBClassifier(
            random_state=42,
            n_jobs=-1,
            objective='multi:softprob'
        )

    print(f"   Explorando {len(param_grid)} hiperparámetros...")
    total_combinaciones = np.prod([len(v) for v in param_grid.values()])
    print(f"   Combinaciones totales: {total_combinaciones}")
    print(f"   Evaluaciones totales: {total_combinaciones * cv.get_n_splits()}")

    inicio = time.time()

    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=cv,
        scoring=scoring_primary,
        n_jobs=-1,
        verbose=1,
        return_train_score=True
    )

    grid_search.fit(X, y)

    duracion = time.time() - inicio

    print(f"\n   ✅ Grid Search completado en {duracion:.2f}s ({duracion/60:.1f} min)")
    print(f"\n   🏆 Mejores parámetros:")
    for param, valor in grid_search.best_params_.items():
        print(f"      {param}: {valor}")
    print(f"\n   📊 Mejor score (CV): {grid_search.best_score_:.4f}")

    # Top 5 configuraciones
    results_df = pd.DataFrame(grid_search.cv_results_)
    top5 = results_df.nlargest(5, 'mean_test_score')[
        ['params', 'mean_test_score', 'std_test_score', 'mean_fit_time']
    ]

    print(f"\n   📋 Top 5 Configuraciones:")
    for idx, row in top5.iterrows():
        print(f"      {idx+1}. Score: {row['mean_test_score']:.4f} (±{row['std_test_score']:.4f}) "
              f"- {row['params']}")

    return grid_search.best_estimator_, grid_search.best_params_, grid_search


def comparar_modelos(resultados_cv):
    """
    Compara resultados de cross-validation entre modelos
    """
    print("\n" + "="*60)
    print("📊 COMPARACIÓN ENTRE MODELOS")
    print("="*60)

    # Crear tabla comparativa
    comparacion = []

    for model_name, resultados in resultados_cv.items():
        fila = {'Modelo': model_name}
        for metric_name, valores in resultados['metricas'].items():
            fila[f"{metric_name}_mean"] = valores['test_mean']
            fila[f"{metric_name}_std"] = valores['test_std']
        comparacion.append(fila)

    df_comp = pd.DataFrame(comparacion)

    print("\n📋 Test Set Performance (Cross-Validation):")
    print("="*80)

    metricas_principales = ['accuracy', 'f1_weighted', 'top3_accuracy', 'top5_accuracy']

    for metric in metricas_principales:
        if f"{metric}_mean" in df_comp.columns:
            print(f"\n{metric.replace('_', ' ').title()}:")
            for _, row in df_comp.iterrows():
                mean_val = row[f"{metric}_mean"]
                std_val = row[f"{metric}_std"]
                print(f"  {row['Modelo']:<20} {mean_val:.4f} ± {std_val:.4f}")

    # Determinar mejor modelo
    print("\n" + "="*60)
    print("🏆 MEJOR MODELO")
    print("="*60)

    mejor_idx = df_comp['f1_weighted_mean'].idxmax()
    mejor_modelo = df_comp.loc[mejor_idx, 'Modelo']
    mejor_f1 = df_comp.loc[mejor_idx, 'f1_weighted_mean']
    mejor_f1_std = df_comp.loc[mejor_idx, 'f1_weighted_std']

    print(f"\n🥇 {mejor_modelo}")
    print(f"   F1-Score: {mejor_f1:.4f} ± {mejor_f1_std:.4f}")
    print(f"   Accuracy: {df_comp.loc[mejor_idx, 'accuracy_mean']:.4f} ± {df_comp.loc[mejor_idx, 'accuracy_std']:.4f}")
    print(f"   Top-3 Acc: {df_comp.loc[mejor_idx, 'top3_accuracy_mean']:.4f} ± {df_comp.loc[mejor_idx, 'top3_accuracy_std']:.4f}")
    print(f"   Top-5 Acc: {df_comp.loc[mejor_idx, 'top5_accuracy_mean']:.4f} ± {df_comp.loc[mejor_idx, 'top5_accuracy_std']:.4f}")

    return df_comp, mejor_modelo


def guardar_resultados(modelo_final, encoders, feature_names, resultados_cv,
                      metricas_test, df_comparacion, output_dir):
    """
    Guarda modelo y resultados
    """
    print("\n" + "="*60)
    print("💾 GUARDANDO RESULTADOS")
    print("="*60)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Guardar modelo
    with open(output_path / 'modelo_propension_compra_cv.pkl', 'wb') as f:
        pickle.dump(modelo_final, f)
    print(f"✅ Modelo guardado: modelo_propension_compra_cv.pkl")

    # Guardar encoders
    with open(output_path / 'encoders.pkl', 'wb') as f:
        pickle.dump(encoders, f)
    print(f"✅ Encoders guardados: encoders.pkl")

    # Guardar feature names
    with open(output_path / 'feature_names.pkl', 'wb') as f:
        pickle.dump(feature_names, f)
    print(f"✅ Feature names guardados: feature_names.pkl")

    # Guardar resultados de CV
    cv_results_path = output_path / 'cv_results.json'
    with open(cv_results_path, 'w') as f:
        json.dump(resultados_cv, f, indent=2)
    print(f"✅ Resultados CV guardados: cv_results.json")

    # Guardar comparación
    df_comparacion.to_csv(output_path / 'model_comparison.csv', index=False)
    print(f"✅ Comparación guardada: model_comparison.csv")

    # Guardar metadata
    metadata = {
        'fecha_entrenamiento': datetime.now().isoformat(),
        'metricas_test_holdout': metricas_test,
        'n_features': len(feature_names),
        'feature_names': feature_names,
        'n_clases': len(encoders['target'].classes_),
        'clases': encoders['target'].classes_.tolist()
    }

    with open(output_path / 'modelo_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata guardada: modelo_metadata.json")

    # Feature importance (si disponible)
    if hasattr(modelo_final, 'feature_importances_'):
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': modelo_final.feature_importances_
        }).sort_values('importance', ascending=False)

        importance_df.to_csv(output_path / 'feature_importance.csv', index=False)
        print(f"✅ Feature importance guardada: feature_importance.csv")

        print(f"\n📊 Top 10 Features más importantes:")
        for idx, row in importance_df.head(10).iterrows():
            print(f"   {idx+1:2d}. {row['feature']:<30} {row['importance']:.4f}")

    print(f"\n📁 Todos los archivos guardados en: {output_path}")

    return output_path


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Entrenamiento con Cross-Validation - Modelo de Propensión'
    )

    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Directorio con datos preparados'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/models/propension_compra_cv',
        help='Directorio de salida para modelos'
    )

    parser.add_argument(
        '--cv-folds',
        type=int,
        default=5,
        help='Número de folds para cross-validation (default: 5)'
    )

    parser.add_argument(
        '--grid-search',
        action='store_true',
        help='Usar GridSearchCV para optimizar hiperparámetros (más lento)'
    )

    parser.add_argument(
        '--only-rf',
        action='store_true',
        help='Entrenar solo Random Forest'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🤖 ENTRENAMIENTO CON CROSS-VALIDATION")
    print("="*60)
    print(f"Configuración:")
    print(f"  - Input: {args.input}")
    print(f"  - Output: {args.output}")
    print(f"  - CV Folds: {args.cv_folds}")
    print(f"  - Grid Search: {'Sí' if args.grid_search else 'No'}")
    print(f"  - Only RF: {'Sí' if args.only_rf else 'No'}")

    # 1. Cargar datasets
    X_train, X_test, y_train, y_test, encoders, feature_names, metadata = cargar_datasets(args.input)

    # 2. Configurar cross-validation
    cv = StratifiedKFold(n_splits=args.cv_folds, shuffle=True, random_state=42)
    scoring = crear_scoring_dict(encoders)

    print(f"\n✅ Cross-Validation configurado:")
    print(f"   - Tipo: Stratified K-Fold")
    print(f"   - Folds: {args.cv_folds}")
    print(f"   - Métricas: {len(scoring)}")

    # 3. Entrenar y evaluar modelos
    resultados_cv = {}
    modelos_finales = {}

    # Random Forest
    print("\n" + "="*60)
    print("🌳 RANDOM FOREST")
    print("="*60)

    if args.grid_search:
        rf_model, rf_params, rf_grid = grid_search_optimization(
            X_train, y_train, 'rf', cv
        )
    else:
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            random_state=42,
            n_jobs=-1
        )
        # Cross-validation
        resultados_cv['Random Forest'] = cross_validate_model(
            rf_model, X_train, y_train, 'Random Forest', cv, scoring
        )

    # Entrenar modelo final
    rf_final, rf_metricas_test, rf_tiempo = entrenar_modelo_final(
        rf_model, X_train, y_train, X_test, y_test, encoders
    )
    modelos_finales['Random Forest'] = {
        'modelo': rf_final,
        'metricas_test': rf_metricas_test,
        'tiempo': rf_tiempo
    }

    # XGBoost (si está disponible y no es only-rf)
    if XGBOOST_AVAILABLE and not args.only_rf:
        print("\n" + "="*60)
        print("🚀 XGBOOST")
        print("="*60)

        if args.grid_search:
            xgb_model, xgb_params, xgb_grid = grid_search_optimization(
                X_train, y_train, 'xgb', cv
            )
        else:
            xgb_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=7,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
                objective='multi:softprob'
            )
            resultados_cv['XGBoost'] = cross_validate_model(
                xgb_model, X_train, y_train, 'XGBoost', cv, scoring
            )

        xgb_final, xgb_metricas_test, xgb_tiempo = entrenar_modelo_final(
            xgb_model, X_train, y_train, X_test, y_test, encoders
        )
        modelos_finales['XGBoost'] = {
            'modelo': xgb_final,
            'metricas_test': xgb_metricas_test,
            'tiempo': xgb_tiempo
        }

    # 4. Comparar modelos
    df_comparacion, mejor_modelo_nombre = comparar_modelos(resultados_cv)

    # 5. Guardar mejor modelo
    mejor_modelo = modelos_finales[mejor_modelo_nombre]['modelo']
    mejor_metricas = modelos_finales[mejor_modelo_nombre]['metricas_test']

    output_path = guardar_resultados(
        mejor_modelo, encoders, feature_names,
        resultados_cv, mejor_metricas, df_comparacion,
        args.output
    )

    print("\n" + "="*60)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("="*60)
    print(f"\n🏆 Mejor modelo: {mejor_modelo_nombre}")
    print(f"📁 Guardado en: {output_path}")
    print(f"\n🚀 Para usar el modelo:")
    print(f"   python backend/ml/predecir_propension.py --modelo {output_path}/modelo_propension_compra_cv.pkl")


if __name__ == "__main__":
    main()
