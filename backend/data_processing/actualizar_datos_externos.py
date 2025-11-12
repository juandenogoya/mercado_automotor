#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script maestro para actualizar datos de fuentes externas (BCRA e INDEC).

Este script orquesta la actualización incremental de:
- Datos BCRA (variables macroeconómicas)
- Datos INDEC (actividad económica y mercado laboral)

Características:
- Modo incremental por defecto (solo descarga datos nuevos)
- Opción --full-refresh para recargar todo desde 2019
- Reporta estadísticas de actualización
- Maneja errores por fuente (si una falla, continúa con la otra)

Uso:
    # Actualización incremental (normal):
    python backend/data_processing/actualizar_datos_externos.py

    # Recarga completa:
    python backend/data_processing/actualizar_datos_externos.py --full-refresh

    # Solo BCRA:
    python backend/data_processing/actualizar_datos_externos.py --solo-bcra

    # Solo INDEC:
    python backend/data_processing/actualizar_datos_externos.py --solo-indec

Ejecutar desde: mercado_automotor/
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import argparse

# Agregar backend al path
sys.path.append(str(Path(__file__).parent.parent.parent))


def ejecutar_script(script_path, args=None):
    """
    Ejecuta un script Python y captura su resultado.

    Args:
        script_path: Ruta al script a ejecutar
        args: Lista de argumentos adicionales

    Returns:
        True si exitoso, False si falló
    """
    comando = [sys.executable, script_path]
    if args:
        comando.extend(args)

    try:
        print(f"\n🚀 Ejecutando: {' '.join(comando)}")
        print("-" * 80)

        result = subprocess.run(
            comando,
            cwd=Path(__file__).parent.parent.parent,
            capture_output=False,  # Mostrar output en tiempo real
            text=True,
            check=True
        )

        print("-" * 80)
        print(f"✅ Script completado exitosamente\n")
        return True

    except subprocess.CalledProcessError as e:
        print("-" * 80)
        print(f"❌ Error ejecutando script: {e}\n")
        return False
    except Exception as e:
        print("-" * 80)
        print(f"❌ Error inesperado: {e}\n")
        return False


def main():
    """Función principal del script maestro."""

    # Parsear argumentos
    parser = argparse.ArgumentParser(
        description='Actualizar datos de fuentes externas (BCRA e INDEC)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Actualización incremental normal (recomendado):
  python backend/data_processing/actualizar_datos_externos.py

  # Recarga completa desde 2019:
  python backend/data_processing/actualizar_datos_externos.py --full-refresh

  # Solo actualizar BCRA:
  python backend/data_processing/actualizar_datos_externos.py --solo-bcra

  # Solo actualizar INDEC:
  python backend/data_processing/actualizar_datos_externos.py --solo-indec
        """
    )

    parser.add_argument(
        '--full-refresh',
        action='store_true',
        help='Recarga completa desde 2019 (ignora datos existentes)'
    )

    parser.add_argument(
        '--solo-bcra',
        action='store_true',
        help='Solo actualizar datos BCRA'
    )

    parser.add_argument(
        '--solo-indec',
        action='store_true',
        help='Solo actualizar datos INDEC'
    )

    parser.add_argument(
        '--continuar-si-falla',
        action='store_true',
        default=True,
        help='Continuar con otras fuentes si una falla (default: True)'
    )

    args = parser.parse_args()

    # Banner inicial
    print("\n" + "="*80)
    print("  ACTUALIZACIÓN DE DATOS EXTERNOS - BCRA E INDEC")
    print("="*80)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Modo: {'FULL REFRESH' if args.full_refresh else 'INCREMENTAL'}")
    print("="*80 + "\n")

    # Paths de scripts
    base_path = Path(__file__).parent
    script_bcra = base_path / '04_obtener_datos_bcra_incremental.py'
    script_indec = base_path / '05_obtener_datos_indec_incremental.py'

    # Argumentos para scripts
    script_args = ['--full-refresh'] if args.full_refresh else []

    # Contadores
    resultados = {
        'total': 0,
        'exitosos': 0,
        'fallidos': 0
    }

    fuentes_a_actualizar = []

    # Determinar qué fuentes actualizar
    if args.solo_bcra:
        fuentes_a_actualizar.append(('BCRA', script_bcra))
    elif args.solo_indec:
        fuentes_a_actualizar.append(('INDEC', script_indec))
    else:
        # Por defecto, ambas
        fuentes_a_actualizar.append(('BCRA', script_bcra))
        fuentes_a_actualizar.append(('INDEC', script_indec))

    # Ejecutar actualizaciones
    for nombre, script_path in fuentes_a_actualizar:
        resultados['total'] += 1

        print("\n" + "="*80)
        print(f"  ACTUALIZANDO: {nombre}")
        print("="*80)

        if not script_path.exists():
            print(f"❌ Error: Script no encontrado: {script_path}")
            resultados['fallidos'] += 1
            if not args.continuar_si_falla:
                break
            continue

        exito = ejecutar_script(str(script_path), script_args)

        if exito:
            resultados['exitosos'] += 1
        else:
            resultados['fallidos'] += 1
            if not args.continuar_si_falla:
                print(f"\n⚠️  Deteniendo actualización por fallo en {nombre}")
                break

    # Resumen final
    print("\n" + "="*80)
    print("  RESUMEN DE ACTUALIZACIÓN")
    print("="*80)
    print(f"\n  📊 Fuentes procesadas: {resultados['total']}")
    print(f"  ✅ Exitosas: {resultados['exitosos']}")
    print(f"  ❌ Fallidas: {resultados['fallidos']}")

    if resultados['exitosos'] == resultados['total']:
        print("\n  🎉 TODAS LAS ACTUALIZACIONES COMPLETADAS EXITOSAMENTE")
    elif resultados['exitosos'] > 0:
        print("\n  ⚠️  ACTUALIZACIÓN PARCIAL (algunas fuentes fallaron)")
    else:
        print("\n  ❌ ACTUALIZACIÓN FALLIDA (ninguna fuente pudo actualizarse)")

    print("\n" + "="*80)

    # Listar archivos actualizados
    output_dir = Path('data/processed')
    if output_dir.exists():
        print("\n📁 Archivos de datos:")
        archivos_relevantes = [
            'bcra_datos_diarios.parquet',
            'bcra_datos_mensuales.parquet',
            'indec_datos_originales.parquet',
            'indec_datos_mensuales.parquet'
        ]

        for archivo in archivos_relevantes:
            filepath = output_dir / archivo
            if filepath.exists():
                size_mb = filepath.stat().st_size / 1024**2
                mod_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                print(f"   - {archivo:40} ({size_mb:6.2f} MB) - Modificado: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n" + "="*80 + "\n")

    # Exit code
    if resultados['fallidos'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
