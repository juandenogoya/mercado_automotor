#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Preparación de Datos para Modelo de Propensión a Compra - VERSIÓN LITE

Esta versión LITE:
- Extrae features directamente desde las vistas KPI LITE (no requiere tabla ML pesada)
- Es mucho más rápida que la versión completa
- Usa menos dimensiones pero sigue siendo útil para predicciones

Uso:
    # RECOMENDADO: Usar todos los años disponibles (omitir --anios)
    python backend/ml/preparar_datos_propension_lite.py --output data/ml/

    # Alternativamente, especificar años concretos
    python backend/ml/preparar_datos_propension_lite.py --anios 2020,2021,2022,2023,2024 --output data/ml/
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
    connection_string = settings.get_database_url_sync()
    return create_engine(connection_string)


def extraer_features_desde_vistas_lite(engine, anios=None, min_inscripciones=10):
    """
    Extrae features desde las vistas KPI LITE y las combina

    Args:
        engine: SQLAlchemy engine
        anios: Lista de años a incluir (None = todos)
        min_inscripciones: Filtrar registros con pocas inscripciones

    Returns:
        DataFrame con features
    """
    print("\n" + "="*60)
    print("📊 EXTRAYENDO FEATURES DESDE VISTAS KPI LITE")
    print("="*60)

    # Construir filtro de años
    filtro_anios = ""
    if anios:
        anios_str = ','.join(map(str, anios))
        filtro_anios = f"AND seg.anio IN ({anios_str})"

    # Query que combina las 4 vistas LITE con JOINs
    # Nota: kpi_antiguedad_vehiculos_lite tiene tipo_transaccion, así que hacemos 2 JOINs
    query = text(f"""
        SELECT
            seg.provincia,
            seg.marca,
            seg.anio,
            seg.mes,
            seg.total_inscripciones,
            seg.edad_promedio,
            seg.modelos_distintos,

            -- Features de financiamiento
            COALESCE(fin.total_prendas, 0) as total_prendas,
            COALESCE(fin.indice_financiamiento, 0) as indice_financiamiento,

            -- Features de antigüedad de vehículos
            -- EVT = Edad promedio de transferencias
            COALESCE(ant_transf.edad_promedio, 0) as evt_promedio,
            -- IAM = Edad promedio de inscripciones
            COALESCE(ant_insc.edad_promedio, 0) as iam_promedio,

            -- Features de demanda activa
            COALESCE(dem.total_transferencias, 0) as total_transferencias,
            COALESCE(dem.indice_demanda_activa, 0) as indice_demanda_activa

        FROM kpi_segmentacion_demografica_lite seg

        LEFT JOIN kpi_financiamiento_lite fin
            ON seg.provincia = fin.provincia
            AND seg.marca = fin.marca
            AND seg.anio = fin.anio
            AND seg.mes = fin.mes

        -- JOIN para EVT (transferencias)
        LEFT JOIN kpi_antiguedad_vehiculos_lite ant_transf
            ON seg.provincia = ant_transf.provincia
            AND seg.marca = ant_transf.marca
            AND seg.anio = ant_transf.anio
            AND seg.mes = ant_transf.mes
            AND ant_transf.tipo_transaccion = 'transferencia'

        -- JOIN para IAM (inscripciones)
        LEFT JOIN kpi_antiguedad_vehiculos_lite ant_insc
            ON seg.provincia = ant_insc.provincia
            AND seg.marca = ant_insc.marca
            AND seg.anio = ant_insc.anio
            AND seg.mes = ant_insc.mes
            AND ant_insc.tipo_transaccion = 'inscripcion'

        LEFT JOIN kpi_demanda_activa_lite dem
            ON seg.provincia = dem.provincia
            AND seg.marca = dem.marca
            AND seg.anio = dem.anio
            AND seg.mes = dem.mes

        WHERE seg.total_inscripciones >= :min_inscripciones
        {filtro_anios}
        ORDER BY seg.anio, seg.mes, seg.provincia, seg.marca
    """)

    print(f"📥 Ejecutando query...")
    print(f"   - Años: {anios if anios else 'Todos'}")
    print(f"   - Mín inscripciones: {min_inscripciones}")

    df = pd.read_sql(query, engine, params={'min_inscripciones': min_inscripciones})

    print(f"✅ Features extraídas: {len(df):,} registros")
    print(f"   - Provincias: {df['provincia'].nunique()}")
    print(f"   - Marcas: {df['marca'].nunique()}")
    print(f"   - Período: {df['anio'].min()}-{df['mes'].min():02d} a {df['anio'].max()}-{df['mes'].max():02d}")
    print(f"   - Total inscripciones: {df['total_inscripciones'].sum():,}")

    return df


