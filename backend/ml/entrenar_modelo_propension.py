#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Entrenamiento de Modelo de Propensión a Compra

Este script:
- Carga los datasets preparados
- Entrena múltiples modelos (RandomForest, XGBoost, LightGBM)
- Evalúa y compara modelos
- Guarda el mejor modelo
- Genera reportes de performance

Uso:
    python backend/ml/entrenar_modelo_propension.py --input data/ml/propension_compra/
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
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, top_k_accuracy_score
)
import warnings
warnings.filterwarnings('ignore')

# Intentar importar XGBoost y LightGBM (opcionales)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️ XGBoost no disponible. Instalar con: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("⚠️ LightGBM no disponible. Instalar con: pip install lightgbm")


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


def entrenar_random_forest(X_train, y_train, n_estimators=100, max_depth=20, random_state=42):
    """
    Entrena un Random Forest
    """
    print("\n🌳 Entrenando Random Forest...")

    inicio = time.time()

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=0,
        class_weight='balanced'
    )

    model.fit(X_train, y_train)

    duracion = time.time() - inicio

    print(f"✅ Random Forest entrenado en {duracion:.2f}s")

    return model, duracion


def entrenar_xgboost(X_train, y_train, n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42):
    """
    Entrena un XGBoost
    """
    if not XGBOOST_AVAILABLE:
        print("❌ XGBoost no disponible")
        return None, 0

    print("\n🚀 Entrenando XGBoost...")

    inicio = time.time()

    model = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=random_state,
        n_jobs=-1,
        verbosity=0,
        objective='multi:softprob'
    )

    model.fit(X_train, y_train)

    duracion = time.time() - inicio

    print(f"✅ XGBoost entrenado en {duracion:.2f}s")

    return model, duracion


def entrenar_lightgbm(X_train, y_train, n_estimators=100, max_depth=20, learning_rate=0.1, random_state=42):
    """
    Entrena un LightGBM
    """
    if not LIGHTGBM_AVAILABLE:
        print("❌ LightGBM no disponible")
        return None, 0

    print("\n⚡ Entrenando LightGBM...")

    inicio = time.time()

    model = lgb.LGBMClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        random_state=random_state,
        n_jobs=-1,
        verbosity=-1,
        objective='multiclass'
    )

    model.fit(X_train, y_train)

    duracion = time.time() - inicio

    print(f"✅ LightGBM entrenado en {duracion:.2f}s")

    return model, duracion


def evaluar_modelo(model, X_test, y_test, model_name, encoders):
    """
    Evalúa un modelo y retorna métricas
    """
    print(f"\n📊 Evaluando {model_name}...")

    if model is None:
        return None

    # Predicciones
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)

    # Métricas
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    # Top-K accuracy (para propensión es útil)
    # Obtener todas las clases posibles del encoder
    all_labels = np.arange(len(encoders['target'].classes_))
    top3_acc = top_k_accuracy_score(y_test, y_pred_proba, k=3, labels=all_labels)
    top5_acc = top_k_accuracy_score(y_test, y_pred_proba, k=5, labels=all_labels)

    metricas = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'top3_accuracy': top3_acc,
        'top5_accuracy': top5_acc
    }

    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")
    print(f"   F1-Score: {f1:.4f}")
    print(f"   Top-3 Accuracy: {top3_acc:.4f}")
    print(f"   Top-5 Accuracy: {top5_acc:.4f}")

    return metricas, y_pred, y_pred_proba


def seleccionar_mejor_modelo(resultados):
    """
    Selecciona el mejor modelo basado en F1-Score
    """
    print("\n" + "="*60)
    print("🏆 SELECCIONANDO MEJOR MODELO")
    print("="*60)

    mejor_modelo = None
    mejor_f1 = 0
    mejor_nombre = None

    for nombre, data in resultados.items():
        if data['metricas'] is None:
            continue

        f1 = data['metricas']['f1_score']
        print(f"  {nombre}: F1={f1:.4f}")

        if f1 > mejor_f1:
            mejor_f1 = f1
            mejor_modelo = data['modelo']
            mejor_nombre = nombre

    print(f"\n✅ Mejor modelo: {mejor_nombre} (F1={mejor_f1:.4f})")

    return mejor_nombre, mejor_modelo, mejor_f1


