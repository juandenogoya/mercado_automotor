#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para realizar predicciones de propensión de compra

Este script:
- Carga el modelo entrenado
- Acepta características de un perfil de usuario/segmento
- Predice las marcas con mayor propensión de compra
- Retorna scores de probabilidad para cada marca

Uso:
    # Desde línea de comandos
    python backend/ml/predecir_propension.py --provincia "BUENOS AIRES" --localidad "LA PLATA" --edad 35 --genero "M" --top 5

    # Desde código Python
    from backend.ml.predecir_propension import predecir_propension_compra
    resultados = predecir_propension_compra(
        provincia="BUENOS AIRES",
        localidad="LA PLATA",
        edad=35,
        genero="M",
        top_n=5
    )
"""

import sys
import argparse
import pickle
import json
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings('ignore')

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))


def cargar_modelo_y_metadata(modelo_dir="data/models/propension_compra_cv"):
    """
    Carga el modelo entrenado con cross-validation, encoders y metadata

    Args:
        modelo_dir: Directorio donde está guardado el modelo
                   Default: data/models/propension_compra_cv (modelo CV)

    Returns:
        tuple: (model, encoders, feature_names, metadata)
    """
    modelo_path = Path(modelo_dir)

    if not modelo_path.exists():
        raise FileNotFoundError(f"Directorio de modelo no encontrado: {modelo_path}")

    # Cargar modelo (probar ambos nombres por compatibilidad)
    modelo_file = modelo_path / "modelo_propension_compra_cv.pkl"
    if not modelo_file.exists():
        # Fallback al nombre antiguo
        modelo_file = modelo_path / "modelo_propension_compra.pkl"
        if not modelo_file.exists():
            raise FileNotFoundError(f"Archivo de modelo no encontrado en: {modelo_path}")

    with open(modelo_file, 'rb') as f:
        model = pickle.load(f)

    # Cargar encoders
    encoders_file = modelo_path / "encoders.pkl"
    if not encoders_file.exists():
        raise FileNotFoundError(f"Archivo de encoders no encontrado: {encoders_file}")

    with open(encoders_file, 'rb') as f:
        encoders = pickle.load(f)

    # Cargar feature names
    features_file = modelo_path / "feature_names.pkl"
    if not features_file.exists():
        raise FileNotFoundError(f"Archivo de feature names no encontrado: {features_file}")

    with open(features_file, 'rb') as f:
        feature_names = pickle.load(f)

    # Cargar metadata
    metadata_file = modelo_path / "modelo_metadata.json"
    metadata = None
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

    return model, encoders, feature_names, metadata


def preparar_features_prediccion(
    provincia,
    localidad,
    edad,
    genero,
    tipo_persona="FISICA",
    tipo_vehiculo="AUTOMOVIL",
    origen="NACIONAL",
    mes=None,
    anio=None,
    indice_financiamiento=None,
    evt_promedio=None,
    iam_promedio=None,
    indice_demanda_activa=None,
    encoders=None,
    feature_names=None
):
    """
    Prepara las features para predicción a partir de características del usuario/segmento

    Args:
        provincia: Provincia del titular
        localidad: Localidad del titular
        edad: Edad del potencial comprador
        genero: Género ('M', 'F', 'OTRO')
        tipo_persona: 'FISICA' o 'JURIDICA'
        tipo_vehiculo: Tipo de vehículo (default: 'AUTOMOVIL')
        origen: 'NACIONAL' o 'IMPORTADO'
        mes: Mes (1-12, default: mes actual)
        anio: Año (default: año actual)
        indice_financiamiento: IF promedio de la localidad (opcional)
        evt_promedio: EVT promedio de la localidad (opcional)
        iam_promedio: IAM promedio de la localidad (opcional)
        indice_demanda_activa: IDA promedio de la localidad (opcional)
        encoders: Diccionario de encoders
        feature_names: Lista de nombres de features esperadas

    Returns:
        np.array: Vector de features listo para predicción
    """
    if mes is None:
        mes = datetime.now().month

    if anio is None:
        anio = datetime.now().year

    # Determinar rango de edad
    if edad < 25:
        rango_edad = '18-24'
    elif edad < 35:
        rango_edad = '25-34'
    elif edad < 45:
        rango_edad = '35-44'
    elif edad < 55:
        rango_edad = '45-54'
    elif edad < 65:
        rango_edad = '55-64'
    else:
        rango_edad = '65+'

    # Crear DataFrame con las features categóricas
    input_data = {
        'provincia': provincia.upper(),
        'localidad': localidad.upper(),
        'rango_edad': rango_edad,
        'genero': genero.upper(),
        'tipo_persona': tipo_persona.upper(),
        'tipo_vehiculo': tipo_vehiculo.upper(),
        'origen': origen.upper(),
        'mes': mes,
        'anio': anio
    }

    # Features numéricas básicas
    input_data['edad_promedio_comprador'] = edad
    input_data['total_inscripciones'] = 100  # Valor promedio
    input_data['modelos_distintos'] = 5  # Valor promedio

    # KPIs (usar promedios si no se proporcionan)
    input_data['indice_financiamiento'] = indice_financiamiento if indice_financiamiento is not None else 35.0
    input_data['total_prendas'] = input_data['total_inscripciones'] * (input_data['indice_financiamiento'] / 100)
    input_data['evt_promedio'] = evt_promedio if evt_promedio is not None else 6.5
    input_data['iam_promedio'] = iam_promedio if iam_promedio is not None else 5.0
    input_data['indice_demanda_activa'] = indice_demanda_activa if indice_demanda_activa is not None else 120.0
    input_data['total_transferencias'] = input_data['total_inscripciones'] * (input_data['indice_demanda_activa'] / 100)

    # Features derivadas
    input_data['concentracion_marca_localidad'] = 0.15  # Valor promedio
    input_data['ranking_marca_localidad'] = 5  # Valor promedio
    input_data['inscripciones_mes_anterior'] = 95  # Valor promedio
    input_data['inscripciones_mismo_mes_anio_anterior'] = 98  # Valor promedio

    # Features adicionales (del feature engineering)
    # Tasa de crecimiento mensual
    input_data['tasa_crecimiento_mensual'] = (
        (input_data['total_inscripciones'] - input_data['inscripciones_mes_anterior']) /
        input_data['inscripciones_mes_anterior']
    )

    # Tasa de crecimiento YoY
    input_data['tasa_crecimiento_yoy'] = (
        (input_data['total_inscripciones'] - input_data['inscripciones_mismo_mes_anio_anterior']) /
        input_data['inscripciones_mismo_mes_anio_anterior']
    )

    # Ratio prendas/inscripciones
    input_data['ratio_prendas_inscripciones'] = input_data['total_prendas'] / max(input_data['total_inscripciones'], 1)

    # Ratio transferencias/inscripciones
    input_data['ratio_transferencias_inscripciones'] = input_data['total_transferencias'] / max(input_data['total_inscripciones'], 1)

    # Estacionalidad
    input_data['mes_sin'] = np.sin(2 * np.pi * mes / 12)
    input_data['mes_cos'] = np.cos(2 * np.pi * mes / 12)

    # Flags
    input_data['es_marca_top'] = 1 if input_data['ranking_marca_localidad'] <= 5 else 0
    input_data['alta_concentracion'] = 1 if input_data['concentracion_marca_localidad'] > 0.3 else 0

    # Segmento de mercado (basado en EVT/IAM)
    if input_data['evt_promedio'] < 3:
        segmento = 'nuevos'
    elif input_data['evt_promedio'] < 7:
        segmento = 'seminuevos'
    else:
        segmento = 'usados'
    input_data['segmento_mercado'] = segmento

    # Convertir a DataFrame
    df = pd.DataFrame([input_data])

    # Codificar variables categóricas usando los encoders
    categoricas = ['provincia', 'localidad', 'rango_edad', 'genero', 'tipo_persona',
                   'tipo_vehiculo', 'origen', 'segmento_mercado']

    for col in categoricas:
        if col in encoders:
            try:
                df[col] = encoders[col].transform(df[col])
            except ValueError:
                # Si la categoría no fue vista en entrenamiento, usar la más frecuente
                df[col] = 0

    # Asegurar que todas las features esperadas están presentes
    for feature in feature_names:
        if feature not in df.columns:
            df[feature] = 0

    # Ordenar columnas según feature_names
    df = df[feature_names]

    return df.values


def predecir_propension_compra(
    provincia,
    localidad,
    edad,
    genero,
    tipo_persona="FISICA",
    tipo_vehiculo="AUTOMOVIL",
    origen="NACIONAL",
    mes=None,
    anio=None,
    indice_financiamiento=None,
    evt_promedio=None,
    iam_promedio=None,
    indice_demanda_activa=None,
    top_n=5,
    modelo_dir="data/ml/modelos"
):
    """
    Predice las marcas con mayor propensión de compra para un perfil dado

    Args:
        provincia: Provincia del titular
        localidad: Localidad del titular
        edad: Edad del potencial comprador
        genero: Género ('M', 'F', 'OTRO')
        tipo_persona: 'FISICA' o 'JURIDICA'
        tipo_vehiculo: Tipo de vehículo
        origen: 'NACIONAL' o 'IMPORTADO'
        mes: Mes (1-12)
        anio: Año
        indice_financiamiento: IF promedio de la localidad
        evt_promedio: EVT promedio de la localidad
        iam_promedio: IAM promedio de la localidad
        indice_demanda_activa: IDA promedio de la localidad
        top_n: Número de marcas top a retornar
        modelo_dir: Directorio del modelo

    Returns:
        list: Lista de tuplas (marca, probabilidad) ordenadas por probabilidad descendente
    """
    # Cargar modelo y metadata
    model, encoders, feature_names, metadata = cargar_modelo_y_metadata(modelo_dir)

    # Preparar features
    X = preparar_features_prediccion(
        provincia=provincia,
        localidad=localidad,
        edad=edad,
        genero=genero,
        tipo_persona=tipo_persona,
        tipo_vehiculo=tipo_vehiculo,
        origen=origen,
        mes=mes,
        anio=anio,
        indice_financiamiento=indice_financiamiento,
        evt_promedio=evt_promedio,
        iam_promedio=iam_promedio,
        indice_demanda_activa=indice_demanda_activa,
        encoders=encoders,
        feature_names=feature_names
    )

    # Realizar predicción de probabilidades
    probabilidades = model.predict_proba(X)[0]

    # Obtener clases (marcas)
    clases = model.classes_

    # Decodificar marcas
    marca_encoder = encoders.get('marca')
    if marca_encoder:
        try:
            marcas = marca_encoder.inverse_transform(clases)
        except:
            marcas = [f"Marca_{c}" for c in clases]
    else:
        marcas = [f"Marca_{c}" for c in clases]

    # Crear lista de tuplas (marca, probabilidad)
    resultados = list(zip(marcas, probabilidades))

    # Ordenar por probabilidad descendente
    resultados_ordenados = sorted(resultados, key=lambda x: x[1], reverse=True)

    # Retornar top N
    return resultados_ordenados[:top_n]


def predecir_batch(input_csv, output_csv, top_n=5, modelo_dir="data/ml/modelos"):
    """
    Realiza predicciones en batch desde un archivo CSV

    Args:
        input_csv: Ruta al CSV con perfiles (columnas: provincia, localidad, edad, genero, ...)
        output_csv: Ruta donde guardar resultados
        top_n: Número de marcas top a incluir
        modelo_dir: Directorio del modelo
    """
    print(f"\n{'='*60}")
    print("📊 PREDICCIÓN EN BATCH - PROPENSIÓN DE COMPRA")
    print(f"{'='*60}")

    # Cargar CSV
    print(f"\n📥 Cargando datos desde: {input_csv}")
    df_input = pd.read_csv(input_csv)
    print(f"   Total de perfiles: {len(df_input):,}")

    # Cargar modelo una sola vez
    model, encoders, feature_names, metadata = cargar_modelo_y_metadata(modelo_dir)

    resultados = []

    print(f"\n🔮 Realizando predicciones...")
    for idx, row in df_input.iterrows():
        try:
            # Preparar features
            X = preparar_features_prediccion(
                provincia=row.get('provincia'),
                localidad=row.get('localidad'),
                edad=row.get('edad'),
                genero=row.get('genero'),
                tipo_persona=row.get('tipo_persona', 'FISICA'),
                tipo_vehiculo=row.get('tipo_vehiculo', 'AUTOMOVIL'),
                origen=row.get('origen', 'NACIONAL'),
                mes=row.get('mes'),
                anio=row.get('anio'),
                indice_financiamiento=row.get('indice_financiamiento'),
                evt_promedio=row.get('evt_promedio'),
                iam_promedio=row.get('iam_promedio'),
                indice_demanda_activa=row.get('indice_demanda_activa'),
                encoders=encoders,
                feature_names=feature_names
            )

            # Predecir
            probabilidades = model.predict_proba(X)[0]
            clases = model.classes_

            # Decodificar marcas
            marca_encoder = encoders.get('marca')
            if marca_encoder:
                try:
                    marcas = marca_encoder.inverse_transform(clases)
                except:
                    marcas = [f"Marca_{c}" for c in clases]
            else:
                marcas = [f"Marca_{c}" for c in clases]

            # Top N
            marca_prob = list(zip(marcas, probabilidades))
            top_marcas = sorted(marca_prob, key=lambda x: x[1], reverse=True)[:top_n]

            # Agregar al resultado
            resultado = row.to_dict()
            for i, (marca, prob) in enumerate(top_marcas, 1):
                resultado[f'marca_top_{i}'] = marca
                resultado[f'probabilidad_top_{i}'] = round(prob * 100, 2)

            resultados.append(resultado)

            if (idx + 1) % 100 == 0:
                print(f"   Procesados: {idx + 1:,}/{len(df_input):,}")

        except Exception as e:
            print(f"   ⚠️ Error en fila {idx}: {e}")

    # Guardar resultados
    print(f"\n💾 Guardando resultados en: {output_csv}")
    df_output = pd.DataFrame(resultados)
    df_output.to_csv(output_csv, index=False)

    print(f"\n✅ Predicciones completadas: {len(resultados):,}/{len(df_input):,}")
    print(f"{'='*60}\n")


def main():
    """
    Función principal para CLI
    """
    parser = argparse.ArgumentParser(
        description='Predicción de propensión de compra por marca',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Modo de operación
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Modo batch: leer desde CSV'
    )

    # Para modo batch
    parser.add_argument(
        '--input',
        type=str,
        help='Archivo CSV de entrada (para modo batch)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Archivo CSV de salida (para modo batch)'
    )

    # Para predicción individual
    parser.add_argument(
        '--provincia',
        type=str,
        help='Provincia del titular'
    )

    parser.add_argument(
        '--localidad',
        type=str,
        help='Localidad del titular'
    )

    parser.add_argument(
        '--edad',
        type=int,
        help='Edad del potencial comprador'
    )

    parser.add_argument(
        '--genero',
        type=str,
        choices=['M', 'F', 'OTRO', 'm', 'f', 'otro'],
        help='Género del potencial comprador'
    )

    parser.add_argument(
        '--tipo-persona',
        type=str,
        default='FISICA',
        choices=['FISICA', 'JURIDICA'],
        help='Tipo de persona (default: FISICA)'
    )

    parser.add_argument(
        '--tipo-vehiculo',
        type=str,
        default='AUTOMOVIL',
        help='Tipo de vehículo (default: AUTOMOVIL)'
    )

    parser.add_argument(
        '--origen',
        type=str,
        default='NACIONAL',
        choices=['NACIONAL', 'IMPORTADO'],
        help='Origen del vehículo (default: NACIONAL)'
    )

    parser.add_argument(
        '--mes',
        type=int,
        choices=range(1, 13),
        help='Mes (1-12, default: mes actual)'
    )

    parser.add_argument(
        '--anio',
        type=int,
        help='Año (default: año actual)'
    )

    # KPIs opcionales
    parser.add_argument(
        '--if',
        type=float,
        dest='indice_financiamiento',
        help='Índice de Financiamiento promedio de la localidad'
    )

    parser.add_argument(
        '--evt',
        type=float,
        dest='evt_promedio',
        help='EVT promedio de la localidad'
    )

    parser.add_argument(
        '--iam',
        type=float,
        dest='iam_promedio',
        help='IAM promedio de la localidad'
    )

    parser.add_argument(
        '--ida',
        type=float,
        dest='indice_demanda_activa',
        help='IDA promedio de la localidad'
    )

    # Configuración
    parser.add_argument(
        '--top',
        type=int,
        default=5,
        help='Número de marcas top a mostrar (default: 5)'
    )

    parser.add_argument(
        '--modelo-dir',
        type=str,
        default='data/ml/modelos',
        help='Directorio donde está el modelo (default: data/ml/modelos)'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("🔮 PREDICCIÓN DE PROPENSIÓN DE COMPRA")
    print("="*60)

    if args.batch:
        # Modo batch
        if not args.input or not args.output:
            print("❌ Error: Para modo batch se requiere --input y --output")
            return

        predecir_batch(
            input_csv=args.input,
            output_csv=args.output,
            top_n=args.top,
            modelo_dir=args.modelo_dir
        )

    else:
        # Modo individual
        if not all([args.provincia, args.localidad, args.edad, args.genero]):
            print("❌ Error: Se requiere --provincia, --localidad, --edad y --genero")
            parser.print_help()
            return

        print(f"\n📋 Perfil de Usuario:")
        print(f"   Provincia: {args.provincia}")
        print(f"   Localidad: {args.localidad}")
        print(f"   Edad: {args.edad}")
        print(f"   Género: {args.genero}")
        print(f"   Tipo Persona: {args.tipo_persona}")
        print(f"   Tipo Vehículo: {args.tipo_vehiculo}")
        print(f"   Origen: {args.origen}")

        if args.mes:
            print(f"   Mes: {args.mes}")
        if args.anio:
            print(f"   Año: {args.anio}")

        print(f"\n🔮 Realizando predicción...")

        resultados = predecir_propension_compra(
            provincia=args.provincia,
            localidad=args.localidad,
            edad=args.edad,
            genero=args.genero,
            tipo_persona=args.tipo_persona,
            tipo_vehiculo=args.tipo_vehiculo,
            origen=args.origen,
            mes=args.mes,
            anio=args.anio,
            indice_financiamiento=args.indice_financiamiento,
            evt_promedio=args.evt_promedio,
            iam_promedio=args.iam_promedio,
            indice_demanda_activa=args.indice_demanda_activa,
            top_n=args.top,
            modelo_dir=args.modelo_dir
        )

        print(f"\n📊 Top {args.top} Marcas con Mayor Propensión:")
        print("="*60)

        for i, (marca, probabilidad) in enumerate(resultados, 1):
            porcentaje = probabilidad * 100
            barra = "█" * int(porcentaje / 2)
            print(f"   {i}. {marca:<20} {porcentaje:6.2f}% {barra}")

        print("="*60 + "\n")


if __name__ == "__main__":
    main()
