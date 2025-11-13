#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exporta dataset de forecasting a Excel con dos hojas:

1. Hoja "Datos": Primeras 100 filas del dataset
2. Hoja "Diccionario": Nombre de variable + descripción del cálculo

Ejecutar desde: mercado_automotor/
Comando: python backend/data_processing/exportar_dataset_a_excel.py
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Configuración
INPUT_FILE = 'data/processed/dataset_forecasting_completo.parquet'
OUTPUT_FILE = 'data/processed/dataset_forecasting_analisis.xlsx'

def crear_diccionario_variables():
    """
    Crea diccionario con nombre y descripción de cada variable.
    """
    diccionario = []

    # TARGET Y BASE
    diccionario.append({
        'Variable': 'fecha',
        'Tipo': 'Base',
        'Cálculo/Descripción': 'Fecha del mes (formato YYYY-MM-DD)',
        'Ejemplo': '2019-01-01'
    })

    diccionario.append({
        'Variable': 'total_operaciones',
        'Tipo': 'Target',
        'Cálculo/Descripción': 'Total de operaciones automotrices en el mes (inscripciones + transferencias + prendas)',
        'Ejemplo': '50000'
    })

    # TIPOS DE OPERACIÓN
    diccionario.append({
        'Variable': 'total_inscripciones',
        'Tipo': 'Base',
        'Cálculo/Descripción': 'Total de inscripciones iniciales (autos 0km)',
        'Ejemplo': '20000'
    })

    diccionario.append({
        'Variable': 'total_transferencias',
        'Tipo': 'Base',
        'Cálculo/Descripción': 'Total de transferencias de dominio (autos usados)',
        'Ejemplo': '25000'
    })

    diccionario.append({
        'Variable': 'total_prendas',
        'Tipo': 'Base',
        'Cálculo/Descripción': 'Total de constitución de prendas (financiamiento)',
        'Ejemplo': '5000'
    })

    # OPERACIONES POR PROVINCIA (Top 10)
    diccionario.append({
        'Variable': 'operaciones_*',
        'Tipo': 'Categórica - Provincial',
        'Cálculo/Descripción': 'Total operaciones por provincia (ej: operaciones_buenos_aires, operaciones_córdoba, etc.)',
        'Ejemplo': '15000'
    })

    # OPERACIONES POR MARCA (Top 10)
    diccionario.append({
        'Variable': 'operaciones_marca_*',
        'Tipo': 'Categórica - Marca',
        'Cálculo/Descripción': 'Total operaciones por marca (ej: operaciones_marca_ford, operaciones_marca_toyota, etc.)',
        'Ejemplo': '3000'
    })

    # VARIABLES MACRO - BCRA
    diccionario.append({
        'Variable': 'tipo_de_cambio_usd_prom',
        'Tipo': 'Macro - BCRA',
        'Cálculo/Descripción': 'Tipo de cambio promedio USD/ARS del mes',
        'Ejemplo': '150.50'
    })

    diccionario.append({
        'Variable': 'BADLAR',
        'Tipo': 'Macro - BCRA',
        'Cálculo/Descripción': 'Tasa BADLAR promedio del mes (% anual)',
        'Ejemplo': '45.2'
    })

    diccionario.append({
        'Variable': 'IPC_mensual',
        'Tipo': 'Macro - BCRA',
        'Cálculo/Descripción': 'Índice de Precios al Consumidor (inflación mensual)',
        'Ejemplo': '3.5'
    })

    diccionario.append({
        'Variable': 'LELIQ',
        'Tipo': 'Macro - BCRA',
        'Cálculo/Descripción': 'Tasa LELIQ promedio del mes (% anual)',
        'Ejemplo': '50.0'
    })

    diccionario.append({
        'Variable': 'reservas_internacionales',
        'Tipo': 'Macro - BCRA',
        'Cálculo/Descripción': 'Reservas internacionales del BCRA en millones USD',
        'Ejemplo': '40000'
    })

    # VARIABLES MACRO - INDEC
    diccionario.append({
        'Variable': 'EMAE',
        'Tipo': 'Macro - INDEC',
        'Cálculo/Descripción': 'Estimador Mensual de Actividad Económica (índice base 2004=100)',
        'Ejemplo': '150.2'
    })

    diccionario.append({
        'Variable': 'desocupacion',
        'Tipo': 'Macro - INDEC',
        'Cálculo/Descripción': 'Tasa de desocupación (% de PEA)',
        'Ejemplo': '7.5'
    })

    diccionario.append({
        'Variable': 'ripte',
        'Tipo': 'Macro - INDEC',
        'Cálculo/Descripción': 'Remuneración Imponible Promedio de los Trabajadores Estables',
        'Ejemplo': '120000'
    })

    # VARIACIONES PORCENTUALES
    diccionario.append({
        'Variable': 'Δtipo_de_cambio_usd_prom',
        'Tipo': 'Variación %',
        'Cálculo/Descripción': 'Δ = (TC_t - TC_{t-1}) / TC_{t-1}. Variación porcentual del TC respecto mes anterior',
        'Ejemplo': '0.05 (5% de aumento)'
    })

    diccionario.append({
        'Variable': 'ΔBADLAR',
        'Tipo': 'Variación %',
        'Cálculo/Descripción': 'Δ = (BADLAR_t - BADLAR_{t-1}) / BADLAR_{t-1}. Variación porcentual de BADLAR',
        'Ejemplo': '0.10 (10% de aumento)'
    })

    diccionario.append({
        'Variable': 'ΔIPC_mensual',
        'Tipo': 'Variación %',
        'Cálculo/Descripción': 'Δ = (IPC_t - IPC_{t-1}) / IPC_{t-1}. Variación porcentual del IPC',
        'Ejemplo': '0.03 (3% de inflación adicional)'
    })

    diccionario.append({
        'Variable': 'ΔLELIQ',
        'Tipo': 'Variación %',
        'Cálculo/Descripción': 'Δ = (LELIQ_t - LELIQ_{t-1}) / LELIQ_{t-1}. Variación porcentual de LELIQ',
        'Ejemplo': '0.08'
    })

    diccionario.append({
        'Variable': 'ΔEMAE',
        'Tipo': 'Variación %',
        'Cálculo/Descripción': 'Δ = (EMAE_t - EMAE_{t-1}) / EMAE_{t-1}. Variación de actividad económica',
        'Ejemplo': '-0.02 (2% de caída)'
    })

    diccionario.append({
        'Variable': 'Δreservas_internacionales',
        'Tipo': 'Variación %',
        'Cálculo/Descripción': 'Δ = (Reservas_t - Reservas_{t-1}) / Reservas_{t-1}. Variación de reservas',
        'Ejemplo': '-0.05 (5% de caída)'
    })

    # RATIOS TRANSACCIONALES
    diccionario.append({
        'Variable': 'ratio_prendas_inscripciones',
        'Tipo': 'Ratio',
        'Cálculo/Descripción': 'total_prendas / total_inscripciones. Mide % de operaciones financiadas',
        'Ejemplo': '0.25 (25% de inscripciones con prenda)'
    })

    diccionario.append({
        'Variable': 'ratio_transferencias_inscripciones',
        'Tipo': 'Ratio',
        'Cálculo/Descripción': 'total_transferencias / total_inscripciones. Mide dinamismo mercado secundario vs primario',
        'Ejemplo': '1.25 (1.25 usados por cada 0km)'
    })

    diccionario.append({
        'Variable': 'Δratio_prendas_inscripciones',
        'Tipo': 'Variación de Ratio',
        'Cálculo/Descripción': 'Δ = (Ratio_t - Ratio_{t-1}) / Ratio_{t-1}. Cambio en nivel de financiamiento',
        'Ejemplo': '0.10 (10% más financiamiento)'
    })

    # PROPORCIONES (MARKET SHARE)
    diccionario.append({
        'Variable': 'prop_*',
        'Tipo': 'Proporción',
        'Cálculo/Descripción': 'operaciones_X / total_operaciones. Market share de provincia/marca (ej: prop_buenos_aires)',
        'Ejemplo': '0.30 (30% del total)'
    })

    diccionario.append({
        'Variable': 'Δprop_*',
        'Tipo': 'Variación de Proporción',
        'Cálculo/Descripción': 'prop_X_t - prop_X_{t-1}. Cambio en market share (diferencia absoluta, no %)',
        'Ejemplo': '0.02 (ganó 2 puntos porcentuales)'
    })

    # LAGS DEL TARGET
    diccionario.append({
        'Variable': 'total_operaciones_lag1',
        'Tipo': 'Lag',
        'Cálculo/Descripción': 'total_operaciones_{t-1}. Valor del target en el mes anterior',
        'Ejemplo': '48000'
    })

    diccionario.append({
        'Variable': 'total_operaciones_lag2',
        'Tipo': 'Lag',
        'Cálculo/Descripción': 'total_operaciones_{t-2}. Valor del target hace 2 meses',
        'Ejemplo': '47000'
    })

    diccionario.append({
        'Variable': 'total_operaciones_lag3',
        'Tipo': 'Lag',
        'Cálculo/Descripción': 'total_operaciones_{t-3}. Valor del target hace 3 meses',
        'Ejemplo': '46000'
    })

    diccionario.append({
        'Variable': 'total_operaciones_lag6',
        'Tipo': 'Lag',
        'Cálculo/Descripción': 'total_operaciones_{t-6}. Valor del target hace 6 meses',
        'Ejemplo': '45000'
    })

    diccionario.append({
        'Variable': 'total_operaciones_lag12',
        'Tipo': 'Lag',
        'Cálculo/Descripción': 'total_operaciones_{t-12}. Valor del target hace 12 meses (mismo mes año anterior)',
        'Ejemplo': '44000'
    })

    # ROLLING MEANS
    diccionario.append({
        'Variable': 'total_operaciones_rolling3',
        'Tipo': 'Rolling Mean',
        'Cálculo/Descripción': 'Promedio móvil de últimos 3 meses del target',
        'Ejemplo': '47000'
    })

    diccionario.append({
        'Variable': 'total_operaciones_rolling6',
        'Tipo': 'Rolling Mean',
        'Cálculo/Descripción': 'Promedio móvil de últimos 6 meses del target',
        'Ejemplo': '46000'
    })

    diccionario.append({
        'Variable': 'total_operaciones_rolling12',
        'Tipo': 'Rolling Mean',
        'Cálculo/Descripción': 'Promedio móvil de últimos 12 meses del target',
        'Ejemplo': '45000'
    })

    # LAGS DE FEATURES AVANZADAS
    diccionario.append({
        'Variable': '*_lag1, *_lag2, *_lag3',
        'Tipo': 'Lags de Features',
        'Cálculo/Descripción': 'Lags de 1, 2, 3 meses de variaciones macro, ratios y proporciones',
        'Ejemplo': 'Δtipo_de_cambio_usd_prom_lag1 = valor hace 1 mes'
    })

    # FEATURES TEMPORALES
    diccionario.append({
        'Variable': 'mes',
        'Tipo': 'Temporal',
        'Cálculo/Descripción': 'Mes del año (1=Enero, 12=Diciembre)',
        'Ejemplo': '3 (Marzo)'
    })

    diccionario.append({
        'Variable': 'trimestre',
        'Tipo': 'Temporal',
        'Cálculo/Descripción': 'Trimestre del año (1, 2, 3, 4)',
        'Ejemplo': '1 (Q1)'
    })

    diccionario.append({
        'Variable': 'anio',
        'Tipo': 'Temporal',
        'Cálculo/Descripción': 'Año',
        'Ejemplo': '2019'
    })

    diccionario.append({
        'Variable': 'semestre',
        'Tipo': 'Temporal',
        'Cálculo/Descripción': 'Semestre del año (1=Ene-Jun, 2=Jul-Dic)',
        'Ejemplo': '1'
    })

    return pd.DataFrame(diccionario)


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("EXPORTAR DATASET A EXCEL PARA ANÁLISIS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 1. Cargar dataset
    print(f"\n📂 Cargando: {INPUT_FILE}")
    df = pd.read_parquet(INPUT_FILE)

    print(f"   ✓ {len(df)} registros")
    print(f"   ✓ {len(df.columns)} columnas")
    print(f"   ✓ Período: {df['fecha'].min()} a {df['fecha'].max()}")

    # 2. Seleccionar primeras 100 filas
    n_rows = min(100, len(df))
    df_export = df.head(n_rows).copy()

    print(f"\n📊 Exportando {n_rows} filas")

    # 3. Crear diccionario de variables
    print(f"\n📝 Creando diccionario de variables...")
    df_diccionario = crear_diccionario_variables()
    print(f"   ✓ {len(df_diccionario)} tipos de variables documentadas")

    # 4. Exportar a Excel con dos hojas
    print(f"\n💾 Guardando en Excel: {OUTPUT_FILE}")

    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        # Hoja 1: Datos
        df_export.to_excel(writer, sheet_name='Datos', index=False)
        print(f"   ✓ Hoja 'Datos': {n_rows} filas × {len(df_export.columns)} columnas")

        # Hoja 2: Diccionario
        df_diccionario.to_excel(writer, sheet_name='Diccionario', index=False)
        print(f"   ✓ Hoja 'Diccionario': {len(df_diccionario)} tipos de variables")

    # 5. Resumen
    print("\n" + "="*80)
    print("✅ EXPORTACIÓN COMPLETADA")
    print("="*80)

    print(f"\n📄 Archivo generado: {OUTPUT_FILE}")
    print(f"\n📊 Contenido:")
    print(f"   - Hoja 'Datos': Primeras {n_rows} filas del dataset")
    print(f"   - Hoja 'Diccionario': Documentación de cada tipo de variable")

    print(f"\n💡 Variables principales en el dataset:")
    print(f"   - Target: total_operaciones")
    print(f"   - Tipos de operación: 3 (inscripciones, transferencias, prendas)")
    print(f"   - Variables macro: {len([c for c in df.columns if c in ['tipo_de_cambio_usd_prom', 'BADLAR', 'IPC_mensual', 'LELIQ', 'EMAE', 'reservas_internacionales']])}")
    print(f"   - Variaciones porcentuales: {len([c for c in df.columns if c.startswith('Δ')])}")
    print(f"   - Ratios: {len([c for c in df.columns if 'ratio_' in c])}")
    print(f"   - Proporciones: {len([c for c in df.columns if c.startswith('prop_')])}")
    print(f"   - Lags: {len([c for c in df.columns if '_lag' in c])}")
    print(f"   - Rolling means: {len([c for c in df.columns if '_rolling' in c])}")
    print(f"   - Temporales: 4 (mes, trimestre, anio, semestre)")

    print(f"\n" + "="*80)


if __name__ == "__main__":
    main()