def calcular_feature_importance(model, feature_names, modelo_tipo, top_n=20):
    """
    Calcula feature importance según el tipo de modelo
    """
    print(f"\n📊 Feature Importance ({modelo_tipo})...")

    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
    else:
        print("   Modelo no soporta feature importance")
        return None

    # Crear DataFrame
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)

    print(f"\n   Top {top_n} Features:")
    for i, row in importance_df.head(top_n).iterrows():
        print(f"   {i+1:2d}. {row['feature']:30s} {row['importance']:.4f}")

    return importance_df


def guardar_modelo(model, modelo_nombre, metricas, feature_names, encoders, feature_importance, output_dir):
    """
    Guarda el modelo entrenado y sus metadatos
    """
    print("\n" + "="*60)
    print("💾 GUARDANDO MODELO")
    print("="*60)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Guardar modelo
    model_file = output_path / 'modelo_propension_compra.pkl'
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)

    print(f"✅ Modelo guardado: {model_file}")

    # Guardar encoders (copiar desde input)
    with open(output_path / 'encoders.pkl', 'wb') as f:
        pickle.dump(encoders, f)

    # Guardar feature names
    with open(output_path / 'feature_names.pkl', 'wb') as f:
        pickle.dump(feature_names, f)

    # Guardar feature importance
    if feature_importance is not None:
        feature_importance.to_csv(output_path / 'feature_importance.csv', index=False)

    # Guardar metadata del modelo
    metadata_modelo = {
        'fecha_entrenamiento': datetime.now().isoformat(),
        'modelo_tipo': modelo_nombre,
        'n_features': len(feature_names),
        'n_clases': len(encoders['target'].classes_),
        'clases': encoders['target'].classes_.tolist(),
        'metricas': metricas,
        'feature_names': feature_names
    }

    with open(output_path / 'modelo_metadata.json', 'w') as f:
        json.dump(metadata_modelo, f, indent=2)

    print(f"✅ Metadata guardada: {output_path / 'modelo_metadata.json'}")
    print(f"\n📁 Archivos del modelo:")
    print(f"   - modelo_propension_compra.pkl")
    print(f"   - encoders.pkl")
    print(f"   - feature_names.pkl")
    print(f"   - feature_importance.csv")
    print(f"   - modelo_metadata.json")

    return output_path


