"""
Script de gestión del proyecto Mercado Automotor
Facilita tareas comunes de desarrollo y deployment
"""
import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.config.logger import setup_logger
from backend.config.settings import settings
from loguru import logger

setup_logger()


def init_db():
    """Inicializa la base de datos."""
    from backend.utils.database import init_db as _init_db

    logger.info("Inicializando base de datos...")
    try:
        _init_db()
        logger.success("✓ Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"✗ Error inicializando base de datos: {e}")
        sys.exit(1)


def drop_db():
    """Elimina todas las tablas (solo en desarrollo)."""
    from backend.utils.database import drop_db as _drop_db

    if settings.is_production:
        logger.error("✗ No se puede ejecutar drop_db en producción")
        sys.exit(1)

    confirm = input("⚠️  ¿Estás seguro de eliminar todas las tablas? (yes/no): ")
    if confirm.lower() != "yes":
        logger.info("Operación cancelada")
        return

    logger.warning("Eliminando todas las tablas...")
    try:
        _drop_db()
        logger.success("✓ Tablas eliminadas correctamente")
    except Exception as e:
        logger.error(f"✗ Error eliminando tablas: {e}")
        sys.exit(1)


def run_scrapers(source: str = "all"):
    """Ejecuta scrapers."""
    from backend.scrapers import AcaraScraper, AdefaScraper
    from backend.api_clients import BCRAClient, MercadoLibreClient

    logger.info(f"Ejecutando scrapers: {source}")

    if source in ["all", "acara"]:
        logger.info("Ejecutando ACARA scraper...")
        try:
            with AcaraScraper() as scraper:
                result = scraper.scrape()
                logger.info(f"ACARA result: {result}")
        except Exception as e:
            logger.error(f"ACARA error: {e}")

    if source in ["all", "adefa"]:
        logger.info("Ejecutando ADEFA scraper...")
        try:
            with AdefaScraper() as scraper:
                result = scraper.scrape()
                logger.info(f"ADEFA result: {result}")
        except Exception as e:
            logger.error(f"ADEFA error: {e}")

    if source in ["all", "bcra"]:
        logger.info("Ejecutando BCRA sync...")
        try:
            client = BCRAClient()
            result = client.sync_all_indicators()
            logger.info(f"BCRA result: {result}")
        except Exception as e:
            logger.error(f"BCRA error: {e}")

    if source in ["all", "mercadolibre", "meli"]:
        logger.info("Ejecutando MercadoLibre scraper...")
        try:
            client = MercadoLibreClient()
            result = client.scrape_market_snapshot()
            logger.info(f"MercadoLibre result: {result}")
        except Exception as e:
            logger.error(f"MercadoLibre error: {e}")

    logger.success("✓ Scrapers ejecutados")


def run_api():
    """Ejecuta la API FastAPI."""
    import uvicorn
    from backend.main import app

    logger.info("Iniciando API FastAPI...")
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )


def run_dashboard():
    """Ejecuta el dashboard Streamlit."""
    import subprocess

    logger.info("Iniciando dashboard Streamlit...")
    subprocess.run([
        "streamlit", "run", "frontend/app.py",
        "--server.port", str(settings.streamlit_server_port),
        "--server.address", settings.streamlit_server_address
    ])


def cargar_datos_macro(tipo: str = "all", historico: bool = False):
    """Carga datos macroeconómicos (IPC, BADLAR, Tipo de Cambio)."""
    from datetime import date
    from dateutil.relativedelta import relativedelta
    from backend.api_clients.indec_client import INDECClient
    from backend.api_clients.bcra_client import BCRAClient

    logger.info(f"Cargando datos macroeconómicos: {tipo}")

    # Determinar rango de fechas
    if historico:
        fecha_desde = date(2016, 1, 1)
        fecha_hasta = date.today()
        logger.info(f"📅 Modo histórico: Desde {fecha_desde} hasta {fecha_hasta}")
    else:
        fecha_hasta = date.today()
        fecha_desde = fecha_hasta - relativedelta(years=5)
        logger.info(f"📅 Últimos 5 años: Desde {fecha_desde} hasta {fecha_hasta}")

    total_registros = 0

    # Cargar IPC
    if tipo in ["all", "ipc"]:
        logger.info("\n" + "="*60)
        logger.info("CARGANDO IPC (INDEC)")
        logger.info("="*60)
        try:
            client = INDECClient()
            result = client.sync_ipc(fecha_desde, fecha_hasta)
            logger.success(f"✓ IPC: {result['records_saved']} registros guardados")
            total_registros += result['records_saved']
        except Exception as e:
            logger.error(f"✗ Error cargando IPC: {e}")

    # Cargar BADLAR
    if tipo in ["all", "badlar"]:
        logger.info("\n" + "="*60)
        logger.info("CARGANDO BADLAR (BCRA)")
        logger.info("="*60)
        try:
            client = BCRAClient()
            result = client.sync_badlar(fecha_desde, fecha_hasta)
            logger.success(f"✓ BADLAR: {result['records_saved']} registros guardados")
            total_registros += result['records_saved']
        except Exception as e:
            logger.error(f"✗ Error cargando BADLAR: {e}")

    # Cargar Tipo de Cambio
    if tipo in ["all", "tipo_cambio", "tc"]:
        logger.info("\n" + "="*60)
        logger.info("CARGANDO TIPO DE CAMBIO (BCRA)")
        logger.info("="*60)
        try:
            client = BCRAClient()
            result = client.sync_tipo_cambio(fecha_desde, fecha_hasta)
            logger.success(f"✓ Tipo de Cambio: {result['records_saved']} registros guardados")
            total_registros += result['records_saved']
        except Exception as e:
            logger.error(f"✗ Error cargando Tipo de Cambio: {e}")

    logger.info("\n" + "="*60)
    logger.success(f"✅ TOTAL: {total_registros} registros guardados")
    logger.info("="*60)


