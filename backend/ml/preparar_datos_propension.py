#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Preparación de Datos para Modelo de Propensión a Compra

Este script:
- Extrae features desde PostgreSQL (tabla ml_features_propension_compra)
- Realiza feature engineering adicional
- Prepara datos para entrenamiento de modelos de ML
- Genera datasets de train/test

Uso:
    python backend/ml/preparar_datos_propension.py --anios 2023,2024 --output data/ml/
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.config.settings import settings


def crear_engine():
    """Crea conexión a PostgreSQL"""
    connection_string = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    return create_engine(connection_string)


def extraer_features_desde_db(engine, anios=None, min_inscripciones=10):
    """
    Extrae features desde la tabla ml_features_propension_compra

    Args:
        engine: SQLAlchemy engine
        anios: Lista de años a incluir (None = todos)
        min_inscripciones: Filtrar registros con pocas inscripciones

    Returns:
        DataFrame con features
    """
    print("\n" + "="*60)
    print("📊 EXTRAYENDO FEATURES DESDE POSTGRESQL")
    print("="*60)

    # Construir query
    filtro_anios = ""
    if anios:
        anios_str = ','.join(map(str, anios))
        filtro_anios = f"AND anio IN ({anios_str})"

    query = text(f"""
        SELECT
            provincia,
            localidad,
            rango_edad,
            genero,
            tipo_persona,
            marca,
            tipo_vehiculo,
            origen,
            anio,
            mes,
            total_inscripciones,
            edad_promedio_comprador,
            modelos_distintos,
            indice_financiamiento,
            total_prendas,
            evt_promedio,
            iam_promedio,
            indice_demanda_activa,
            total_transferencias,
            concentracion_marca_localidad,
            ranking_marca_localidad,
            inscripciones_mes_anterior,
            inscripciones_mismo_mes_anio_anterior
        FROM ml_features_propension_compra
        WHERE total_inscripciones >= :min_inscripciones
        {filtro_anios}
        ORDER BY anio, mes, provincia, localidad
    """)

    print(f"📥 Ejecutando query...")
    print(f"   - Años: {anios if anios else 'Todos'}")
    print(f"   - Mín inscripciones: {min_inscripciones}")

    df = pd.read_sql(query, engine, params={'min_inscripciones': min_inscripciones})

    print(f"✅ Features extraídas: {len(df):,} registros")
    print(f"   - Provincias: {df['provincia'].nunique()}")
    print(f"   - Localidades: {df['localidad'].nunique()}")
    print(f"   - Marcas: {df['marca'].nunique()}")
    print(f"   - Período: {df['anio'].min()}-{df['mes'].min()} a {df['anio'].max()}-{df['mes'].max()}")

    return df


