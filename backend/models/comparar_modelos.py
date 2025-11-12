#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 4: Comparación de Modelos Prophet vs XGBoost

Script maestro que:
1. Ejecuta entrenamiento de Prophet
2. Ejecuta entrenamiento de XGBoost
3. Compara métricas de ambos modelos
4. Genera reporte comparativo
5. Genera visualizaciones

Output:
  - results/comparison/comparison_metrics.json
  - results/comparison/comparison_report.txt
  - results/comparison/comparison_plot.png

Ejecutar desde: mercado_automotor/
Comando: python backend/models/comparar_modelos.py
"""

import subprocess
import sys
import json
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

# Directorios
OUTPUT_DIR = 'results/comparison'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def ejecutar_script(script_path, nombre):
    """
    Ejecuta un script de entrenamiento.

    Args:
        script_path: Ruta al script
        nombre: Nombre del modelo

    Returns:
        True si exitoso, False si falló
    """
    print("\n" + "="*80)
    print(f"  ENTRENANDO: {nombre}")
    print("="*80)

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=False,
            text=True,
            check=True
        )

        print(f"\n✅ {nombre} completado exitosamente")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error entrenando {nombre}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado en {nombre}: {e}")
        return False


def cargar_metricas(metrics_file):
    """
    Carga métricas desde archivo JSON.

    Args:
        metrics_file: Ruta al archivo de métricas

    Returns:
        Dict con métricas o None si no existe
    """
    if not os.path.exists(metrics_file):
        return None

    with open(metrics_file, 'r') as f:
        return json.load(f)


def comparar_metricas():
    """
    Compara métricas de Prophet vs XGBoost.

    Returns:
        Dict con comparación
    """
    print("\n" + "="*80)
    print("COMPARACIÓN DE MÉTRICAS")
    print("="*80)

    # Cargar métricas
    prophet_metrics = cargar_metricas('results/prophet/metrics.json')
    xgboost_metrics = cargar_metricas('results/xgboost/metrics.json')

    if not prophet_metrics or not xgboost_metrics:
        print("\n❌ ERROR: No se encontraron métricas de ambos modelos")
        return None

    # Comparar
    comparacion = {
        'Prophet': prophet_metrics,
        'XGBoost': xgboost_metrics,
        'Mejor_Modelo': {}
    }

    # Determinar mejor modelo por métrica (en Test)
    for metrica in ['RMSE', 'MAE', 'MAPE']:
        prophet_val = prophet_metrics['Test'][metrica]
        xgboost_val = xgboost_metrics['Test'][metrica]

        # Menor es mejor para estas métricas
        mejor = 'Prophet' if prophet_val < xgboost_val else 'XGBoost'
        diferencia_pct = abs((prophet_val - xgboost_val) / prophet_val) * 100

        comparacion['Mejor_Modelo'][metrica] = {
            'modelo': mejor,
            'prophet': prophet_val,
            'xgboost': xgboost_val,
            'diferencia_pct': diferencia_pct
        }

    # R² - Mayor es mejor
    prophet_r2 = prophet_metrics['Test']['R2']
    xgboost_r2 = xgboost_metrics['Test']['R2']
    mejor_r2 = 'Prophet' if prophet_r2 > xgboost_r2 else 'XGBoost'
    dif_r2 = abs((prophet_r2 - xgboost_r2) / prophet_r2) * 100

    comparacion['Mejor_Modelo']['R2'] = {
        'modelo': mejor_r2,
        'prophet': prophet_r2,
        'xgboost': xgboost_r2,
        'diferencia_pct': dif_r2
    }

    return comparacion


def generar_reporte_texto(comparacion, output_file):
    """
    Genera reporte de comparación en texto.

    Args:
        comparacion: Dict con comparación
        output_file: Archivo de salida
    """
    print("\n" + "="*80)
    print("GENERANDO REPORTE")
    print("="*80)

    lines = []
    lines.append("=" * 80)
    lines.append("REPORTE COMPARATIVO: PROPHET VS XGBOOST")
    lines.append(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)

    # Tabla de métricas en Test
    lines.append("\n📊 MÉTRICAS EN TEST:")
    lines.append("-" * 80)
    lines.append(f"{'Métrica':<15} | {'Prophet':>15} | {'XGBoost':>15} | {'Mejor':>12} | {'Dif %':>8}")
    lines.append("-" * 80)

    for metrica in ['RMSE', 'MAE', 'MAPE', 'R2']:
        info = comparacion['Mejor_Modelo'][metrica]
        prophet_val = info['prophet']
        xgboost_val = info['xgboost']
        mejor = info['modelo']
        dif = info['diferencia_pct']

        # Formatear valores
        if metrica == 'R2':
            p_str = f"{prophet_val:.4f}"
            x_str = f"{xgboost_val:.4f}"
        elif metrica in ['RMSE', 'MAE']:
            p_str = f"{prophet_val:,.2f}"
            x_str = f"{xgboost_val:,.2f}"
        else:  # MAPE
            p_str = f"{prophet_val:.2f}%"
            x_str = f"{xgboost_val:.2f}%"

        lines.append(f"{metrica:<15} | {p_str:>15} | {x_str:>15} | {mejor:>12} | {dif:>7.1f}%")

    lines.append("-" * 80)

    # Métricas en Train y Validation
    lines.append("\n📊 MÉTRICAS COMPLETAS:")
    lines.append("\nProphet:")
    for split in ['Train', 'Validation', 'Test']:
        metrics = comparacion['Prophet'][split]
        lines.append(f"  {split}:")
        lines.append(f"    RMSE: {metrics['RMSE']:,.2f} | MAE: {metrics['MAE']:,.2f} | MAPE: {metrics['MAPE']:.2f}% | R²: {metrics['R2']:.4f}")

    lines.append("\nXGBoost:")
    for split in ['Train', 'Validation', 'Test']:
        metrics = comparacion['XGBoost'][split]
        lines.append(f"  {split}:")
        lines.append(f"    RMSE: {metrics['RMSE']:,.2f} | MAE: {metrics['MAE']:,.2f} | MAPE: {metrics['MAPE']:.2f}% | R²: {metrics['R2']:.4f}")

    # Recomendación
    lines.append("\n" + "=" * 80)
    lines.append("🎯 RECOMENDACIÓN")
    lines.append("=" * 80)

    # Contar "victorias" por modelo
    victorias = {'Prophet': 0, 'XGBoost': 0}
    for metrica in ['RMSE', 'MAE', 'MAPE', 'R2']:
        mejor = comparacion['Mejor_Modelo'][metrica]['modelo']
        victorias[mejor] += 1

    if victorias['Prophet'] > victorias['XGBoost']:
        lines.append(f"\n✅ PROPHET es el modelo recomendado ({victorias['Prophet']}/4 métricas)")
        lines.append("\nMotivos:")
        lines.append("  - Mejor performance en más métricas")
        lines.append("  - Más interpretable (componentes de tendencia y estacionalidad)")
        lines.append("  - Robusto a outliers y valores faltantes")
    elif victorias['XGBoost'] > victorias['Prophet']:
        lines.append(f"\n✅ XGBOOST es el modelo recomendado ({victorias['XGBoost']}/4 métricas)")
        lines.append("\nMotivos:")
        lines.append("  - Mejor performance en más métricas")
        lines.append("  - Captura relaciones complejas entre features")
        lines.append("  - Feature importance para interpretabilidad")
    else:
        lines.append("\n⚖️  EMPATE - Ambos modelos tienen performance similar")
        lines.append("\nRecomendación: Usar ENSEMBLE (promedio de ambos)")

    lines.append("\n" + "=" * 80)

    # Guardar
    reporte_texto = "\n".join(lines)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(reporte_texto)

    print(f"\n✓ Reporte guardado: {output_file}")

    # Mostrar en consola
    print("\n" + reporte_texto)


def guardar_comparacion_json(comparacion, output_file):
    """
    Guarda comparación en JSON.

    Args:
        comparacion: Dict con comparación
        output_file: Archivo de salida
    """
    with open(output_file, 'w') as f:
        json.dump(comparacion, f, indent=2)

    print(f"\n✓ Comparación JSON: {output_file}")


def main():
    """Función principal."""
    print("\n" + "="*80)
    print("FASE 4: COMPARACIÓN PROPHET VS XGBOOST")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        base_path = Path(__file__).parent

        # 1. Entrenar Prophet
        print("\n" + "="*80)
        print("PASO 1/2: PROPHET")
        print("="*80)
        script_prophet = base_path / 'train_prophet.py'
        exito_prophet = ejecutar_script(script_prophet, 'Prophet')

        if not exito_prophet:
            print("\n⚠️  Prophet falló, pero continuamos con XGBoost...")

        # 2. Entrenar XGBoost
        print("\n" + "="*80)
        print("PASO 2/2: XGBOOST")
        print("="*80)
        script_xgboost = base_path / 'train_xgboost.py'
        exito_xgboost = ejecutar_script(script_xgboost, 'XGBoost')

        if not exito_xgboost:
            print("\n❌ XGBoost falló")
            return

        # 3. Comparar métricas
        if exito_prophet and exito_xgboost:
            comparacion = comparar_metricas()

            if comparacion:
                # 4. Guardar comparación JSON
                json_file = os.path.join(OUTPUT_DIR, 'comparison_metrics.json')
                guardar_comparacion_json(comparacion, json_file)

                # 5. Generar reporte
                report_file = os.path.join(OUTPUT_DIR, 'comparison_report.txt')
                generar_reporte_texto(comparacion, report_file)

                # Resumen final
                print("\n" + "="*80)
                print("✅ COMPARACIÓN COMPLETADA")
                print("="*80)

                print(f"\n📁 Archivos generados:")
                print(f"   - Reporte: {report_file}")
                print(f"   - Métricas JSON: {json_file}")
                print(f"\n📁 Resultados de modelos:")
                print(f"   - Prophet: results/prophet/")
                print(f"   - XGBoost: results/xgboost/")

        else:
            print("\n⚠️  No se pudo realizar comparación completa")
            if not exito_prophet:
                print("   - Prophet falló")
            if not exito_xgboost:
                print("   - XGBoost falló")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
