"""
Script para cargar datos macroeconómicos en PostgreSQL.

Fuentes:
- IPC: INDEC API
- BADLAR: BCRA API
- Tipo de Cambio: BCRA API

Uso:
    # Cargar todos los datos (últimos 5 años)
    python backend/scripts/cargar_datos_macro.py --all

    # Cargar solo IPC
    python backend/scripts/cargar_datos_macro.py --ipc

    # Cargar solo BADLAR
    python backend/scripts/cargar_datos_macro.py --badlar

    # Cargar solo Tipo de Cambio
    python backend/scripts/cargar_datos_macro.py --tipo-cambio

    # Cargar con rango personalizado
    python backend/scripts/cargar_datos_macro.py --all --desde 2019-01-01 --hasta 2024-12-31

    # Carga histórica completa (desde 2016)
    python backend/scripts/cargar_datos_macro.py --all --historico
"""
import sys
import argparse
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path

# Agregar el directorio raíz al path para imports
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from loguru import logger
from backend.config.logger import setup_logger
from backend.api_clients.indec_client import INDECClient
from backend.api_clients.bcra_client import BCRAClient
from backend.utils.database import init_db


def cargar_ipc(fecha_desde: date, fecha_hasta: date) -> dict:
    """
    Carga datos de IPC desde INDEC.

    Args:
        fecha_desde: Fecha inicial
        fecha_hasta: Fecha final

    Returns:
        Dict con resultado de la carga
    """
    logger.info("=" * 80)
    logger.info("CARGANDO IPC (INDEC)")
    logger.info("=" * 80)

    client = INDECClient()
    result = client.sync_ipc(fecha_desde, fecha_hasta)

    logger.info(f"Resultado: {result['records_saved']} registros guardados")
    logger.info("")

    return result


def cargar_badlar(fecha_desde: date, fecha_hasta: date) -> dict:
    """
    Carga datos de BADLAR desde BCRA.

    Args:
        fecha_desde: Fecha inicial
        fecha_hasta: Fecha final

    Returns:
        Dict con resultado de la carga
    """
    logger.info("=" * 80)
    logger.info("CARGANDO BADLAR (BCRA)")
    logger.info("=" * 80)

    client = BCRAClient()
    result = client.sync_badlar(fecha_desde, fecha_hasta)

    logger.info(f"Resultado: {result['records_saved']} registros guardados")
    logger.info("")

    return result


def cargar_tipo_cambio(fecha_desde: date, fecha_hasta: date) -> dict:
    """
    Carga datos de Tipo de Cambio desde BCRA.

    Args:
        fecha_desde: Fecha inicial
        fecha_hasta: Fecha final

    Returns:
        Dict con resultado de la carga
    """
    logger.info("=" * 80)
    logger.info("CARGANDO TIPO DE CAMBIO (BCRA)")
    logger.info("=" * 80)

    client = BCRAClient()
    result = client.sync_tipo_cambio(fecha_desde, fecha_hasta)

    logger.info(f"Resultado: {result['records_saved']} registros guardados")
    logger.info("")

    return result


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Cargar datos macroeconómicos en PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Cargar todos los datos (últimos 5 años)
  python backend/scripts/cargar_datos_macro.py --all

  # Cargar solo IPC
  python backend/scripts/cargar_datos_macro.py --ipc

  # Cargar con rango personalizado
  python backend/scripts/cargar_datos_macro.py --all --desde 2019-01-01 --hasta 2024-12-31

  # Carga histórica completa (desde 2016)
  python backend/scripts/cargar_datos_macro.py --all --historico
        """
    )

    # Opciones de datos a cargar
    parser.add_argument('--all', action='store_true', help='Cargar todos los datos macroeconómicos')
    parser.add_argument('--ipc', action='store_true', help='Cargar solo IPC')
    parser.add_argument('--badlar', action='store_true', help='Cargar solo BADLAR')
    parser.add_argument('--tipo-cambio', action='store_true', help='Cargar solo Tipo de Cambio')

    # Opciones de rango de fechas
    parser.add_argument('--desde', type=str, help='Fecha inicial (YYYY-MM-DD)')
    parser.add_argument('--hasta', type=str, help='Fecha final (YYYY-MM-DD, default: hoy)')
    parser.add_argument('--historico', action='store_true', help='Carga histórica completa (desde 2016)')

    args = parser.parse_args()

    # Setup logging
    setup_logger()

    # Verificar que se especificó al menos una opción
    if not any([args.all, args.ipc, args.badlar, args.tipo_cambio]):
        parser.print_help()
        logger.error("\n❌ Debes especificar al menos una opción: --all, --ipc, --badlar o --tipo-cambio")
        sys.exit(1)

    # Inicializar base de datos (crear tablas si no existen)
    logger.info("Inicializando base de datos...")
    init_db()
    logger.success("✓ Base de datos inicializada\n")

    # Determinar rango de fechas
    if args.historico:
        fecha_desde = date(2016, 1, 1)
        fecha_hasta = date.today()
        logger.info(f"📅 Modo histórico: Desde {fecha_desde} hasta {fecha_hasta}")
    elif args.desde:
        try:
            fecha_desde = datetime.strptime(args.desde, '%Y-%m-%d').date()
        except ValueError:
            logger.error("❌ Formato de fecha inválido para --desde. Usa YYYY-MM-DD")
            sys.exit(1)

        if args.hasta:
            try:
                fecha_hasta = datetime.strptime(args.hasta, '%Y-%m-%d').date()
            except ValueError:
                logger.error("❌ Formato de fecha inválido para --hasta. Usa YYYY-MM-DD")
                sys.exit(1)
        else:
            fecha_hasta = date.today()

        logger.info(f"📅 Rango personalizado: Desde {fecha_desde} hasta {fecha_hasta}")
    else:
        # Por defecto: últimos 5 años
        fecha_hasta = date.today()
        fecha_desde = fecha_hasta - relativedelta(years=5)
        logger.info(f"📅 Rango default: Desde {fecha_desde} hasta {fecha_hasta} (últimos 5 años)")

    logger.info("")

    # Acumuladores
    total_registros = 0
    resultados = {}

    try:
        # Cargar IPC
        if args.all or args.ipc:
            result = cargar_ipc(fecha_desde, fecha_hasta)
            resultados['ipc'] = result
            total_registros += result['records_saved']

        # Cargar BADLAR
        if args.all or args.badlar:
            result = cargar_badlar(fecha_desde, fecha_hasta)
            resultados['badlar'] = result
            total_registros += result['records_saved']

        # Cargar Tipo de Cambio
        if args.all or args.tipo_cambio:
            result = cargar_tipo_cambio(fecha_desde, fecha_hasta)
            resultados['tipo_cambio'] = result
            total_registros += result['records_saved']

        # Resumen final
        logger.info("=" * 80)
        logger.info("RESUMEN FINAL")
        logger.info("=" * 80)

        for fuente, result in resultados.items():
            logger.info(f"  {fuente.upper():20s}: {result['records_saved']:>6} registros")

        logger.info("-" * 80)
        logger.info(f"  {'TOTAL':20s}: {total_registros:>6} registros")
        logger.info("=" * 80)
        logger.success("\n✅ Carga completada exitosamente!")

    except Exception as e:
        logger.error(f"\n❌ Error durante la carga: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