def generar_reporte_entrenamiento(resultados, mejor_nombre, output_dir):
    """
    Genera reporte de entrenamiento
    """
    print("\n" + "="*60)
    print("📄 GENERANDO REPORTE")
    print("="*60)

    output_path = Path(output_dir)

    reporte = []
    reporte.append("="*60)
    reporte.append("REPORTE DE ENTRENAMIENTO - MODELO DE PROPENSIÓN A COMPRA")
    reporte.append("="*60)
    reporte.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    reporte.append("")

    reporte.append("MODELOS ENTRENADOS:")
    reporte.append("")

    for nombre, data in resultados.items():
        if data['metricas'] is None:
            reporte.append(f"❌ {nombre}: No disponible")
            continue

        marcador = "🏆" if nombre == mejor_nombre else "  "
        reporte.append(f"{marcador} {nombre}:")
        reporte.append(f"     Accuracy:      {data['metricas']['accuracy']:.4f}")
        reporte.append(f"     Precision:     {data['metricas']['precision']:.4f}")
        reporte.append(f"     Recall:        {data['metricas']['recall']:.4f}")
        reporte.append(f"     F1-Score:      {data['metricas']['f1_score']:.4f}")
        reporte.append(f"     Top-3 Acc:     {data['metricas']['top3_accuracy']:.4f}")
        reporte.append(f"     Top-5 Acc:     {data['metricas']['top5_accuracy']:.4f}")
        reporte.append(f"     Tiempo:        {data['tiempo']:.2f}s")
        reporte.append("")

    reporte.append("="*60)
    reporte.append(f"MEJOR MODELO: {mejor_nombre}")
    reporte.append("="*60)

    reporte_text = '\n'.join(reporte)
    print(reporte_text)

    with open(output_path / 'reporte_entrenamiento.txt', 'w') as f:
        f.write(reporte_text)

    print(f"\n✅ Reporte guardado: {output_path / 'reporte_entrenamiento.txt'}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Entrenamiento de modelo de propensión a compra'
    )

    parser.add_argument(
        '--input',
        type=str,
        default='data/ml/propension_compra',
        help='Directorio con datasets preparados'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/models/propension_compra',
        help='Directorio de salida para modelo entrenado'
    )

    parser.add_argument(
        '--n-estimators',
        type=int,
        default=100,
        help='Número de árboles para ensemble models'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        default=20,
        help='Profundidad máxima de los árboles'
    )

    parser.add_argument(
        '--only-rf',
        action='store_true',
        help='Entrenar solo Random Forest (más rápido)'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🤖 ENTRENAMIENTO - MODELO DE PROPENSIÓN A COMPRA")
    print("="*60)
    print(f"Parámetros:")
    print(f"  - Input: {args.input}")
    print(f"  - Output: {args.output}")
    print(f"  - N estimators: {args.n_estimators}")
    print(f"  - Max depth: {args.max_depth}")
    print(f"  - Only RF: {args.only_rf}")

    # 1. Cargar datasets
    X_train, X_test, y_train, y_test, encoders, feature_names, metadata = cargar_datasets(args.input)

    # 2. Entrenar modelos
    resultados = {}

    # Random Forest (siempre disponible)
    rf_model, rf_tiempo = entrenar_random_forest(
        X_train, y_train,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth
    )
    rf_metricas, rf_pred, rf_proba = evaluar_modelo(
        rf_model, X_test, y_test, "Random Forest", encoders
    )
    resultados['RandomForest'] = {
        'modelo': rf_model,
        'metricas': rf_metricas,
        'tiempo': rf_tiempo,
        'predictions': rf_pred,
        'probabilities': rf_proba
    }

    if not args.only_rf:
        # XGBoost
        xgb_model, xgb_tiempo = entrenar_xgboost(
            X_train, y_train,
            n_estimators=args.n_estimators,
            max_depth=min(args.max_depth, 10)  # XGBoost prefiere menor depth
        )
        if xgb_model:
            xgb_metricas, xgb_pred, xgb_proba = evaluar_modelo(
                xgb_model, X_test, y_test, "XGBoost", encoders
            )
            resultados['XGBoost'] = {
                'modelo': xgb_model,
                'metricas': xgb_metricas,
                'tiempo': xgb_tiempo,
                'predictions': xgb_pred,
                'probabilities': xgb_proba
            }

        # LightGBM
        lgb_model, lgb_tiempo = entrenar_lightgbm(
            X_train, y_train,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth
        )
        if lgb_model:
            lgb_metricas, lgb_pred, lgb_proba = evaluar_modelo(
                lgb_model, X_test, y_test, "LightGBM", encoders
            )
            resultados['LightGBM'] = {
                'modelo': lgb_model,
                'metricas': lgb_metricas,
                'tiempo': lgb_tiempo,
                'predictions': lgb_pred,
                'probabilities': lgb_proba
            }

    # 3. Seleccionar mejor modelo
    mejor_nombre, mejor_modelo, mejor_f1 = seleccionar_mejor_modelo(resultados)

    # 4. Feature importance
    feature_importance = calcular_feature_importance(
        mejor_modelo, feature_names, mejor_nombre
    )

    # 5. Guardar modelo
    output_path = guardar_modelo(
        mejor_modelo,
        mejor_nombre,
        resultados[mejor_nombre]['metricas'],
        feature_names,
        encoders,
        feature_importance,
        args.output
    )

    # 6. Generar reporte
    generar_reporte_entrenamiento(resultados, mejor_nombre, args.output)

    print("\n" + "="*60)
    print("✅ ENTRENAMIENTO COMPLETADO")
    print("="*60)
    print(f"\n🏆 Mejor modelo: {mejor_nombre} (F1={mejor_f1:.4f})")
    print(f"📁 Modelo guardado en: {output_path}")
    print(f"\n🚀 Siguiente paso:")
    print(f"   python backend/ml/predecir_propension.py --modelo {args.output}")


if __name__ == "__main__":
    main()
