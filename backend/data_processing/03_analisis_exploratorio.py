"""
Script para análisis exploratorio del dataset unificado.

Objetivo:
- Cargar dataset Parquet generado
- Análisis estadístico descriptivo
- Detectar outliers y anomalías
- Análisis de series temporales
- Generar visualizaciones básicas

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/03_analisis_exploratorio.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Configuración
INPUT_FILE = 'data/processed/dataset_transaccional_unificado.parquet'


def cargar_dataset():
    """Carga dataset desde Parquet."""
    print(f"\n📥 Cargando dataset...")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"❌ No se encontró el archivo: {INPUT_FILE}\n"
                                f"   Ejecuta primero: python backend/data_processing/02_unir_datasets.py")

    df = pd.read_parquet(INPUT_FILE)
    print(f"   ✓ Dataset cargado: {len(df):,} registros, {len(df.columns)} columnas")

    return df


def analisis_estadistico(df):
    """Análisis estadístico descriptivo."""
    print(f"\n{'='*100}")
    print("ANÁLISIS ESTADÍSTICO DESCRIPTIVO")
    print('='*100)

    # 1. Estadísticas de columnas numéricas
    print(f"\n📊 COLUMNAS NUMÉRICAS:")
    print("-" * 100)

    columnas_numericas = ['anio', 'mes', 'trimestre', 'dia_semana', 'semana_anio',
                          'automotor_anio_modelo', 'dias_desde_origen']

    for col in columnas_numericas:
        if col in df.columns:
            print(f"\n{col}:")
            print(f"   Min: {df[col].min()}")
            print(f"   Max: {df[col].max()}")
            print(f"   Media: {df[col].mean():.2f}")
            print(f"   Mediana: {df[col].median():.2f}")
            print(f"   Std: {df[col].std():.2f}")

    # 2. Distribuciones categóricas
    print(f"\n\n📋 DISTRIBUCIONES CATEGÓRICAS:")
    print("-" * 100)

    print(f"\nTipo de operación:")
    print(df['tipo_operacion'].value_counts())

    print(f"\nOrigen del vehículo:")
    print(df['automotor_origen'].value_counts().head(5))

    print(f"\nUso del vehículo:")
    print(df['automotor_uso'].value_counts().head(5))


def analisis_temporal(df):
    """Análisis de series temporales."""
    print(f"\n{'='*100}")
    print("ANÁLISIS TEMPORAL")
    print('='*100)

    # Asegurar que tramite_fecha es datetime
    df['tramite_fecha'] = pd.to_datetime(df['tramite_fecha'])

    # 1. Agregación mensual
    print(f"\n📅 EVOLUCIÓN MENSUAL:")
    print("-" * 100)

    df_mensual = df.groupby([df['tramite_fecha'].dt.to_period('M'), 'tipo_operacion']).size().reset_index(name='count')
    df_mensual_pivot = df_mensual.pivot(index=0, columns='tipo_operacion', values='count').fillna(0)

    print(f"\nÚltimos 12 meses:")
    print(df_mensual_pivot.tail(12).to_string())

    # 2. Estacionalidad mensual
    print(f"\n\n📊 ESTACIONALIDAD MENSUAL (promedio por mes del año):")
    print("-" * 100)

    df_estacionalidad = df.groupby(['mes', 'tipo_operacion']).size().reset_index(name='count')
    df_estacionalidad_pivot = df_estacionalidad.pivot(index='mes', columns='tipo_operacion', values='count')

    meses_nombres = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    df_estacionalidad_pivot.index = df_estacionalidad_pivot.index.map(meses_nombres)
    print(df_estacionalidad_pivot.to_string())

    # 3. Tendencia anual
    print(f"\n\n📈 TENDENCIA ANUAL:")
    print("-" * 100)

    df_anual = df.groupby(['anio', 'tipo_operacion']).size().reset_index(name='count')
    df_anual_pivot = df_anual.pivot(index='anio', columns='tipo_operacion', values='count').fillna(0)

    print(df_anual_pivot.to_string())

    # Calcular crecimiento YoY
    print(f"\n\n📊 CRECIMIENTO AÑO A AÑO (YoY %):")
    print("-" * 100)

    df_yoy = df_anual_pivot.pct_change() * 100
    print(df_yoy.round(2).to_string())


def analisis_provincias(df):
    """Análisis por provincia."""
    print(f"\n{'='*100}")
    print("ANÁLISIS POR PROVINCIA")
    print('='*100)

    # 1. Top provincias por tipo de operación
    print(f"\n📍 TOP 10 PROVINCIAS POR TIPO DE OPERACIÓN:")
    print("-" * 100)

    for tipo in df['tipo_operacion'].unique():
        df_tipo = df[df['tipo_operacion'] == tipo]
        top_prov = df_tipo['registro_seccional_provincia'].value_counts().head(10)

        print(f"\n{tipo.upper()}:")
        for prov, count in top_prov.items():
            pct = 100 * count / len(df_tipo)
            print(f"   {prov:30} : {count:10,} ({pct:5.2f}%)")

    # 2. Concentración de mercado
    print(f"\n\n📊 CONCENTRACIÓN DE MERCADO (% acumulado):")
    print("-" * 100)

    for tipo in df['tipo_operacion'].unique():
        df_tipo = df[df['tipo_operacion'] == tipo]
        prov_counts = df_tipo['registro_seccional_provincia'].value_counts()
        prov_pct = 100 * prov_counts / len(df_tipo)
        cumsum_pct = prov_pct.cumsum()

        top3_pct = cumsum_pct.iloc[2] if len(cumsum_pct) >= 3 else cumsum_pct.iloc[-1]
        top10_pct = cumsum_pct.iloc[9] if len(cumsum_pct) >= 10 else cumsum_pct.iloc[-1]

        print(f"\n{tipo.upper()}:")
        print(f"   Top 3 provincias: {top3_pct:.2f}%")
        print(f"   Top 10 provincias: {top10_pct:.2f}%")


def analisis_vehiculos(df):
    """Análisis de vehículos."""
    print(f"\n{'='*100}")
    print("ANÁLISIS DE VEHÍCULOS")
    print('='*100)

    # 1. Top marcas
    print(f"\n🚗 TOP 15 MARCAS:")
    print("-" * 100)

    top_marcas = df['automotor_marca_descripcion'].value_counts().head(15)
    for marca, count in top_marcas.items():
        pct = 100 * count / len(df)
        print(f"   {marca:30} : {count:10,} ({pct:5.2f}%)")

    # 2. Top tipos de vehículo
    print(f"\n\n🚙 TOP 15 TIPOS DE VEHÍCULO:")
    print("-" * 100)

    top_tipos = df['automotor_tipo_descripcion'].value_counts().head(15)
    for tipo, count in top_tipos.items():
        pct = 100 * count / len(df)
        print(f"   {tipo:40} : {count:10,} ({pct:5.2f}%)")

    # 3. Distribución por año modelo
    print(f"\n\n📅 DISTRIBUCIÓN POR AÑO MODELO (últimos 10 años):")
    print("-" * 100)

    anios_modelo = df['automotor_anio_modelo'].value_counts().sort_index(ascending=False).head(10)
    for anio, count in anios_modelo.items():
        pct = 100 * count / len(df)
        print(f"   {anio} : {count:10,} ({pct:5.2f}%)")


def detectar_outliers(df):
    """Detecta outliers y anomalías."""
    print(f"\n{'='*100}")
    print("DETECCIÓN DE OUTLIERS Y ANOMALÍAS")
    print('='*100)

    # 1. Años modelo anómalos (futuros o muy antiguos)
    print(f"\n🔍 AÑOS MODELO ANÓMALOS:")
    print("-" * 100)

    anio_actual = datetime.now().year
    df_futuro = df[df['automotor_anio_modelo'] > anio_actual + 1]
    df_antiguo = df[df['automotor_anio_modelo'] < 1950]

    print(f"   Vehículos con año futuro (>{anio_actual + 1}): {len(df_futuro):,}")
    print(f"   Vehículos muy antiguos (<1950): {len(df_antiguo):,}")

    # 2. Registros por día (detectar picos)
    print(f"\n\n📊 DÍAS CON MÁS OPERACIONES (Top 10):")
    print("-" * 100)

    df['fecha_solo'] = df['tramite_fecha'].dt.date
    dias_top = df['fecha_solo'].value_counts().head(10)

    for fecha, count in dias_top.items():
        print(f"   {fecha} : {count:10,} operaciones")

    # 3. Días con menos operaciones (posibles errores)
    print(f"\n\n📊 DÍAS CON MENOS OPERACIONES (Bottom 10):")
    print("-" * 100)

    dias_bottom = df['fecha_solo'].value_counts().tail(10)

    for fecha, count in dias_bottom.items():
        print(f"   {fecha} : {count:10,} operaciones")


def generar_resumen(df):
    """Genera resumen ejecutivo."""
    print(f"\n{'='*100}")
    print("RESUMEN EJECUTIVO - DATASET UNIFICADO")
    print('='*100)

    print(f"\n📋 CARACTERÍSTICAS GENERALES:")
    print(f"   Total registros: {len(df):,}")
    print(f"   Total columnas: {len(df.columns)}")
    print(f"   Período: {df['tramite_fecha'].min()} a {df['tramite_fecha'].max()}")
    print(f"   Días totales: {(df['tramite_fecha'].max() - df['tramite_fecha'].min()).days:,}")

    print(f"\n📊 DISTRIBUCIÓN:")
    tipo_dist = df['tipo_operacion'].value_counts()
    for tipo, count in tipo_dist.items():
        pct = 100 * count / len(df)
        print(f"   {tipo:15} : {count:10,} ({pct:5.2f}%)")

    print(f"\n🎯 CALIDAD DE DATOS:")
    total_nulos = df.isnull().sum().sum()
    pct_nulos = 100 * total_nulos / (len(df) * len(df.columns))
    print(f"   Total valores nulos: {total_nulos:,} ({pct_nulos:.2f}%)")

    print(f"\n✅ DATASET LISTO PARA:")
    print(f"   ✓ Análisis exploratorio adicional")
    print(f"   ✓ Feature engineering avanzado")
    print(f"   ✓ Modelado de forecasting")
    print(f"   ✓ Integración con datos macroeconómicos (Fase 2)")


def main():
    """Función principal."""
    print("\n" + "="*100)
    print("ANÁLISIS EXPLORATORIO DEL DATASET UNIFICADO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    try:
        # Cargar dataset
        df = cargar_dataset()

        # Ejecutar análisis
        analisis_estadistico(df)
        analisis_temporal(df)
        analisis_provincias(df)
        analisis_vehiculos(df)
        detectar_outliers(df)

        # Resumen final
        generar_resumen(df)

        print(f"\n{'='*100}")
        print("✅ ANÁLISIS COMPLETADO")
        print('='*100)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