def feature_engineering_adicional(df):
    """
    Crea features adicionales derivadas
    """
    print("\n" + "="*60)
    print("🔧 FEATURE ENGINEERING ADICIONAL")
    print("="*60)

    df_eng = df.copy()

    # 1. Tasa de crecimiento mensual
    df_eng['tasa_crecimiento_mensual'] = (
        (df_eng['total_inscripciones'] - df_eng['inscripciones_mes_anterior']) /
        df_eng['inscripciones_mes_anterior'].replace(0, np.nan)
    ).fillna(0)

    # 2. Tasa de crecimiento año a año
    df_eng['tasa_crecimiento_yoy'] = (
        (df_eng['total_inscripciones'] - df_eng['inscripciones_mismo_mes_anio_anterior']) /
        df_eng['inscripciones_mismo_mes_anio_anterior'].replace(0, np.nan)
    ).fillna(0)

    # 3. Ratio prendas/inscripciones (complemento al IF)
    df_eng['ratio_prendas_inscripciones'] = (
        df_eng['total_prendas'] / df_eng['total_inscripciones'].replace(0, np.nan)
    ).fillna(0)

    # 4. Ratio transferencias/inscripciones (complemento al IDA)
    df_eng['ratio_transferencias_inscripciones'] = (
        df_eng['total_transferencias'] / df_eng['total_inscripciones'].replace(0, np.nan)
    ).fillna(0)

    # 5. Estacionalidad (mes como categórica cíclica)
    df_eng['mes_sin'] = np.sin(2 * np.pi * df_eng['mes'] / 12)
    df_eng['mes_cos'] = np.cos(2 * np.pi * df_eng['mes'] / 12)

    # 6. Flag de marca top (ranking <= 5)
    df_eng['es_marca_top'] = (df_eng['ranking_marca_localidad'] <= 5).astype(int)

    # 7. Segmento de mercado
    df_eng['segmento_mercado'] = pd.cut(
        df_eng['edad_promedio_comprador'],
        bins=[0, 30, 45, 60, 100],
        labels=['Joven', 'Adulto', 'Maduro', 'Senior']
    )

    # 8. Flag de alta concentración
    df_eng['alta_concentracion'] = (df_eng['concentracion_marca_localidad'] > 0.3).astype(int)

    # 9. Completar NaN en features numéricas
    numeric_features = [
        'edad_promedio_comprador', 'modelos_distintos', 'indice_financiamiento',
        'total_prendas', 'evt_promedio', 'iam_promedio', 'indice_demanda_activa',
        'total_transferencias', 'concentracion_marca_localidad', 'ranking_marca_localidad',
        'inscripciones_mes_anterior', 'inscripciones_mismo_mes_anio_anterior'
    ]

    for col in numeric_features:
        if col in df_eng.columns:
            df_eng[col] = df_eng[col].fillna(df_eng[col].median())

    print(f"✅ Features adicionales creadas:")
    print(f"   - tasa_crecimiento_mensual")
    print(f"   - tasa_crecimiento_yoy")
    print(f"   - ratio_prendas_inscripciones")
    print(f"   - ratio_transferencias_inscripciones")
    print(f"   - mes_sin, mes_cos (estacionalidad)")
    print(f"   - es_marca_top")
    print(f"   - segmento_mercado")
    print(f"   - alta_concentracion")

    return df_eng


def preparar_para_entrenamiento(df, target_column='marca', test_size=0.2, random_state=42):
    """
    Prepara los datos para entrenamiento de modelos

    Args:
        df: DataFrame con features
        target_column: Columna target (ej: 'marca', 'tipo_vehiculo')
        test_size: Proporción del test set
        random_state: Semilla para reproducibilidad

    Returns:
        X_train, X_test, y_train, y_test, encoders
    """
    print("\n" + "="*60)
    print(f"🎯 PREPARANDO DATOS PARA ENTRENAMIENTO")
    print(f"   Target: {target_column}")
    print("="*60)

    df_prep = df.copy()

    # Features categóricas a encodear
    categorical_features = [
        'provincia', 'localidad', 'rango_edad', 'genero', 'tipo_persona',
        'tipo_vehiculo', 'origen', 'segmento_mercado'
    ]

    # Encoders para features categóricas
    encoders = {}

    for col in categorical_features:
        if col in df_prep.columns and col != target_column:
            le = LabelEncoder()
            df_prep[col] = le.fit_transform(df_prep[col].fillna('UNKNOWN'))
            encoders[col] = le

    # Target encoding
    if target_column in df_prep.columns:
        le_target = LabelEncoder()
        y = le_target.fit_transform(df_prep[target_column])
        encoders['target'] = le_target
    else:
        raise ValueError(f"Columna target '{target_column}' no encontrada")

    # Seleccionar features numéricas y categóricas encodadas
    feature_columns = [
        # Demográficas
        'provincia', 'localidad', 'rango_edad', 'genero', 'tipo_persona',
        'edad_promedio_comprador',

        # Características del vehículo
        'tipo_vehiculo', 'origen', 'modelos_distintos',

        # KPIs
        'indice_financiamiento', 'evt_promedio', 'iam_promedio', 'indice_demanda_activa',

        # Volúmenes
        'total_inscripciones', 'total_prendas', 'total_transferencias',

        # Posicionamiento
        'concentracion_marca_localidad', 'ranking_marca_localidad',

        # Tendencias
        'inscripciones_mes_anterior', 'inscripciones_mismo_mes_anio_anterior',
        'tasa_crecimiento_mensual', 'tasa_crecimiento_yoy',

        # Ratios
        'ratio_prendas_inscripciones', 'ratio_transferencias_inscripciones',

        # Estacionalidad
        'mes_sin', 'mes_cos',

        # Flags
        'es_marca_top', 'alta_concentracion'
    ]

    # Filtrar solo columnas que existen
    feature_columns = [col for col in feature_columns if col in df_prep.columns]

    X = df_prep[feature_columns]

    # Reemplazar infinitos por NaN y luego por 0
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    print(f"✅ Datos preparados:")
    print(f"   - Features: {len(feature_columns)}")
    print(f"   - Train samples: {len(X_train):,}")
    print(f"   - Test samples: {len(X_test):,}")
    print(f"   - Clases (marcas): {len(encoders['target'].classes_)}")
    print(f"\n📋 Features utilizadas:")
    for i, col in enumerate(feature_columns, 1):
        print(f"   {i:2d}. {col}")

    return X_train, X_test, y_train, y_test, encoders, feature_columns


