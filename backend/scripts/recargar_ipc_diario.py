"""
Script para limpiar y re-expandir IPC diario con valores correctos.

Este script:
1. Elimina todos los registros de ipc_diario
2. Llama al script expandir_ipc_diario.py para re-expandir
3. Verifica que los valores sean correctos

Uso:
    python backend/scripts/recargar_ipc_diario.py
    python backend/scripts/recargar_ipc_diario.py --export-excel ipc_diario_corregido.xlsx
"""
import sys
import argparse
import subprocess
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.utils.database import get_db
from backend.models.ipc_diario import IPCDiario


def limpiar_ipc_diario():
    """Elimina todos los registros de ipc_diario."""
    logger.info("="*80)
    logger.info("LIMPIANDO TABLA IPC_DIARIO")
    logger.info("="*80)

    with get_db() as db:
        count_antes = db.query(IPCDiario).count()
        logger.info(f"\n  Registros actuales: {count_antes:,}")

        if count_antes > 0:
            logger.warning(f"\n  Eliminando {count_antes:,} registros...")
            db.query(IPCDiario).delete()
            db.commit()
            logger.success(f"  ✓ {count_antes:,} registros eliminados")
        else:
            logger.info("  Tabla ya está vacía")

    return count_antes


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Limpiar y re-expandir IPC diario con valores correctos"
    )

    parser.add_argument(
        '--export-excel',
        type=str,
        default='ipc_diario_corregido.xlsx',
        help='Nombre del archivo Excel a exportar (default: ipc_diario_corregido.xlsx)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger()

    logger.info("="*80)
    logger.info("🔄 RECARGAR IPC DIARIO CON VALORES CORRECTOS")
    logger.info("="*80)

    # Paso 1: Limpiar tabla
    deleted_count = limpiar_ipc_diario()

    # Paso 2: Llamar al script de expansión
    logger.info("\n" + "="*80)
    logger.info("RE-EXPANDIENDO IPC MENSUAL A DIARIO")
    logger.info("="*80)

    cmd = [
        sys.executable,  # python
        "manage.py",
        "expandir-ipc-diario",
        "--export-excel", args.export_excel
    ]

    logger.info(f"\nEjecutando: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=root_dir)

    if result.returncode != 0:
        logger.error("\n❌ Error ejecutando expansión")
        sys.exit(1)

    # Paso 3: Verificar resultados
    logger.info("\n" + "="*80)
    logger.info("VERIFICACIÓN FINAL")
    logger.info("="*80)

    with get_db() as db:
        count_total = db.query(IPCDiario).count()
        count_con_valores = db.query(IPCDiario).filter(IPCDiario.ipc_mensual > 0).count()
        count_cero = db.query(IPCDiario).filter(IPCDiario.ipc_mensual == 0).count()

        logger.info(f"\n📊 Estadísticas:")
        logger.info(f"  Registros eliminados: {deleted_count:,}")
        logger.info(f"  Registros totales ahora: {count_total:,}")
        logger.info(f"  Registros con IPC > 0: {count_con_valores:,}")
        logger.info(f"  Registros con IPC = 0: {count_cero:,}")

        if count_cero == 0 and count_con_valores > 0:
            logger.success(f"\n✅ PERFECTO: Todos los registros tienen IPC > 0")
            logger.success(f"✅ Excel exportado: {args.export_excel}")
        elif count_cero > 0:
            logger.error(f"\n❌ PROBLEMA: Aún hay {count_cero:,} registros con IPC = 0")
            logger.error("Verifica que ejecutaste: python backend/scripts/calcular_variaciones_ipc.py")
        else:
            logger.warning("\n⚠️  No se generaron registros")

    logger.info("\n" + "="*80)


if __name__ == "__main__":
    main()