def feature_engineering_adicional(df):
    """
    Crea features adicionales derivadas (versión LITE)
    """
    print("\n" + "="*60)
    print("🔧 FEATURE ENGINEERING ADICIONAL")
    print("="*60)

    df_eng = df.copy()

    # 1. Estacionalidad (mes como categórica cíclica)
    df_eng['mes_sin'] = np.sin(2 * np.pi * df_eng['mes'] / 12)
    df_eng['mes_cos'] = np.cos(2 * np.pi * df_eng['mes'] / 12)

    # 2. Ratio prendas/inscripciones
    df_eng['ratio_prendas_inscripciones'] = (
        df_eng['total_prendas'] / df_eng['total_inscripciones'].replace(0, np.nan)
    ).fillna(0)

    # 3. Ratio transferencias/inscripciones
    df_eng['ratio_transferencias_inscripciones'] = (
        df_eng['total_transferencias'] / df_eng['total_inscripciones'].replace(0, np.nan)
    ).fillna(0)

    # 4. Concentración de marca por provincia (% de inscripciones de esa marca)
    total_por_provincia = df_eng.groupby(['provincia', 'anio', 'mes'])['total_inscripciones'].transform('sum')
    df_eng['concentracion_marca'] = (df_eng['total_inscripciones'] / total_por_provincia.replace(0, np.nan)).fillna(0)

    # 5. Ranking de marca por provincia
    df_eng['ranking_marca'] = df_eng.groupby(['provincia', 'anio', 'mes'])['total_inscripciones'].rank(
        ascending=False, method='dense'
    ).astype(int)

    # 6. Flag de marca top
    df_eng['es_marca_top'] = (df_eng['ranking_marca'] <= 5).astype(int)

    # 7. Flag de alta concentración
    df_eng['alta_concentracion'] = (df_eng['concentracion_marca'] > 0.3).astype(int)

    # 8. Segmento de mercado por edad promedio
    df_eng['segmento_mercado'] = pd.cut(
        df_eng['edad_promedio'],
        bins=[0, 30, 45, 60, 100],
        labels=['Joven', 'Adulto', 'Maduro', 'Senior']
    )

    # 9. Tendencias temporales (inscripciones mes anterior)
    df_eng = df_eng.sort_values(['provincia', 'marca', 'anio', 'mes'])
    df_eng['inscripciones_mes_anterior'] = df_eng.groupby(['provincia', 'marca'])['total_inscripciones'].shift(1).fillna(0)

    # 10. Inscripciones mismo mes año anterior
    df_eng['inscripciones_mismo_mes_anio_anterior'] = df_eng.groupby(['provincia', 'marca', 'mes'])['total_inscripciones'].shift(12).fillna(0)

    # 11. Tasa de crecimiento mensual
    df_eng['tasa_crecimiento_mensual'] = (
        (df_eng['total_inscripciones'] - df_eng['inscripciones_mes_anterior']) /
        df_eng['inscripciones_mes_anterior'].replace(0, np.nan)
    ).fillna(0)

    # 12. Tasa de crecimiento año a año
    df_eng['tasa_crecimiento_yoy'] = (
        (df_eng['total_inscripciones'] - df_eng['inscripciones_mismo_mes_anio_anterior']) /
        df_eng['inscripciones_mismo_mes_anio_anterior'].replace(0, np.nan)
    ).fillna(0)

    # 13. Completar NaN en features numéricas
    numeric_features = [
        'edad_promedio', 'modelos_distintos', 'total_prendas', 'indice_financiamiento',
        'evt_promedio', 'iam_promedio', 'total_transferencias', 'indice_demanda_activa'
    ]

    for col in numeric_features:
        if col in df_eng.columns:
            df_eng[col] = df_eng[col].fillna(df_eng[col].median())

    print(f"✅ Features adicionales creadas:")
    print(f"   - mes_sin, mes_cos (estacionalidad)")
    print(f"   - ratio_prendas_inscripciones")
    print(f"   - ratio_transferencias_inscripciones")
    print(f"   - concentracion_marca")
    print(f"   - ranking_marca")
    print(f"   - es_marca_top")
    print(f"   - alta_concentracion")
    print(f"   - segmento_mercado")
    print(f"   - tendencias temporales (mes anterior, año anterior)")
    print(f"   - tasas de crecimiento (mensual, YoY)")

    return df_eng