def guardar_datasets(X_train, X_test, y_train, y_test, encoders, feature_columns, output_dir):
    """
    Guarda los datasets preparados
    """
    print("\n" + "="*60)
    print("💾 GUARDANDO DATASETS")
    print("="*60)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Guardar datasets
    np.save(output_path / 'X_train.npy', X_train.values)
    np.save(output_path / 'X_test.npy', X_test.values)
    np.save(output_path / 'y_train.npy', y_train)
    np.save(output_path / 'y_test.npy', y_test)

    # Guardar encoders
    with open(output_path / 'encoders.pkl', 'wb') as f:
        pickle.dump(encoders, f)

    # Guardar feature names
    with open(output_path / 'feature_names.pkl', 'wb') as f:
        pickle.dump(feature_columns, f)

    # Guardar metadata
    metadata = {
        'fecha_creacion': datetime.now().isoformat(),
        'n_features': len(feature_columns),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'n_clases': len(encoders['target'].classes_),
        'clases': encoders['target'].classes_.tolist(),
        'feature_names': feature_columns
    }

    import json
    with open(output_path / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Datasets guardados en: {output_path}")
    print(f"   - X_train.npy ({X_train.shape})")
    print(f"   - X_test.npy ({X_test.shape})")
    print(f"   - y_train.npy ({len(y_train)} samples)")
    print(f"   - y_test.npy ({len(y_test)} samples)")
    print(f"   - encoders.pkl")
    print(f"   - feature_names.pkl")
    print(f"   - metadata.json")

    return output_path


def generar_reporte_eda(df, output_dir):
    """
    Genera reporte exploratorio de los datos
    """
    print("\n" + "="*60)
    print("📈 GENERANDO REPORTE EDA")
    print("="*60)

    output_path = Path(output_dir)

    reporte = []
    reporte.append("="*60)
    reporte.append("REPORTE DE ANÁLISIS EXPLORATORIO")
    reporte.append("="*60)
    reporte.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    reporte.append(f"Total de registros: {len(df):,}")
    reporte.append("")

    # Top marcas
    reporte.append("TOP 10 MARCAS:")
    top_marcas = df.groupby('marca')['total_inscripciones'].sum().nlargest(10)
    for i, (marca, total) in enumerate(top_marcas.items(), 1):
        reporte.append(f"  {i:2d}. {marca}: {total:,} inscripciones")
    reporte.append("")

    # Distribución por provincia
    reporte.append("DISTRIBUCIÓN POR PROVINCIA:")
    top_prov = df.groupby('provincia')['total_inscripciones'].sum().nlargest(10)
    for i, (prov, total) in enumerate(top_prov.items(), 1):
        reporte.append(f"  {i:2d}. {prov}: {total:,} inscripciones")
    reporte.append("")

    # Estadísticas de KPIs
    reporte.append("ESTADÍSTICAS DE KPIs:")
    reporte.append(f"  IF promedio: {df['indice_financiamiento'].mean():.2f}%")
    reporte.append(f"  EVT promedio: {df['evt_promedio'].mean():.2f} años")
    reporte.append(f"  IAM promedio: {df['iam_promedio'].mean():.2f} años")
    reporte.append(f"  IDA promedio: {df['indice_demanda_activa'].mean():.2f}%")
    reporte.append("")

    # Distribución por edad
    reporte.append("DISTRIBUCIÓN POR RANGO DE EDAD:")
    edad_dist = df.groupby('rango_edad')['total_inscripciones'].sum()
    for rango, total in edad_dist.items():
        pct = (total / edad_dist.sum() * 100)
        reporte.append(f"  {rango}: {total:,} ({pct:.1f}%)")

    # Guardar reporte
    reporte_text = '\n'.join(reporte)
    with open(output_path / 'eda_reporte.txt', 'w') as f:
        f.write(reporte_text)

    print(reporte_text)
    print(f"\n✅ Reporte guardado en: {output_path / 'eda_reporte.txt'}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Preparación de datos para modelo de propensión a compra'
    )

    parser.add_argument(
        '--anios',
        type=str,
        help='Años a incluir (separados por coma, ej: 2023,2024)',
        default=None
    )

    parser.add_argument(
        '--min-inscripciones',
        type=int,
        default=10,
        help='Mínimo de inscripciones para incluir registro'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/ml/propension_compra',
        help='Directorio de salida para datasets'
    )

    parser.add_argument(
        '--target',
        type=str,
        default='marca',
        choices=['marca', 'tipo_vehiculo'],
        help='Variable target a predecir'
    )

    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proporción del test set (default: 0.2)'
    )

    args = parser.parse_args()

    # Parsear años
    anios = None
    if args.anios:
        anios = [int(a.strip()) for a in args.anios.split(',')]

    print("\n" + "="*60)
    print("🤖 PREPARACIÓN DE DATOS - MODELO DE PROPENSIÓN A COMPRA")
    print("="*60)
    print(f"Parámetros:")
    print(f"  - Años: {anios if anios else 'Todos'}")
    print(f"  - Mín inscripciones: {args.min_inscripciones}")
    print(f"  - Target: {args.target}")
    print(f"  - Test size: {args.test_size}")
    print(f"  - Output: {args.output}")

    # 1. Conectar a DB
    engine = crear_engine()

    # 2. Extraer features
    df = extraer_features_desde_db(engine, anios, args.min_inscripciones)

    if len(df) == 0:
        print("\n❌ No se encontraron datos. Verifica que las vistas KPI estén creadas.")
        return

    # 3. Feature engineering
    df_eng = feature_engineering_adicional(df)

    # 4. Preparar para entrenamiento
    X_train, X_test, y_train, y_test, encoders, feature_cols = preparar_para_entrenamiento(
        df_eng,
        target_column=args.target,
        test_size=args.test_size
    )

    # 5. Guardar datasets
    output_path = guardar_datasets(
        X_train, X_test, y_train, y_test, encoders, feature_cols, args.output
    )

    # 6. Generar reporte EDA
    generar_reporte_eda(df_eng, args.output)

    print("\n" + "="*60)
    print("✅ PREPARACIÓN COMPLETADA")
    print("="*60)
    print(f"\n📁 Datasets listos en: {output_path}")
    print(f"\n🚀 Siguiente paso:")
    print(f"   python backend/ml/entrenar_modelo_propension.py --input {args.output}")


if __name__ == "__main__":
    main()