def expandir_ipc_diario_cmd(export_excel: str = None):
    """Expande IPC mensual a diario y opcionalmente exporta a Excel."""
    import subprocess

    cmd = ["python", "backend/scripts/expandir_ipc_diario.py"]

    if export_excel:
        cmd.extend(["--export-excel", export_excel])

    subprocess.run(cmd)


def calcular_indicadores_cmd(export_excel: str = None, fecha_desde: str = None, limpiar: bool = False):
    """Calcula indicadores macroeconómicos derivados."""
    import subprocess

    cmd = ["python", "backend/scripts/calcular_indicadores_macro.py"]

    if export_excel:
        cmd.extend(["--export-excel", export_excel])

    if fecha_desde:
        cmd.extend(["--fecha-desde", fecha_desde])

    if limpiar:
        cmd.append("--limpiar")

    subprocess.run(cmd)


def show_stats():
    """Muestra estadísticas de la base de datos."""
    from backend.utils.database import get_db
    from backend.models import Patentamiento, Produccion, BCRAIndicador, MercadoLibreListing, IPC, IPCDiario, BADLAR, TipoCambio, IndicadorCalculado

    logger.info("Obteniendo estadísticas de la base de datos...")

    with get_db() as db:
        stats = {
            "Patentamientos": db.query(Patentamiento).count(),
            "Producción": db.query(Produccion).count(),
            "BCRA Indicadores": db.query(BCRAIndicador).count(),
            "MercadoLibre Listings": db.query(MercadoLibreListing).count(),
            "IPC (mensual)": db.query(IPC).count(),
            "IPC Diario": db.query(IPCDiario).count(),
            "BADLAR": db.query(BADLAR).count(),
            "Tipo de Cambio": db.query(TipoCambio).count(),
            "Indicadores Calculados": db.query(IndicadorCalculado).count(),
        }

    logger.info("📊 Estadísticas de la base de datos:")
    for table, count in stats.items():
        logger.info(f"  - {table}: {count:,} registros")

    # Mostrar desglose de indicadores calculados
    if stats["Indicadores Calculados"] > 0:
        logger.info("\n📈 Indicadores Calculados (desglose):")
        indicadores_desglose = db.query(
            IndicadorCalculado.indicador,
            db.func.count(IndicadorCalculado.id).label('count')
        ).group_by(IndicadorCalculado.indicador).all()

        for indicador, count in indicadores_desglose:
            logger.info(f"  - {indicador}: {count:,} registros")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Script de gestión del proyecto Mercado Automotor"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # init-db
    subparsers.add_parser("init-db", help="Inicializar base de datos")

    # drop-db
    subparsers.add_parser("drop-db", help="Eliminar todas las tablas (solo dev)")

    # run-scrapers
    parser_scrapers = subparsers.add_parser("run-scrapers", help="Ejecutar scrapers")
    parser_scrapers.add_argument(
        "--source",
        choices=["all", "acara", "adefa", "bcra", "mercadolibre", "meli"],
        default="all",
        help="Fuente a scrapear"
    )

    # run-api
    subparsers.add_parser("run-api", help="Ejecutar API FastAPI")

    # run-dashboard
    subparsers.add_parser("run-dashboard", help="Ejecutar dashboard Streamlit")

    # stats
    subparsers.add_parser("stats", help="Mostrar estadísticas de la BD")

    # cargar-macro
    parser_macro = subparsers.add_parser("cargar-macro", help="Cargar datos macroeconómicos")
    parser_macro.add_argument(
        "--tipo",
        choices=["all", "ipc", "badlar", "tipo_cambio", "tc"],
        default="all",
        help="Tipo de datos a cargar"
    )
    parser_macro.add_argument(
        "--historico",
        action="store_true",
        help="Cargar datos históricos desde 2016"
    )

    # expandir-ipc-diario
    parser_ipc_diario = subparsers.add_parser("expandir-ipc-diario", help="Expandir IPC mensual a diario")
    parser_ipc_diario.add_argument(
        "--export-excel",
        type=str,
        help="Nombre del archivo Excel a exportar (ej: ipc_diario.xlsx)"
    )

    # calcular-indicadores
    parser_indicadores = subparsers.add_parser("calcular-indicadores", help="Calcular indicadores macroeconómicos derivados")
    parser_indicadores.add_argument(
        "--export-excel",
        type=str,
        help="Nombre del archivo Excel a exportar (ej: indicadores_macro.xlsx)"
    )
    parser_indicadores.add_argument(
        "--fecha-desde",
        type=str,
        help="Fecha desde la cual calcular (YYYY-MM-DD)"
    )
    parser_indicadores.add_argument(
        "--limpiar",
        action="store_true",
        help="Limpiar indicadores anteriores antes de calcular"
    )

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "drop-db":
        drop_db()
    elif args.command == "run-scrapers":
        run_scrapers(args.source)
    elif args.command == "run-api":
        run_api()
    elif args.command == "run-dashboard":
        run_dashboard()
    elif args.command == "stats":
        show_stats()
    elif args.command == "cargar-macro":
        cargar_datos_macro(args.tipo, args.historico)
    elif args.command == "expandir-ipc-diario":
        expandir_ipc_diario_cmd(args.export_excel)
    elif args.command == "calcular-indicadores":
        calcular_indicadores_cmd(args.export_excel, args.fecha_desde, args.limpiar)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