def preparar_para_entrenamiento(df, target_column='marca', test_size=0.2, random_state=42):
    """
    Prepara los datos para entrenamiento de modelos

    Args:
        df: DataFrame con features
        target_column: Columna target (ej: 'marca')
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
    categorical_features = ['provincia', 'segmento_mercado']

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

    # Seleccionar features para el modelo
    feature_columns = [
        # Demográficas y geográficas
        'provincia', 'edad_promedio',

        # Volúmenes
        'total_inscripciones', 'modelos_distintos',

        # KPIs
        'indice_financiamiento', 'total_prendas',
        'evt_promedio', 'iam_promedio',
        'indice_demanda_activa', 'total_transferencias',

        # Posicionamiento
        'concentracion_marca', 'ranking_marca',

        # Tendencias
        'inscripciones_mes_anterior', 'inscripciones_mismo_mes_anio_anterior',
        'tasa_crecimiento_mensual', 'tasa_crecimiento_yoy',

        # Ratios
        'ratio_prendas_inscripciones', 'ratio_transferencias_inscripciones',

        # Estacionalidad
        'mes_sin', 'mes_cos',

        # Flags
        'es_marca_top', 'alta_concentracion',

        # Segmento
        'segmento_mercado'
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
        'version': 'LITE',
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
    reporte.append("REPORTE DE ANÁLISIS EXPLORATORIO - VERSIÓN LITE")
    reporte.append("="*60)
    reporte.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    reporte.append(f"Total de registros: {len(df):,}")
    reporte.append(f"Total de inscripciones: {df['total_inscripciones'].sum():,}")
    reporte.append("")

    # Top marcas
    reporte.append("TOP 10 MARCAS:")
    top_marcas = df.groupby('marca')['total_inscripciones'].sum().nlargest(10)
    for i, (marca, total) in enumerate(top_marcas.items(), 1):
        pct = (total / df['total_inscripciones'].sum() * 100)
        reporte.append(f"  {i:2d}. {marca}: {total:,} inscripciones ({pct:.1f}%)")
    reporte.append("")

    # Distribución por provincia
    reporte.append("DISTRIBUCIÓN POR PROVINCIA:")
    top_prov = df.groupby('provincia')['total_inscripciones'].sum().nlargest(10)
    for i, (prov, total) in enumerate(top_prov.items(), 1):
        pct = (total / df['total_inscripciones'].sum() * 100)
        reporte.append(f"  {i:2d}. {prov}: {total:,} inscripciones ({pct:.1f}%)")
    reporte.append("")

    # Estadísticas de KPIs
    reporte.append("ESTADÍSTICAS DE KPIs:")
    reporte.append(f"  IF promedio: {df['indice_financiamiento'].mean():.2f}%")
    reporte.append(f"  EVT promedio: {df['evt_promedio'].mean():.2f} años")
    reporte.append(f"  IAM promedio: {df['iam_promedio'].mean():.2f} años")
    reporte.append(f"  IDA promedio: {df['indice_demanda_activa'].mean():.2f}%")
    reporte.append(f"  Edad promedio compradores: {df['edad_promedio'].mean():.1f} años")
    reporte.append("")

    # Distribución temporal
    reporte.append("DISTRIBUCIÓN TEMPORAL:")
    temporal = df.groupby('anio')['total_inscripciones'].sum()
    for anio, total in temporal.items():
        pct = (total / df['total_inscripciones'].sum() * 100)
        reporte.append(f"  {anio}: {total:,} inscripciones ({pct:.1f}%)")

    # Guardar reporte
    reporte_text = '\n'.join(reporte)
    with open(output_path / 'eda_reporte.txt', 'w', encoding='utf-8') as f:
        f.write(reporte_text)

    print(reporte_text)
    print(f"\n✅ Reporte guardado en: {output_path / 'eda_reporte.txt'}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Preparación de datos para modelo de propensión a compra - VERSIÓN LITE'
    )

    parser.add_argument(
        '--anios',
        type=str,
        help='Años a incluir (separados por coma, ej: 2023,2024). Si se omite, usa TODOS',
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
        default='data/ml/propension_compra_lite',
        help='Directorio de salida para datasets'
    )

    parser.add_argument(
        '--target',
        type=str,
        default='marca',
        help='Variable target a predecir (default: marca)'
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
    print("🤖 PREPARACIÓN DE DATOS - MODELO DE PROPENSIÓN (LITE)")
    print("="*60)
    print(f"Parámetros:")
    print(f"  - Versión: LITE (usa vistas KPI LITE)")
    print(f"  - Años: {anios if anios else 'Todos'}")
    print(f"  - Mín inscripciones: {args.min_inscripciones}")
    print(f"  - Target: {args.target}")
    print(f"  - Test size: {args.test_size}")
    print(f"  - Output: {args.output}")

    # 1. Conectar a DB
    engine = crear_engine()

    # 2. Extraer features desde vistas LITE
    df = extraer_features_desde_vistas_lite(engine, anios, args.min_inscripciones)

    if len(df) == 0:
        print("\n❌ No se encontraron datos. Verifica que las vistas KPI LITE estén creadas.")
        print("\n💡 Ejecuta: python backend/scripts/crear_kpis_lite_simple.py")
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
    print("✅ PREPARACIÓN COMPLETADA (VERSIÓN LITE)")
    print("="*60)
    print(f"\n📁 Datasets listos en: {output_path}")
    print(f"\n🚀 Siguiente paso:")
    print(f"   python backend/ml/entrenar_modelo_propension.py --input {args.output}")
    print(f"\n💡 Nota: Esta versión LITE usa menos dimensiones pero es mucho más rápida")


if __name__ == "__main__":
    main()
