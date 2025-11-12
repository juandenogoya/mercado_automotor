#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script maestro para ejecutar toda la pipeline de datos para forecasting.

Ejecuta en secuencia:
1. Unificación de datos transaccionales (inscripciones + transferencias + prendas)
2. Descarga de datos BCRA (variables macroeconómicas)
3. Descarga de datos INDEC (actividad económica)
4. Unificación de todos los datasets para forecasting

Uso:
    # Pipeline completa:
    python backend/data_processing/ejecutar_pipeline_completa.py

    # Solo dataset transaccional:
    python backend/data_processing/ejecutar_pipeline_completa.py --solo-transaccional

    # Solo APIs (BCRA + INDEC):
    python backend/data_processing/ejecutar_pipeline_completa.py --solo-apis

    # Sin unificación final:
    python backend/data_processing/ejecutar_pipeline_completa.py --sin-unificacion
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import argparse


def ejecutar_script(script_path, nombre, args=None):
    """
    Ejecuta un script Python y captura su resultado.

    Args:
        script_path: Ruta al script
        nombre: Nombre descriptivo para logs
        args: Argumentos adicionales para el script

    Returns:
        True si exitoso, False si falló
    """
    comando = [sys.executable, str(script_path)]
    if args:
        comando.extend(args)

    print(f"\n{'='*80}")
    print(f"  EJECUTANDO: {nombre}")
    print('='*80)
    print(f"Comando: {' '.join(comando)}\n")

    try:
        result = subprocess.run(
            comando,
            cwd=Path(__file__).parent.parent.parent,
            capture_output=False,
            text=True,
            check=True
        )

        print(f"\n✅ {nombre} completado exitosamente")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error en {nombre}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error inesperado en {nombre}: {e}")
        return False


def main():
    """Función principal."""

    # Parser de argumentos
    parser = argparse.ArgumentParser(
        description='Ejecutar pipeline completa de datos para forecasting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:

  # Pipeline completa (recomendado):
  python backend/data_processing/ejecutar_pipeline_completa.py

  # Solo generar dataset transaccional:
  python backend/data_processing/ejecutar_pipeline_completa.py --solo-transaccional

  # Solo descargar APIs (BCRA + INDEC):
  python backend/data_processing/ejecutar_pipeline_completa.py --solo-apis

  # Generar datasets base sin unificar:
  python backend/data_processing/ejecutar_pipeline_completa.py --sin-unificacion
        """
    )

    parser.add_argument(
        '--solo-transaccional',
        action='store_true',
        help='Solo ejecutar script de dataset transaccional'
    )

    parser.add_argument(
        '--solo-apis',
        action='store_true',
        help='Solo ejecutar scripts de APIs (BCRA + INDEC)'
    )

    parser.add_argument(
        '--sin-unificacion',
        action='store_true',
        help='No ejecutar script de unificación final'
    )

    args = parser.parse_args()

    # Banner inicial
    print("\n" + "="*80)
    print("  PIPELINE COMPLETA DE DATOS PARA FORECASTING")
    print("="*80)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Paths de scripts
    base_path = Path(__file__).parent
    scripts = {
        'transaccional': base_path / '02_unir_datasets_v3.py',
        'bcra': base_path / '04_obtener_datos_bcra_v2.py',
        'indec': base_path / '05_obtener_datos_indec.py',
        'unificacion': base_path / '07_unificar_datasets_forecasting.py'
    }

    # Verificar que existan los scripts
    for nombre, path in scripts.items():
        if not path.exists():
            print(f"❌ Script no encontrado: {path}")
            return False

    # Resultados
    resultados = {
        'total': 0,
        'exitosos': 0,
        'fallidos': 0,
        'detalles': []
    }

    # Determinar qué ejecutar
    ejecutar = {
        'transaccional': not args.solo_apis,
        'bcra': not args.solo_transaccional,
        'indec': not args.solo_transaccional,
        'unificacion': not (args.sin_unificacion or args.solo_transaccional or args.solo_apis)
    }

    # Pipeline
    pipeline = []

    if ejecutar['transaccional']:
        pipeline.append(('Dataset Transaccional (Inscripciones + Transferencias + Prendas)', scripts['transaccional']))

    if ejecutar['bcra']:
        pipeline.append(('Datos BCRA (Variables Macroeconómicas)', scripts['bcra']))

    if ejecutar['indec']:
        pipeline.append(('Datos INDEC (Actividad Económica)', scripts['indec']))

    if ejecutar['unificacion']:
        pipeline.append(('Unificación de Datasets para Forecasting', scripts['unificacion']))

    # Mostrar plan
    print(f"\n📋 Pipeline a ejecutar ({len(pipeline)} pasos):")
    for i, (nombre, _) in enumerate(pipeline, 1):
        print(f"   {i}. {nombre}")

    # Confirmar
    print(f"\n⏱️  Tiempo estimado:")
    if ejecutar['transaccional']:
        print(f"   - Dataset transaccional: ~5 minutos")
    if ejecutar['bcra']:
        print(f"   - Datos BCRA: ~30 segundos")
    if ejecutar['indec']:
        print(f"   - Datos INDEC: ~30 segundos")
    if ejecutar['unificacion']:
        print(f"   - Unificación: ~1 minuto")

    # Ejecutar pipeline
    for nombre, script_path in pipeline:
        resultados['total'] += 1
        exito = ejecutar_script(script_path, nombre)

        if exito:
            resultados['exitosos'] += 1
            resultados['detalles'].append((nombre, '✅ Exitoso'))
        else:
            resultados['fallidos'] += 1
            resultados['detalles'].append((nombre, '❌ Fallido'))
            print(f"\n⚠️  Deteniendo pipeline por error en: {nombre}")
            break

    # Resumen final
    print("\n" + "="*80)
    print("  RESUMEN DE EJECUCIÓN")
    print("="*80)

    print(f"\n📊 Estadísticas:")
    print(f"   - Total de pasos: {resultados['total']}")
    print(f"   - Exitosos: {resultados['exitosos']}")
    print(f"   - Fallidos: {resultados['fallidos']}")

    print(f"\n📋 Detalle:")
    for nombre, estado in resultados['detalles']:
        print(f"   {estado} {nombre}")

    if resultados['fallidos'] == 0:
        print(f"\n🎉 PIPELINE COMPLETADA EXITOSAMENTE")

        if ejecutar['unificacion']:
            print(f"\n📁 Dataset final generado:")
            print(f"   data/processed/dataset_forecasting_completo.parquet")
            print(f"\n🎯 Listo para entrenar modelos de forecasting!")
        else:
            print(f"\n📁 Datasets base generados:")
            if ejecutar['transaccional']:
                print(f"   - data/processed/dataset_transaccional_unificado.parquet")
            if ejecutar['bcra']:
                print(f"   - data/processed/bcra_datos_mensuales.parquet")
            if ejecutar['indec']:
                print(f"   - data/processed/indec_datos_mensuales.parquet")

    else:
        print(f"\n❌ PIPELINE INCOMPLETA")
        print(f"   Algunos pasos fallaron. Revisa los logs arriba.")

    print("\n" + "="*80 + "\n")

    # Exit code
    sys.exit(0 if resultados['fallidos'] == 0 else 1)


if __name__ == "__main__":
    main()
